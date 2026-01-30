import json
import os


def get_root_path():
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def read_json(dir_name, json_name):
    root = get_root_path()
    dest = os.path.join(root, "Vshow_CASE", dir_name, f"{json_name}.json")
    if not os.path.exists(dest):
        raise Exception(f"不存在该json文件-{dir_name}/{json_name}.json")
    with open(dest, encoding='utf-8') as f:
        data = json.load(f)
        return data

if __name__ == '__main__':
    print(read_json(dir_name="Regression_case/Login", json_name="Login01").get("vshow_app_config"))
    a = read_json(dir_name="Regression_case/Login", json_name="Login01").get("vshow_appium_url")
    print(a)

