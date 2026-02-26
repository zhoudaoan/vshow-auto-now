
from Vshow_TOOLS.common_actions import *
from Vshow_TOOLS.read_cfg import get_config
from Vshow_TOOLS.scroll_to_element import scroll_to_element

logger = logging.getLogger(__name__)

class LoginPage:
    def __init__(self, driver):
        self.driver = driver
        self.user = get_config(section="app_account",option="user")
        self.app_conf = get_config(section="vshow_app_conf",option="vshow_app_conf")

    def login(self):
        """登录 App：先执行三步操作，再判断 tvCountry 是否出现，否则重启重试"""
        max_retries = 3
        app_package = self.app_conf.get("appPackage")
        app_activity = self.app_conf.get("appActivity")
        target_element_id = app_package+":id/tvCountry"



        for attempt in range(1, max_retries + 1):
            logger.info(f"\n🔁 第 {attempt} 次尝试：执行登录前置步骤...")

            try:
                # --- 步骤1: 执行三个前置点击 ---
                click_element_by_id(
                    self.driver,
                    element_id=app_package+":id/rb_test",
                    step_name="点击测试环境"
                )
                click_element_by_id(
                    self.driver,
                    element_id=app_package+":id/agreementCheckBox",
                    step_name="点击我已阅读并同意"
                )
                click(
                    self.driver,
                    xpath='//android.widget.LinearLayout[@resource-id="'+app_package+':id/loginWayBottom"]/android.widget.ImageView[1]',
                    step_name="点击手机登录"
                )

                # --- 步骤2: 判断 tvCountry 是否出现 ---
                logger.info("🔍 等待 'tvCountry' 元素出现...")
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.ID, target_element_id))
                    )
                    print("✅ 'tvCountry' 已出现，继续后续登录流程")
                    break  # 成功，跳出重试循环
                except Exception as e:
                    logger.error(f"❌ 第 {attempt} 次：'tvCountry' 未出现，准备重启 App 重试")

                # --- 步骤3: 杀掉 App 并重启 ---
                try:
                    self.driver.terminate_app(app_package)
                    if self.driver.is_keyboard_shown():
                        self.driver.hide_keyboard()
                    logger.info(f"✅ 已终止 App: {app_package}")
                except Exception as kill_e:
                    logger.error(f"⚠️ 终止 App 失败: {kill_e}")

                time.sleep(2)

                # 重新启动 App
                try:
                    self.driver.activate_app(app_package)
                    logger.info(f"✅ 已重启 App: {app_package}")
                except Exception as start_e:
                    logger.error(f"⚠️ activate_app 失败，尝试 start_activity: {start_e}")
                    self.driver.start_activity(app_package, app_activity)

                time.sleep(3)  # 等待页面加载

            except Exception as step_e:
                logger.error(f"❌ 第 {attempt} 次执行前置步骤失败: {step_e}")
                if attempt == max_retries:
                    raise RuntimeError(f"登录失败：已重试 {max_retries} 次，仍然无法进入登录页。") from step_e

                # 否则等待后重试
                time.sleep(2)

        # --- 外层：tvCountry 已出现，继续后续登录 ---
        click_element_by_id(self.driver, element_id=app_package+":id/phoneEdit", step_name="点击输入手机号")
        send_keys_to_element(self.driver, element_id=app_package+":id/phoneEdit", text=self.user.get("user_name"), step_name="输入用户名")
        click_element_by_id(self.driver, element_id=app_package+":id/nextButton", step_name="点击下一步")

        send_keys_to_element(self.driver, element_id=app_package+":id/phonePassword", text=self.user.get("passwd"), step_name="输入密码")
        click_element_by_id(self.driver, element_id=app_package+":id/nextButton", step_name="点击登录按钮")

        time.sleep(5)
        click_element_if_exists(
            self.driver,
            (AppiumBy.XPATH, '//android.widget.TextView[@resource-id="'+app_package+':id/negativeButton"]'),
            step_name="取消显示弹窗"
        )
        wait_for_page_text(self.driver, ["探索"],"成功登录到app的首页--直播页面")
        logger.info("✅ 登录成功！")

    def logout(self):
        """退出账号"""
        app_package = self.app_conf.get("appPackage")
        click_element_by_id(self.driver, element_id=app_package + ":id/navMe",
                            step_name="进如【我的】页面")
        click_element_by_id(self.driver, element_id=app_package + ":id/btn_settings",
                            step_name="点击进入设置页面")
        scroll_to_element(
            self.driver,
            locator=(AppiumBy.ID, app_package + ":id/tv_logout_label"),
            direction="up",
            max_swipes=10
        )
        click_button_by_text(self.driver, "退出登录", "点击退出按钮，退出APP")
        self.driver.terminate_app(app_package)





