import logging
import pytest
import allure

from Vshow_Page.Vshow_H5.vshow_task_h5 import get_user_id, search_user
from Vshow_TOOLS.common_actions import click_element_by_id, wait_for_page_text
from Vshow_TOOLS.more_devices import more_driver
from Vshow_TOOLS.read_cfg import get_config
from Vshow_Page.vshow_conf import driver, login
from Vshow_TOOLS.clear_app import clear_app_background

logger = logging.getLogger(__name__)

@allure.feature("输入正确的id搜索--正常搜索到对应内容，点击正常")
class Test_VSHOWBASE_Search01:

    def setup_class(self):
        logger.info("初始化--获取app的配置信息用于退出后台")
        self.driver_data_2 = get_config(section="vshow_app_conf", option="vshow_app_conf_2")
        self.driver_data = get_config(section="vshow_app_conf", option="vshow_app_conf")
        self.appium_url_2 = get_config(section="vshow_app_conf", option="vshow_appium_url_2")
        self.user_two = get_config(section="app_account", option="user_1").get("user_name")
        self.pwd_two = get_config(section="app_account", option="user_1").get("passwd")

    def setup_method(self):
        logger.info("主播端--登录app，进入首页获取userid")
        self.new_driver = more_driver(self.driver_data_2, self.appium_url_2)
        self.userID, self.userName = get_user_id(self.new_driver)

    def test_produce(self, driver):
        """
        操作步骤:
            输入正确的id搜索
        预期结果:
           正常搜索到对应内容，点击正常
        """
        logger.info("观众端--登录app，搜索发布动态的用户-由详情页进行")
        search_user(driver, self.userID)
        wait_for_page_text(driver,[self.userName, self.userID])
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage")+":id/ivAvatar", step_name="点击主播头像进入详情页")
        wait_for_page_text(driver,[self.userName, self.userID,"资料","荣誉墙"])



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
    pytest.main(["-s", "VSHOWBASE_Search01"])
