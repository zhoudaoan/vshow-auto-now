import datetime
import time


def get_timestamps():
    # 获取当前时间
    now = datetime.datetime.now().strftime("%Y-%m-%d 00:00:00")

    # 计算前一天和后一天时间
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")

    # 转换为UNIX时间戳（毫秒级）
    now_ts = int(time.mktime(datetime.datetime.strptime(now, "%Y-%m-%d %H:%M:%S").timetuple())) * 1000
    yesterday_ts = int(time.mktime(datetime.datetime.strptime(yesterday, "%Y-%m-%d %H:%M:%S").timetuple())) * 1000
    tomorrow_ts = int(time.mktime(datetime.datetime.strptime(tomorrow, "%Y-%m-%d %H:%M:%S").timetuple())) * 1000

    return {
        "current": now_ts,
        "yesterday": yesterday_ts,
        "tomorrow": tomorrow_ts
    }


if __name__ == "__main__":
    print(get_timestamps())
