import traceback
from typing import Dict, Any

from ...config.settings import settings
from ...drivers.appium_driver import driver_manager
from ...drivers.element_handler import extract_ui_elements, dismiss_common_popups
from ...utils.task_verifier import verify_live_task_progress


def take_screenshot(state: Dict[str, Any]) -> dict:
    print("📸 正在截取屏幕...")
    try:
        drv = driver_manager.driver

        dismiss_common_popups(max_rounds=2)
        drv.get_screenshot_as_file(settings.CURRENT_SCREEN_PATH)

        ui_elements = extract_ui_elements()

        live_started = state.get("live_started", False)
        live_ended = state.get("live_ended", False)

        new_live_started, new_live_ended, is_task_complete, verify_reason = verify_live_task_progress(
            task=state.get("task", ""),
            ui_elements=ui_elements,
            live_started=live_started,
            live_ended=live_ended,
        )

        print(f"🧩 已提取 UI 元素: {len(ui_elements)} 个")
        print(f"🔎 任务验证结果: {verify_reason}")
        print(f"✅ 截图保存至: {settings.CURRENT_SCREEN_PATH}")

        return {
            "screenshot_path": settings.CURRENT_SCREEN_PATH,
            "page_source_path": settings.CURRENT_PAGE_SOURCE_PATH,
            "ui_elements": ui_elements,
            "live_started": new_live_started,
            "live_ended": new_live_ended,
            "is_complete": is_task_complete,
            "error_message": None,
            "history": state.get("history", []) + [f"截图并验证页面: {verify_reason}"]
        }

    except Exception as e:
        print(f"❌ 截图失败: {repr(e)}")
        traceback.print_exc()

        return {
            "screenshot_path": "",
            "page_source_path": "",
            "ui_elements": [],
            "error_message": repr(e),
            "history": state.get("history", []) + [f"Screenshot error: {repr(e)}"]
        }