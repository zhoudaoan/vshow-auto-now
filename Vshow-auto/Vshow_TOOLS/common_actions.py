from selenium.webdriver.common.by import By
from typing import Union, List
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, \
    ElementClickInterceptedException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from appium.webdriver.common.appiumby import AppiumBy
from Vshow_TOOLS.dismiss_known_popups import with_popup_dismiss
from selenium.common.exceptions import NoSuchElementException
import logging

logger = logging.getLogger(__name__)
# allure_step = AllureStep.allure_step

import time

@with_popup_dismiss
def click_element_by_id(
        driver,
        element_id: str,
        step_name: str,
        timeout: int = 10,
        retries: int = 20
):
    """
    更强健的点击：不依赖 WebDriverWait 返回结果，而是直接尝试点击 + 重试。
    适用于高动态页面（直播、PK、聊天等）。
    """
    logger.info(f"--- {step_name} ---")

    end_time = time.time() + timeout

    for attempt in range(retries + 1):
        try:
            element = driver.find_element(AppiumBy.ID, element_id)
            element.click()
            logger.info(f"✅ 成功点击: {step_name}")
            return

        except (StaleElementReferenceException, NoSuchElementException, WebDriverException) as e:
            # 如果还在总超时时间内，且还有重试次数，则继续
            if time.time() < end_time and attempt < retries:
                wait_time = 0.2 + attempt * 0.15  # 更短间隔，快速重试
                logger.warning(
                    f"⚠️ 第 {attempt + 1}/{retries + 1} 次点击 '{element_id}' 失败 "
                    f"({type(e).__name__})，{wait_time:.2f}s 后重试..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"💥 所有重试失败或超时: {step_name} | 最终错误: {e}")
                raise

        except Exception as e:
            logger.error(f"🔥 未知异常: {step_name} | {e}")
            raise

@with_popup_dismiss
def send_keys_to_element(
    driver,
    element_id: str,
    text: str,
    step_name: str,
    timeout: int = 10,
):
    """
    向 ID 元素输入文本（防 StaleElement）
    每次操作都重新查找元素，避免引用失效。
    """
    logger.info(f"--- {step_name} ---")
    end_time = time.time() + timeout
    attempt = 0

    while time.time() < end_time:
        try:
            # ⭐ 每次都重新查找元素（关键！）
            element = driver.find_element(AppiumBy.ID, element_id)

            # 点击聚焦（确保获得焦点）
            element.click()

            # 清空
            try:
                element.clear()
                if element.text.strip() != "":
                    raise Exception("clear() did not work")
            except Exception as e:
                logger.warning(f"{step_name}: clear() failed, fallback to backspace: {e}")
                element.send_keys('\b' * 50)

            # 输入
            element.send_keys(text)
            logger.info(f"✅ {step_name}: 输入完成 -> {repr(text)}")
            return

        except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
            wait_time = min(0.3 + attempt * 0.1, 1.0)
            logger.warning(
                f"⚠️ 第 {attempt + 1} 次输入 '{element_id}' 失败 ({type(e).__name__})，{wait_time:.2f}s 后重试..."
            )
            time.sleep(wait_time)
            attempt += 1
        except Exception as e:
            logger.error(f"🔥 未知异常: {step_name} | {e}")
            raise

    raise TimeoutError(f"💥 超时 {timeout} 秒，未能向元素输入文本: {element_id}")


@with_popup_dismiss
def click_element_if_exists(
    driver,
    locator: tuple,
    step_name: str,
    timeout: float = 10.0,      # 默认值
    poll_frequency: float = 0.2  # 每 0.2 秒检查一次（默认是 0.5）
):
    """
    如果元素在指定时间内出现且可点击，则点击它；否则跳过。
    使用 element_to_be_clickable 确保元素不仅存在，而且可交互。

    :param driver: Appium WebDriver 实例
    :param locator: 元素定位器，如 (AppiumBy.ID, "com.xxx:id/close")
    :param step_name: Allure 步骤名称（可配合 with allure.step 使用）
    :param timeout: 最大等待时间（秒），默认 2 秒
    :param poll_frequency: 轮询间隔（秒），默认 0.2 秒
    """
    start_time = time.time()
    try:
        # 等待元素出现并可点击（比 presence 更可靠）
        el = WebDriverWait(driver, timeout, poll_frequency=poll_frequency).until(
            EC.element_to_be_clickable(locator)
        )
        el.click()
        waited = time.time() - start_time
        logger.info(f"✅ [{step_name}] 点击了元素: {locator}（等待 {waited:.2f}s）")
    except (TimeoutException, NoSuchElementException) as e:
        logger.warning(f"⚠️ [{step_name}] 元素未在 {timeout}s 内出现或不可点击，跳过: {locator}")
    except Exception as e:
        logger.error(f"❌ [{step_name}] 点击元素时发生异常: {e}")

@with_popup_dismiss
def wait_for_all_elements(driver, locators, step_name, timeout=20, visible=True):
    """
    等待一个或多个元素全部出现（全部可见或存在）

    :param driver: WebDriver 实例
    :param locators:
        - 单个定位器: (by, value)  例如 (AppiumBy.ID, "xxx")
        - 多个定位器: [(by1, val1), (by2, val2), ...]
    :param step_name: Allure 步骤名称
    :param timeout: 超时时间（秒）
    :param visible: 是否要求可见
    :return: True（全部出现）或 False（任一未出现）
    """
    # 标准化为列表
    if isinstance(locators, tuple) and len(locators) == 2:
        locator_list = [locators]
    elif isinstance(locators, list):
        locator_list = locators
    else:
        raise ValueError("locators 必须是 (by, value) 元组 或 [(by, value), ...] 列表")

    # with allure_step(step_name, driver):
    wait = WebDriverWait(driver, timeout)
    condition = EC.visibility_of_element_located if visible else EC.presence_of_element_located

    try:
        for by, value in locator_list:
            wait.until(condition((by, value)))
        return True
    except TimeoutException:
        return False

@with_popup_dismiss
def click_button_by_text(
        driver,
        text: str,
        step_name: str = "",
        timeout: int = 10,
        wait_for_disappear: bool = False,
):
    full_step_name = f"点击按钮: {text}" if not step_name else step_name
    logger.info(f"--- {full_step_name} ---")

    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.find_element(AppiumBy.XPATH, f'//*[@text="{text}"]').is_displayed()
        )

        element = driver.find_element(AppiumBy.XPATH, f'//*[@text="{text}"]')
        element.click()
        logger.info(f"✅ 成功点击按钮: {text}")

        if wait_for_disappear:
            WebDriverWait(driver, timeout).until_not(
                EC.presence_of_element_located((AppiumBy.XPATH, f'//*[@text="{text}"]'))
            )
            logger.info(f"✅ 按钮 '{text}' 已消失")

    except (TimeoutException, NoSuchElementException) as e:
        logger.error(f"❌ 未找到或无法点击按钮: '{text}' | 错误: {e}")
        raise

