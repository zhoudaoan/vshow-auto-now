from typing import Union
from selenium.webdriver.remote.webdriver import WebDriver
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class Direction(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

def swipe_(
    driver: WebDriver,
    direction: Union[str, Direction],
    distance_pct: float = 0.5
) -> None:
    """
    在 Android 真机上执行滑动操作（兼容当前 Appium UiAutomator2）

    注意：
      - 使用屏幕尺寸动态计算起始/结束坐标
      - 不依赖 Appium 2+ 的简化 swipeGesture 语法
      - 兼容所有主流 Appium 版本
    """
    # 标准化方向
    if isinstance(direction, Direction):
        dir_str = direction.value
    else:
        dir_str = str(direction).lower()

    if dir_str not in {'up', 'down', 'left', 'right'}:
        raise ValueError("direction 必须是 'up', 'down', 'left', 'right' 或对应的 Direction 枚举")

    # 获取屏幕尺寸
    window_size = driver.get_window_size()
    width = window_size['width']
    height = window_size['height']

    # 安全边界：避免状态栏/导航栏干扰（取中间 80% 区域）
    margin_x = width * 0.1
    margin_y = height * 0.1
    safe_width = width - 2 * margin_x
    safe_height = height - 2 * margin_y
    center_x = width / 2
    center_y = height / 2

    # 限制 distance_pct 在合理范围
    percent = max(0.1, min(1.0, distance_pct))

    # 计算滑动距离
    if dir_str in ('left', 'right'):
        distance = safe_width * percent
        start_y = end_y = center_y
        if dir_str == 'left':
            start_x = center_x + distance / 2
            end_x = center_x - distance / 2
        else:  # right
            start_x = center_x - distance / 2
            end_x = center_x + distance / 2
    else:  # up / down
        distance = safe_height * percent
        start_x = end_x = center_x
        if dir_str == 'up':
            start_y = center_y + distance / 2
            end_y = center_y - distance / 2
        else:  # down
            start_y = center_y - distance / 2
            end_y = center_y + distance / 2

    # 转为整数坐标
    start_x, start_y = int(start_x), int(start_y)
    end_x, end_y = int(end_x), int(end_y)

    # 执行滑动（使用原生 swipe，兼容性最好）
    try:
        driver.swipe(start_x, start_y, end_x, end_y, duration=300)
        logger.info(f"Swiped {dir_str} with {percent * 100:.0f}% of screen: "
                    f"from ({start_x}, {start_y}) to ({end_x}, {end_y})")
    except Exception as e:
        logger.error(f"Swipe failed on Android: {e}")
        raise