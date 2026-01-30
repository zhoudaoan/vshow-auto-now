import logging
from Vshow_TOOLS.random_str import create_string_number
from Vshow_AW.Vshow_Common_Aw import VshowCommonAW
from Vshow_TOOLS.get_unix_timestamp import get_timestamps

logger = logging


class Task_AW(VshowCommonAW):
    """
    任务模块的封装
    """

    def __init__(self, connet_info):
        super(Task_AW, self).__init__(connet_info)

    def task_add(self, param_info):
        """新增任务"""
        random_name = "Vshow_Autotest+" + create_string_number(4)
        startDate = get_timestamps().get("current")
        endDate = get_timestamps().get("tomorrow")
        data = {"startDate": startDate, "endDate": endDate, "taskIntro": random_name, "taskTitle": random_name,
                "taskActionTitle": random_name}
        param = param_info | data
        response_code = self.task_api.add_task(param).get("code")
        return response_code, random_name

    def get_task_lists(self, task_name) -> int:
        """获取自动化新增的任务ID"""
        try:
            task_list = self.task_api.get_task_list(self.format_query_info()).get("data").get("records")
            if not task_list:
                logger.warning("任务列表为空")
                raise Exception("没有获取到任务id，请检查")

            matching_tasks = []
            for task in task_list:
                task_intro = task.get("taskIntro")
                task_title = task.get("taskTitle")
                if task_name == task_intro and task_name == task_title:
                    matching_tasks.append(task.get("id"))

            if not matching_tasks:
                logger.warning("没有找到符合条件的任务")
                raise Exception("没有获取到任务id，请检查")

            return matching_tasks[0] if len(matching_tasks) == 1 else matching_tasks
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            raise "获取任务列表失败, 请排查"

    def delete_task(self, task_id):
        """删除任务"""
        response_code = self.task_api.delete_task(task_id).get("code")
        logger.info(f"删除的任务ID：{task_id}")
        assert response_code == 200
        return response_code
