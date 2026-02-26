import pytest
import allure

from Vshow_Page.Vshow_H5.vshow_task_h5 import get_user_id, live_room, search_user
from Vshow_TOOLS.common_actions import *
from Vshow_TOOLS.read_cfg import get_config
from Vshow_TOOLS.more_devices import more_driver
from Vshow_Page.vshow_conf import driver
from Vshow_TOOLS.read_json import read_json
from Vshow_TOOLS.clear_app import clear_app_background
from Vshow_API.Admin_Api import AdminApi



logger = logging.getLogger(__name__)

@allure.feature("主播点击观众头像弹出用户卡片,财富等级和直播等级正常")
class Test_VSHOWBASE_Live11:

    def setup_class(self):
        logger.info("获取设备相关信息和第二个用户信息")
        connet_info = get_config()
        self.parma_info = read_json("Regression_case/Live","Live11")
        self.driver_data_2 = get_config(section="vshow_app_conf", option="vshow_app_conf_2")
        self.driver_data = get_config(section="vshow_app_conf", option="vshow_app_conf")
        self.appium_url_2 = get_config(section="vshow_app_conf", option="vshow_appium_url_2")
        self.user_two = get_config(section="app_account", option="user_1").get("user_name")
        self.pwd_two = get_config(section="app_account", option="user_1").get("passwd")
        self.admin_api = AdminApi(connet_info, service="admin")

    def setup_method(self):
        logger.info("实例化主播用户进行登录，开启直播间")
        self.new_driver = more_driver(self.driver_data_2, self.appium_url_2)
        self.userID, self.userName = get_user_id(self.new_driver)
        live_room(self.new_driver)


    def test_produce(self, driver):
        """
        操作步骤:
            在直播间内，用户点击在线观众头像
        预期结果:
            弹出用户卡片，查看财富等级和直播等级正常
        """
        logger.info("初始化APP，用户登录进去进入直播间并获取后台数据与前台数据是否能相等")
        user_id, _ = get_user_id(driver)
        search_user(driver, self.userID)
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage")+":id/ivAvatar", step_name="点击主播头像进入直播间")

        logger.info("主播操作直播间点击观众的头像弹出用户信息")
        time.sleep(2)
        click_element_by_id(self.new_driver, element_id=self.driver_data_2.get("appPackage")+":id/tv_online_number", step_name="点击在线人数")
        click_element_by_id(self.new_driver, element_id=self.driver_data_2.get("appPackage")+":id/iv_avatar", step_name="点击直播间用户头像弹出用户卡片")
        wait_for_page_text(self.new_driver,["礼物展馆","勋章","送礼","Fans","PK段位",self.userName],match_all=False)
        # 点击卡片无法点击翻转获取不到ID
        live_level = self.new_driver.find_element(AppiumBy.ID, self.driver_data_2.get("appPackage")+":id/ivLiveLevel").text
        wealth_level = self.new_driver.find_element(AppiumBy.ID, self.driver_data_2.get("appPackage")+":id/ivWealthLevel").text
        assert live_level > 0, "获取到的直播等级是有数据的"
        assert wealth_level > 0,"获取到的财富等级是有数据的"


    def teardown_method(self):
        """清除后台"""
        try:
            if hasattr(self, 'new_driver') and self.new_driver:
                self.new_driver.quit()
        except Exception as e:
            logger.warning(f"new_driver quit failed: {e}")
        finally:
            clear_app_background(self.driver_data_2.get("udid"), self.driver_data_2.get("appPackage"))
            clear_app_background(self.driver_data.get("udid"), self.driver_data.get("appPackage"))

if __name__ == "__main__":
    pytest.main(["-s", "VSHOWBASE_Live11.py"])
