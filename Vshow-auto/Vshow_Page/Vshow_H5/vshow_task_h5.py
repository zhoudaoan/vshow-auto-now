import time

from appium.webdriver.extensions.android.nativekey import AndroidKey
from Vshow_TOOLS.common_actions import *
import logging
from Vshow_TOOLS.read_cfg import get_config
from Vshow_TOOLS.random_str import create_string_number, generate_random_chinese
app_package = get_config(section="vshow_app_conf",option="vshow_app_conf").get("appPackage")
logger = logging.getLogger(__name__)



# @with_popup_dismiss
def my_deatil(driver):
    click_element_by_id(driver, element_id=app_package+":id/navMe", step_name="进如【我的】页面")
    click_element_by_id(driver, element_id=app_package+":id/mine_user_info_view", step_name="进入到我的详情页面")
    click_element_by_id(driver, element_id=app_package+":id/editButton", step_name="进入我的详情编辑页面")

# @with_popup_dismiss
def back_to_my_home(driver):
    click_element_by_id(driver, element_id=app_package + ":id/backBtn", step_name="回退到我的详情页面")
    click_element_by_id(driver, element_id=app_package + ":id/backButton", step_name="回退到我的页面")

# @with_popup_dismiss
def task_page(driver):
    """
    从我的页面进入奖励页面
    :param driver:
    :return:
    """
    click_element_by_id(driver, element_id=app_package+":id/iv", step_name="从【我的】页面进入到奖励页面")
    wait_for_page_text(driver, "奖励")

# @with_popup_dismiss
def live_room(driver):
    """
    进入直播间，进行开播不做其它操作
    """
    click_element_by_id(
        driver,
        element_id=app_package + ":id/navLive",
        step_name="进入直播间列表页",
        timeout=15
    )
    click_element_by_id(
        driver,
        element_id=app_package + ":id/openLive",
        step_name="进入直播间开播页",
        timeout=15
    )

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((AppiumBy.ID, app_package + ":id/textView"))
    )
    click_text_by_resource_id(
        driver,
        text="聊天",
        element_id=app_package + ":id/textView",
        step_name="选择直播间标签"
    )

    click_element_by_id(
        driver,
        element_id=app_package + ":id/action_before_live_start",
        step_name="点击开始直播",
        timeout=15
    )

    wait_for_page_text(
        driver,
        texts=["所有", "房间", "聊天"],
        timeout=20,
        step_name="等待进入直播间成功"
    )

    logger.info(f"✅ 直播间创建成功")

# @with_popup_dismiss
def live_room_for_title_and_cover(driver):
    """
    进入直播间，设置标题、封面等操作
    :param driver: Appium WebDriver 实例
    :return: str - 直播间标题
    """
    live_title = create_string_number(7)

    click_element_by_id(
        driver,
        element_id=app_package + ":id/openLive",
        step_name="进入直播间开播页",
        timeout=15
    )

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((AppiumBy.ID, app_package + ":id/textView"))
    )
    click_text_by_resource_id(
        driver,
        text="聊天",
        element_id=app_package + ":id/textView",
        step_name="选择直播间标签"
    )

    send_keys(
        driver,
        xpath='//android.widget.EditText[@hint="请输入内容"]',
        text=live_title,
        step_name="输入直播间标题"
    )
    safe_hide_keyboard(driver)

    click_element_by_id(
        driver,
        element_id=app_package + ":id/uploadCoverHint",
        step_name="点击设置封面区域"
    )

    time.sleep(3)
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((AppiumBy.XPATH, '//*[@text="更换封面"]'))
    )
    click_button_by_text(driver, "更换封面", "点击更换封面按钮")

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((AppiumBy.XPATH, '//*[@text="添加照片"]'))
    )
    click_button_by_text(driver, "添加照片", "点击添加照片按钮")

    select_pic_xpath = f'(//android.widget.TextView[@resource-id="{app_package}:id/tvCheck"])[1]'
    click_element_if_exists(
        driver,
        (AppiumBy.XPATH, select_pic_xpath),
        step_name="选择第一张图片"
    )

    click_element_by_id(
        driver,
        element_id=app_package + ":id/ps_tv_complete",
        step_name="点击选择图片的下一步"
    )

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((AppiumBy.ID, app_package + ":id/menu_crop"))
    )
    click_element_by_id(
        driver,
        element_id=app_package + ":id/menu_crop",
        step_name="确认裁剪"
    )
    time.sleep(3)

    # 模拟手动返回
    if wait_for_page_text(driver,["专业模式", "轻松模式"],"判断当前页面是否是直播封面的设置页面"):
        try:
            driver.press_keycode(AndroidKey.BACK)
        except Exception:
            driver.press_keycode(4)


    click_element_by_id(
        driver,
        element_id=app_package + ":id/action_before_live_start",
        step_name="点击开始直播",
        timeout=15
    )

    wait_for_page_text(
        driver,
        texts=["所有", "房间", "聊天"],
        timeout=20,
        step_name="等待进入直播间成功"
    )

    logger.info(f"✅ 直播间创建成功，标题: {live_title}")
    return live_title

