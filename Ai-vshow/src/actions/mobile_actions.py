import time
import traceback
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, \
    WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from ..drivers.appium_driver import driver_manager
from ..utils.logger import logger
from ..drivers.element_handler import bounds_to_center

# --- 关键修复：使用 driver_manager.driver 获取 driver ---
def _get_driver():
    """安全获取 driver 实例"""
    try:
        return driver_manager.driver
    except Exception as e:
        raise RuntimeError(f"无法获取 Appium Driver: {repr(e)}")


def _is_click_retryable(exception: Exception) -> bool:
    """判断点击失败是否值得重试"""
    msg = str(exception).lower()
    retry_keywords = [
        "not clickable",
        "not interactable",
        "would receive the click",
        "element is not visible",
        "stale element",
        "unable to click",
        "element could not be scrolled into view",
        "other element would receive the click",
    ]
    return any(kw in msg for kw in retry_keywords)


def _robust_click(element: WebElement, max_retries: int = 2) -> bool:
    """安全点击：支持重试 + 指数退避 + 精准异常捕获"""
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            element.click()
            return True
        except WebDriverException as e:
            last_exception = e
            if _is_click_retryable(e) and attempt < max_retries:
                wait_time = 0.3 * (2 ** attempt)  # 指数退避：0.3s, 0.6s, 1.2s...
                logger.warning(
                    f"      ⚠️ 点击失败（尝试 {attempt+1}/{max_retries+1}），"
                    f"等待 {wait_time:.1f}s 后重试: {type(e).__name__}: {e}"
                )
                time.sleep(wait_time)
                continue
            # 不可重试或已达上限，跳出循环
            break
    # 所有尝试失败，抛出最后一次异常
    if last_exception:
        raise last_exception
    raise WebDriverException("点击失败：未知原因")


def click_by_id(resource_id: str, timeout: int = 10) -> bool:
    """点击指定 resource-id 的元素（智能等待可点击状态）"""
    drv = _get_driver()
    try:
        element = WebDriverWait(drv, timeout).until(
            EC.element_to_be_clickable((AppiumBy.ID, resource_id))
        )
        _robust_click(element)
        logger.info(f"   -> 动作执行成功: Clicked element with ID: {resource_id}")
        return True
    except Exception as e:
        logger.error(f"   -> 尝试失败: {type(e).__name__}({str(e)})")
        raise


