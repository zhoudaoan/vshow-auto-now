import json
from pathlib import Path
from typing import List, Dict, Any, Optional


def load_test_cases(directory: str = "test_cases", case_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    加载测试用例目录下的所有 JSON 用例。

    :param directory: 测试用例目录路径，默认为 "test_cases"
    :param case_name: 可选，指定要加载的用例名称（精确匹配 'name' 字段）
    :return: 测试用例列表（即使只加载一个，也返回单元素列表）
    """
    test_cases = []
    test_dir = Path(directory)

    if not test_dir.exists():
        raise FileNotFoundError(f"测试用例目录 {test_dir} 不存在")

    # 获取所有 JSON 文件
    json_files = list(test_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"目录 {test_dir} 中未找到任何 .json 测试用例文件")

    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                case_data = json.load(f)
                # 如果指定了 case_name，只保留匹配项
                if case_name is not None:
                    if case_data.get("name") == case_name:
                        test_cases.append(case_data)
                        print(f"✅ 加载指定测试用例: {case_name} (来自 {file_path.name})")
                        break  # 找到即可退出（假设 name 唯一）
                else:
                    test_cases.append(case_data)
                    print(f"✅ 加载测试用例: {case_data.get('name', file_path.name)}")
        except Exception as e:
            print(f"❌ 加载测试用例失败 {file_path}: {e}")
            continue

    # 如果指定了 case_name 但未找到
    if case_name is not None and not test_cases:
        available_names = []
        for fp in json_files:
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "name" in data:
                        available_names.append(data["name"])
            except:
                pass
        raise ValueError(
            f"未找到名为 '{case_name}' 的测试用例。\n"
            f"可用的用例名称: {available_names}"
        )

    return test_cases