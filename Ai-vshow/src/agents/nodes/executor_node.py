# src/agents/nodes/executor_node.py
import time
import traceback
from typing import Dict, Any
from ...actions.mobile_actions import (
    click_by_text, click_by_id, click_by_xpath, click_by_coordinate,
    click_center_of_bounds, do_swipe, press_back, try_focus_and_type
)
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import NoSuchElementException
from ...drivers.appium_driver import driver_manager

def execute_planned_action(state: Dict[str, Any]) -> dict:
    planned_actions = state.get("planned_actions", [])
    current_step_index = state.get("current_step_index", 0)

    # 如果所有动作都已执行完毕
    if current_step_index >= len(planned_actions):
        return {"current_step_index": current_step_index, "error_message": None}

    action = planned_actions[current_step_index]
    action_type = action["type"]
    value = action["value"]
    print(f"🤖 第 {current_step_index + 1} 步，准备执行动作: {action_type} - {value}")

    try:
        if action_type == "click_text":
            # --- 增强版 click_text ---
            drv = driver_manager.driver
            found_and_clicked = False

            # 尝试 1: 精确文本匹配
            try:
                element = drv.find_element(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{value}")')
                element.click()
                found_and_clicked = True
                print(f" -> 点击精确文本: {value}")
            except NoSuchElementException:
                pass

            # 尝试 2: 文本包含匹配 (最常用)
            if not found_and_clicked:
                try:
                    element = drv.find_element(AppiumBy.ANDROID_UIAUTOMATOR,
                                               f'new UiSelector().textContains("{value}")')
                    element.click()
                    found_and_clicked = True
                    print(f" -> 点击包含文本: {value}")
                except NoSuchElementException:
                    pass

            # 尝试 3: 描述匹配 (accessibility id)
            if not found_and_clicked:
                try:
                    element = drv.find_element(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().description("{value}")')
                    element.click()
                    found_and_clicked = True
                    print(f" -> 点击描述文本: {value}")
                except NoSuchElementException:
                    pass

            # 尝试 4: 针对“确认”类按钮的特殊处理
            if not found_and_clicked and value in ["确认", "确定", "好的", "是"]:
                confirm_texts = ["确认", "确定", "好的", "是", "OK", "ok", "允许", "同意"]
                for text in confirm_texts:
                    try:
                        element = drv.find_element(AppiumBy.ANDROID_UIAUTOMATOR,
                                                   f'new UiSelector().textContains("{text}")')
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
            x, y = value["x"], value["y"]
            click_by_coordinate(x, y)
            print(f" -> 点击坐标: ({x}, {y})")
        elif action_type == "click_bounds":
            click_center_of_bounds(value)
            print(f" -> 点击 bounds 中心: {value}")
        elif action_type == "type_text":
            try_focus_and_type(value)
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
        else:
            print(f"⚠️ 未知动作类型: {action_type}")

        # --- 关键修复：确保成功后 index 一定递增 ---
        return {
            "current_step_index": current_step_index + 1,
            "error_message": None
        }

    except Exception as e:
        error_msg = f"{action_type}({value}) -> {repr(e)}"
        print(f"❌ 执行动作失败: {error_msg}")
        # 失败时保持当前 index 不变，以便重规划
        return {
            "current_step_index": current_step_index,
            "error_message": error_msg
        }