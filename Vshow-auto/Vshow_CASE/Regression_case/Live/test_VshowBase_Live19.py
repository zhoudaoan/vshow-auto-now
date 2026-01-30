import pytest
import allure

from Vshow_Page.Vshow_H5.vshow_task_h5 import get_user_id, live_room, search_user
from Vshow_TOOLS.common_actions import *
from Vshow_TOOLS.read_cfg import get_config
from Vshow_TOOLS.more_devices import more_driver
from Vshow_Page.vshow_conf import driver
from Vshow_TOOLS.read_json import read_json
from Vshow_TOOLS.clear_app import clear_app_background
from Vshow_API.Admin_Api import AdminApi

logger = logging.getLogger(__name__)


@allure.feature("余额不足选择付费礼物 点击赠送--礼物无法正常送出且弹出充值窗口")
class Test_VSHOWBASE_Live19:

    def setup_class(self):
        logger.info("获取设备相关信息和第二个用户信息")
        connet_info = get_config()
        self.parma_info = read_json("Regression_case/Live", "Live19")
        self.driver_data_2 = get_config(section="vshow_app_conf", option="vshow_app_conf_2")
        self.driver_data = get_config(section="vshow_app_conf", option="vshow_app_conf")
        self.appium_url_2 = get_config(section="vshow_app_conf", option="vshow_appium_url_2")
        self.user_two = get_config(section="app_account", option="user_1").get("user_name")
        self.pwd_two = get_config(section="app_account", option="user_1").get("passwd")
        self.admin_api = AdminApi(connet_info, service="admin")

    def setup_method(self):
        logger.info("实例化主播用户进行登录，开启直播间")
        self.new_driver = more_driver(self.driver_data_2, self.appium_url_2)
        self.userID, _ = get_user_id(self.new_driver)
        live_room(self.new_driver)


    def test_produce(self, driver):
        """
        操作步骤:
            余额不足选择付费礼物 点击赠送--礼物无法正常送出且弹出充值窗口
        预期结果:
            礼物无法正常送出且弹出充值窗口
        """
        logger.info("获取观众uid进行去除金币")
        user_id, _ = get_user_id(driver)
        coins = self.admin_api.user_profile({"uid":user_id,"_action": "userFund", "commonParam":"value"}).get("coins")
        logger.info(f"获取到的金钱数：{coins}")
        if coins>0:
            parma_info = self.parma_info | {"id": user_id} | {"coins": -coins}
            self.admin_api.user_add_coin(parma_info)

        logger.info("观众端进入直播间")
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage")+":id/navLive", step_name="进如【直播】页面")
        search_user(driver, self.userID)
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/ivAvatar",
                            step_name="点击主播头像进入直播间")
        logger.info("观众端给主播端进行送礼")
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/giftButton",
                            step_name="点击主播直播间的送礼按钮")
        click(
            driver,
            xpath=f'//android.widget.TextView[@resource-id="{self.driver_data.get("appPackage")}:id/tv_tab_title_rtl" and @text="礼物"]',
            step_name="点击礼物的tab"
        )
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/ivGift",
                            step_name="随机点击礼物按钮")
        click_element_by_id(driver, element_id=self.driver_data.get("appPackage") + ":id/singleBtn",
                            step_name="点击赠送按钮")
        wait_for_page_text(driver,["立即充值","遇到充值问题，联系客服"])

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
    pytest.main(["-s", "VSHOWBASE_Live19.py"])
