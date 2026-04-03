# src/actions/mobile_actions.py
import time
import traceback
from typing import Dict, Any
from appium.webdriver.common.appiumby import AppiumBy
from ..config.settings import settings
from ..drivers.appium_driver import driver_manager
from ..drivers.element_handler import parse_bounds

def click_by_text(text: str) -> bool:
    drv = driver_manager.driver
    selectors = [
        f'new UiSelector().text("{text}")',
        f'new UiSelector().textContains("{text}")',
        f'new UiSelector().description("{text}")',
        f'new UiSelector().descriptionContains("{text}")',
    ]
    for sel in selectors:
        try:
            drv.find_element(AppiumBy.ANDROID_UIAUTOMATOR, sel).click()
            return True
        except Exception:
            pass
    return False

def click_by_id(resource_id: str):
    drv = driver_manager.driver
    drv.find_element(AppiumBy.ID, resource_id).click()

def click_by_xpath(xpath: str):
    drv = driver_manager.driver
    drv.find_element(AppiumBy.XPATH, xpath).click()

def click_by_coordinate(x: int, y: int):
    drv = driver_manager.driver
    drv.execute_script("mobile: clickGesture", {"x": int(x), "y": int(y)})

def click_center_of_bounds(bounds: str):
    parsed = parse_bounds(bounds)
    if not parsed:
        raise ValueError(f"非法 bounds: {bounds}")
    click_by_coordinate(parsed["center_x"], parsed["center_y"])

def do_swipe(direction: str):
    drv = driver_manager.driver
    size = drv.get_window_size()
    width = size["width"]
    height = size["height"]
    drv.execute_script(
        "mobile: swipeGesture",
        {
            "left": int(width * 0.1),
            "top": int(height * 0.1),
            "width": int(width * 0.8),
            "height": int(height * 0.8),
            "direction": direction,
            "percent": 0.7
        }
    )

def press_back():
    driver_manager.driver.back()

def try_focus_and_type(text: str):
    drv = driver_manager.driver
    try:
        el = drv.switch_to.active_element
        el.send_keys(text)
        return
    except Exception:
        pass

    editable_classes = ["android.widget.EditText"]
    for class_name in editable_classes:
        try:
            el = drv.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().className("{class_name}")'
            )
            el.click()
            time.sleep(0.5)
            el.send_keys(text)
            return
        except Exception:
            pass
    raise RuntimeError("未找到可输入的输入框")