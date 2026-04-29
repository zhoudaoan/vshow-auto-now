import time
import traceback
from typing import Optional
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, \
    WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..drivers.appium_driver import driver_manager
from ..utils.logger import logger


# --- 关键修复：使用 driver_manager.driver 获取 driver ---
def _get_driver():
    """安全获取 driver 实例"""
    try:
        return driver_manager.driver
    except Exception as e:
        raise RuntimeError(f"无法获取 Appium Driver: {repr(e)}")


def _is_element_visible_and_sized(element) -> bool:
    """
    辅助函数：判断元素是否真正可见且有有效尺寸
    """
    try:
        # 检查 is_displayed 是否为 True
        if not element.is_displayed():
            return False
        # 检查元素尺寸是否有效 (宽高都大于0)
        size = element.size
        if size.get('width', 0) <= 0 or size.get('height', 0) <= 0:
            return False
        return True
    except Exception:
        # 如果任何检查失败，认为元素不可见
        return False


def click_by_id(resource_id: str, timeout: int = 10) -> bool:
    """
    点击指定 resource-id 的元素，并确保它是可见的
    """
    drv = _get_driver()  # ✅ 正确获取 driver
    try:
        # 使用 WebDriverWait 等待元素出现
        elements = WebDriverWait(drv, timeout).until(
            lambda d: d.find_elements(AppiumBy.ID, resource_id)
        )

        # 过滤出真正可见且尺寸有效的元素
        visible_elements = [e for e in elements if _is_element_visible_and_sized(e)]

        if not visible_elements:
            raise TimeoutException(f"No VISIBLE element found for ID: {resource_id}")

        # 点击第一个可见元素
        element = visible_elements[0]
        element.click()
        logger.info(f"   -> 动作执行成功: Clicked VISIBLE element with ID: {resource_id}")
        return True

    except Exception as e:
        logger.error(f"   -> 尝试失败: {type(e).__name__}({str(e)})")
        raise


