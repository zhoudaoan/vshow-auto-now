import logging
import pytest
import allure

from Vshow_API.Admin_Api import AdminApi
from Vshow_TOOLS.read_json import read_json
from Vshow_TOOLS.read_cfg import get_config

logger = logging.getLogger(__name__)

@allure.feature("用例标题")
class Test_VSHOWBASE_XXXX:
    """
    1、类名只需要更改后面的四位数字
    """

    def setup_class(self):
        """
        用例的初始化类似init
        """
        logger.info("用例初始化以及参数的准备")
        connet_info = get_config()
        # self.param_info = read_json("test_case_path")
        self.parma_info = read_json("Regression_case/Live","Live11")
        self.admin_api = AdminApi(connet_info, service="admin")

        print("this is init")

    def setup_method(self):
        """
        用例的前置：
        """
        logger.info("用例的前置")
        print("this is setup")

    def test_produce(self):
        """
        操作步骤:
            用例步骤放在这里
        预期结果:
            用例结果放在这里
        """
        logger.info("用例的步骤")
        parma_info = self.parma_info | {"uid": "37146369"}
        user_profile = self.admin_api.user_profile(parma_info)
        print(user_profile)

    def teardown_method(self):
        """
        用例的后置
        """
        logger.info("用例数据的处理")
        print("this is teardown")


if __name__ == "__main__":
    pytest.main(["-s", "去除test的文件名.py"])
