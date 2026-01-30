import subprocess
import logging
import os

logger = logging.getLogger(__name__)

import re
import subprocess
import logging
import os

logger = logging.getLogger(__name__)

def clear_app_background(udid: str, package_name: str) -> bool:
    if not udid or not package_name:
        logger.warning(f"Invalid input: udid={udid!r}, package_name={package_name!r}")
        return False

    adb = os.getenv("ADB_PATH", "adb")
    success = True

    # Step 1: force-stop（保留）
    try:
        result = subprocess.run(
            [adb, "-s", udid, "shell", "am", "force-stop", package_name],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            logger.info(f"✅ force-stop {package_name}")
        else:
            logger.warning(f"⚠️ force-stop failed: {result.stderr.strip()}")
            success = False
    except Exception as e:
        logger.error(f"❌ force-stop error: {e}")
        success = False
    return success


if __name__ == "__main__":
    # 👇 替换成你的真实设备 UDID 和包名
    udid = "5TU8CY85NBZL65I7"          # 用 adb devices 查看
    package_name = "com.baitu.qingshu"   # 替换为你要测试的 App 包名
    # udid = "5e0c4268"          # 用 adb devices 查看
    # package_name = "com.baitu.qingshu"
    success = clear_app_background(udid, package_name)
    print(f"Result: {'Success' if success else 'Failed'}")