# src/nodes/executor_node.py
import traceback
from typing import Dict, Any
from ...actions.mobile_actions import perform_single_action


def execute_planned_action(state: Dict[str, Any]) -> dict:
    """执行器节点：按顺序执行 planned_actions 中的动作"""
    print("🤖 执行器节点被调用")
    history = state.get("history", []) or []
    planned_actions = state.get("planned_actions", []) or []
    current_index = state.get("current_step_index", 0)
    executed_actions = state.get("executed_actions", []) or []  # 获取已执行的动作列表
    step_count = state.get("step_count", 0)
    max_steps = state.get("max_steps", 10)
    error_message = None
    is_complete = False

    # 如果没有计划或已执行完所有计划
    if not planned_actions or current_index >= len(planned_actions):
        print("⚠️ 没有可执行的动作或已执行完毕")
        return {
            "executed_actions": executed_actions,
            "current_step_index": current_index,
            "step_count": step_count,
            "error_message": error_message,
            "is_complete": is_complete,
            "history": history + ["No actions to execute"]
        }

    # --- 关键修改：只处理当前索引指向的单个动作 ---
    action = planned_actions[current_index]
    print(f"🤖 第 {current_index + 1} 步，准备执行动作: {action['type']} - {action['value']}")

    try:
        # 执行单个动作
        result = perform_single_action(action)
        print(f"   -> 动作执行成功: {result}")

        # --- 仅在成功时才更新 executed_actions 和 step_count ---
        executed_actions.append(action)
        step_count += 1
        current_index += 1

        # 检查是否完成
        if action.get("type") == "done":
            is_complete = True
            print("✅ 检测到 'done' 动作，任务标记为完成")

    except Exception as e:
        error_msg = f"{action['type']}({action['value']}) -> {repr(e)}"
        print(f"❌ 执行动作失败: {error_msg}")
        error_message = error_msg
        # --- 失败时不增加 step_count 和 current_index ---
        # 留在当前步骤，等待重规划

    return {
        "executed_actions": executed_actions,
        "current_step_index": current_index,  # 下次要执行的索引
        "step_count": step_count,  # 总成功步数
        "error_message": error_message,
        "is_complete": is_complete,
        "history": history + [f"Executed: {action}"]
    }