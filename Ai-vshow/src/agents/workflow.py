from typing import Literal
from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes.screenshot_node import take_screenshot
from .nodes.planner_node import llm_planner
from .nodes.executor_node import execute_planned_action


def should_continue_or_replan(state: AgentState) -> Literal["continue", "replan", "end"]:
    """根据当前状态决定下一步是继续执行、重规划还是结束"""
    error = state.get("error_message")
    planned_actions = state.get("planned_actions", []) or []
    executed_actions = state.get("executed_actions", []) or []
    executed_count = len(executed_actions)
    step_count = state.get("step_count", 0)
    max_steps = state.get("max_steps", 10)

    print("🔍 当前流程判断状态:")
    print(f"   - error_message: {error}")
    print(f"   - planned_actions数量: {len(planned_actions)}")
    print(f"   - executed_actions数量: {executed_count}")
    print(f"   - step_count/max_steps: {step_count}/{max_steps}")

    # 1. 达到最大步数，强制结束
    if step_count >= max_steps:
        print(f"🛑 达到最大步数限制: {max_steps}")
        return "end"

    # 2. 如果没有计划动作，直接结束
    if not planned_actions:
        print("⚠️ 没有可执行的计划动作，结束流程")
        return "end"

    # 3. 如果有 error，但还有未执行动作，优先继续执行（例如 fallback 动作）
    if error and executed_count < len(planned_actions):
        print("⚠️ 存在错误信息，但当前仍有可执行动作，继续执行")
        return "continue"

    # 4. 如果有 error，且动作都执行完了，则进入重规划
    if error and executed_count >= len(planned_actions):
        print("🔄 检测到错误且当前动作已执行完，触发重规划流程")
        return "replan"

    # 5. 如果还有动作没执行完，继续执行
    if executed_count < len(planned_actions):
        print("➡️ 继续执行下一个计划动作")
        return "continue"

    # 6. 如果动作都执行完了，检查最后一步是否 done
    if executed_count >= len(planned_actions):
        last_action = planned_actions[-1] if planned_actions else {}
        if last_action.get("type") == "done":
            print("🏁 检测到结束条件 done，终止循环")
            return "end"

        print("🔄 当前计划动作已执行完毕，但未显式结束，进入重规划")
        return "replan"

    print("⚠️ 未命中任何分支，默认结束")
    return "end"


# 构建工作流
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("initial_screenshot", take_screenshot)
workflow.add_node("plan", llm_planner)
workflow.add_node("execute", execute_planned_action)
workflow.add_node("re_screenshot", take_screenshot)
workflow.add_node("replan", llm_planner)

# 设置入口
workflow.set_entry_point("initial_screenshot")

# 初始流程
workflow.add_edge("initial_screenshot", "plan")
workflow.add_edge("plan", "execute")

# 条件分支：执行后根据状态决定走向
workflow.add_conditional_edges(
    "execute",
    should_continue_or_replan,
    {
        "continue": "execute",
        "replan": "re_screenshot",
        "end": END,
    }
)

# 重规划路径
workflow.add_edge("re_screenshot", "replan")
workflow.add_edge("replan", "execute")

# 编译工作流
app = workflow.compile()