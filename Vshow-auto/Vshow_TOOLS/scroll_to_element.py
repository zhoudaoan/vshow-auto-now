import time
import logging
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from appium.webdriver.common.appiumby import AppiumBy

logger = logging.getLogger(__name__)


def scroll_to_element(
        driver,
        locator: tuple,
        direction: str = "up",
        max_swipes: int = 5,
        swipe_duration: int = 600,
        wait_after_swipe: float = 1.0,
        timeout_per_check: float = 3.0,
        screenshot_on_failure: bool = True
):
    """
    滚动查找元素并安全点击（推荐直接使用此函数）

    :param driver: Appium WebDriver 实例
    :param locator: 元素定位器，例如 (AppiumBy.ID, "com.example:id/tvContent")
    :param direction: 滑动方向，"up"（默认）或 "down"
    :param max_swipes: 最大滑动次数
    :param swipe_duration: 滑动持续时间（毫秒）
    :param wait_after_swipe: 滑动后等待时间（秒）
    :param timeout_per_check: 每次查找元素的超时（秒）
    :param screenshot_on_failure: 失败时是否截图
    :return: None
    :raises: TimeoutException 如果未找到或不可点击
    """
    logger.info(f"🔍 开始滚动查找并点击元素: {locator}")

    element = _scroll_to_element_internal(
        driver=driver,
        locator=locator,
        direction=direction,
        max_swipes=max_swipes,
        swipe_duration=swipe_duration,
        wait_after_swipe=wait_after_swipe,
        timeout_per_check=timeout_per_check,
        screenshot_on_failure=screenshot_on_failure
    )

    # 确保元素可点击（双重保险）
    logger.info("⏳ 等待元素变为可点击状态...")
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(locator))

    # 执行点击
    logger.info(
        f"🖱️ 执行点击操作 (text='{element.text}', displayed={element.is_displayed()}, enabled={element.is_enabled()})")
    element.click()
    logger.info("✅ 点击成功")


def _scroll_to_element_internal(
        driver,
        locator: tuple,
        direction: str = "up",
        max_swipes: int = 5,
        swipe_duration: int = 600,
        wait_after_swipe: float = 1.0,
        timeout_per_check: float = 3.0,
        screenshot_on_failure: bool = True
):
    """内部滚动查找函数（使用 element_to_be_clickable 保证可交互）"""
    logger.info(f"🔍 开始滑动查找元素: {locator}，方向: {direction}，最多 {max_swipes} 次")

    for attempt in range(1, max_swipes + 1):
        try:
            element = WebDriverWait(driver, timeout_per_check).until(
                EC.element_to_be_clickable(locator)
            )
            logger.info(f"✅ 第 {attempt} 次尝试：成功找到可点击元素！")
            return element

        except TimeoutException:
            logger.warning(f"第 {attempt}/{max_swipes} 次：未找到可点击元素，准备滑动...")

            if attempt == max_swipes:
                break

            # 执行滑动
            if direction == "up":
                _swipe_up(driver, duration=swipe_duration)
            elif direction == "down":
                _swipe_down(driver, duration=swipe_duration)
            else:
                raise ValueError("direction 必须是 'up' 或 'down'")

            time.sleep(wait_after_swipe)

    # 所有尝试失败
    error_msg = f"❌ 滑动 {max_swipes} 次后仍未找到可点击元素: {locator}"
    logger.error(error_msg)

    if screenshot_on_failure:
        screenshot_name = f"scroll_not_found_{int(time.time())}.png"
        driver.save_screenshot(screenshot_name)
        logger.info(f"📸 已保存失败截图: {screenshot_name}")

    raise TimeoutException(error_msg)


# ===== 私有滑动函数（保持不变）=====

def _swipe_up(driver, duration=600):
    size = driver.get_window_size()
    start_x = size['width'] // 2
    start_y = size['height'] * 0.8
    end_y = size['height'] * 0.3
    driver.swipe(start_x, start_y, start_x, end_y, duration)


def _swipe_down(driver, duration=600):
    size = driver.get_window_size()
    start_x = size['width'] // 2
    start_y = size['height'] * 0.3
    end_y = size['height'] * 0.8
    driver.swipe(start_x, start_y, start_x, end_y, duration)


def pull_to_refresh(driver, duration_ms: int = 1500):
    """
    模拟下拉刷新操作（兼容 Appium Python Client v3+）
    :param driver: Appium WebDriver 实例
    :param duration_ms: 拖拽持续时间（毫秒）
    """
    logger.info("🔄 执行下拉刷新操作...")

    size = driver.get_window_size()
    start_x = size['width'] / 2
    start_y = size['height'] * 0.15  # 起点靠近顶部
    end_y = size['height'] * 0.6     # 下拉到中部

    # 创建 PointerInput
    finger = PointerInput(interaction.POINTER_TOUCH, "finger")

    # 使用 ActionBuilder 正确方式（v3+）
    action = ActionBuilder(driver, finger)
    action.pointer_action.move_to_location(start_x, start_y)
    action.pointer_action.pointer_down()
    action.pointer_action.pause(duration_ms / 1000)  # 持续时间（秒）
    action.pointer_action.move_to_location(start_x, end_y)
    action.pointer_action.release()
    action.perform()