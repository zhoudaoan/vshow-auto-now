import os
import configparser
import json

pro_dir = os.path.dirname(os.path.abspath(__file__))  # 当前文件路径


# 读取配置文件
def get_config(filename="vshow.cfg", section="environment", option="testEnvironment"):
    """
    :param filename 文件名称
    :param section: 服务
    :param option: 配置参数
    :return:返回配置信息
    """

    config_path = os.path.join(os.path.abspath(pro_dir + os.path.sep + ".."), filename)

    # 关键修复：禁用 interpolation，避免 % 被误解析
    conf = configparser.ConfigParser(interpolation=None)

    conf.read(config_path, encoding="utf-8")
    config = json.loads(conf.get(section, option))
    return config


if __name__ == '__main__':
    cookie = get_config(section="vshow_app_conf", option="vshow_app_conf")
    print(cookie.get("appPackage"))