import logging
import pytest
import allure
from appium.webdriver.common.appiumby import AppiumBy

from Vshow_Page.Vshow_H5.vshow_task_h5 import join_fedd
from Vshow_TOOLS.common_actions import click_element_by_id, send_keys_to_element, get_text_by_id, click
from Vshow_TOOLS.more_devices import more_driver
from Vshow_TOOLS.random_str import generate_random_chinese
from Vshow_TOOLS.read_cfg import get_config
from Vshow_Page.vshow_conf import driver
from Vshow_TOOLS.clear_app import clear_app_background
from Vshow_TOOLS.scroll_to_element import scroll_to_element

logger = logging.getLogger(__name__)

@allure.feature("@好友功能--正常@好友且发布")
class Test_VSHOWBASE_Dynamic04:

    def setup_class(self):
        logger.info("初始化--获取app的配置信息用于退出后台")
        self.driver_data_2 = get_config(section="vshow_app_conf", option="vshow_app_conf_2")
        self.driver_data = get_config(section="vshow_app_conf", option="vshow_app_conf")
        self.appium_url_2 = get_config(section="vshow_app_conf", option="vshow_appium_url_2")

    def setup_method(self):
        self.new_driver = more_driver(self.driver_data_2, self.appium_url_2)
        logger.info("登录app，进入动态，选择话题正常@好友且发布")
        join_fedd(self.new_driver)
        click(
            self.new_driver,
            xpath='//android.widget.LinearLayout[@resource-id="' + self.driver_data.get(
                "appPackage") + ':id/topBar"]/android.widget.ImageView[2]',
            step_name="点击广场动态发布页面的发布按钮"
        )
        send_keys_to_element(self.new_driver, element_id=self.driver_data_2.get("appPackage") + ":id/content", text=generate_random_chinese(51),
                             step_name="输入发布内容")
        click_element_by_id(self.new_driver, element_id=self.driver_data_2.get("appPackage") + ":id/ivA", step_name="点击发布动态页面的@按钮")
        click_element_by_id(self.new_driver, element_id=self.driver_data_2.get("appPackage") + ":id/iv_check", step_name="选择好友")
        click_element_by_id(self.new_driver, element_id=self.driver_data_2.get("appPackage") + ":id/topBarRightBtnTxt", step_name="点击完成按钮")
        click_element_by_id(self.new_driver, element_id=self.driver_data_2.get("appPackage") + ":id/topBarRightBtnTxt", step_name="点击发布按钮")

    def test_produce(self, driver):
        """
        操作步骤:
            @好友功能
        预期结果:
            正常@好友且发布
        """
        logger.info("登录app，进入消息查看消息通知")
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage")+":id/navMe", step_name="进如【我的】页面")
        self.user_name = get_text_by_id(driver, self.driver_data.get("appPackage") + ":id/tv_nickname")
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/navMsg", step_name="点击底部的消息按钮")
        scroll_to_element(
            driver,
            locator=(AppiumBy.XPATH, '//android.widget.TextView[@resource-id="'+self.driver_data.get("appPackage")+':id/nickname" and @text="互动消息"]'),
            direction="up",
            max_swipes=10
        )
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/tvMessage", step_name="点击消息进入动态详情")
        content = get_text_by_id(driver, self.driver_data.get("appPackage") + ":id/tvContent")

        assert self.user_name in content

    def teardown_method(self):
        logger.info("清除手机后台指定APP应用")
        try:
            if hasattr(self, 'new_driver') and self.new_driver:
                self.new_driver.quit()
        except Exception as e:
            logger.warning(f"new_driver quit failed: {e}")
        finally:
            clear_app_background(self.driver_data_2.get("udid"), self.driver_data_2.get("appPackage"))
            clear_app_background(self.driver_data.get("udid"), self.driver_data.get("appPackage"))


if __name__ == "__main__":
    pytest.main(["-s", "VSHOWBASE_Dynamic04"])
