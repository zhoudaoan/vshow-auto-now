import logging
import pytest
import allure
from selenium.webdriver.support.wait import WebDriverWait

from Vshow_Page.Vshow_H5.vshow_task_h5 import get_user_id, search_user
from Vshow_TOOLS.common_actions import click_element_by_id, wait_for_page_text, click_button_by_text, get_text_by_id
from Vshow_TOOLS.more_devices import more_driver
from selenium.webdriver.support import expected_conditions as EC
from Vshow_TOOLS.read_cfg import get_config
from Vshow_Page.vshow_conf import driver
from Vshow_TOOLS.clear_app import clear_app_background
from Vshow_TOOLS.scroll_to_element import scroll_to_element
from appium.webdriver.common.appiumby import AppiumBy

logger = logging.getLogger(__name__)


@allure.feature("删除动态--删除正常")
class Test_VSHOWBASE_Dynamic09:

    def setup_class(self):
        logger.info("初始化--获取app的配置信息用于退出后台")
        self.driver_data_2 = get_config(section="vshow_app_conf", option="vshow_app_conf_2")
        self.driver_data = get_config(section="vshow_app_conf", option="vshow_app_conf")
        self.appium_url_2 = get_config(section="vshow_app_conf", option="vshow_appium_url_2")

    def setup_method(self):
        logger.info("主播端--登录app，进入个人中心动态，删除第一条动态")
        self.new_driver = more_driver(self.driver_data_2, self.appium_url_2)
        self.userID_newDriver, _ = get_user_id(self.new_driver)
        click_element_by_id(self.new_driver, element_id=self.driver_data_2.get("appPackage") + ":id/mine_user_info_view", step_name="进入到我的详情页面")
        WebDriverWait(self.new_driver, 15).until(
            EC.element_to_be_clickable((AppiumBy.XPATH, "//*[contains(@text, '动态(')]"))).click()
        self.content = get_text_by_id(self.new_driver,element_id=self.driver_data.get("appPackage") + ":id/tvContent")
        click_element_by_id(self.new_driver, element_id=self.driver_data.get("appPackage") + ":id/tvMore",
                            step_name="点击单个动态的更多按钮")
        click_button_by_text(self.new_driver, "删除", "点击底部的弹窗上的删除按钮")
        click_button_by_text(self.new_driver, "确认", "点击弹窗上的确认按钮")


    def test_produce(self, driver):
        """
        操作步骤:
            删除动态
        预期结果:
           删除正常
        """
        logger.info("观众端--登录app，搜索发布动态的用户-由详情页进入")
        search_user(driver, self.userID_newDriver)
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/ivAvatar",
                            step_name="点击主播头像进入详情页")
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((AppiumBy.XPATH, "//*[contains(@text, '动态(')]"))).click()
        assert wait_for_page_text(driver, self.content,step_name="观众端查看主播端的动态是否删除") == False;"观众端去查看主播端删除的内容，主播端删除失败"

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
    pytest.main(["-s", "VSHOWBASE_Dynamic07"])
