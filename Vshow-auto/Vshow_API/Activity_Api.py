from Vshow_API.Vshow_Common_Api import VshowCommonApi

class ActivityApi(VshowCommonApi):
    """
    活动相关的API路径
    """
    def __init__(self, connect_info):
        print("被调用到了")
        super(ActivityApi, self).__init__(connect_info, service="activity")

    def new_api(self):
        pass


