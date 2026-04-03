# src/agents/nodes/screenshot_node.py
import time
import traceback
from typing import Dict, Any
from ...config.settings import settings
from ...drivers.appium_driver import driver_manager
from ...drivers.element_handler import extract_ui_elements, dismiss_common_popups

def take_screenshot(state: Dict[str, Any]) -> dict:
    print("📸 正在截取屏幕...")
    try:
        drv = driver_manager.driver
        dismiss_common_popups(max_rounds=2)
        drv.get_screenshot_as_file(settings.CURRENT_SCREEN_PATH)
        ui_elements = extract_ui_elements()
        print(f"✅ 截图保存至: {settings.CURRENT_SCREEN_PATH}")
        return {
            "screenshot_path": settings.CURRENT_SCREEN_PATH,
            "page_source_path": settings.CURRENT_PAGE_SOURCE_PATH,
            "ui_elements": ui_elements,
            "error_message": None
        }
    except Exception as e:
        print(f"❌ 截图失败: {repr(e)}")
        traceback.print_exc()
        return {
            "screenshot_path": "",
            "page_source_path": "",
            "ui_elements": [],
            "error_message": repr(e),
            "history": state["history"] + [f"Screenshot error: {repr(e)}"]
        }