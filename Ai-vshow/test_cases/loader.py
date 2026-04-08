# test_cases/loader.py
import json
from pathlib import Path
from typing import List, Dict, Any


def load_test_cases(directory: str = "test_cases") -> List[Dict[str, Any]]:
    test_cases = []
    test_dir = Path(directory)

    if not test_dir.exists():
        raise FileNotFoundError(f"测试用例目录 {test_dir} 不存在")

    for file_path in test_dir.glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                case_data = json.load(f)
                test_cases.append(case_data)
                print(f"✅ 加载测试用例: {case_data.get('name', file_path.name)}")
        except Exception as e:
            print(f"❌ 加载测试用例失败 {file_path}: {e}")
            continue

    return test_cases