def click_by_text(text: str, timeout: int = 10) -> bool:
    """点击指定文本的元素"""
    drv = _get_driver()
    try:
        element = WebDriverWait(drv, timeout).until(
            EC.element_to_be_clickable((AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{text}")'))
        )
        element.click()
        logger.info(f"   -> 动作执行成功: Clicked element with text: {text}")
        return True
    except Exception as e:
        logger.error(f"   -> 尝试失败: {type(e).__name__}({str(e)})")
        raise


def click_by_xpath(xpath: str, timeout: int = 10) -> bool:
    """点击指定 xpath 的元素"""
    drv = _get_driver()
    try:
        element = WebDriverWait(drv, timeout).until(
            EC.element_to_be_clickable((AppiumBy.XPATH, xpath))
        )
        element.click()
        logger.info(f"   -> 动作执行成功: Clicked element with xpath: {xpath}")
        return True
    except Exception as e:
        logger.error(f"   -> 尝试失败: {type(e).__name__}({str(e)})")
        raise


def click_by_bounds(bounds_str: str, timeout: int = 10) -> bool:
    """点击指定 bounds 的中心点"""
    drv = _get_driver()
    try:
        from ..utils.element_handler import bounds_to_center
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
    在指定 resource-id 的输入框中输入文本。
    会先点击该元素以聚焦，然后清除原有内容并输入新文本。
    """
    drv = _get_driver()
    try:
        # 等待元素出现并可点击
        elements = WebDriverWait(drv, timeout).until(
            lambda d: d.find_elements(AppiumBy.ID, resource_id)
        )

        # 过滤出真正可见且尺寸有效的元素
        visible_elements = [e for e in elements if _is_element_visible_and_sized(e)]

        if not visible_elements:
            raise TimeoutException(f"No VISIBLE element found for ID: {resource_id}")

        element = visible_elements[0]

        element.click()

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


def assert_text_exists(expected_text: str) -> bool:
    """
    断言指定的文本存在于当前页面上。
    如果存在，返回 True；如果不存在，抛出 AssertionError。
    """
    drv = _get_driver()
    try:
        # 获取当前页面的所有文本元素
        all_elements = drv.find_elements(AppiumBy.XPATH, "//*")
        all_texts = []

        for el in all_elements:
            try:
                text = el.text.strip()
                content_desc = el.get_attribute("content-desc") or ""
                if text:
                    all_texts.append(text)
                if content_desc.strip():
                    all_texts.append(content_desc.strip())
            except Exception:
                # 忽略无法读取的元素
                continue

        # 检查期望的文本是否在任何元素中
        for text in all_texts:
            if expected_text in text:
                logger.info(f"   -> 断言成功: 页面包含文本 '{expected_text}'")
                return True

        # 如果未找到，抛出异常
        raise AssertionError(f"断言失败: 未在页面上找到文本 '{expected_text}'. 扫描了 {len(all_texts)} 个文本元素。")

    except Exception as e:
        logger.error(f"   -> 尝试失败: {type(e).__name__}({str(e)})")
        raise


# --- 自定义动作支持 (Custom Action Support) ---

# 1. 定义一个全局字典作为自定义函数的注册表
_CUSTOM_ACTION_REGISTRY = {}


def register_custom_action(name: str):
    """
    装饰器：用于向注册表中注册自定义动作函数。

    使用示例:
        @register_custom_action("my_special_task")
        def my_special_task(driver, params: dict):
            # 您的业务逻辑
            pass
    """

    def decorator(func):
        if name in _CUSTOM_ACTION_REGISTRY:
            raise ValueError(f"Custom action '{name}' is already registered.")
        _CUSTOM_ACTION_REGISTRY[name] = func
        logger.info(f"Registered custom action: {name}")
        return func

    return decorator


def _execute_custom_action(action_config: dict) -> bool:
    """
    执行一个自定义动作。

    :param action_config: 来自JSON的动作定义，必须包含 'name' 键。
        示例: {"type": "custom", "name": "my_special_task", "params": {"arg1": "value1"}}
    :return: 动作执行结果，通常为 True。
    """
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
        # 调用注册的函数，并传入 driver 和 params
        result = _CUSTOM_ACTION_REGISTRY[action_name](driver=drv, params=params)
        logger.info(f"   -> 自定义动作执行成功: {action_name}")
        # 如果您的自定义函数不返回值，我们默认返回 True
        return result if result is not None else True
    except Exception as e:
        logger.error(f"   -> 自定义动作执行失败: {action_name}, Error: {repr(e)}\n{traceback.format_exc()}")
        raise


def perform_single_action(action: dict) -> bool:
    """执行单个动作"""
    action_type = action.get("type")
    value = action.get("value", "")

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
        return assert_text_exists(value)
    elif action_type == "send_content":
        # 约定 value 格式为: "resource_id||text_to_input"
        if "||" not in value:
            raise ValueError("send_content 的 value 必须为 'resource_id||text' 格式")
        resource_id, text = value.split("||", 50)
        return send_content(resource_id.strip(), text.strip())
    # --- 新增：处理自定义动作 ---
    elif action_type == "custom":
        return _execute_custom_action(action)
    else:
        raise ValueError(f"Unsupported action type: {action_type}")


# --- 在此处定义您的自定义动作函数 ---
@register_custom_action("log_current_activity")
def log_current_activity(driver, params: dict):
    """一个简单的自定义动作：记录当前 Activity"""
    current_activity = driver.current_activity
    logger.info(f"[Custom Action] Current Activity: {current_activity}")


@register_custom_action("safe_hide_keyboard")
def safe_hide_keyboard(driver):
    """
    安全收起键盘：优先尝试标准方法，失败则点击空白区域
    """
    try:
        if driver.is_keyboard_shown():
            driver.hide_keyboard()
    except Exception as e:
        logger.debug(f"hide_keyboard() 失败，改用点击空白区域: {e}")
        size = driver.get_window_size()
        driver.tap([(size['width'] // 2, size['height'] - 150)], 100)
