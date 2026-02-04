import logging
import time

from Vshow_TOOLS.common_actions import click_element_by_id, safe_hide_keyboard
from Vshow_TOOLS.read_cfg import get_config

logger = logging.getLogger(__name__)

app_conf = get_config(section="vshow_app_conf", option="vshow_app_conf")

def uid_login(driver, app_package):
    app_activity = app_conf.get("appActivity")
    click_element_by_id(
        driver,
        element_id=app_package + ":id/rb_test",
        step_name="点击测试环境"
    )
    driver.terminate_app(app_package)
    # safe_hide_keyboard(driver)
    time.sleep(2)
    try:
        driver.activate_app(app_package)
        logger.info(f"✅ 已重启 App: {app_package}")
    except Exception as start_e:
        logger.error(f"⚠️ activate_app 失败，尝试 start_activity: {start_e}")
        driver.start_activity(app_package, app_activity)
    click_element_by_id(
        driver,
        element_id=app_package + ":id/agreementCheckBox",
        step_name="点击我已阅读并同意"
    )
    XPathHelper.click(
        driver,
        xpath='//android.widget.LinearLayout[@resource-id="' + app_package + ':id/loginWayBottom"]/android.widget.ImageView[2]',
        step_name="点击手机登录"
    )




