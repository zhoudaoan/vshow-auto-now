import logging
import pytest
import allure

from Vshow_Page.Vshow_H5.vshow_task_h5 import join_fedd, dynamic_put_video_or_photo
from Vshow_TOOLS.read_cfg import get_config
from Vshow_Page.vshow_conf import driver
from Vshow_TOOLS.clear_app import clear_app_background




logger = logging.getLogger(__name__)

@allure.feature("上传图片发布,发布成功")
class Test_VSHOWBASE_Dynamic01:

    def setup_method(self):
        logger.info("获取app的配置信息用于退出后台")
        self.driver_data = get_config(section="vshow_app_conf", option="vshow_app_conf")

    def test_produce(self, driver):
        """
        操作步骤:
            上传图片发布
        预期结果:
            上传成功，发布成功
        """
        logger.info("登录app，进入动态，上传图片")
        join_fedd(driver)
        dynamic_put_video_or_photo(driver)



    def teardown_method(self):
        logger.info("清除手机后台指定APP应用")
        clear_app_background(self.driver_data.get("udid"),self.driver_data.get("appPackage"))


if __name__ == "__main__":
    pytest.main(["-s", "VSHOWBASE_Dynamic01"])
