import pytest
import allure

from Vshow_Page.Vshow_H5.vshow_task_h5 import get_user_id, live_room, search_user
from Vshow_TOOLS.common_actions import *
from Vshow_TOOLS.read_cfg import get_config
from Vshow_TOOLS.more_devices import more_driver
from Vshow_Page.vshow_conf import driver
from Vshow_TOOLS.clear_app import clear_app_background



logger = logging.getLogger(__name__)

@allure.feature("主播点击观众头像弹出用户卡片---点击头像后正常弹出用户卡片")
class Test_VSHOWBASE_Live10:


    def setup_class(self):
        logger.info("获取设备相关信息和第二个用户信息")
        self.driver_data_2 = get_config(section="vshow_app_conf", option="vshow_app_conf_2")
        self.driver_data = get_config(section="vshow_app_conf", option="vshow_app_conf")
        self.appium_url_2 = get_config(section="vshow_app_conf", option="vshow_appium_url_2")
        self.user_two = get_config(section="app_account", option="user_1").get("user_name")
        self.pwd_two = get_config(section="app_account", option="user_1").get("passwd")

    def setup_method(self):
        logger.info("实例化第二个用户进行登录，开启直播间")
        self.new_driver = more_driver(self.driver_data_2, self.appium_url_2)
        self.userID, _ = get_user_id(self.new_driver)
        click_element_by_id(self.new_driver, element_id=self.driver_data_2.get("appPackage")+":id/navLive", step_name="进入直播间页面")
        live_room(self.new_driver)


    def test_produce(self, driver):
        """
        操作步骤:
            在直播间内，用户点击在线观众头像
        预期结果:
            弹出用户卡片
        """
        logger.info("初始化APP，用户登录进去进入直播间")
        search_user(driver, self.userID)
        click_element_by_id(driver, element_id=self.driver_data_2.get("appPackage")+":id/ivAvatar", step_name="点击头像进入直播间")

        logger.info("主播操作直播间点击观众的头像弹出用户信息")
        click_element_by_id(self.new_driver, element_id=self.driver_data_2.get("appPackage")+":id/tv_online_number", step_name="点击在线人数")
        click_element_by_id(self.new_driver, element_id=self.driver_data_2.get("appPackage")+":id/iv_avatar", step_name="点击直播间用户头像弹出用户卡片")
        wait_for_page_text(self.new_driver,["礼物展馆","勋章", "粉丝团","财富等级","直播等级"])



    def teardown_method(self):
        """
        清除手机后台所有应用
        """
        try:
            if hasattr(self, 'new_driver') and self.new_driver:
                self.new_driver.quit()
        except Exception as e:
            logger.warning(f"new_driver quit failed: {e}")
        finally:
            clear_app_background(self.driver_data_2.get("udid"), self.driver_data_2.get("appPackage"))
            clear_app_background(self.driver_data.get("udid"), self.driver_data.get("appPackage"))


if __name__ == "__main__":
    pytest.main(["-s", "VSHOWBASE_Live10.py"])