def click_by_text(text: str, timeout: int = 10) -> bool:
    """点击指定文本的元素（智能等待可点击状态）"""
    drv = _get_driver()
    try:
        element = WebDriverWait(drv, timeout).until(
            EC.element_to_be_clickable((AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{text}")'))
        )
        _robust_click(element)
        logger.info(f"   -> 动作执行成功: Clicked element with text: {text}")
        return True
    except Exception as e:
        logger.error(f"   -> 尝试失败: {type(e).__name__}({str(e)})")
        raise


def click_by_xpath(xpath: str, timeout: int = 10) -> bool:
    """点击指定 xpath 的元素（智能等待可点击状态）"""
    drv = _get_driver()
    try:
        element = WebDriverWait(drv, timeout).until(
            EC.element_to_be_clickable((AppiumBy.XPATH, xpath))
        )
        _robust_click(element)
        logger.info(f"   -> 动作执行成功: Clicked element with xpath: {xpath}")
        return True
    except Exception as e:
        logger.error(f"   -> 尝试失败: {type(e).__name__}({str(e)})")
        raise


def click_by_bounds(bounds_str: str, timeout: int = 10) -> bool:
    """点击指定 bounds 的中心点"""
    drv = _get_driver()
    try:
        x, y = bounds_to_center(bounds_str)
        drv.tap([(x, y)])
        logger.info(f"   -> 动作执行成功: Tapped at center of bounds: {bounds_str} -> ({x}, {y})")
        return True
    except Exception as e:
        logger.error(f"   -> 尝试失败: {type(e).__name__}({str(e)})")
        raise


def wait_for_seconds(seconds: int) -> bool:
    """等待指定秒数"""
    time.sleep(seconds)
    logger.info(f"   -> 动作执行成功: Waited for {seconds} seconds")
    return True


def perform_back() -> bool:
    """执行返回操作"""
    drv = _get_driver()
    try:
        drv.back()
        logger.info("   -> 动作执行成功: Performed back action")
        return True
    except Exception as e:
        logger.error(f"   -> 尝试失败: {type(e).__name__}({str(e)})")
        raise


def send_content(resource_id: str, text: str, timeout: int = 10) -> bool:
    """
    在指定 resource-id 的输入框中输入文本（智能等待可交互状态）
    """
    drv = _get_driver()
    try:
        element = WebDriverWait(drv, timeout).until(
            EC.element_to_be_clickable((AppiumBy.ID, resource_id))
        )
        element.clear()
        element.send_keys(text)
        logger.info(f"   -> 动作执行成功: Input text '{text}' into element with ID: {resource_id}")
        return True
    except Exception as e:
        logger.error(f"   -> 尝试失败: {type(e).__name__}({str(e)})")
        raise


def perform_swipe(direction: str) -> bool:
    """执行滑动操作"""
    drv = _get_driver()
    try:
        window_size = drv.get_window_size()
        width = window_size['width']
        height = window_size['height']
        start_x, start_y, end_x, end_y = width / 2, height / 2, width / 2, height / 2

        if direction == "up":
            start_y, end_y = height * 0.8, height * 0.2
        elif direction == "down":
            start_y, end_y = height * 0.2, height * 0.8
        elif direction == "left":
            start_x, end_x = width * 0.8, width * 0.2
        elif direction == "right":
            start_x, end_x = width * 0.2, width * 0.8
        else:
            raise ValueError(f"Unknown swipe direction: {direction}")

        drv.swipe(start_x, start_y, end_x, end_y, 500)
        logger.info(f"   -> 动作执行成功: Swiped {direction}")
        return True
    except Exception as e:
        logger.error(f"   -> 尝试失败: {type(e).__name__}({str(e)})")
        raise


def assert_text_exists(expected_text: str, timeout: int = 10) -> bool:
    """
    断言指定的文本存在于当前页面上（使用智能等待）
    """
    drv = _get_driver()
    try:
        WebDriverWait(drv, timeout).until(
            lambda d: expected_text in d.page_source
        )
        logger.info(f"   -> 断言成功: 页面包含文本 '{expected_text}'")
        return True
    except TimeoutException:
        raise AssertionError(f"断言失败: 未在页面上找到文本 '{expected_text}' (超时 {timeout} 秒)")
    except Exception as e:
        logger.error(f"   -> 尝试失败: {type(e).__name__}({str(e)})")
        raise


# --- 自定义动作支持 (Custom Action Support) ---

_CUSTOM_ACTION_REGISTRY = {}


def register_custom_action(name: str):
    def decorator(func):
        if name in _CUSTOM_ACTION_REGISTRY:
            raise ValueError(f"Custom action '{name}' is already registered.")
        _CUSTOM_ACTION_REGISTRY[name] = func
        logger.info(f"Registered custom action: {name}")
        return func
    return decorator


def _execute_custom_action(action_config: dict) -> bool:
    drv = _get_driver()
    action_name = action_config.get("name")
    if not action_name:
        raise ValueError("Custom action missing required 'name' field.")

    params = action_config.get("params", {})

    if action_name not in _CUSTOM_ACTION_REGISTRY:
        raise ValueError(
            f"Custom action '{action_name}' is not registered. Available actions: {list(_CUSTOM_ACTION_REGISTRY.keys())}")

    try:
        logger.info(f"   -> 正在执行自定义动作: {action_name} with params: {params}")
        result = _CUSTOM_ACTION_REGISTRY[action_name](driver=drv, params=params)
        logger.info(f"   -> 自定义动作执行成功: {action_name}")
        return result if result is not None else True
    except Exception as e:
        logger.error(f"   -> 自定义动作执行失败: {action_name}, Error: {repr(e)}\n{traceback.format_exc()}")
        raise


def perform_single_action(action: dict) -> bool:
    """执行单个动作"""
    if "type" not in action:
        raise ValueError(f"Action missing 'type' field: {action}")

    action_type = action["type"]

    # 对于 custom 动作，必须有 value 且为 dict
    if action_type == "custom":
        if "value" not in action:
            raise ValueError("Custom action missing 'value' field")
        value = action["value"]
        if not isinstance(value, dict):
            raise TypeError(f"Custom action 'value' must be a dict, got {type(value).__name__}: {value}")
        return _execute_custom_action(value)

    # 其他动作：value 应为字符串（或可转为字符串）
    if "value" not in action:
        raise ValueError(f"Action '{action_type}' missing 'value' field")
    value = str(action["value"])  # 统一转为字符串，避免 int/float 等问题

    if action_type == "click_id":
        return click_by_id(value)
    elif action_type == "click_text":
        return click_by_text(value)
    elif action_type == "click_xpath":
        return click_by_xpath(value)
    elif action_type == "click_bounds":
        return click_by_bounds(value)
    elif action_type == "wait":
        return wait_for_seconds(int(value))
    elif action_type == "back":
        return perform_back()
    elif action_type == "swipe":
        return perform_swipe(value)
    elif action_type == "assert_text":
        if "||" in value:
            text, to = value.split("||", 1)
            return assert_text_exists(text.strip(), timeout=int(to.strip()))
        else:
            return assert_text_exists(value)
    elif action_type == "send_content":
        if "||" not in value:
            raise ValueError("send_content 的 value 必须为 'resource_id||text' 格式")
        resource_id, text = value.split("||", 1)
        return send_content(resource_id.strip(), text.strip())
    else:
        raise ValueError(f"Unsupported action type: {action_type}")



# --- 自定义动作示例 ---
@register_custom_action("log_current_activity")
def log_current_activity(driver, params: dict):
    current_activity = driver.current_activity
    logger.info(f"[Custom Action] Current Activity: {current_activity}")


@register_custom_action("safe_hide_keyboard")
def safe_hide_keyboard(driver, params: dict = None):
    try:
        if driver.is_keyboard_shown():
            driver.hide_keyboard()
    except Exception as e:
        logger.debug(f"hide_keyboard() 失败，改用点击空白区域: {e}")
        size = driver.get_window_size()
        driver.tap([(size['width'] // 2, size['height'] - 150)], 100)