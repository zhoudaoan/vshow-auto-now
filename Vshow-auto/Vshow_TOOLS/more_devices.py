from selenium.webdriver.support import expected_conditions as EC
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.wait import WebDriverWait

from Vshow_Page.vshow_conf import force_cold_start
from Vshow_TOOLS.read_cfg import get_config
import Vshow_TOOLS.allure_untils
import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
import Vshow_TOOLS.allure_untils
import logging

from Vshow_TOOLS.read_json import read_json

logger = logging.getLogger(__name__)

def more_driver(vshow_app_config, vshow_appium_url):
    """
    多个设备使用时进行初始化
    "vshow_app_config": {
      "udid": 设备的uid,
      "appPackage": app的包名,
      "appActivity": 参考vshow.cfg,
      "newCommandTimeout": 600,
      "vshow_appium_url": 本地appium的服务地址}
    """
    # 定义内部的生成器函数，用于管理生命周期
    def _driver_lifecycle():
        logger.info("\n--- Setup: more Driver Initializing Appium Driver ---")
        driver_instance = None

        udid = vshow_app_config.get("udid")
        app_package = vshow_app_config.get("appPackage")
        force_cold_start(udid, app_package)

        try:
            options = UiAutomator2Options()
            options.platform_name = "Android"
            options.automation_name = "UiAutomator2"
            options.udid = vshow_app_config.get("udid")
            options.app_package = app_package
            options.app_activity = vshow_app_config.get("appActivity")
            options.no_reset = True
            options.autoGrantPermissions = True
            options.new_command_timeout = vshow_app_config.get("newCommandTimeout")

            driver_instance = webdriver.Remote(
                command_executor=vshow_appium_url,
                options=options
            )
            Vshow_TOOLS.allure_untils.driver = driver_instance
            logger.info("✅ Appium driver connected. Waiting for app to be ready...")

            # ⭐⭐⭐ 等待首页标志性元素出现 ⭐⭐⭐
            home_ready_indicator = f"{app_package}:id/navLive"
            wait_timeout = 15  # 最多等待 15 秒

            WebDriverWait(driver_instance, wait_timeout).until(
                EC.presence_of_element_located((AppiumBy.ID, home_ready_indicator)),
                message=f"App 未在 {wait_timeout} 秒内进入首页（未找到 {home_ready_indicator}）"
            )
            logger.info("✅ App is ready! Home indicator detected.")

        except Exception as e:
            if driver_instance:
                try:
                    driver_instance.quit()
                except:
                    pass
            pytest.fail(f"❌ Failed to initialize or wait for app readiness: {e}")

        yield driver_instance

        # Teardown
        logger.info("\n--- Teardown: Quitting Appium Driver ---")
        if driver_instance:
            try:
                driver_instance.quit()
                logger.info("✅ Appium driver quit successfully.")
            except Exception as e:
                logger.warning(f"⚠️ Error quitting driver: {e}")

    gen = _driver_lifecycle()
    return next(gen)
