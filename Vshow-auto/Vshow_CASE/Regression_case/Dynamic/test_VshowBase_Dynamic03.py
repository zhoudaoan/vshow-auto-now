import logging
import pytest
import allure

from Vshow_Page.Vshow_H5.vshow_task_h5 import join_fedd
from Vshow_TOOLS.common_actions import click_element_by_id, send_keys_to_element, get_text_by_id, \
    click_text_by_resource_id, is_text_count_greater_than_safe, wait_for_page_text, XPathHelper, click
from Vshow_TOOLS.more_devices import more_driver
from Vshow_TOOLS.random_str import generate_random_chinese
from Vshow_TOOLS.read_cfg import get_config
from Vshow_TOOLS.clear_app import clear_app_background



logger = logging.getLogger(__name__)

@allure.feature("检查 话题功能--勾选话题正常发布，且正常进入话题详情页面")
class Test_VSHOWBASE_Dynamic03:

    def setup_method(self):
        logger.info("获取app的配置信息用于退出后台")
        self.driver_data_2 = get_config(section="vshow_app_conf", option="vshow_app_conf_2")
        self.appium_url_2 = get_config(section="vshow_app_conf", option="vshow_appium_url_2")

    def test_produce(self):
        """
        操作步骤:
            检查 话题功能
        预期结果:
            勾选话题正常发布，且正常进入话题详情页面
        """
        logger.info("登录app，进入动态，选择话题发布")
        new_driver = more_driver(self.driver_data_2, self.appium_url_2)
        join_fedd(new_driver)
        click(
            new_driver,
            xpath='//android.widget.LinearLayout[@resource-id="' + self.driver_data_2.get("appPackage") + ':id/topBar"]/android.widget.ImageView[2]',
            step_name="点击广场动态发布页面的发布按钮"
        )
        send_keys_to_element(new_driver, element_id=self.driver_data_2.get("appPackage") + ":id/content", text=generate_random_chinese(51),
                             step_name="输入发布内容")
        topic = get_text_by_id(new_driver, element_id=self.driver_data_2.get("appPackage")+":id/tvTag")
        click_text_by_resource_id(new_driver, topic, self.driver_data_2.get("appPackage")+":id/tvTag","选择话题并点击")
        click_element_by_id(new_driver, element_id=self.driver_data_2.get("appPackage") + ":id/topBarRightBtnTxt", step_name="点击发布按钮")
        # wait_for_toast(new_driver, "发布成功", "发布动态成功，返回发布动态页面")
        if get_text_by_id(new_driver, element_id=self.driver_data_2.get("appPackage")+":id/tvTopic") == topic:
            click_text_by_resource_id(new_driver, topic, self.driver_data_2.get("appPackage")+":id/tvTopic","选择话题并点击")
            if not wait_for_page_text(new_driver, topic):
                click_element_by_id(new_driver, element_id=self.driver_data_2.get("appPackage") + ":id/top_left_back_img",
                                    step_name="点击返回按钮，返回至话题详情页")
            is_text_count_greater_than_safe(new_driver, topic)
            assert get_text_by_id(new_driver, element_id=self.driver_data_2.get("appPackage") + ":id/tv_title") == topic; "获取到的话题详情页标题与话题不一致"

    def teardown_method(self):
        logger.info("清除手机后台指定APP应用")
        clear_app_background(self.driver_data_2.get("udid"),self.driver_data_2.get("appPackage"))


if __name__ == "__main__":
    pytest.main(["-s", "VSHOWBASE_Dynamic03"])
