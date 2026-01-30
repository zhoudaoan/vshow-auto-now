# import pytest
# import allure
# from Vshow_Page.Vshow_H5.vshow_task_h5 import My_account
# from Vshow_TOOLS.common_actions import *
# from Vshow_TOOLS.read_cfg import get_config
# from Vshow_TOOLS.more_devices import more_driver
# from Vshow_Page.vshow_conf import driver, login, logout
# from Vshow_TOOLS.read_json import read_json
# from Vshow_TOOLS.register_and_nweDevices import register, new_login
# from Vshow_TOOLS.clear_app import clear_app_background
# from Vshow_API.Admin_Api import AdminApi
#
#
#
# logger = logging.getLogger(__name__)
#
# @allure.feature("开party：语音party--开party显示正常；")
# class Test_VSHOWBASE_Party53:
#
#
#     def setup_method(self):
#         logger.info("获取配置相关信息")
#         self.driver_data = get_config(section="vshow_app_conf", option="vshow_app_conf")
#         self.my_account = My_account()
#
#
#
#     def test_produce(self, driver):
#         """
#         操作步骤:
#             开party：语音party
#         预期结果:
#             开party显示正常；
#         """
#
#         self.my_account.join_party_room(driver)
#
#         logger.info("用户在Party直播间开启直播间的摄像头---通过开启摄像头的提示判断")
#         XPathHelper.click(
#             driver,
#             xpath='//android.widget.ImageView[@resource-id="'+self.driver_data.get("appPackage")+':id/moreButton"]',
#             step_name="点击Party直播间的工具按钮"
#         )
#         click_text_by_resource_id(driver, "视频", element_id=self.driver_data.get("appPackage")+":id/tvItem", step_name="点击工具里面的视频按钮")
#         wait_for_toast(driver, "监控人员会进行24小时检查，直播时长开始统计。请维护好直播间的氛围。")
#         assert get_text_by_id(driver, element_id=self.driver_data.get("appPackage")+":id/alertMessage") == "监控人员会进行24小时检查，直播时长开始统计。请维护好直播间的氛围。"; "此时的房间并非Party语音房间，请手动检查"
#
#     def teardown_method(self):
#         """清除后台"""
#         clear_app_background(self.driver_data.get("udid"), self.driver_data.get("appPackage"))
#
# if __name__ == "__main__":
#     pytest.main(["-s", "VSHOWBASE_Party53.py"])
