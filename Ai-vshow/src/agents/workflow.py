# src/agents/workflow.py
from typing import Literal
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes.screenshot_node import take_screenshot
from .nodes.planner_node import llm_planner
from .nodes.executor_node import execute_planned_action

def should_continue_or_replan(state: AgentState) -> Literal["continue", "replan", "end"]:
    error = state.get('error_message')
    planned_actions = state.get('planned_actions', [])
    executed_count = len(state.get('executed_actions', []))
    step_count = state.get('step_count', 0)
    max_steps = state.get('max_steps', 10)

    if step_count >= max_steps:
        print(f"🛑 达到最大步数限制: {max_steps}")
        return "end"

    if error:
        print("🔄 检测到执行错误，触发重规划流程")
        return "replan"

    if executed_count >= len(planned_actions):
        last_action = planned_actions[-1] if planned_actions else {}
        if last_action.get('type') == 'done':
            print("🏁 检测到结束条件，终止循环")
            return "end"
        else:
            print("🏁 所有计划动作已执行完毕")
            return "end"

    print("➡️ 继续执行下一个计划动作")
    return "continue"

workflow = StateGraph(AgentState)

workflow.add_node("initial_screenshot", take_screenshot)
workflow.add_node("plan", llm_planner)
workflow.add_node("execute", execute_planned_action)
workflow.add_node("re_screenshot", take_screenshot)
workflow.add_node("replan", llm_planner)

workflow.set_entry_point("initial_screenshot")
workflow.add_edge("initial_screenshot", "plan")
workflow.add_edge("plan", "execute")

workflow.add_conditional_edges(
    "execute",
    should_continue_or_replan,
    {
        "continue": "execute",
        "replan": "re_screenshot",
        "end": END
    }
)

workflow.add_edge("re_screenshot", "replan")
workflow.add_edge("replan", "execute")

app = workflow.compile()