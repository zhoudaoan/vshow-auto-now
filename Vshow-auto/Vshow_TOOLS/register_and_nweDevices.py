import time

from Vshow_TOOLS.common_actions import *
from Vshow_TOOLS.read_cfg import get_config
from Vshow_TOOLS.scroll_to_element import scroll_to_element

logger = logging.getLogger(__name__)

app_conf = get_config(section="vshow_app_conf", option="vshow_app_conf")
# app_package = app_conf.get("appPackage")

def register(driver, app_package):
    """登录 App：先执行三步操作，再判断 tvCountry 是否出现，否则重启重试"""
    max_retries = 3
    app_activity = app_conf.get("appActivity")
    target_element_id = app_package + ":id/tvCountry"

    for attempt in range(1, max_retries + 1):
        logger.info(f"\n🔁 第 {attempt} 次尝试：执行登录前置步骤...")

        try:
            # --- 步骤1: 执行三个前置点击 ---
            click_element_by_id(
                driver,
                element_id=app_package + ":id/rb_test",
                step_name="点击测试环境"
            )
            click_element_by_id(
                driver,
                element_id=app_package + ":id/agreementCheckBox",
                step_name="点击我已阅读并同意"
            )
            click(
                driver,
                xpath='//android.widget.LinearLayout[@resource-id="' + app_package + ':id/loginWayBottom"]/android.widget.ImageView[1]',
                step_name="点击手机登录"
            )

            # --- 步骤2: 判断 tvCountry 是否出现 ---
            logger.info("🔍 等待 'tvCountry' 元素出现...")
            try:
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, target_element_id))
                )
                logger.info("✅ 'tvCountry' 已出现，继续后续登录流程")
                break  # 成功，跳出重试循环
            except Exception as e:
                logger.error(f"❌ 第 {attempt} 次：'tvCountry' 未出现，准备重启 App 重试")

            # --- 步骤3: 杀掉 App 并重启 ---
            try:
                driver.terminate_app(app_package)
                safe_hide_keyboard(driver)
                logger.info(f"✅ 已终止 App: {app_package}")
            except Exception as kill_e:
                logger.error(f"⚠️ 终止 App 失败: {kill_e}")

            time.sleep(2)

            # 重新启动 App
            try:
                driver.activate_app(app_package)
                logger.info(f"✅ 已重启 App: {app_package}")
            except Exception as start_e:
                logger.error(f"⚠️ activate_app 失败，尝试 start_activity: {start_e}")
                driver.start_activity(app_package, app_activity)

            time.sleep(3)  # 等待页面加载

        except Exception as step_e:
            logger.error(f"❌ 第 {attempt} 次执行前置步骤失败: {step_e}")
            if attempt == max_retries:
                raise RuntimeError(f"登录失败：已重试 {max_retries} 次，仍然无法进入登录页。") from step_e

            # 否则等待后重试
            time.sleep(2)

def new_login(driver, user: str, pwd: str,app_package: str,tag: int = 1):
    """
    注册登录或者使用新账号登录操作
    :param app_package: 获取当前app的包名
    :param driver: 初始化的appium
    :param user: 新用户的手机号
    :param pwd: 新用户的密码
    :param tag: 用来区分当前的动作是注册还是登录,1表示注册，2表示登录
    :return:
    """
    if tag == 1:
        click_element_by_id(driver, element_id=app_package + ":id/phoneEdit", step_name="点击输入手机号")
        send_keys_to_element(driver, element_id=app_package + ":id/phoneEdit", text=user,
                             step_name="输入用户名")
        click_element_by_id(driver, element_id=app_package + ":id/nextButton", step_name="点击下一步")
        click_element_if_exists(
            driver,
            (AppiumBy.XPATH, '//android.widget.Button[@resource-id="aliyunCaptcha-btn-close"]'),
            step_name="点击关闭滑动弹窗"
        )
        send_keys_to_element(driver, element_id=app_package + ":id/etCode", text="123456",step_name="输入随机的验证码")
        safe_hide_keyboard(driver)

        send_keys_to_element(driver, element_id=app_package + ":id/etPwd", text=pwd,
                             step_name="设置账号密码")
        safe_hide_keyboard(driver)
        click_element_by_id(driver, element_id=app_package + ":id/tvCommit", step_name="点击下一步按钮")

        click_element_by_id(driver, element_id=app_package + ":id/tv_perfectInfoSexFemale", step_name="选择账号性别--默认女性")
        click_element_by_id(driver, element_id=app_package + ":id/perfectInfoPhoto", step_name="点击头像选择图片")
        click_element_if_exists(
            driver,
            (AppiumBy.XPATH, '(//android.widget.TextView[@resource-id="'+ app_package +':id/tvCheck"])[1]'),
            step_name="选择头像图片--默认选择第一张"
        )
        click_element_by_id(driver, element_id=app_package + ":id/ps_tv_complete", step_name="点击选择头像图片的下一步")
        click_element_by_id(driver, element_id=app_package + ":id/menu_crop", step_name="对头像进行裁剪")


        scroll_to_element(
            driver,
            locator=(AppiumBy.ID, app_package + ":id/completeButton"),
            direction="up",
            max_swipes=10
        )
    else:
        click_element_by_id(driver, element_id=app_package + ":id/phoneEdit", step_name="点击输入手机号")
        send_keys_to_element(driver, element_id=app_package + ":id/phoneEdit", text=user,
                             step_name="输入用户名")
        click_element_by_id(driver, element_id=app_package + ":id/nextButton", step_name="点击下一步")

        send_keys_to_element(driver, element_id=app_package + ":id/phonePassword", text=pwd,
                             step_name="输入密码")
        click_element_by_id(driver, element_id=app_package + ":id/nextButton", step_name="点击登录按钮")

    # 注释系统弹窗
    # click_element_if_exists(
    #     driver,
    #     (AppiumBy.XPATH, '//android.widget.TextView[@resource-id="' + app_package + ':id/negativeButton"]'),
    #     step_name="取消显示弹窗"
    # )
    wait_for_page_text(driver, ["探索", "关注"], "成功登录到app的首页--直播页面")


