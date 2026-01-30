import pytest
import allure

from Vshow_Page.Vshow_H5.vshow_task_h5 import get_user_id, live_room, search_user
from Vshow_TOOLS.common_actions import *
from Vshow_TOOLS.read_cfg import get_config
from Vshow_TOOLS.more_devices import more_driver
from Vshow_Page.vshow_conf import driver, login
from Vshow_TOOLS.read_json import read_json
from Vshow_TOOLS.clear_app import clear_app_background
from Vshow_API.Admin_Api import AdminApi
from Vshow_TOOLS.direction import swipe_



logger = logging.getLogger(__name__)

@allure.feature("直播间右滑清屏--正常清屏")
class Test_VSHOWBASE_Live34:

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
        self.userID, _ = get_user_id(self.new_driver)
        live_room(self.new_driver)



    def test_produce(self, driver):
        """
        操作步骤:
            直播间右滑清屏
        预期结果:
            正常清屏
        """
        logger.info("初始化APP，用户登录进去进入主播直播间--右滑清屏")
        search_user(driver, self.userID)
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage")+":id/ivAvatar", step_name="点击主播头像进入直播间")
        swipe_(driver, "right")
        time.sleep(1)

        assert wait_for_page_text(driver,["所有","房间", "聊天"]) == False; "直播间右滑清屏没有清除掉"



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
    pytest.main(["-s", "VSHOWBASE_Live34.py"])
