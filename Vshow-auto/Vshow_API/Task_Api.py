from Vshow_API.Vshow_Common_Api import VshowCommonApi

class TaskApi(VshowCommonApi):
    """
    任务模块的所有API路径
    """
    def __int__(self, connect_info):
        super(TaskApi, self).__init__(connect_info, service="task")

    def add_task(self, param_info):
        """新增任务接口"""
        uri = "backend/task/add"
        return self.post(uri=uri, data=param_info)

    def get_task_list(self, param_info):
        """查询任务接口"""
        uri = "backend/task/getPageList"
        return self.post(uri=uri, data=param_info)

    def delete_task(self, task_id):
        """删除指定任务"""
        uri = "backend/task/delete"
        return self.post(uri=uri, data=task_id)