@with_popup_dismiss
def click_text_by_resource_id(driver, text: str, element_id: str, step_name: str = None, timeout: int = 10):
    # step_name = step_name or f"点击文本 '{text}'"
    xpath = f'//android.widget.TextView[@resource-id="{element_id}" and @text="{text}"]'

    # with allure_step(step_name, driver):
    wait = WebDriverWait(driver, timeout)
    element = wait.until(
        EC.element_to_be_clickable((AppiumBy.XPATH, xpath))
    )
    element.click()

@with_popup_dismiss
def wait_for_page_text(
    driver,
    texts: Union[str, List[str]],
    step_name: str = None,
    timeout: int = 10,
    match_all: bool = True
) -> bool:
    """
    等待页面中出现指定的一个或多个文案，用于判断页面加载成功。

    :param driver: Appium driver 实例
    :param texts: 要查找的文本，可以是字符串（单个）或字符串列表（多个）
    :param step_name: Allure 步骤名称
    :param timeout: 最大等待时间（秒）
    :param match_all:
        - True（默认）：所有文本都必须出现
        - False：任意一个文本出现即成功
    :return: True if condition met, False otherwise
    """
    if isinstance(texts, str):
        texts = [texts]

    if not texts:
        logger.warning("⚠️ 未提供任何待校验文本，直接返回 True")
        return True

    def _check_texts():
        page_source = driver.page_source
        found_texts = []
        for text in texts:
            if text in page_source:
                found_texts.append(text)
        if match_all:
            return len(found_texts) == len(texts), found_texts
        else:
            return len(found_texts) > 0, found_texts

    try:
        # with allure_step(step_name or f"等待页面包含文本: {texts}", driver):
        start_time = time.time()
        while time.time() - start_time < timeout:
            is_match, found = _check_texts()
            if is_match:
                logger.info(f"✅ 页面加载成功，{'所有' if match_all else '部分'}文本已出现: {found}")
                return True
            time.sleep(0.5)  # 避免频繁拉取 page_source

        # 超时后最后一次检查
        is_match, found = _check_texts()
        if is_match:
            return True

        missing = [t for t in texts if t not in driver.page_source]
        logger.error(f"❌ 页面加载超时，未找到文本: {missing}（期望: {texts}）")
        return False

    except Exception as e:
        logger.error(f"监听页面文本时发生异常: {e}")
        return False


