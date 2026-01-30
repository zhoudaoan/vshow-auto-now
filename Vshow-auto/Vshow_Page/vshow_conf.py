"""初始化Appium Driver"""
import re
import subprocess
import time
from selenium.webdriver.support import expected_conditions as EC
import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.wait import WebDriverWait

from Vshow_TOOLS.read_cfg import get_config
import Vshow_TOOLS.allure_untils
from Vshow_TOOLS.login_app import LoginPage
import logging

logger = logging.getLogger(__name__)

def force_cold_start(udid: str, package_name: str):
    """强制冷启动：彻底杀死进程 + 清理最近任务（尽力而为）"""
    if not udid or not package_name:
        logger.warning("Skip cold start: invalid udid or package")
        return

    adb = "adb"

    # Step 1: 强制停止（关键！）
    try:
        subprocess.run([adb, "-s", udid, "shell", "am", "force-stop", package_name],
                       capture_output=True, timeout=5)
        logger.info(f"✅ Force-stopped {package_name}")
    except Exception as e:
        logger.debug(f"Force-stop error (non-fatal): {e}")

    # Step 2: 尝试清理最近任务（MIUI 兼容）
    try:
        result = subprocess.run(
            [adb, "-s", udid, "shell", "dumpsys", "activity", "recents"],
            capture_output=True, text=True, timeout=6
        )
        if result.returncode == 0:
            # 匹配所有 #taskId 且包名匹配的行（兼容 mHiddenTasks）
            pattern = r'#(\d+).*?A=[^:]*:' + re.escape(package_name)
            task_ids = set(re.findall(pattern, result.stdout))
            for tid in task_ids:
                subprocess.run([adb, "-s", udid, "shell", "am", "stack", "remove", tid],
                               capture_output=True, timeout=2)
            if task_ids:
                logger.info(f"🧹 Removed {len(task_ids)} recent/hidden tasks for {package_name}")
    except Exception as e:
        logger.debug(f"Task cleanup error (non-fatal): {e}")

    # Step 3: 再次 force-stop（对抗 MIUI 保活）
    time.sleep(0.5)
    try:
        subprocess.run([adb, "-s", udid, "shell", "am", "force-stop", package_name],
                       capture_output=True, timeout=5)
    except:
        pass


@pytest.fixture(scope="function")
def driver():
    logger.info("\n--- Setup: Initializing Appium Driver ---")
    driver_instance = None
    vshow_app_config = get_config(section="vshow_app_conf", option="vshow_app_conf")
    vshow_appium_url = get_config(section="vshow_app_conf", option="vshow_appium_url")

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

    # Teardown 不变
    logger.info("\n--- Teardown: Quitting Appium Driver ---")
    if driver_instance:
        try:
            driver_instance.quit()
            logger.info("✅ Appium driver quit successfully.")
        except Exception as e:
            logger.warning(f"⚠️ Error quitting driver: {e}")


@pytest.fixture
def login(driver):
    """
    自动登录 fixture，调用 LoginPage.login()
    """
    logger.info("\n--- Setup: Logging in ---")
    try:
        login_page = LoginPage(driver)
        login_page.login()  # 可替换为配置文件读取
        logger.info("✅ Login successful.")
    except Exception as e:
        pytest.fail(f"❌ Login failed: {e}")
    return login_page

@pytest.fixture
def logout(driver):
    """
    退出账号 fixture，调用 LoginPage.logout()
    """
    yield
    logger.info("\n--- Setup: Logout in ---")
    try:
        logout_page = LoginPage(driver)
        logout_page.logout()
        logger.info("✅ Logout successful.")
    except Exception as e:
        pytest.fail(f"❌ Logout failed: {e}")
    return logout_page

