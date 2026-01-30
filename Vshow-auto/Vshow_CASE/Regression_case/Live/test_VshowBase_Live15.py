import pytest
import allure

from Vshow_Page.Vshow_H5.vshow_task_h5 import get_user_id, live_room, search_user
from Vshow_TOOLS.common_actions import *
from Vshow_TOOLS.read_cfg import get_config
from Vshow_TOOLS.more_devices import more_driver
from Vshow_Page.vshow_conf import driver
from Vshow_TOOLS.read_json import read_json
from Vshow_TOOLS.clear_app import clear_app_background

logger = logging.getLogger(__name__)


@allure.feature("上麦用户可以正常开启视频--开启视频主播点击可以打开麦上用户的视频/关闭")
class Test_VSHOWBASE_Live15:

    def setup_class(self):
        logger.info("获取设备相关信息和第二个用户信息")
        self.parma_info = read_json("Regression_case/Live", "Live11")
        self.driver_data_2 = get_config(section="vshow_app_conf", option="vshow_app_conf_2")
        self.driver_data = get_config(section="vshow_app_conf", option="vshow_app_conf")
        self.appium_url_2 = get_config(section="vshow_app_conf", option="vshow_appium_url_2")
        self.user_two = get_config(section="app_account", option="user_1").get("user_name")
        self.pwd_two = get_config(section="app_account", option="user_1").get("passwd")

    def setup_method(self):
        logger.info("实例化主播用户进行登录，开启直播间")
        self.new_driver = more_driver(self.driver_data_2, self.appium_url_2)
        self.userID, _ = get_user_id(self.new_driver)
        live_room(self.new_driver)

    def test_produce(self, driver):
        """
        操作步骤:
            上麦用户可以正常开启视频--开启视频主播点击可以打开麦上用户的视频/关闭
        预期结果:
            可以打开麦上用户的视频/关闭
        """
        logger.info("初始化APP，用户登录进去进入直播间并获取后台数据与前台数据是否能相等")
        search_user(driver, self.userID)
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/ivAvatar",
                            step_name="点击主播头像进入直播间")
        logger.info("观众端点击上麦按钮")
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/iv_up_mic",
                            step_name="点击直播间上麦按钮")
        wait_for_page_text(driver, ["您已成功排麦，等待主播同意"])
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/positiveButton",
                            step_name="点击排麦成功的OK按钮")
        logger.info("主播端点击接受按钮")
        click_element_by_id(self.new_driver, element_id=self.driver_data_2.get("appPackage") + ":id/iv_up_mic",
                            step_name="点击直播间上麦按钮")
        click_element_by_id(self.new_driver, element_id=self.driver_data_2.get("appPackage") + ":id/ivAccept",
                            step_name="点击接受上麦按钮")
        logger.info("观众端出现语音的图标")
        wait_for_all_elements(driver, (AppiumBy.ID, self.driver_data.get("appPackage") + ":id/positiveButton"),
                              step_name="接受上麦后观众端出现麦克风的图标")
        logger.info("观众端点击按钮开启视频")
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/linear_mic",
                            step_name="观众端点击上麦头像，弹出开启视频按钮")
        click(
            driver,
            xpath='//android.widget.TextView[@text="开启视频"]',
            step_name="点击开启视频按钮"
        )
        wait_for_all_elements(driver, [(AppiumBy.ID, self.driver_data.get("appPackage") + "id/iv_bottom_mask"),
                                       (AppiumBy.ID, self.driver_data.get("appPackage") + ":id/iv_top_mask"),
                                       (AppiumBy.ID, self.driver_data.get("appPackage") + ":id/upMicClose")],
                              step_name="观众端用户开启上麦视频")
        logger.info("主播端操作打开或者关闭麦上用户的视频")
        click_element_by_id(self.new_driver, element_id=self.driver_data.get("appPackage") + ":id/iv_video",
                            step_name="主播端点击开启视频按钮")
        wait_for_all_elements(self.new_driver, [(AppiumBy.ID, self.driver_data.get("appPackage") + "id/iv_bottom_mask"),
                                       (AppiumBy.ID, self.driver_data.get("appPackage") + ":id/iv_top_mask"),
                                       (AppiumBy.ID, self.driver_data.get("appPackage") + ":id/upMicClose")],
                              step_name="主播端能看到用户的视频")
        click_element_by_id(self.new_driver, element_id=self.driver_data.get("appPackage") + ":id/iv_video",
                            step_name="主播端点击关闭视频按钮")

        wait_for_all_elements(self.new_driver, [(AppiumBy.ID, self.driver_data.get("appPackage") + "id/iv_bottom_mask"),
                                       (AppiumBy.ID, self.driver_data.get("appPackage") + ":id/iv_top_mask"),
                                       (AppiumBy.ID, self.driver_data.get("appPackage") + ":id/upMicClose")],
                              step_name="主播端看不到用户的视频", visible=False)



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
    pytest.main(["-s", "VSHOWBASE_Live15.py"])
