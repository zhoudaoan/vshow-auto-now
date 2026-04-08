import traceback
from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from ..config.settings import settings

class AppiumDriverManager:
    def __init__(self):
        self._driver = None

    def _build_options(self) -> UiAutomator2Options:
        options = UiAutomator2Options()
        options.automation_name = "UiAutomator2"
        options.platform_name = "Android"
        options.device_name = settings.ANDROID_DEVICE_NAME
        options.app_package = settings.APP_PACKAGE
        options.app_activity = settings.APP_ACTIVITY
        options.no_reset = True
        options.auto_grant_permissions = True
        options.new_command_timeout = 600
        return options

    def create_session(self):
        try:
            options = self._build_options()
            drv = webdriver.Remote(settings.APPIUM_SERVER_URL, options=options)
            print("✅ Appium Session 创建成功")

            try:
                WebDriverWait(drv, 20).until(
                    EC.presence_of_element_located(("id", settings.HOME_READY_ID))
                )
                print("✅ 已进入首页")
            except Exception as e:
                print(f"⚠️ 首页校验失败，但 driver 仍可用: {repr(e)}")

            try:
                drv.get_screenshot_as_file(settings.STARTUP_DEBUG_SCREEN_PATH)
                print(f"📷 已保存启动截图: {settings.STARTUP_DEBUG_SCREEN_PATH}")
            except Exception as se:
                print(f"⚠️ 保存启动截图失败: {repr(se)}")

            self._save_page_source(drv, settings.STARTUP_PAGE_SOURCE_PATH)
            return drv

        except Exception as e:
            print(f"❌ Driver 初始化失败: {repr(e)}")
            traceback.print_exc()
            return None

    def _save_page_source(self, drv, path: str):
        try:
            source = drv.page_source
            with open(path, "w", encoding="utf-8") as f:
                f.write(source)
            print(f"🧾 已保存 page_source: {path}")
        except Exception as e:
            print(f"⚠️ 保存 page_source 失败: {repr(e)}")

    @property
    def driver(self):
        if self._driver is None:
            self._driver = self.create_session()
            if self._driver is None:
                raise RuntimeError("driver 初始化失败")
        return self._driver

driver_manager = AppiumDriverManager()