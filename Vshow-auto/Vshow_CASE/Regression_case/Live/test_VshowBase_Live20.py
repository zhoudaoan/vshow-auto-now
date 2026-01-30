import pytest
import allure

from Vshow_Page.Vshow_H5.vshow_task_h5 import live_room_for_title_and_cover
from Vshow_TOOLS.common_actions import *
from Vshow_TOOLS.read_cfg import get_config
from Vshow_TOOLS.more_devices import more_driver
from Vshow_Page.vshow_conf import driver, login
from Vshow_TOOLS.clear_app import clear_app_background
from Vshow_TOOLS.scroll_to_element import pull_to_refresh

logger = logging.getLogger(__name__)


@allure.feature("点击“开始直播”设置标题、封面等--直播间创建成功，观众可进入观看")
class Test_VSHOWBASE_Live20:

    def setup_class(self):
        logger.info("获取设备相关信息和第二个用户信息")
        self.driver_data_2 = get_config(section="vshow_app_conf", option="vshow_app_conf_2")
        self.driver_data = get_config(section="vshow_app_conf", option="vshow_app_conf")
        self.appium_url_2 = get_config(section="vshow_app_conf", option="vshow_appium_url_2")
        self.user_two = get_config(section="app_account", option="user_1").get("user_name")
        self.pwd_two = get_config(section="app_account", option="user_1").get("passwd")

    def setup_method(self):
        logger.info("实例化主播用户进行登录，开启直播间")
        self.new_driver = more_driver(self.driver_data_2, self.appium_url_2)
        self.live_title = live_room_for_title_and_cover(self.new_driver)



    def test_produce(self, driver):
        """
        操作步骤:
            点击“开始直播”设置标题、封面等--直播间创建成功，观众可进入观看
        预期结果:
            直播间创建成功，观众可进入观看
        """
        logger.info("观众端在直播页搜索进入直播间")
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/ivTagMore",
                            step_name="点击标签的下拉框弹出“精选”按钮")
        # click_button_by_text(driver,text="精选", step_name="切换tab栏到精选的位置")
        # 临时替代方案
        click_button_by_text(driver,text="菲律宾", step_name="切换tab栏到精选的位置")
        logger.info("在精选的tab下拉刷新获取直播间所有数据")
        pull_to_refresh(driver)

        click_text_by_resource_id(driver, text=self.live_title,element_id=self.driver_data.get("appPackage") + ":id/nickname",step_name="根据直播间标题查找直播间并点击进入直播间")
        wait_for_page_text(driver,["所有","房间","聊天"])


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
    pytest.main(["-s", "VSHOWBASE_Live20.py"])