@with_popup_dismiss
def get_text_by_id(
    driver,
    element_id: str,
    timeout: int = 10,
    retries: int = 1,
    default: str = "",
    use_attribute_fallback: bool = True
) -> str:
    """
     获取resource-id元素的文本内容。
    :param driver: Appium WebDriver 实例
    :param element_id: 元素的 ID（如 'com.baitu.poppo:id/tvTitle'）
    :param timeout: 等待元素出现的最大秒数，默认 10s
    :param retries: 失败时重试次数（用于应对短暂 UI 变化），默认 1 次（即总共尝试 2 次）
    :param default: 若始终失败，返回的默认值
    :param use_attribute_fallback: 是否在 .text 为空时尝试 get_attribute('text')
    :return: 元素的文本内容（strip 后），若失败则返回 default
    """
    attempt = 0
    while attempt <= retries:
        try:
            logger.debug(f"尝试第 {attempt + 1} 次：查找元素 ID='{element_id}'")
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located(("id", element_id))
            )

            text = element.text
            if text.strip():
                result = text.strip()
                logger.info(f"✅ 通过 .text 获取到文本: '{result}' (ID: {element_id})")
                return result

            if use_attribute_fallback:
                attr_text = element.get_attribute("text") or ""
                if attr_text.strip():
                    result = attr_text.strip()
                    logger.info(f"✅ 通过 get_attribute('text') 获取到文本: '{result}' (ID: {element_id})")
                    return result

            logger.warning(f"⚠️ 元素存在但文本为空 (ID: {element_id})")
            return ""

        except (TimeoutException, NoSuchElementException) as e:
            logger.warning(f"第 {attempt + 1} 次尝试失败：未找到元素 ID='{element_id}' ({e})")
            attempt += 1
            if attempt <= retries:
                time.sleep(1)
            else:
                logger.error(f"❌ 所有 {retries + 1} 次尝试均失败，无法获取文本 (ID: {element_id})")
                return default

        except Exception as e:
            logger.error(f"❌ 获取文本时发生未知错误 (ID: {element_id}): {e}")
            return default

    return default

@with_popup_dismiss
def wait_for_toast(
        driver,
        partial_text: str,
        step_name: str = None,
        timeout: int = 5,
        raise_on_not_found: bool = True
) -> bool:
    """
    等待包含指定文本的 Toast 出现。

    :param driver: Appium WebDriver 实例
    :param partial_text: 要匹配的 Toast 文本片段
    :param step_name: Allure 步骤名称（可选）
    :param timeout: 最大等待时间（秒）
    :param raise_on_not_found: 若为 True，未找到时抛出 AssertionError；否则返回 False
    :return: 成功找到返回 True，未找到且 raise_on_not_found=False 时返回 False
    """
    xpath = f"//*[contains(@text, '{partial_text}')]"

    try:
        # with allure_step(step_name or f"等待 Toast 包含 '{partial_text}'", driver):
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        found_text = element.text.strip()
        logger.info(f"✅ Toast 出现: '{found_text}'")
        return True

    except TimeoutException:
        msg = f"❌ 未找到包含 '{partial_text}' 的 Toast（等待 {timeout}s）"
        logger.error(msg)
        # if raise_on_not_found:
        #     raise AssertionError(msg)
        # else:
        return False

