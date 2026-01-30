import pytest
import allure
from Vshow_Page.vshow_conf import driver, login, logout
from Vshow_TOOLS.clear_app import clear_app_background
from Vshow_Page.Vshow_H5.vshow_task_h5 import *
from Vshow_TOOLS.random_str import create_string_number


logger = logging.getLogger(__name__)

@allure.feature("点击编辑资料-修改昵称-修改成功")
class Test_VSHOWBASE_My03:


    def setup_method(self):
        logger.info("获取设备的udid和设备包名用作最后的清除动作")
        self.uid = get_config(section="vshow_app_conf", option="vshow_app_conf").get("udid")
        self.appPackage = get_config(section="vshow_app_conf", option="vshow_app_conf").get("appPackage")


    def test_produce(self, driver):
        """
        操作步骤:
            点击编辑资料-修改昵称
        预期结果:
            修改成功
        """
        logger.info("登录app,修改昵称")
        my_deatil(driver)
        click_element_by_id(driver, element_id=app_package+":id/nickname", step_name="点击昵称")
        send_keys_to_element(driver, element_id=app_package+":id/nickname", text=create_string_number(5), step_name="输入新的昵称")

        if wait_for_page_text(driver, ["提示：本次修改昵称需要扣除10000金币。"]):
            click(
                driver,
                xpath='//android.widget.TextView[@text="保存"]',
                step_name="点击保存按钮"
            )
            click_element_by_id(driver, element_id=app_package + ":id/positiveButton", step_name="点击确认花费1000金币修改名称")
            if not wait_for_page_text(driver, ["保存成功"]):
                return True
        else:
            click(
                driver,
                xpath='//android.widget.TextView[@text="保存"]',
                step_name="点击保存按钮"
            )
            wait_for_page_text(driver, ["成功"])

        return None

    def teardown_method(self):
        """
        清除手机后台所有应用
        """
        clear_app_background(self.uid, self.appPackage)


if __name__ == "__main__":
    pytest.main(["-s", "VSHOWBASE_My02.py"])
