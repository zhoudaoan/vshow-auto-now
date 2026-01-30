
import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
import Vshow_TOOLS.allure_untils
import logging

from Vshow_TOOLS.read_json import read_json

logger = logging.getLogger(__name__)

def more_driver(vshow_app_config, appium_uri):
    """
    多个设备使用时进行初始化
    "vshow_app_config": {
      "udid": 设备的uid,
      "appPackage": app的包名,
      "appActivity": 参考vshow.cfg,
      "newCommandTimeout": 600,
      "vshow_appium_url": 本地appium的服务地址}
    """
    # subprocess.run(
    #     ["adb", "-s", vshow_app_config.get("udid"), "shell", "settings", "put", "system", "screen_off_timeout",
    #      "2147483647"], check=True)
    # logger.info("✅ 屏幕常亮已启用（screen_off_timeout=2147483647）")
    logger.info("\n--- Setup: Initializing  More Appium Driver ---")
    driver_instance = None
    try:
        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.automation_name = "UiAutomator2"
        options.udid = vshow_app_config.get("udid")
        options.app_package = vshow_app_config.get("appPackage")
        options.app_activity = vshow_app_config.get("appActivity")
        options.no_reset = True
        options.autoGrantPermissions = True
        options.new_command_timeout = vshow_app_config.get("newCommandTimeout")

        driver_instance = webdriver.Remote(
            command_executor=appium_uri,
            options=options
        )
        Vshow_TOOLS.allure_untils.driver = driver_instance
        logger.info("✅ Appium driver initialized successfully.")
    except Exception as e:
        pytest.fail(f"❌ Failed to initialize Appium driver: {e}")

    return driver_instance

if __name__ == '__main__':
    a = read_json(dir_name="Regression_case/Login", json_name="Login01")
    config = a["vshow_app_config"]