# @with_popup_dismiss
def close_live_or_party_room(driver, tag=1):
    """
    观众端退出直播间或者party直播间
    :param tag: 1表示主播端退出直播间，2表示观众端退出直播间，默认是1
    :param driver:
    :return:
    """
    click_element_by_id(driver, element_id=app_package+":id/liveClose", step_name="点击直播间的关闭按钮")
    if tag==1:
        click_element_by_id(driver, element_id=app_package+":id/positiveButton", step_name="点击确认按钮")
        try:
            driver.press_keycode(AndroidKey.BACK)
        except Exception:
            driver.press_keycode(4)
        wait_for_toast(driver, "退出直播间", "退出直播间")

    else:
        wait_for_page_text(driver, "直播已关闭","观众端看到直播关闭页面")
        try:
            driver.press_keycode(AndroidKey.BACK)
        except Exception:
            driver.press_keycode(4)
        wait_for_toast(driver, "退出直播间", "退出直播间")

# @with_popup_dismiss
def join_party_room(driver):
    """
    进入并开启一个 Party 直播间（视频 + 9宫格）
    :param driver: 已初始化的 Appium driver
    """
    logger.info("🎬 开始进入 Party 直播流程...")

    # 1. 进入 Party 页面
    click_element_by_id(driver, element_id=app_package + ":id/navParty", step_name="进入 Party 页面")
    WebDriverWait(driver, 8).until(
        EC.presence_of_element_located((AppiumBy.ID, app_package + ":id/openLive")),
        message="未能在 Party 页面找到 '开播' 按钮"
    )

    # 2. 进入开播页
    click_element_by_id(driver, element_id=app_package + ":id/openLive", step_name="进入 Party 开播页")
    WebDriverWait(driver, 8).until(
        EC.presence_of_element_located((AppiumBy.ID, app_package + ":id/textView")),
        message="未能加载开播页标签栏"
    )

    # 3. 选择“聊天”标签（确保是 Party 直播类型）
    click_text_by_resource_id(
        driver,
        text="聊天",
        element_id=app_package + ":id/textView",
        step_name="选择 Party 直播间标签：聊天"
    )
    time.sleep(0.5)
    # 4. 选择视频模式
    click_element_by_id(
        driver,
        element_id=app_package + ":id/rbtn_party_media_video",
        step_name="选择视频模式"
    )

    # 5. 选择 9 宫格布局
    click_element_by_id(
        driver,
        element_id=app_package + ":id/rbtn_party_person_9",
        step_name="选择 9 宫格布局"
    )

    # 6. 点击开播按钮
    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((AppiumBy.ID, app_package + ":id/action_before_live_start")),
        message="开播按钮未变为可点击状态"
    )
    click_element_by_id(
        driver,
        element_id=app_package + ":id/action_before_live_start",
        step_name="点击开 Party 按钮"
    )

    logger.info("✅ Party 直播已成功开启！")

# @with_popup_dismiss
def login_retroaction(driver):
    """
    登录反馈
    :param driver: 初始化的appium
    :return: None
    """
    click_element_by_id(driver, element_id=app_package+":id/ivFeedback", step_name="点击首页右上角的登录反馈按钮")
    click(
        driver,
        xpath='//android.view.View[@text="登录失败"]',
        step_name="点击登录失败反馈"
    )
    send_keys(driver, xpath='//android.view.View[@resource-id="container"]/android.widget.EditText', text="vshow"*12, step_name="输入问题描述")
    click(
        driver,
        xpath='//android.view.View[@resource-id="container"]/android.view.View[8]',
        step_name="点击上传图片"
    )
    click(
        driver,
        xpath='//android.widget.Button[@text="添加图片"]',
        step_name="点击添加图片按钮"
    )
    click(
        driver,
        xpath='//android.widget.TextView[@text="添加照片"]',
        step_name="点击添加照片按钮"
    )
    click_element_if_exists(
                driver,
                (AppiumBy.XPATH, '(//android.widget.TextView[@resource-id="'+ app_package +':id/tvCheck"])[1]'),
                step_name="选择头像图片--默认选择第一张"
            )
    click_element_by_id(driver, element_id=app_package + ":id/ps_tv_complete", step_name="点击选择图片的下一步")
    send_keys(driver, xpath='//android.view.View[@resource-id="container"]/android.view.View[11]/android.view.View/android.widget.EditText', text="vshow@136.com", step_name="输入邮箱")
    click(
        driver,
        xpath='//android.view.View[@text="提交"]',
        step_name="点击提交按钮"
    )

