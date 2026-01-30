from Vshow_API.Vshow_Common_Api import VshowCommonApi

class AdminApi(VshowCommonApi):
    """
    总后台模块的所有API路径
    """
    def __int__(self, connect_info):
        super(AdminApi, self).__init__(connect_info, service="admin")

    def user_profile(self, parma_info):
        """用户资料获取"""
        uri = "user/user-data"
        return self.get(uri=uri, params=parma_info)

    def user_add_coin(self, parma_info):
        """用户增加/减少金币"""
        uri = "user/add-coin"
        return self.post(uri=uri, data=parma_info)