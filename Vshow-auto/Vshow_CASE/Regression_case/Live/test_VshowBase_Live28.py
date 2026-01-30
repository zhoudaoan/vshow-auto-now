import pytest
import allure

from Vshow_Page.Vshow_H5.vshow_task_h5 import live_room
from Vshow_TOOLS.common_actions import *
from Vshow_TOOLS.read_cfg import get_config
from Vshow_TOOLS.more_devices import more_driver
from Vshow_Page.vshow_conf import driver
from Vshow_TOOLS.read_json import read_json
from Vshow_TOOLS.clear_app import clear_app_background
from Vshow_API.Admin_Api import AdminApi



logger = logging.getLogger(__name__)

@allure.feature("直播间发起pk--发起pk随机pk 双方画面正常显示")
class Test_VSHOWBASE_Live28:

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
        logger.info("实例化主播用户进行登录，开启直播间，开启随机PK")
        self.new_driver = more_driver(self.driver_data_2, self.appium_url_2)
        live_room(self.new_driver)
        click_element_by_id(self.new_driver, element_id=self.driver_data_2.get("appPackage")+":id/iv_pk", step_name="在直播间点击PK的icon")
        if self.new_driver.find_element('id', self.driver_data_2.get("appPackage") + ":id/cBox_allow_party"):
            click_element_by_id(self.new_driver, element_id=self.driver_data_2.get("appPackage") + ":id/cBox_allow_party",
                                step_name="取消勾选允许匹配party")


    def test_produce(self, driver):
        """
        操作步骤:
            直播间发起pk
        预期结果:
            发起pk随机pk 双方画面正常显示
        """
        logger.info("初始化APP，用户登录进去进入直播间开启PK--开启随机PK")
        live_room(driver)
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/iv_pk",
                            step_name="在直播间点击PK的icon")
        if driver.find_element('id', self.driver_data.get("appPackage") + ":id/cBox_allow_party"):
            click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/cBox_allow_party",
                                step_name="取消勾选允许匹配party")
        logger.info("点击PK按钮-等待随机PK匹配上队友")
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/btn_matching_start_pk",
                            step_name="在直播间点击观众端PK按钮")
        click_element_by_id(self.new_driver,
                            element_id=self.driver_data_2.get("appPackage") + ":id/btn_matching_start_pk",
                            step_name="在直播间点击主播端PK按钮")

        wait_for_all_elements(self.new_driver, [(AppiumBy.ID,self.driver_data_2.get("appPackage")+":id/tv_pk_time"),
                                                (AppiumBy.ID, self.driver_data_2.get("appPackage") + ":id/tv_other_WinningStreak"),
                                                (AppiumBy.ID,self.driver_data_2.get("appPackage") + ":id/tv_my_WinningStreak"),
                                                ],"判断主播此时的画面是出现PK场景的画面",30)



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
    pytest.main(["-s", "VSHOWBASE_Live28.py"])
