# import logging
# import pytest
# import allure
# from Vshow_TOOLS.read_json import read_json
# from Vshow_AW.Task_Aw import Task_AW
# from Vshow_TOOLS.read_cfg import get_config
# from Vshow_Page.Vshow_H5.vshow_task_h5 import My_account
# from Vshow_Page.vshow_conf import login, logout, driver
# from Vshow_TOOLS.more_devices import more_driver
#
#
# logger = logging.getLogger(__name__)
#
# @allure.feature("新增任务")
# class Test_VSHOWBASE_taskAdd:
#
#     def setup_class(self):
#         """
#         初始化后台相关信息以及页面调用配置
#         """
#         self.my_account = My_account()
#         connet_info = get_config()
#         self.param_info = read_json("Task_case", "task_add_case")
#         self.task_aw = Task_AW(connet_info)
#         # vshow_app_config = get_config(section="vshow_app_conf", option="vshow_app_conf_2")
#         # vshow_appium_url = get_config(section="vshow_app_conf", option="vshow_appium_url_2")
#
#         # self.driver_one = more_driver(vshow_app_config)
#
#     def setup_method(self):
#         """
#         生成后台任务配置
#         """
#         responses, task_name = self.task_aw.task_add(self.param_info)
#         assert responses == "200"
#         self.task_id = self.task_aw.get_task_lists(task_name)
#
#
#     def test_produce(self):
#         """
#         1、登录popp，进入到我的页面
#         2、在进入到奖励页面
#         """
#         logger.info("XXXXX")
#         # self.my_account.my_home(driver)
#         # self.my_account.task_page(driver)
#         # self.my_account.live_room(driver)
#         # self.my_account.join_party_room(driver)
#         # self.my_account.close_live_or_party_room_live_or_party_room(driver)
#         # self.my_account.join_party_room(self.driver_one)
#         # self.my_account.close_live_or_party_room(self.driver_one)
#         #
#
#     def teardown_method(self):
#         """
#         删除配置的任务
#         """
#         logger.info("删除新增的任务")
#
#         self.task_aw.delete_task(self.task_id)
#
#
# if __name__ == "__main__":
#     pytest.main(["-s", "Task_add_case.py"])
