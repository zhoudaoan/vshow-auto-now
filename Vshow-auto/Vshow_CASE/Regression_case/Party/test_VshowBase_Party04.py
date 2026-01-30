import time

import pytest
import allure
from Vshow_Page.Vshow_H5.vshow_task_h5 import get_user_id, join_party_room, search_user, \
    close_live_or_party_room
from Vshow_TOOLS.common_actions import *
from Vshow_TOOLS.read_cfg import get_config
from Vshow_TOOLS.more_devices import more_driver
from Vshow_Page.vshow_conf import driver, login, logout
from Vshow_TOOLS.clear_app import clear_app_background



logger = logging.getLogger(__name__)

@allure.feature("party房主开启/关闭麦位--关闭-麦位展示一个锁的标识，且用户无法上麦 开启-用户正常上下麦")
class Test_VSHOWBASE_Party04:

    def setup_class(self):
        logger.info("获取设备相关信息和第二个用户信息")
        self.driver_data_2 = get_config(section="vshow_app_conf", option="vshow_app_conf_2")
        self.driver_data = get_config(section="vshow_app_conf", option="vshow_app_conf")
        self.appium_url_2 = get_config(section="vshow_app_conf", option="vshow_appium_url_2")
        self.user_two = get_config(section="app_account", option="user_1").get("user_name")
        self.pwd_two = get_config(section="app_account", option="user_1").get("passwd")

    def setup_method(self):
        logger.info("实例化主播用户进行登录，开启Party直播间")
        self.new_driver = more_driver(self.driver_data_2, self.appium_url_2)
        self.userID, _= get_user_id(self.new_driver)
        join_party_room(self.new_driver)
        logger.info("在Party直播间关闭上麦位")
        time.sleep(4)
        click_element_by_id(self.new_driver, element_id=self.driver_data.get("appPackage")+":id/fl_person_9_seat_position_5", step_name="点击上麦位，弹出上麦位设置")

        click_button_by_text(self.new_driver, "关闭麦位", "点击关闭麦位按钮")

    def test_produce(self, driver):
        """
        操作步骤:
            party房主开启/关闭麦位
        预期结果:
            关闭-麦位展示一个锁的标识，且用户无法上麦 开启-用户正常上下麦
        """
        logger.info("初始化APP，获取当前用户昵称")
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage")+":id/navMe", step_name="进如【我的】页面")
        user_name = get_text_by_id(driver, element_id=self.driver_data.get("appPackage")+":id/tv_nickname")
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage")+":id/navLive", step_name="进如【直播】页面")

        logger.info("用户登录进去进入party直播间")
        search_user(driver, self.userID)
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage")+":id/ivAvatar", step_name="点击主播头像进入party直播间")

        logger.info("观众端在直播间判断是否包含锁的标识的resource-ID")
        wait_for_all_elements(driver,(AppiumBy.ID, self.driver_data.get("appPackage") + ":id/iv_close_seat"),"观众端判断Party直播间是否包含锁的标识的resource-ID")
        # click_element_by_id(driver, element_id=self.driver_data.get("appPackage")+":id/tv_close_seat", step_name="观众端点击带锁标识的上麦位")
        # wait_for_toast(driver, "您已成功排麦，等待主播同意", raise_on_not_found=False)

        logger.info("主播在party直播间，开启上麦位")
        click_element_by_id(self.new_driver, element_id=self.driver_data.get("appPackage")+":id/fl_person_9_seat_position_5", step_name="点击带锁标识的上麦位")

        click_button_by_text(self.new_driver, "开启麦位", "点击开启麦位按钮")

        logger.info("观众在party直播间，点击上麦位")
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage")+":id/fl_person_9_seat_position_3", step_name="点击上麦位")
        wait_for_toast(driver, "您已成功排麦，等待主播同意")
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/positiveButton", step_name="点击确认按钮")

        logger.info("主播在party直播间，点击同意上麦")
        click_element_by_id(self.new_driver, element_id=self.driver_data_2.get("appPackage")+":id/iv_up_mic", step_name="点击主播直播间排队上麦按钮")
        click_element_by_id(self.new_driver, element_id=self.driver_data_2.get("appPackage")+":id/ivAccept", step_name="点击接受上麦按钮")

        logger.info("获取上麦用户的昵称进行校验是否上麦成功")
        wait_for_page_text(self.new_driver, texts=user_name)
        wait_for_page_text(driver, texts=user_name)

        logger.info("观众端离开上麦位")
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/iv_motion_webp", step_name="点击上麦用户头像唤起底部弹窗")
        click_button_by_text(driver, "离开座位","点击离开座位的按钮")
        wait_for_page_text(driver, texts=user_name)

        logger.info("主播退出直播间")
        close_live_or_party_room(self.new_driver)


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
    pytest.main(["-s", "VSHOWBASE_Party04.py"])