@with_popup_dismiss
def safe_hide_keyboard(driver):
    """
    安全收起键盘：优先尝试标准方法，失败则点击空白区域
    """
    try:
        # 先尝试标准方法
        if driver.is_keyboard_shown():
            driver.hide_keyboard()
    except Exception as e:
        logger.debug(f"hide_keyboard() 失败，改用点击空白区域: {e}")
        # 回退到点击屏幕底部
        size = driver.get_window_size()
        driver.tap([(size['width'] // 2, size['height'] - 150)], 100)

@with_popup_dismiss
def _escape_xpath_text(text: str) -> str:
    """安全地将文本嵌入 XPath，避免单引号/双引号导致语法错误"""
    if "'" not in text:
        return f"'{text}'"
    if '"' not in text:
        return f'"{text}"'
    # 同时包含 ' 和 "，用 concat 拼接（较少见）
    parts = text.split("'")
    return "concat('" + "', \"'\", '".join(parts) + "')"

@with_popup_dismiss
def is_text_count_greater_than_safe(
    driver,
    text: str,
    exact_match: bool = True,
    timeout: int = 10,
    min_count: int = 2
) -> bool:
    """
    检查 Android 页面中 text 属性匹配的元素数量是否 > min_count

    参数:
        driver: Appium WebDriver（Android）
        text: 要查找的文本
        exact_match: 是否精确匹配（True）还是部分包含（False）
        timeout: 最大等待时间（秒）
        min_count: 阈值，默认为2（即 >2 表示至少3个）

    返回:
        bool: 元素数量 > min_count 则返回 True
    """
    try:
        escaped_text = _escape_xpath_text(text)
        if exact_match:
            xpath = f"//*[@text={escaped_text}]"
        else:
            xpath = f"//*[contains(@text, {escaped_text}) or contains(@content-desc, {escaped_text})]"

        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        elements = driver.find_elements(By.XPATH, xpath)
        logger.info(f"获取到的话题数量文本超过2个，判断是在详情页，话题数量文本：{len(elements)}")
        return len(elements) > min_count
    except Exception:
        return False

@with_popup_dismiss
def click_text_with_prefix(driver, prefix: str, timeout: int = 10):
    """
    查找包含指定前缀的可点击文本元素并点击（增强版）
    """
    # 更精准的 XPath：优先匹配 TextView/Button，且要求 clickable 或 focusable
    xpath = (
        f"//*["
        f"(@class='android.widget.TextView' or @class='android.widget.Button') and "
        f"(contains(@text, '{prefix}') or contains(@content-desc, '{prefix}')) and "
        f"(@clickable='true' or @focusable='true')"
        f"]"
    )

    try:
        # ✅ 关键：使用显式等待，直到元素可点击
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((AppiumBy.XPATH, xpath))
        )

        # 可选：滚动到可见区域（某些设备需要）
        driver.execute_script("arguments[0].scrollIntoView(true);", element)

        # 执行点击
        element.click()
        actual_text = element.text or element.get_attribute('content-desc')
        logger.info(f"✅ 成功点击文本（前缀='{prefix}'）: '{actual_text}'")
        return True

    except TimeoutException:
        print(f"❌ 超时：{timeout}秒内未找到可点击的文本（前缀='{prefix}'）")
        # 可选：打印当前页面源码用于调试
        # print("当前页面结构:\n", driver.page_source[:2000])
        return False

    except ElementClickInterceptedException:
        print(f"❌ 点击被拦截：可能有弹窗/遮挡层（前缀='{prefix}'）")
        return False

    except Exception as e:
        print(f"❌ 点击失败（前缀='{prefix}'）: {type(e).__name__}: {e}")
        return False

@with_popup_dismiss
def find_text_in_list_cards(
        driver,
        list_container_xpath="//androidx.recyclerview.widget.RecyclerView",
        target_text="",
        max_cards=20,
        scroll_if_not_found=True,
        swipe_func=None,
        max_scrolls=5,
        wait_timeout=10,
        match_all=False  # 👈 新增参数：False=任一匹配，True=全部匹配
):
    """
    在消息列表中查找卡片。
    - 若 match_all=False：任一 target_text 匹配即成功（原逻辑）
    - 若 match_all=True：必须所有 target_text 都出现在同一张卡片中才算成功
    """
    # 标准化 target_text
    target_texts = [target_text] if isinstance(target_text, str) else list(target_text)
    # 过滤空值
    target_texts = [str(t) for t in target_texts if t]

    if not target_texts:
        logger.error("⚠️ target_text 为空，无法查找")
        return None, None

    scroll_count = 0

    while scroll_count <= max_scrolls:
        try:
            # 等待列表容器
            try:
                WebDriverWait(driver, wait_timeout).until(
                    EC.presence_of_element_located((By.XPATH, list_container_xpath))
                )
            except TimeoutException:
                logger.error(f"⚠️ 列表容器未在 {wait_timeout} 秒内出现")
                if not scroll_if_not_found or not swipe_func or scroll_count >= max_scrolls:
                    break
                pass

            card_xpath = f"{list_container_xpath}/*[self::android.view.ViewGroup]"
            cards = driver.find_elements(By.XPATH, card_xpath)
            logger.info(f"🔍 当前屏幕共找到 {len(cards)} 张卡片")

            for i, card in enumerate(cards[:max_cards]):
                matched_texts = []
                all_matched = True

                for text in target_texts:
                    try:
                        # 安全构造 XPath（防单引号）
                        if "'" not in text:
                            xpath_expr = f".//android.widget.TextView[contains(@text, '{text}')]"
                        else:
                            # 使用 concat 处理含单引号的文本
                            parts = text.split("'")
                            concat_str = "concat(" + ", \"'\", ".join(f"'{p}'" for p in parts) + ")"
                            xpath_expr = f".//android.widget.TextView[contains(@text, {concat_str})]"

                        elements = card.find_elements(By.XPATH, xpath_expr)
                        if elements:
                            matched_texts.append(text)
                        else:
                            all_matched = False
                            break  # 有一个没匹配，直接跳过这张卡（优化性能）
                    except StaleElementReferenceException:
                        all_matched = False
                        break
                    except Exception as e:
                        logger.error(f"⚠️ 查找 '{text}' 出错: {e}")
                        all_matched = False
                        break

                # ✅ 关键判断：是否全部匹配？
                if match_all:
                    if all_matched and len(matched_texts) == len(target_texts):
                        logger.info(f"✅ 第 {i + 1} 张卡片匹配全部文本: {matched_texts}")
                        return card, matched_texts  # 返回全部匹配的文本列表
                else:
                    # 原逻辑：任一匹配
                    if matched_texts:
                        logger.info(f"✅ 第 {i + 1} 张卡片匹配文本: '{matched_texts[0]}'")
                        return card, matched_texts[0]

            # 滑动加载更多
            if scroll_if_not_found and swipe_func and scroll_count < max_scrolls:
                logger.info("🔄 当前屏幕未找到目标，正在下滑加载更多...")
                try:
                    swipe_func(driver, direction="down", distance_pct=0.6, duration_ms=500)
                except Exception as e:
                    logger.error(f"⚠️ 滑动失败: {e}")
                time.sleep(1.8)
                scroll_count += 1
            else:
                break

        except Exception as e:
            logger.error(f"❌ 查找过程中发生异常: {type(e).__name__}: {e}")
            break

    if match_all:
        message = f"❌ 滑动 {scroll_count} 次后，未找到同时包含以下所有文本的卡片: {target_texts}"
    else:
        message = f"❌ 滑动 {scroll_count} 次后，未找到包含任一目标文本的卡片: {target_texts}"

    raise AssertionError(message)


@with_popup_dismiss
def click(driver, xpath: str, step_name: str, timeout: int = 10):
    """
    通过 XPath 点击元素（带重试机制）

    :param driver: Appium/Selenium WebDriver 实例
    :param xpath: 要点击元素的 XPath 表达式
    :param step_name: 日志/报告中的步骤名称
    :param timeout: 总超时时间（秒），默认 10 秒
    """
    logger.info(f"--- {step_name} ---")
    end_time = time.time() + timeout
    attempt = 0

    while time.time() < end_time:
        try:
            element = driver.find_element(AppiumBy.XPATH, xpath)
            element.click()
            logger.info(f"✅ 成功点击: {step_name}")
            return
        except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
            wait_time = min(0.3 + attempt * 0.1, 1.0)  # 0.3s ～ 1.0s 退避
            logger.warning(
                f"⚠️ 第 {attempt + 1} 次点击 '{xpath}' 失败 ({type(e).__name__})，{wait_time:.2f}s 后重试..."
            )
            time.sleep(wait_time)
            attempt += 1
        except Exception as e:
            logger.error(f"🔥 未知异常: {step_name} | {e}")
            raise

    raise TimeoutError(f"💥 超时 {timeout} 秒，未能点击元素: {xpath}")


@with_popup_dismiss
def send_keys(driver, xpath: str, text: str, step_name: str, timeout: int = 10):
    """通过 XPath 输入文本（带重试机制）"""
    logger.info(f"--- {step_name} ---")
    end_time = time.time() + timeout
    attempt = 0

    while time.time() < end_time:
        try:
            element = driver.find_element(AppiumBy.XPATH, xpath)
            # 点击聚焦
            element.click()

            # 清空逻辑
            try:
                element.clear()
                if element.text.strip() != "":
                    raise Exception("clear() did not work")
            except Exception as clear_e:
                logger.warning(f"{step_name}: clear() failed, fallback to backspace: {clear_e}")
                element.send_keys('\b' * 50)

            # 输入文本
            element.send_keys(text)
            logger.info(f"✅ {step_name}: 输入完成 -> {repr(text)}")
            return

        except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
            wait_time = min(0.3 + attempt * 0.1, 1.0)
            logger.warning(
                f"⚠️ 第 {attempt + 1} 次输入 '{xpath}' 失败 ({type(e).__name__})，{wait_time:.2f}s 后重试..."
            )
            time.sleep(wait_time)
            attempt += 1
        except Exception as e:
            logger.error(f"🔥 未知异常: {step_name} | {e}")
            raise

    raise TimeoutError(f"💥 超时 {timeout} 秒，未能向元素输入文本: {xpath}")


@with_popup_dismiss
def get_text(driver, xpath: str, step_name: str, timeout: int = 10) -> str:
    """通过 XPath 获取元素文本（带重试机制）"""
    logger.info(f"--- {step_name} ---")
    end_time = time.time() + timeout
    attempt = 0

    while time.time() < end_time:
        try:
            element = driver.find_element(AppiumBy.XPATH, xpath)
            text = element.text
            logger.info(f"✅ {step_name}: 获取文本 -> {repr(text)}")
            return text
        except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
            wait_time = min(0.3 + attempt * 0.1, 1.0)
            logger.warning(
                f"⚠️ 第 {attempt + 1} 次获取文本 '{xpath}' 失败 ({type(e).__name__})，{wait_time:.2f}s 后重试..."
            )
            time.sleep(wait_time)
            attempt += 1
        except Exception as e:
            logger.error(f"🔥 未知异常: {step_name} | {e}")
            raise

    raise TimeoutError(f"💥 超时 {timeout} 秒，未能获取元素文本: {xpath}")


@with_popup_dismiss
def is_displayed(driver, xpath: str, step_name: str, timeout: int = 10) -> bool:
    """通过 XPath 判断元素是否可见（带重试机制）"""
    logger.info(f"--- {step_name} ---")
    end_time = time.time() + timeout
    attempt = 0

    while time.time() < end_time:
        try:
            element = driver.find_element(AppiumBy.XPATH, xpath)
            displayed = element.is_displayed()
            logger.debug(f"🔍 {step_name}: 元素可见性 = {displayed}")
            return displayed
        except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
            # 元素不存在或失效，视为 not displayed
            wait_time = min(0.2 + attempt * 0.05, 0.5)
            logger.debug(
                f"⏳ 第 {attempt + 1} 次检查 '{xpath}' 未找到，{wait_time:.2f}s 后重试..."
            )
            time.sleep(wait_time)
            attempt += 1
        except Exception as e:
            logger.error(f"🔥 未知异常: {step_name} | {e}")
            raise

    logger.warning(f"⏱️ 超时 {timeout} 秒未找到元素，返回 False")
    return False