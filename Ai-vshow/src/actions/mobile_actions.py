# src/actions/mobile_actions.py

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from ..drivers.appium_driver import driver_manager
from ..drivers.element_handler import parse_bounds
from selenium.common.exceptions import TimeoutException, WebDriverException
import time

def click_by_text(text: str, timeout: int = 10) -> bool:
    """
    尝试点击指定文本的元素，并带有智能等待。
    """
    drv = driver_manager.driver
    selectors = [
        f'new UiSelector().text("{text}")',
        f'new UiSelector().textContains("{text}")',
        f'new UiSelector().description("{text}")',
        f'new UiSelector().descriptionContains("{text}")',
    ]

    for sel in selectors:
        try:
            element = WebDriverWait(drv, timeout).until(
                EC.element_to_be_clickable(("android uiautomator", sel))
            )
            element.click()
            return True
        except Exception:
            continue
    return False


def click_by_id(resource_id: str, timeout: int = 10, retries: int = 3):
    """
    带重试机制的点击 by id
    """
    drv = driver_manager.driver
    for attempt in range(retries):
        try:
            print(f"   -> 尝试第 {attempt + 1} 次查找并点击 ID: {resource_id}")
            element = WebDriverWait(drv, timeout).until(
                EC.element_to_be_clickable(("id", resource_id))
            )
            element.click()
            return True
        except (TimeoutException, WebDriverException) as e:
            print(f"   -> 尝试失败: {repr(e)}")
            if attempt < retries - 1:
                time.sleep(1) # 等待1秒后重试
                continue
            else:
                raise RuntimeError(f"在 {retries} 次重试后仍无法点击元素: {resource_id}") from e


def click_by_xpath(xpath: str, timeout: int = 10):
    drv = driver_manager.driver
    element = WebDriverWait(drv, timeout).until(
        EC.element_to_be_clickable(("xpath", xpath))
    )
    element.click()


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


def try_focus_and_type(text: str, timeout: int = 10):
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
            el = WebDriverWait(drv, timeout).until(
                EC.element_to_be_clickable(
                    ("android uiautomator", f'new UiSelector().className("{class_name}")')
                )
            )
            el.click()
            time.sleep(0.5)
            el.send_keys(text)
            return
        except Exception:
            pass
    raise RuntimeError("未找到可输入的输入框")