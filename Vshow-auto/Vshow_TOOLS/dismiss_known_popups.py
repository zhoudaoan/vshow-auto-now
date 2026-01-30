from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    WebDriverException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    NoSuchElementException
)

logger = logging.getLogger(__name__)

# ==============================
# 已知弹窗关闭方式（按常见程度排序）
# ==============================
POPUP_CLOSE_BUTTONS = [
    (AppiumBy.ID, "com.baitu.qingshu:id/iv_close", "右上角X"),
    (AppiumBy.ID, "com.baitu.qingshu:id/btn_close", "关闭按钮"),
    (AppiumBy.XPATH, "//*[@text='我知道了']", "我知道了"),
    # (AppiumBy.XPATH, "//*[@text='取消']", "取消"),
    # (AppiumBy.XPATH, "//*[@text='不再提示']//following-sibling::*[@text='确定']", "不再提示+确定"),
    # (AppiumBy.ID, "android:id/button2", "系统弹窗-取消"),
    (AppiumBy.XPATH, '//android.view.View[@resource-id="main"]/android.view.View/android.view.View[2]/android.view.View/android.view.View[4]', "召回弹窗的关闭"),
]

# ==============================
# 弹窗关键词（中英文混合，覆盖 H5 弹窗）
# ==============================
POPUP_INDICATORS = [
    # 中文
    "新人", "福利", "活动", "领取", "限时", "恭喜", "开启", "奖励", "提示", "通知", "邀请",
    "立即", "免费", "红包", "任务", "完成", "专属", "礼包", "弹窗", "我知道了", "确定",
    # 英文（关键！覆盖你的 POPPo LIVE 等 H5 弹窗）
    "LIVE", "POPPO", "popup", "close", "x", "cancel", "ok", "got it", "reward", "claim",
    "congrats", "welcome", "new user", "POPPO LIVE", "bonus", "gift", "tap to", "dismiss"
]


def is_popup_likely_present(driver) -> bool:
    """智能判断是否可能有弹窗：
       - 包含关键词
       - 或存在非主页面的 WebView（如 H5 弹窗）
    """
    try:
        source = driver.page_source

        # 1. 检查关键词
        if any(kw in source for kw in POPUP_INDICATORS):
            return True

        # 2. 检查是否存在 WebView（且内容疑似弹窗）
        webviews = driver.find_elements(AppiumBy.CLASS_NAME, "android.webkit.WebView")
        for wv in webviews:
            try:
                text = wv.text
                if text and ("LIVE" in text or "POPPo" in text or len(text.strip()) < 100):
                    # 简单启发：文本短 + 含关键词 → 很可能是弹窗
                    return True
            except Exception:
                continue
        return False
    except Exception as e:
        logger.debug(f"🔍 is_popup_likely_present error: {e}")
        return False


def click_outside_to_dismiss(driver):
    """安全点击 WebView 内部顶部边缘（避开状态栏），尝试关闭 H5 弹窗"""
    try:
        # 先找 WebView
        webview = driver.find_element(AppiumBy.CLASS_NAME, "android.webkit.WebView")
        rect = webview.rect  # {'x', 'y', 'width', 'height'}

        if rect['height'] < 100:
            return False  # 太小，忽略

        # ✅ 安全点击点：WebView 内部顶部 + 偏移 30px（避开系统状态栏影响）
        x = rect['x'] + rect['width'] // 2
        y = rect['y'] + 30  # 顶部 30px 处，通常是遮罩层

        logger.debug(f"🖱️ 安全点击 WebView 顶部: ({int(x)}, {int(y)}) | rect={rect}")
        driver.tap([(int(x), int(y))], duration=150)
        time.sleep(0.4)

        # 检查是否关闭
        if not is_popup_likely_present(driver):
            return True
        return False

    except NoSuchElementException:
        # 没有 WebView，不执行点击（避免误触原生页面）
        logger.debug("🔍 无 WebView，跳过点击空白")
        return False
    except Exception as e:
        logger.debug(f"⚠️ 点击空白失败: {e}")
        return False

