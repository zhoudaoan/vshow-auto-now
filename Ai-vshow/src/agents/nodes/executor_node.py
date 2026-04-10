import time
from typing import Dict, Any, List

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import NoSuchElementException

from ...actions.mobile_actions import (
    click_by_id,
    click_by_xpath,
    click_by_coordinate,
    click_center_of_bounds,
    do_swipe,
    press_back,
    try_focus_and_type,
)
from ...drivers.appium_driver import driver_manager


def execute_planned_action(state: Dict[str, Any]) -> dict:
    planned_actions: List[Dict[str, Any]] = state.get("planned_actions", []) or []
    executed_actions: List[Dict[str, Any]] = state.get("executed_actions", []) or []
    history: List[str] = state.get("history", []) or []

    current_step_index = state.get("current_step_index", 0)
    step_count = state.get("step_count", 0)

    # 所有动作已执行完
    if current_step_index >= len(planned_actions):
        print("🏁 当前计划动作已全部执行完毕")
        return {
            "current_step_index": current_step_index,
            "executed_actions": executed_actions,
            "step_count": step_count,
            "error_message": None,
        }

    action = planned_actions[current_step_index]
    action_type = action.get("type")
    value = action.get("value")
    print(f"🤖 第 {current_step_index + 1} 步，准备执行动作: {action_type} - {value}")

    try:
        if action_type == "click_text":
            drv = driver_manager.driver
            found_and_clicked = False

            # 1. 精确文本匹配
            try:
                element = drv.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().text("{value}")'
                )
                element.click()
                found_and_clicked = True
                print(f" -> 点击精确文本: {value}")
            except NoSuchElementException:
                pass

            # 2. 文本包含匹配
            if not found_and_clicked:
                try:
                    element = drv.find_element(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().textContains("{value}")'
                    )
                    element.click()
                    found_and_clicked = True
                    print(f" -> 点击包含文本: {value}")
                except NoSuchElementException:
                    pass

            # 3. 描述匹配
            if not found_and_clicked:
                try:
                    element = drv.find_element(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().description("{value}")'
                    )
                    element.click()
                    found_and_clicked = True
                    print(f" -> 点击描述文本: {value}")
                except NoSuchElementException:
                    pass

            # 4. “确认类按钮”兜底
            if not found_and_clicked and value in ["确认", "确定", "好的", "是"]:
                confirm_texts = ["确认", "确定", "好的", "是", "OK", "ok", "允许", "同意"]
                for text in confirm_texts:
                    try:
                        element = drv.find_element(
                            AppiumBy.ANDROID_UIAUTOMATOR,
                            f'new UiSelector().textContains("{text}")'
                        )
                        element.click()
                        found_and_clicked = True
                        print(f" -> 点击备选确认文本: {text}")
                        break
                    except NoSuchElementException:
                        continue

            if not found_and_clicked:
                raise RuntimeError(f"未找到文本元素: {value}")

        elif action_type == "click_id":
            click_by_id(value)
            print(f" -> 点击 resource-id: {value}")

        elif action_type == "click_xpath":
            click_by_xpath(value)
            print(f" -> 点击 xpath: {value}")

        elif action_type == "click_coordinate":
            if not isinstance(value, dict) or "x" not in value or "y" not in value:
                raise ValueError(f"click_coordinate 的 value 格式不正确: {value}")
            x, y = value["x"], value["y"]
            click_by_coordinate(x, y)
            print(f" -> 点击坐标: ({x}, {y})")

        elif action_type == "click_bounds":
            click_center_of_bounds(value)
            print(f" -> 点击 bounds 中心: {value}")

        elif action_type == "type_text":
            try_focus_and_type(str(value))
            print(f" -> 输入文本: {value}")

        elif action_type == "swipe":
            do_swipe(value)
            print(f" -> 执行滑动: {value}")

        elif action_type == "back":
            press_back()
            print(" -> 点击返回键")

        elif action_type == "wait":
            seconds = int(value)
            time.sleep(seconds)
            print(f" -> 等待 {seconds} 秒")

        elif action_type == "done":
            print(" -> 任务已完成")
            new_executed_actions = executed_actions + [action]
            new_history = history + [f"执行完成动作: {action_type} - {value}"]
            return {
                "current_step_index": current_step_index + 1,
                "executed_actions": new_executed_actions,
                "step_count": step_count + 1,
                "error_message": None,
                "is_complete": True,
                "history": new_history,
            }

        else:
            raise ValueError(f"未知动作类型: {action_type}")

        new_executed_actions = executed_actions + [action]
        new_history = history + [f"执行动作成功: {action_type} - {value}"]

        return {
            "current_step_index": current_step_index + 1,
            "executed_actions": new_executed_actions,
            "step_count": step_count + 1,
            "error_message": None,
            "history": new_history,
        }

    except Exception as e:
        error_msg = f"{action_type}({value}) -> {repr(e)}"
        print(f"❌ 执行动作失败: {error_msg}")

        new_history = history + [f"执行动作失败: {error_msg}"]

        # 失败时不推进 current_step_index，交给 workflow 决定是否重规划
        return {
            "current_step_index": current_step_index,
            "executed_actions": executed_actions,
            "step_count": step_count + 1,
            "error_message": error_msg,
            "history": new_history,
            "is_complete": False,
        }
