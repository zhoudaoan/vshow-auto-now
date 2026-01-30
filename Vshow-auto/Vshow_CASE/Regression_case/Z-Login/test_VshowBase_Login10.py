import logging
import pytest
import allure
from Vshow_TOOLS.read_cfg import get_config
from Vshow_TOOLS.more_devices import more_driver
import random
from Vshow_Page.vshow_conf import driver, logout
from Vshow_TOOLS.register_and_nweDevices import register, new_login
from Vshow_TOOLS.clear_app import clear_app_background
from Vshow_TOOLS.uid_login import uid_login

logger = logging.getLogger(__name__)

@allure.feature("ID登录---id登录，登录成功")
class Test_VSHOWBASE_Login10:
    """
    1、类名只需要更改后面的四位数字
    """

    def setup_method(self):
        logger.info("获取登录的uid和pwd")
        self.driver_data = get_config(section="vshow_app_conf", option="vshow_app_conf")
        self.uid_and_pwd = get_config(section="app_account", option="uid_and_pwd")
        self.uid = self.uid_and_pwd.get("uid")
        self.pwd = self.uid_and_pwd.get("pwd")

    def test_produce(self, driver, logout):
        """
        操作步骤:
            ID登录
        预期结果:
            id登录，登录成功
        """
        logger.info("初始化APP，使用id进行登录")
        uid_login(driver, self.driver_data.get("appPackage"))
        new_login(driver, self.uid, self.pwd,self.driver_data.get("appPackage"), 2)

    def teardown_method(self):
        """
        清除手机后台所有应用
        """

        clear_app_background(self.driver_data.get("udid"),self.driver_data.get("appPackage"))


if __name__ == "__main__":
    pytest.main(["-s", "VSHOWBASE_Login10.py"])
