# import logging
# import pytest
# import allure
# from selenium.webdriver.support.wait import WebDriverWait
#
# from Vshow_Page.Vshow_H5.vshow_task_h5 import get_user_id, search_user, mutually_add_friends
# from Vshow_TOOLS.common_actions import click_element_by_id, wait_for_page_text, click_button_by_text, get_text_by_id
# from Vshow_TOOLS.more_devices import more_driver
# from selenium.webdriver.support import expected_conditions as EC
# from Vshow_TOOLS.read_cfg import get_config
# from Vshow_Page.vshow_conf import driver
# from Vshow_TOOLS.clear_app import clear_app_background
# from Vshow_TOOLS.scroll_to_element import scroll_to_element
# from appium.webdriver.common.appiumby import AppiumBy
#
# logger = logging.getLogger(__name__)
#
#
# @allure.feature("分享动态--分享成功，并可以点击查看")
# class Test_VSHOWBASE_Dynamic10:
#
#     def setup_class(self):
#         logger.info("初始化--获取app的配置信息用于退出后台")
#         self.driver_data_2 = get_config(section="vshow_app_conf", option="vshow_app_conf_2")
#         self.driver_data = get_config(section="vshow_app_conf", option="vshow_app_conf")
#         self.appium_url_2 = get_config(section="vshow_app_conf", option="vshow_appium_url_2")
#
#     def setup_method(self):
#         logger.info("主播端--登录app，进入个人中心动态，删除第一条动态")
#         self.new_driver = more_driver(self.driver_data_2, self.appium_url_2)
#         self.userID_newDriver, _ = get_user_id(self.new_driver)
#
#
#
#
#     def test_produce(self, driver):
#         """
#         操作步骤:
#             分享动态
#         预期结果:
#            分享成功，并可以点击查看
#         """
#         mutually_add_friends(driver, self.userID_newDriver)
#
#     def teardown_method(self):
#         logger.info("清除手机后台指定APP应用")
#         try:
#             if hasattr(self, 'new_driver') and self.new_driver:
#                 self.new_driver.quit()
#         except Exception as e:
#             logger.warning(f"new_driver quit failed: {e}")
#         finally:
#             clear_app_background(self.driver_data_2.get("udid"), self.driver_data_2.get("appPackage"))
#             clear_app_background(self.driver_data.get("udid"), self.driver_data.get("appPackage"))
#
#
# if __name__ == "__main__":
#     pytest.main(["-s", "VSHOWBASE_Dynamic07"])