def dismiss_known_popups(driver, max_rounds: int = 5, interval: float = 0.25):
    """
    健壮的弹窗清理器：
      - 支持中英文弹窗识别
      - 自动检测 H5 WebView 弹窗
      - 精准点击 WebView 内部空白区
      - 防御性兜底：即使未识别也尝试点击一次
    """
    # ⏱️ 首轮等待弹窗完全渲染
    if max_rounds > 0:
        time.sleep(0.8)

    for round_num in range(max_rounds):
        closed_any = False

        # === 1. 尝试关闭所有已知按钮 ===
        for locator_type, locator_value, desc in POPUP_CLOSE_BUTTONS:
            try:
                elements = driver.find_elements(locator_type, locator_value)
                valid_elements = []
                for el in elements:
                    try:
                        if el.is_displayed() and el.is_enabled():
                            valid_elements.append(el)
                    except StaleElementReferenceException:
                        continue
                valid_elements.sort(key=lambda e: e.location.get('y', 0), reverse=True)

                for el in valid_elements:
                    try:
                        el.click()
                        logger.info(f"✅ 关闭弹窗: {desc} | ({locator_type}={locator_value})")
                        closed_any = True
                        time.sleep(interval)
                        break
                    except (WebDriverException, ElementClickInterceptedException):
                        continue
            except Exception as find_e:
                logger.debug(f"🔍 定位 {desc} 失败: {find_e}")
                continue

        # === 2. 如果没关掉，但疑似有弹窗 → 点击空白 ===
        if not closed_any and is_popup_likely_present(driver):
            if click_outside_to_dismiss(driver):
                closed_any = True

        # === 3. 如果本轮完全没动作，退出 ===
        if not closed_any:
            # 防御性兜底：即使 is_popup_likely_present=False，也尝试点一次（低风险）
            logger.debug("🛡️ 防御性操作：尝试点击空白区域（即使未识别弹窗）")
            click_outside_to_dismiss(driver)
            break
    else:
        logger.warning(f"⚠️ 弹窗清理达到最大轮数 ({max_rounds})，可能存在未覆盖弹窗！")


# ==============================
# 装饰器：自动清理弹窗后执行函数
# ==============================
def with_popup_dismiss(func):
    def wrapper(driver, *args, **kwargs):
        dismiss_known_popups(driver)
        return func(driver, *args, **kwargs)

    return wrapper


def swipe_left(driver, duration_ms: int = 300):
    """执行物理左滑"""
    size = driver.get_window_size()
    start_x = size['width'] * 0.8
    end_x = size['width'] * 0.2
    y = size['height'] * 0.5
    driver.swipe(start_x, y, end_x, y, duration_ms)

def click_element_or_swipe_left_if_not_found(
        driver,
        locator,
        timeout: float = 2.0,
        swipe_after_fail: bool = True
) -> bool:
    """
    尝试点击指定元素；若未找到或点击失败，则执行一次左滑（可选）。

    :param driver: Appium WebDriver 实例
    :param locator: 元素定位器，如 (AppiumBy.ID, "com.xxx:id/button")
    :param timeout: 查找元素的超时时间（秒）
    :param swipe_after_fail: 找不到时是否左滑（默认 True）
    :return: True 表示成功点击，False 表示失败并已执行兜底（如左滑）
    """
    # 先调用弹窗清理
    dismiss_known_popups(driver, max_rounds=2, interval=0.2)

    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        element.click()
        logger.info(f"✅ 成功点击元素: {locator}")
        return True
    except Exception as e:
        logger.debug(f"❌ 点击失败（可能未找到/不可点）: {locator}, error={e}")
        if swipe_after_fail:
            logger.info("⬅️ 执行左滑（因元素未找到/不可操作）")
            swipe_left(driver)
            time.sleep(0.5)
        return False