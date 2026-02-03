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
from typing import Optional, Callable, Union, Tuple, Any

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
    retries: int = 20,
):
    """
    向 ID 元素输入文本（防 StaleElement）
    每次操作都重新查找元素，避免引用失效。
    结合重试次数与总超时时间，适用于高动态页面。
    """
    logger.info(f"--- {step_name} ---")
    end_time = time.time() + timeout

    for attempt in range(retries + 1):
        try:
            element = driver.find_element(AppiumBy.ID, element_id)
            element.click()

            try:
                element.clear()
                if element.text.strip() != "":
                    raise Exception("clear() did not work")
            except Exception as e:
                logger.warning(f"{step_name}: clear() failed, fallback to backspace: {e}")
                element.send_keys('\b' * 50)

            element.send_keys(text)
            logger.info(f"✅ {step_name}: 输入完成 -> {repr(text)}")
            return

        except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
            if time.time() < end_time and attempt < retries:
                wait_time = 0.2 + attempt * 0.15  # 快速重试策略
                logger.warning(
                    f"⚠️ 第 {attempt + 1}/{retries + 1} 次输入 '{element_id}' 失败 "
                    f"({type(e).__name__})，{wait_time:.2f}s 后重试..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"💥 所有重试失败或超时: {step_name} | 最终错误: {e}")
                raise

        except Exception as e:
            logger.error(f"🔥 未知异常: {step_name} | {e}")
            raise

    raise TimeoutError(f"💥 超时 {timeout} 秒且耗尽 {retries} 次重试，未能向元素输入文本: {element_id}")

@with_popup_dismiss
def click_element_if_exists(
    driver,
    locator: tuple,
    step_name: str,
    timeout: float = 10.0,
    retries: int = 20,
):
    """
    如果元素在指定时间内出现且可点击，则点击它；否则安静跳过。
    每次尝试都重新查找元素，避免 StaleElement，适用于高动态页面（如直播、弹窗等）。

    :param driver: Appium WebDriver 实例
    :param locator: 元素定位器，如 (AppiumBy.ID, "com.xxx:id/close")
    :param step_name: 步骤名称，用于日志和 Allure
    :param timeout: 最大等待时间（秒），默认 10 秒
    :param retries: 最多重试次数，默认 20 次（配合快速轮询）
    """
    logger.info(f"--- [{step_name}] 尝试点击（若存在）---")
    end_time = time.time() + timeout

    for attempt in range(retries + 1):
        if time.time() > end_time:
            logger.warning(f"⚠️ [{step_name}] 超时 {timeout}s，未找到可点击元素: {locator}")
            return

        try:
            element = driver.find_element(*locator)
            if element.is_displayed() and element.is_enabled():
                element.click()
                waited = time.time() - (end_time - timeout)
                logger.info(f"✅ [{step_name}] 成功点击元素: {locator}（等待 {waited:.2f}s）")
                return
            else:
                pass
        except (NoSuchElementException, StaleElementReferenceException, WebDriverException):
            pass
        except Exception as e:
            logger.error(f"❌ [{step_name}] 点击过程中发生未知异常: {e}")
            return

        wait_time = 0.2 + attempt * 0.15
        time.sleep(min(wait_time, end_time - time.time()))  # 避免 sleep 超过剩余时间

    logger.warning(f"⚠️ [{step_name}] 耗尽 {retries} 次重试，未找到可点击元素: {locator}")

@with_popup_dismiss
def wait_for_all_elements(
    driver,
    locators,
    step_name: str,
    timeout: float = 20.0,
    visible: bool = True,
    retries: int = 30,
):
    """
    等待一个或多个元素全部出现（全部可见或存在），适用于高动态页面。
    每次检查都重新查找所有元素，避免 StaleElement 或短暂消失导致误判。

    :param driver: WebDriver 实例
    :param locators:
        - 单个定位器: (by, value)  例如 (AppiumBy.ID, "xxx")
        - 多个定位器: [(by1, val1), (by2, val2), ...]
    :param step_name: 步骤名称（用于日志）
    :param timeout: 最大等待时间（秒），默认 20 秒
    :param visible: 是否要求元素可见（若 False 则仅需存在）
    :param retries: 最多重试次数，默认 30 次（配合快速轮询）
    :return: True（全部满足）或 False（超时/重试耗尽仍未满足）
    """
    # 标准化为列表
    if isinstance(locators, tuple) and len(locators) == 2:
        locator_list = [locators]
    elif isinstance(locators, list):
        locator_list = locators
    else:
        raise ValueError("locators 必须是 (by, value) 元组 或 [(by, value), ...] 列表")

    logger.info(f"--- [{step_name}] 等待 {len(locator_list)} 个元素全部{'可见' if visible else '存在'} ---")

    end_time = time.time() + timeout

    for attempt in range(retries + 1):
        if time.time() > end_time:
            logger.warning(f"⚠️ [{step_name}] 超时 {timeout}s，未满足全部元素条件")
            return False

        all_found = True
        for by, value in locator_list:
            try:
                element = driver.find_element(by, value)
                if visible:
                    if not (element.is_displayed() and element.is_enabled()):
                        all_found = False
                        break
            except (NoSuchElementException, StaleElementReferenceException, WebDriverException):
                all_found = False
                break
            except Exception as e:
                logger.error(f"❌ [{step_name}] 检查元素 ({by}, {value}) 时发生未知异常: {e}")
                all_found = False
                break

        if all_found:
            waited = time.time() - (end_time - timeout)
            logger.info(f"✅ [{step_name}] 所有元素已满足（等待 {waited:.2f}s）")
            return True

        wait_time = 0.2 + attempt * 0.1
        time.sleep(min(wait_time, end_time - time.time()))

    logger.warning(f"⚠️ [{step_name}] 耗尽 {retries} 次重试，仍未满足全部元素条件")
    return False

@with_popup_dismiss
def click_button_by_text(
        driver,
        text: str,
        step_name: str = "",
        timeout: int = 10,
        wait_for_disappear: bool = False,
        retries: int = 20,
):
    """
    通过按钮文本点击元素，适用于高动态页面。
    每次尝试都重新查找，避免 StaleElement 或短暂不可见问题。

    :param driver: Appium WebDriver 实例
    :param text: 按钮显示的文本
    :param step_name: 自定义步骤名（若为空则自动生成）
    :param timeout: 总超时时间（秒），默认 10 秒
    :param wait_for_disappear: 点击后是否等待该按钮消失
    :param retries: 最多重试次数，默认 20 次
    """
    full_step_name = f"点击按钮: {text}" if not step_name else step_name
    logger.info(f"--- {full_step_name} ---")

    end_time = time.time() + timeout
    xpath = f'//*[@text="{text}"]'

    for attempt in range(retries + 1):
        if time.time() > end_time:
            break

        try:
            element = driver.find_element(AppiumBy.XPATH, xpath)
            if element.is_displayed() and element.is_enabled():
                element.click()
                logger.info(f"✅ 成功点击按钮: {text}")

                if wait_for_disappear:
                    disappear_end_time = time.time() + timeout
                    disappear_retries = retries
                    for dis_attempt in range(disappear_retries + 1):
                        if time.time() > disappear_end_time:
                            break
                        try:
                            driver.find_element(AppiumBy.XPATH, xpath)
                            # 仍存在，继续等待
                        except (NoSuchElementException, StaleElementReferenceException):
                            logger.info(f"✅ 按钮 '{text}' 已消失")
                            return  # 成功完成
                        except WebDriverException:
                            logger.info(f"✅ 按钮 '{text}' 所在上下文已失效，视为消失")
                            return

                        wait_time = 0.2 + dis_attempt * 0.1
                        time.sleep(min(wait_time, disappear_end_time - time.time()))


                    logger.error(f"❌ 按钮 '{text}' 在点击后未在 {timeout}s 内消失")
                    raise TimeoutError(f"按钮 '{text}' 未按预期消失")

                return

        except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
            pass
        except Exception as e:
            logger.error(f"🔥 点击按钮 '{text}' 时发生未知异常: {e}")
            raise

        wait_time = 0.2 + attempt * 0.15
        time.sleep(min(wait_time, end_time - time.time()))

    logger.error(f"❌ 超时 {timeout} 秒或耗尽 {retries} 次重试，未能点击按钮: '{text}'")
    raise TimeoutError(f"未能点击按钮: '{text}'")

@with_popup_dismiss
def click_text_by_resource_id(
    driver,
    text: str,
    element_id: str,
    step_name: str = None,
    timeout: int = 10,
    retries: int = 20,
):
    """
    点击指定 resource-id 且文本匹配的 TextView。
    适用于高动态页面，每次尝试都重新查找，避免 StaleElement。

    :param driver: Appium WebDriver 实例
    :param text: 期望的文本内容
    :param element_id: Android resource-id，如 "com.xxx:id/title"
    :param step_name: 自定义步骤名（若为 None 则自动生成）
    :param timeout: 总超时时间（秒），默认 10 秒
    :param retries: 最多重试次数，默认 20 次
    """
    full_step_name = step_name or f"点击文本 '{text}' (ID: {element_id})"
    logger.info(f"--- {full_step_name} ---")

    xpath = f'//android.widget.TextView[@resource-id="{element_id}" and @text="{text}"]'
    end_time = time.time() + timeout

    for attempt in range(retries + 1):
        if time.time() > end_time:
            break

        try:
            element = driver.find_element(AppiumBy.XPATH, xpath)
            if element.is_displayed() and element.is_enabled():
                element.click()
                logger.info(f"✅ 成功点击: {xpath}")
                return
        except (NoSuchElementException, StaleElementReferenceException, WebDriverException):
            pass
        except Exception as e:
            logger.error(f"🔥 点击时发生未知异常 ({full_step_name}): {e}")
            raise

        wait_time = 0.2 + attempt * 0.15
        time.sleep(min(wait_time, end_time - time.time()))

    logger.error(f"❌ 超时 {timeout} 秒或耗尽 {retries} 次重试，未能点击元素: {xpath}")
    raise TimeoutError(f"未能点击文本 '{text}' (ID: {element_id})")

@with_popup_dismiss
def wait_for_page_text(
    driver,
    texts: Union[str, List[str]],
    step_name: str = None,
    timeout: int = 10,
    match_all: bool = True,
    retries: int = 20,
) -> bool:
    """
    等待页面中出现指定的一个或多个文案，用于判断页面加载成功。
    通过轮询 page_source 实现，适用于无法通过元素定位判断的场景。

    :param driver: Appium WebDriver 实例
    :param texts: 要查找的文本（字符串或字符串列表）
    :param step_name: 步骤名称（用于日志）
    :param timeout: 最大等待时间（秒），默认 10 秒
    :param match_all:
        - True（默认）：所有文本都必须出现
        - False：任意一个出现即成功
    :param retries: 最多重试次数，默认 20 次
    :return: True if condition met within timeout, else False
    """
    if isinstance(texts, str):
        texts = [texts]

    if not texts:
        logger.warning("⚠️ 未提供任何待校验文本，直接返回 True")
        return True

    full_step_name = step_name or f"等待页面包含文本: {texts}"
    logger.info(f"--- [{full_step_name}] ---")

    end_time = time.time() + timeout

    for attempt in range(retries + 1):
        if time.time() > end_time:
            break

        try:
            page_source = driver.page_source
        except (WebDriverException, Exception) as e:
            logger.warning(f"⚠️ 获取 page_source 失败（第 {attempt + 1} 次）: {e}")
            page_source = ""

        found_texts = [text for text in texts if text in page_source]

        if match_all:
            if len(found_texts) == len(texts):
                waited = time.time() - (end_time - timeout)
                logger.info(f"✅ 页面加载成功，所有文本已出现（等待 {waited:.2f}s）: {found_texts}")
                return True
        else:
            if found_texts:
                waited = time.time() - (end_time - timeout)
                logger.info(f"✅ 页面加载成功，部分文本已出现（等待 {waited:.2f}s）: {found_texts}")
                return True

        # 计算下一次检查间隔（基础 0.3s + 退避）
        wait_time = 0.3 + attempt * 0.1
        time.sleep(min(wait_time, end_time - time.time()))

    # 超时后最终检查（可选，但通常最后一次已覆盖）
    try:
        final_source = driver.page_source
        final_found = [t for t in texts if t in final_source]
        missing = [t for t in texts if t not in final_source]
    except Exception:
        final_found = []
        missing = texts

    if match_all:
        is_success = len(final_found) == len(texts)
    else:
        is_success = len(final_found) > 0

    if is_success:
        logger.info(f"✅ 超时边界命中：文本条件满足: {final_found}")
        return True
    else:
        logger.error(f"❌ 页面加载超时 {timeout}s，未满足文本条件 | 期望: {texts} | 缺失: {missing}")
        return False

@with_popup_dismiss
def get_text_by_id(
    driver,
    element_id: str,
    timeout: int = 10,
    retries: int = 5,  # 建议适当提高默认重试次数（原为1太低）
    default: str = "",
    use_attribute_fallback: bool = True,
) -> str:
    """
    获取指定 resource-id 元素的文本内容，适用于高动态页面。
    每次尝试都重新查找元素，避免 StaleElement 或短暂未渲染问题。

    :param driver: Appium WebDriver 实例
    :param element_id: Android resource-id，如 'com.xxx:id/tvTitle'
    :param timeout: 总等待超时时间（秒），默认 10 秒
    :param retries: 最多重试次数（总尝试 = retries + 1），默认 5 次
    :param default: 所有尝试失败后返回的默认值
    :param use_attribute_fallback: 若 .text 为空，是否尝试 element.get_attribute('text')
    :return: 获取到的文本（strip 后），若失败则返回 default
    """
    logger.info(f"--- 尝试获取文本 (ID: {element_id}) ---")
    end_time = time.time() + timeout

    for attempt in range(retries + 1):
        if time.time() > end_time:
            break

        try:
            element = driver.find_element(AppiumBy.ID, element_id)

            # 优先使用 .text
            text = getattr(element, 'text', "") or ""
            if text.strip():
                result = text.strip()
                logger.info(f"✅ 通过 .text 获取到文本: '{result}' (ID: {element_id})")
                return result

            # 回退到 get_attribute('text')
            if use_attribute_fallback:
                attr_text = element.get_attribute("text") or ""
                if attr_text.strip():
                    result = attr_text.strip()
                    logger.info(f"✅ 通过 get_attribute('text') 获取到文本: '{result}' (ID: {element_id})")
                    return result

            # 元素存在但无文本
            logger.warning(f"⚠️ 元素存在但文本为空 (ID: {element_id})")
            return ""

        except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
            pass
        except Exception as e:
            logger.error(f"🔥 获取文本时发生未知异常 (ID: {element_id}): {e}")
            return default

        wait_time = 0.2 + attempt * 0.15
        time.sleep(min(wait_time, end_time - time.time()))

    logger.error(f"❌ 超时 {timeout} 秒或耗尽 {retries + 1} 次尝试，未能获取文本 (ID: {element_id})")
    return default

@with_popup_dismiss
def wait_for_toast(
    driver,
    partial_text: str,
    step_name: str = None,
    timeout: int = 5,
    raise_on_not_found: bool = True,
    retries: int = 15,  # 高频短间隔重试，适合瞬态 toast
) -> bool:
    """
    等待包含指定文本片段的 Toast 出现（适用于原生 Android Toast）。
    通过高频轮询 page_source 或 find_element 实现，适应 Toast 瞬态特性。

    :param driver: Appium WebDriver 实例
    :param partial_text: 要匹配的 Toast 文本片段
    :param step_name: 步骤名称（用于日志）
    :param timeout: 最大等待时间（秒），默认 5 秒
    :param raise_on_not_found: 若为 True，未找到时抛出 AssertionError；否则返回 False
    :param retries: 最多重试次数，默认 15 次（配合短间隔）
    :return: 找到返回 True；未找到且 raise_on_not_found=False 时返回 False
    """
    full_step_name = step_name or f"等待 Toast 包含 '{partial_text}'"
    logger.info(f"--- [{full_step_name}] ---")

    # 更精准的 XPath（限定常见 Toast 类，提高准确性）
    xpath = f"//android.widget.Toast[contains(@text, '{partial_text}')]" \
            f" | //*[@class='android.widget.Toast' and contains(@text, '{partial_text}')]" \
            f" | //*[contains(@text, '{partial_text}') and @package]"

    end_time = time.time() + timeout

    for attempt in range(retries + 1):
        if time.time() > end_time:
            break

        try:
            # 尝试查找 toast 元素
            element = driver.find_element(AppiumBy.XPATH, xpath)
            found_text = element.text.strip()
            if found_text:
                logger.info(f"✅ Toast 出现: '{found_text}'")
                return True
        except (NoSuchElementException, StaleElementReferenceException, WebDriverException):
            # 元素未找到或失效，正常现象（toast 可能还没出现或已消失）
            pass
        except Exception as e:
            logger.warning(f"⚠️ 查找 Toast 时发生异常（尝试 {attempt + 1}）: {e}")

        # Toast 是瞬态的，需高频检查（短间隔）
        wait_time = 0.1 + attempt * 0.05  # 初始 0.1s，逐步增至 ～0.85s
        time.sleep(min(wait_time, end_time - time.time()))

    # 超时未找到
    msg = f"❌ 未找到包含 '{partial_text}' 的 Toast（等待 {timeout}s）"
    logger.error(msg)

    if raise_on_not_found:
        raise AssertionError(msg)
    else:
        return False

@with_popup_dismiss
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
    检查页面中 text 属性匹配的元素数量是否 > min_count

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
def find_text_in_list_cards(
    driver,
    list_container_xpath: str = "//androidx.recyclerview.widget.RecyclerView",
    target_text: Union[str, List[str]] = "",
    max_cards: int = 20,
    scroll_if_not_found: bool = True,
    swipe_func: Optional[Callable[..., Any]] = None,  # ✅ 改为 [..., Any]
    max_scrolls: int = 5,
    wait_timeout: int = 10,
    match_all: bool = False,
) -> Tuple[Optional[Any], Union[str, List[str], None]]:  # ✅ 保留原意
    """
    在消息列表中查找包含指定文本的卡片。
    - 若 match_all=False：任一 target_text 匹配即成功（返回第一个匹配项）
    - 若 match_all=True：必须所有 target_text 都出现在同一张卡片中才算成功

    :param driver: Appium WebDriver 实例
    :param list_container_xpath: 列表容器 XPath
    :param target_text: 要查找的文本（字符串或字符串列表）
    :param max_cards: 每屏最多检查的卡片数
    :param scroll_if_not_found: 未找到时是否滑动加载更多
    :param swipe_func: 自定义滑动函数，签名: (driver, direction, distance_pct, duration_ms)
    :param max_scrolls: 最大滑动次数
    :param wait_timeout: 总等待超时时间（秒）
    :param match_all: 是否要求所有文本在同一卡片中
    :return: (card_element, matched_result) 或抛出 AssertionError
    """
    # 标准化 target_text
    if isinstance(target_text, str):
        target_texts = [target_text] if target_text else []
    else:
        target_texts = [str(t) for t in target_text if t]

    if not target_texts:
        logger.error("⚠️ target_text 为空，无法查找")
        raise ValueError("target_text 不能为空")

    full_step_name = f"查找卡片 {'(全部匹配)' if match_all else '(任一匹配)'}: {target_texts}"
    logger.info(f"--- [{full_step_name}] ---")

    end_time = time.time() + wait_timeout
    scroll_count = 0

    while time.time() < end_time and scroll_count <= max_scrolls:
        try:
            # 尝试获取列表容器（不强依赖 WebDriverWait）
            container = None
            try:
                container = driver.find_element(AppiumBy.XPATH, list_container_xpath)
            except (NoSuchElementException, WebDriverException):
                # 容器未出现，可能是加载中
                pass

            # 即使容器存在，也可能无子卡片；我们直接尝试找卡片
            card_xpath = f"{list_container_xpath}/*[self::android.view.ViewGroup or self::android.widget.LinearLayout]"
            cards = []
            try:
                cards = driver.find_elements(AppiumBy.XPATH, card_xpath)
            except Exception as e:
                logger.debug(f"获取卡片列表时异常（可能无卡片）: {e}")

            logger.info(f"🔍 当前屏幕共找到 {len(cards)} 张卡片")

            # 遍历卡片（限制数量）
            for i, card in enumerate(cards[:max_cards]):
                matched_texts = []
                all_matched = True

                for text in target_texts:
                    try:
                        # 安全构造 XPath：处理单引号
                        if "'" not in text:
                            xpath_expr = f".//android.widget.TextView[contains(@text, '{text}')]"
                        else:
                            # 使用 concat 处理含单引号的文本
                            parts = text.split("'")
                            concat_parts = ", \"'\", ".join(f"'{p}'" for p in parts)
                            concat_str = f"concat({concat_parts})"
                            xpath_expr = f".//android.widget.TextView[contains(@text, {concat_str})]"

                        elements = card.find_elements(AppiumBy.XPATH, xpath_expr)
                        if elements:
                            matched_texts.append(text)
                        else:
                            all_matched = False
                            break  # 提前退出（性能优化）

                    except StaleElementReferenceException:
                        all_matched = False
                        break
                    except Exception as e:
                        logger.warning(f"⚠️ 在卡片 {i+1} 中查找 '{text}' 时异常: {e}")
                        all_matched = False
                        break

                # 判断匹配结果
                if match_all:
                    if all_matched and len(matched_texts) == len(target_texts):
                        logger.info(f"✅ 第 {i + 1} 张卡片匹配全部文本: {matched_texts}")
                        return card, matched_texts
                else:
                    if matched_texts:
                        logger.info(f"✅ 第 {i + 1} 张卡片匹配文本: '{matched_texts[0]}'")
                        return card, matched_texts[0]

            # === 未找到，决定是否滑动 ===
            if scroll_if_not_found and swipe_func and scroll_count < max_scrolls and time.time() < end_time:
                logger.info("🔄 当前屏幕未找到目标，正在下滑加载更多...")
                try:
                    swipe_func(driver, direction="down", distance_pct=0.6, duration_ms=500)
                except Exception as e:
                    logger.error(f"⚠️ 滑动失败: {e}")
                time.sleep(min(1.8, end_time - time.time()))
                scroll_count += 1
            else:
                break

        except Exception as e:
            logger.error(f"❌ 查找过程中发生异常: {type(e).__name__}: {e}")
            break

    # 超时或滑动耗尽仍未找到
    if match_all:
        message = f"❌ 滑动 {scroll_count} 次或超时 {wait_timeout}s 后，未找到同时包含所有文本的卡片: {target_texts}"
    else:
        message = f"❌ 滑动 {scroll_count} 次或超时 {wait_timeout}s 后，未找到包含任一目标文本的卡片: {target_texts}"

    logger.error(message)
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