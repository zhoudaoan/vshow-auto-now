# src/agents/nodes/executor_node.py
import time
import traceback
from typing import Dict, Any
from ...actions.mobile_actions import (
    click_by_text, click_by_id, click_by_xpath, click_by_coordinate,
    click_center_of_bounds, do_swipe, press_back, try_focus_and_type
)


def execute_planned_action(state: Dict[str, Any]) -> dict:
    planned_actions = state.get('planned_actions', [])
    executed_count = len(state.get('executed_actions', []))
    step_count = executed_count + 1

    if executed_count >= len(planned_actions):
        return {
            "error_message": "没有更多计划动作可执行。",
            "step_count": step_count
        }

    next_action = planned_actions[executed_count]
    action_type = next_action.get("type")
    value = next_action.get("value")
    print(f"🤖 第 {step_count} 步，准备执行动作: {action_type} - {value}")

    try:
        time.sleep(1)
        if action_type == "click_text":
            if not value:
                raise ValueError("click_text 缺少 value")
            print(f" -> 点击文本: {value}")
            ok = click_by_text(str(value))
            if not ok:
                raise RuntimeError(f"未找到文本元素: {value}")

        elif action_type == "click_id":
            if not value:
                raise ValueError("click_id 缺少 value")
            print(f" -> 点击 resource-id: {value}")
            click_by_id(str(value))

        elif action_type == "click_xpath":
            if not value:
                raise ValueError("click_xpath 缺少 value")
            print(f" -> 点击 xpath: {value}")
            click_by_xpath(str(value))

        elif action_type == "click_coordinate":
            if not isinstance(value, dict) or "x" not in value or "y" not in value:
                raise ValueError("click_coordinate 的 value 必须包含 x/y")
            x, y = int(value["x"]), int(value["y"])
            print(f" -> 点击坐标: ({x}, {y})")
            click_by_coordinate(x, y)

        elif action_type == "click_bounds":
            if not value:
                raise ValueError("click_bounds 缺少 value")
            print(f" -> 点击 bounds 中心: {value}")
            click_center_of_bounds(str(value))

        elif action_type == "type_text":
            if value is None:
                raise ValueError("type_text 缺少 value")
            print(f" -> 输入文本: {value}")
            try_focus_and_type(str(value))

        elif action_type == "swipe":
            if value not in ["up", "down", "left", "right"]:
                raise ValueError("swipe 的 value 必须是 up/down/left/right")
            print(f" -> 执行滑动: {value}")
            do_swipe(str(value))

        elif action_type == "back":
            print(" -> 执行返回")
            press_back()

        elif action_type == "wait":
            seconds = int(value) if value else 2
            print(f" -> 等待 {seconds} 秒")
            time.sleep(seconds)

        elif action_type == "done":
            print("✅ 任务标记为完成")
            return {
                "is_complete": True,
                "executed_actions": state.get('executed_actions', []) + [next_action],
                "step_count": step_count,
                "history": state["history"] + [f"Done: {value}"]
            }

        else:
            raise ValueError(f"未知动作类型: {action_type}")

        new_executed = state.get('executed_actions', []) + [next_action]
        return {
            "executed_actions": new_executed,
            "history": state["history"] + [f"Executed: {action_type}({value})"],
            "step_count": step_count,
            "error_message": None
        }

    except Exception as e:
        error_msg = f"执行动作失败: {action_type}({value}) -> {repr(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return {
            "history": state["history"] + [error_msg],
            "step_count": step_count,
            "error_message": error_msg
        }