import copy
from datetime import timedelta, datetime, timezone
from time import strptime, mktime
from Vshow_API.Task_Api import TaskApi
from Vshow_API.Activity_Api import ActivityApi
import json_tools


class VshowCommonAW:
    def __init__(self, connect_info):
        self.account = connect_info.get("account")
        self.task_api = TaskApi(connect_info, service="task")
        self.activity_api = ActivityApi(connect_info)

    @staticmethod
    def get_data_time(day=0, hour=0, minutes=0, seconds=0):
        """
        生成时间
        Args:
            day(int)(M): 生成距离当前days天的时间（可以为负数，负数表示过去）
            hour(int)(M): 生成距离当前hours小时的时间（可以为负数，负数表示过去）
            minutes(int)(M): 生成距离当前minutes分钟的时间（可以为负数，负数表示过去）
            seconds(int)(M): 生成距离当前seconds秒的时间（可以为负数，负数表示过去）
        Returns:
            date_time: "%Y-%m-%d %H:%M:%S"
        """
        tz_utc_8 = timezone(timedelta(hours=8))
        d_t = datetime.now(tz=tz_utc_8) + timedelta(days=day, hours=hour, minutes=minutes, seconds=seconds)
        return d_t.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def format_query_info(page_index=1, page_size=2, **kwargs):
        """
        生成vshow任务模块默认查询参数模板
        """
        example = {"pageIndex": page_index, "pageSize": page_size, "taskType": "",
                   "pageSorts": [{"asc": False, "column": "id"}]}
        example.update(kwargs)
        return example

    @staticmethod
    def catch_error(func, *args, **kwargs):
        """
        异常捕获函数
        Args:
            func(M): 函数引用地址，例self.testcase.query_something
            *args: 函数参数
            **kwargs: 函数参数
        Returns:
            res(dict): 对应接口返回值
        """
        try:
            func(*args, **kwargs)
        except Exception as error:
            return error.args[0].json()
        else:
            raise Exception("未捕获到异常")

    @staticmethod
    def jsondiff(before, after, update_info):
        """
        对两个字典进行json比对
        Args:
            before(dict)(M): 修改前的结构体
            after(dict)(M): 修改后的结构体，请保持修改前后结构体的层次结构一致
            update_info(dict)(M): 更新的字典
        Returns:
            is_update(bool): 是否修改成功，True：成功； False：失败
        """
        keys = update_info.keys()
        count = 0
        pre_keys = [[key, False] for key in keys]
        results = json_tools.diff(before, after)
        filter_res = [res for res in results if res.get("replace")]
        for f_res in filter_res:
            for i, [key, flag] in enumerate(pre_keys):
                if not flag and key in f_res.get("replace"):
                    count += 1
                    pre_keys[i][1] = True
        return count == len(keys)

    @staticmethod
    def is_time_in_begin_and_end(begin_time, end_time, test_time=None, test_timestamp=None):
        """
        判断时间是否在beginTime与endTime范围内
        Args:
            begin_time(str)(M): 开始时间，格式为"%Y-%m-%d %H:%M:%S"
            end_time(str)(M): 结束时间，格式为"%Y-%m-%d %H:%M:%S"
            test_time(str)(O): 测试时间字符，格式为"%Y-%m-%d %H:%M:%S"
            test_timestamp(float)(O): 测试时间时间戳，支持s形式与ms形式，与test_time只能存在一个
        Returns:
            True or False
        """

        def _date_to_timestamp(date_time):
            time_a = strptime(date_time, "%Y-%m-%d %H:%M:%S")
            return round(mktime(time_a) * 1000)

        if test_timestamp and test_time:
            raise Exception("请勿同时传入test_timestamp与test_time")
        begin_time = _date_to_timestamp(begin_time)
        end_time = _date_to_timestamp(end_time)
        if test_timestamp:
            if len(str(int(test_timestamp))) == 10:
                test_timestamp = round(test_timestamp * 1000)
            return begin_time <= test_timestamp <= end_time

        if test_time:
            return begin_time <= _date_to_timestamp(test_time) <= end_time

    @staticmethod
    def replace_key_name(dict_info, **kwargs):
        """
        替换dict_info中key的名字
        Args：
            dict_info(M): 替换被替换的字典
            **kwargs：键值对形式替换，如oldKey="NewKey"
        Returns:
            replaced_dict: 替换后的字典
        """
        replaced_dict = copy.deepcopy(dict_info)
        for key, value in kwargs.items():
            if replaced_dict.get(key):
                replaced_dict[value] = replaced_dict[key]
        return replaced_dict
