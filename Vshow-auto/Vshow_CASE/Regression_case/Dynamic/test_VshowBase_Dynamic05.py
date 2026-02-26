import logging
import pytest
import allure
from selenium.webdriver.support.wait import WebDriverWait

from Vshow_Page.Vshow_H5.vshow_task_h5 import get_user_id, search_user
from Vshow_TOOLS.common_actions import click_element_by_id, find_text_in_list_cards
from Vshow_TOOLS.more_devices import more_driver
from selenium.webdriver.support import expected_conditions as EC
from Vshow_TOOLS.read_cfg import get_config
from Vshow_Page.vshow_conf import driver
from Vshow_TOOLS.clear_app import clear_app_background
from Vshow_TOOLS.scroll_to_element import scroll_to_element
from appium.webdriver.common.appiumby import AppiumBy

logger = logging.getLogger(__name__)


@allure.feature("动态点赞--正常点赞成功")
class Test_VSHOWBASE_Dynamic05:

    def setup_class(self):
        logger.info("初始化--获取app的配置信息用于退出后台")
        self.driver_data_2 = get_config(section="vshow_app_conf", option="vshow_app_conf_2")
        self.driver_data = get_config(section="vshow_app_conf", option="vshow_app_conf")
        self.appium_url_2 = get_config(section="vshow_app_conf", option="vshow_appium_url_2")
        self.user_two = get_config(section="app_account", option="user_1").get("user_name")
        self.pwd_two = get_config(section="app_account", option="user_1").get("passwd")

    def setup_method(self):
        logger.info("主播端--登录app，进入动态，发布动态")
        self.new_driver = more_driver(self.driver_data_2, self.appium_url_2)
        self.userID, _ = get_user_id(self.new_driver)

    def test_produce(self, driver):
        """
        操作步骤:
            动态点赞
        预期结果:
           正常点赞成功
        """
        logger.info("观众端--登录app，搜索发布动态的用户-由详情页进行")
        _, self.userName = get_user_id(driver)
        click_element_by_id(driver, element_id=self.driver_data_2.get("appPackage")+":id/navLive", step_name="进入直播间页面")
        search_user(driver, self.userID)
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/ivAvatar",
                            step_name="点击主播头像进入详情页")
        # 用户详情页面进入到动态列表页面
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((AppiumBy.XPATH, "//*[contains(@text, '动态(')]"))).click()
        click_element_by_id(driver, element_id=self.driver_data_2.get("appPackage") + ":id/tv_content", step_name="进入到动态详情页面")

        scroll_to_element(
            driver,
            locator=(AppiumBy.ID, self.driver_data.get("appPackage") + ":id/ivLikeNo"),
            direction="up",
            max_swipes=10
        )
        logger.info("主播端--查看收到的点赞信息通知")
        click_element_by_id(self.new_driver, element_id=self.driver_data.get("appPackage") + ":id/navMsg",
                            step_name="点击底部的消息按钮")
        scroll_to_element(
            self.new_driver,
            locator=(AppiumBy.XPATH, '//android.widget.TextView[@resource-id="' + self.driver_data.get(
                "appPackage") + ':id/nickname" and @text="互动消息"]'),
            direction="up",
            max_swipes=10
        )

        find_text_in_list_cards(self.new_driver, target_text=["赞了你的动态", self.userName], match_all=True)

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
    pytest.main(["-s", "VSHOWBASE_Dynamic05"])