# @with_popup_dismiss
def dynamic_put_video_or_photo(driver, tag=1):
    """
    :param driver: 初始化的appium
    :param tag: 用来区分需要进行发布视频还是图片动态,1是图片，2是视频
    :return:
    """
    # click_element_by_id(driver, element_id=app_package+":id/ivAdd", step_name="点击发布动态页面的发布按钮")
    click(
        driver,
        xpath='//android.widget.LinearLayout[@resource-id="' + app_package + ':id/topBar"]/android.widget.ImageView[2]',
        step_name="点击广场动态发布页面的发布按钮"
    )

    send_keys_to_element(driver, element_id=app_package+":id/content", text=generate_random_chinese(51), step_name="输入发布内容")
    click(
        driver,
        xpath='//android.widget.ImageButton[@resource-id="' + app_package + ':id/iv_add"]',
        step_name="点击添加照片按钮"
    )
    if tag == 1:
        click(
                    driver,
                    xpath='//android.widget.TextView[@text="添加照片"]',
                    step_name="点击添加照片按钮"
                )
    else:
        click(
            driver,
            xpath='//android.widget.TextView[@text="添加视频"]',
            step_name="点击添加视频按钮"
        )
    click(
        driver,
        xpath='(//android.widget.TextView[@resource-id="' + app_package + ':id/tvCheck"])[1]',
        step_name="选择头像图片/视频--默认选择第一个"
    )
    click_element_by_id(driver, element_id=app_package + ":id/ps_tv_complete", step_name="点击选择图片/视频的下一步")
    if tag == 2:
        click_element_by_id(driver, element_id=app_package + ":id/activity_trim_video_confirm", step_name="点击选择视频的下一步")

    click_element_by_id(driver, element_id=app_package + ":id/topBarRightBtnTxt", step_name="点击发布按钮")
    time.sleep(5)
    # wait_for_toast(driver, "发布成功", "发布动态成功，返回发布动态页面")

# @with_popup_dismiss
def get_user_id(
        driver,
        timeout: int = 10,
        retries: int = 20
):
    """
    通过【我的】页面获取当前用户的 UID 和昵称。
    :param driver: Appium WebDriver 实例
    :param timeout: 总超时时间（秒）
    :param retries: 最大重试次数
    :return: (str user_id, str nickname)
    :raises: RuntimeError 如果最终未能获取用户信息
    """
    click_element_by_id(
        driver,
        element_id=f"{app_package}:id/navMe",
        step_name="进入【我的】页面"
    )

    logger.info("--- 获取用户ID和昵称 ---")
    end_time = time.time() + timeout

    for attempt in range(retries + 1):
        try:
            user_id_el = driver.find_element(AppiumBy.ID, f"{app_package}:id/tv_user_id")
            nickname_el = driver.find_element(AppiumBy.ID, f"{app_package}:id/tv_nickname")

            user_id = user_id_el.text.strip()
            nickname = nickname_el.text.strip()

            if user_id and nickname:
                logger.info(f"✅ 成功获取用户信息: UID={user_id}, 昵称={nickname}")
                return user_id, nickname
            else:
                raise ValueError("用户ID或昵称为空")

        except (NoSuchElementException, StaleElementReferenceException, WebDriverException, ValueError) as e:
            if time.time() < end_time and attempt < retries:
                wait_time = 0.2 + attempt * 0.15
                logger.warning(
                    f"⚠️ 第 {attempt + 1}/{retries + 1} 次获取用户信息失败 "
                    f"({type(e).__name__})，{wait_time:.2f}s 后重试..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"💥 所有重试失败或超时: 无法获取用户信息 | 最终错误: {e}")
                raise RuntimeError("Failed to retrieve user ID and nickname") from e

        except Exception as e:
            logger.error(f"🔥 未知异常: 获取用户信息 | {e}")
            raise
    return None


# @with_popup_dismiss
def search_user(driver, user_id):
    """
    使用userid进行搜索
    :param driver:
    :param user_id:
    :return:
    """
    click(
        driver,
        xpath='//android.widget.LinearLayout[@resource-id="'+app_package+':id/topBarLayout"]/android.widget.ImageView[1]',
        step_name="点击搜索按钮"
    )
    send_keys_to_element(driver, element_id=app_package+":id/etContent", text=user_id, step_name="输入用户id")
    driver.execute_script('mobile: performEditorAction', {'action': 'search'})  # 触发模拟键盘上的搜索动作

# @with_popup_dismiss
def join_fedd(driver):
    """
    进入广场的页面
    :param driver:  初始化的appium
    :return:
    """
    click_element_by_id(driver, element_id=app_package+":id/navDynamic", step_name="点击底部发布动态的按钮")
    click(
        driver,
        xpath='//android.widget.TextView[@text="广场"]',
        step_name="点击广场按钮"
    )

# @with_popup_dismiss
def content_operate(driver,tag):
    """
    进入到动态详情页面操作动态数据点赞，删除和评论
    :param driver: 初始化的appium
    :param tag: 1、点赞，
    :return:
    """
    click_element_by_id(driver, element_id=app_package+":id/tv_content", step_name="进入到动态详情页面")





















