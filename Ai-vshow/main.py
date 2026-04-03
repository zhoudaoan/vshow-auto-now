# main.py
import traceback
from datetime import datetime
from src.config.settings import settings
from src.agents.workflow import app
from src.agents.state import AgentState
from src.drivers.appium_driver import driver_manager
from src.drivers.element_handler import extract_ui_elements
from src.drivers.appium_driver import AppiumDriverManager


def debug_dump_current_screen():
    try:

        drv = driver_manager.driver
        drv.get_screenshot_as_file(settings.CURRENT_SCREEN_PATH)
        AppiumDriverManager()._save_page_source(drv, settings.CURRENT_PAGE_SOURCE_PATH)
        elements = extract_ui_elements()

        print(f"📷 当前截图: {settings.CURRENT_SCREEN_PATH}")
        print(f"🧾 当前页面源码: {settings.CURRENT_PAGE_SOURCE_PATH}")
        print_top_ui_elements(elements, limit=30)
    except Exception as e:
        print(f"❌ debug_dump_current_screen 失败: {repr(e)}")
        traceback.print_exc()

def print_top_ui_elements(elements, limit=20):
    print(f"🔎 当前 UI 元素（最多显示 {limit} 个）:")
    for i, item in enumerate(elements[:limit], start=1):
        print(
            f"[{i}] text={item.get('text', '')!r}, "
            f"id={item.get('resource_id', '')!r}, "
            f"desc={item.get('content_desc', '')!r}, "
            f"bounds={item.get('bounds', '')!r}, "
            f"clickable={item.get('clickable', '')!r}"
        )

if __name__ == "__main__":
    task = "点击当前页面的live按钮，再接着点击开始直播按钮，播10s钟，先点击关闭直播间在点击弹窗确认按钮"
    if not task:
        task = settings.DEFAULT_TASK

    initial_state: AgentState = {
        "task": task,
        "history": [],
        "screenshot_path": "",
        "page_source_path": "",
        "ui_elements": [],
        "planned_actions": [],
        "executed_actions": [],
        "error_message": None,
        "is_complete": False,
        "step_count": 0,
        "max_steps": 10,
    }

    print("🚀 智能体启动...")
    print(f'开始时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f"📝 当前任务: {task}")

    try:
        final_state = app.invoke(initial_state)
        print("✅ 任务结束")
        print("📜 历史操作:")
        for idx, item in enumerate(final_state.get("history", []), start=1):
            print(f"  {idx}. {item}")

        if final_state.get("screenshot_path"):
            print("📷 最后截图:", final_state.get("screenshot_path"))
        if final_state.get("page_source_path"):
            print("🧾 最后页面源码:", final_state.get("page_source_path"))
        print(f'结束时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    except Exception as e:
        print(f"❌ 任务执行出错: {repr(e)}")
        traceback.print_exc()
        try:
            print("🛠️ 尝试导出当前页面调试信息...")
            debug_dump_current_screen()
        except Exception:
            pass
    finally:
        try:
            if driver_manager._driver is not None:
                driver_manager._driver.quit()
                print("👋 Driver 已关闭")
        except Exception as e:
            print(f"⚠️ 关闭 driver 失败: {repr(e)}")