import pytest
import allure
from Vshow_TOOLS.common_actions import *
from Vshow_TOOLS.read_cfg import get_config
from Vshow_Page.vshow_conf import driver
from Vshow_TOOLS.clear_app import clear_app_background



logger = logging.getLogger(__name__)

@allure.feature("开party：视频party---开party 显示正常；功能：开启/关闭视频正常")
class Test_VSHOWBASE_Party03:


    def setup_method(self):
        logger.info("获取配置相关信息")
        self.driver_data = get_config(section="vshow_app_conf", option="vshow_app_conf")
        self.my_account = My_account()



    def test_produce(self, driver):
        """
        操作步骤:
            开party：视频party
        预期结果:
            开party 显示正常；功能：开启/关闭视频正常
        """
        logger.info("初始化APP，用户登录进去进入Party直播间关闭直播间的摄像头")
        self.my_account.join_party_room(driver)
        click(
            driver,
            xpath='//android.widget.ImageView[@resource-id="'+self.driver_data.get("appPackage")+':id/moreButton"]',
            step_name="点击Party直播间的工具按钮"
        )
        click_text_by_resource_id(driver, "视频", element_id=self.driver_data.get("appPackage")+":id/tvItem", step_name="点击工具里面的视频按钮")
        wait_for_toast(driver, "关闭视频后，直播时长将停止统计")
        assert get_text_by_id(driver, element_id=self.driver_data.get("appPackage")+":id/alertMessage") == "关闭视频后，直播时长将停止统计"; "此时的房主镜头并非打开的状态，请手动检查"
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage")+":id/positiveButton", step_name="点击二次确认弹窗的确定按钮")
        logger.info("用户在Party直播间开启直播间的摄像头")
        click(
            driver,
            xpath='//android.widget.ImageView[@resource-id="'+self.driver_data.get("appPackage")+':id/moreButton"]',
            step_name="点击Party直播间的工具按钮"
        )
        click_text_by_resource_id(driver, "视频", element_id=self.driver_data.get("appPackage")+":id/tvItem", step_name="点击工具里面的视频按钮")
        wait_for_toast(driver, "监控人员会进行24小时检查，直播时长开始统计。请维护好直播间的氛围。")
        assert get_text_by_id(driver, element_id=self.driver_data.get("appPackage")+":id/alertMessage") == "监控人员会进行24小时检查，直播时长开始统计。请维护好直播间的氛围。"; "此时的房主镜头并非关闭的状态，请手动检查"
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage")+":id/positiveButton", step_name="点击二次确认弹窗的确定按钮")

    def teardown_method(self):
        """清除后台"""
        clear_app_background(self.driver_data.get("udid"), self.driver_data.get("appPackage"))

if __name__ == "__main__":
    pytest.main(["-s", "VSHOWBASE_Party03.py"])
