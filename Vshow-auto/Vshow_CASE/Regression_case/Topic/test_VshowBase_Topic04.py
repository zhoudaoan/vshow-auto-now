import logging
import pytest
import allure
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from Vshow_Page.Vshow_H5.vshow_task_h5 import join_fedd
from Vshow_TOOLS.common_actions import click_element_by_id, send_keys_to_element, get_text_by_id, \
    click_text_by_resource_id, is_text_count_greater_than_safe, wait_for_page_text, click
from Vshow_TOOLS.more_devices import more_driver
from Vshow_TOOLS.random_str import generate_random_chinese
from Vshow_TOOLS.read_cfg import get_config
from Vshow_TOOLS.clear_app import clear_app_background



logger = logging.getLogger(__name__)

@allure.feature("若用户详情页存在话题活动窗口，点击窗口进入详情页--正常进入详情页")
class Test_VSHOWBASE_Topic04:

    def setup_method(self):
        logger.info("获取app的配置信息用于退出后台")
        self.driver_data_2 = get_config(section="vshow_app_conf", option="vshow_app_conf_2")
        self.appium_url_2 = get_config(section="vshow_app_conf", option="vshow_appium_url_2")

    def test_produce(self):
        """
        操作步骤:
            若用户详情页存在话题活动窗口，点击窗口进入详情页
        预期结果:
            正常进入详情页
        """
        logger.info("登录app，进入动态，选择话题发布")
        new_driver = more_driver(self.driver_data_2, self.appium_url_2)
        click_element_by_id(new_driver, element_id=self.driver_data_2.get("appPackage") + ":id/navDynamic",
                            step_name="点击底部发布动态的按钮")
        click(
            new_driver,
            xpath='//android.widget.TextView[@text="话题"]',
            step_name="点击话题按钮"
        )


    def teardown_method(self):
        logger.info("清除手机后台指定APP应用")
        clear_app_background(self.driver_data_2.get("udid"),self.driver_data_2.get("appPackage"))


if __name__ == "__main__":
    pytest.main(["-s", "VSHOWBASE_Topic04"])
