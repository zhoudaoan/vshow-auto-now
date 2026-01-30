import pytest
import allure
from Vshow_Page.vshow_conf import driver, login, logout
from Vshow_TOOLS.clear_app import clear_app_background
from Vshow_Page.Vshow_H5.vshow_task_h5 import *



logger = logging.getLogger(__name__)

@allure.feature("点击编辑资料-修改头像-上传头像正常")
class Test_VSHOWBASE_My02:

    def setup_method(self):
        logger.info("获取设备的udid和设备包名用作最后的清除动作")
        self.uid = get_config(section="vshow_app_conf", option="vshow_app_conf").get("udid")
        self.appPackage = get_config(section="vshow_app_conf", option="vshow_app_conf").get("appPackage")



    def test_produce(self, driver):
        """
        操作步骤:
            点击编辑资料-修改头像
        预期结果:
            图片上传成功
        """
        logger.info("登录app,修改头像")
        my_deatil(driver)
        click_element_by_id(driver, element_id=app_package+":id/drag_item_mask_view", step_name="点击头像")
        click(
                        driver,
                        xpath='//android.widget.TextView[@text="重新上传"]',
                        step_name="点击重新上传按钮"
                    )
        click(
            driver,
            xpath='//android.widget.TextView[@text="从相册选择"]',
            step_name="点击从相册选择按钮"
        )
        click(
            driver,
            xpath='(//android.widget.TextView[@resource-id="' + app_package + ':id/tvCheck"])[1]',
            step_name="选择头像图片--默认选择第一个"
        )
        click_element_by_id(driver, element_id=app_package + ":id/ps_tv_complete", step_name="点击选择图片的下一步")
        click_element_by_id(driver, element_id=app_package + ":id/menu_crop", step_name="对头像进行裁剪")

    def teardown_method(self):
        """
        清除手机后台所有应用
        """
        clear_app_background(self.uid, self.appPackage)


if __name__ == "__main__":
    pytest.main(["-s", "VSHOWBASE_My02.py"])
