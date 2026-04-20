# main.py
import argparse
import os
import traceback
from test_cases.loader import load_test_cases
from src.config.settings import settings
from src.agents.workflow import app
from src.agents.state import AgentState, TestCaseConfig
from src.drivers.appium_driver import driver_manager
import allure
from allure_commons.types import AttachmentType

@allure.step("执行AI规划的动作")
def _execute_ai_planned_steps(initial_state: AgentState) -> dict:
    return app.invoke(initial_state)

@allure.step("保存调试附件到报告")
def _attach_debug_artifacts():
    try:
        if os.path.exists(settings.CURRENT_SCREEN_PATH):
            allure.attach.file(
                settings.CURRENT_SCREEN_PATH,
                name="Current Screen",
                attachment_type=AttachmentType.PNG
            )
        if os.path.exists(settings.CURRENT_PAGE_SOURCE_PATH):
            with open(settings.CURRENT_PAGE_SOURCE_PATH, 'r', encoding='utf-8') as f:
                allure.attach(
                    f.read(),
                    name="Current Page Source",
                    attachment_type=AttachmentType.XML
                )
    except Exception as e:
        print(f"⚠️ 附加调试文件到Allure失败: {e}")

def run_single_test_case(test_case: TestCaseConfig):
    allure.dynamic.title(test_case["name"])
    allure.dynamic.description(test_case["description"])

    with allure.step("🧪 初始化测试环境"):
        print(f"\n{'='*60}")
        print(f"🧪 开始执行测试用例: {test_case['name']}")
        print(f"📝 描述: {test_case['description']}")
        print(f"🎯 完整任务: {test_case['task']}")
        print(f"{'='*60}")

    try:
        if "predefined_actions" in test_case and test_case["predefined_actions"]:
            from src.agents.predefined_executor import execute_predefined_test_case
            is_passed = execute_predefined_test_case(test_case)
        else:
            initial_state: AgentState = {
                "original_task": test_case["task"],
                "task": test_case["task"],
                "history": [],
                "screenshot_path": "",
                "page_source_path": "",
                "ui_elements": [],
                "planned_actions": [],
                "executed_actions": [],
                "error_message": None,
                "is_complete": False,
                "step_count": 0,
                "max_steps": test_case["max_steps"],
                "test_case": test_case
            }
            final_state = _execute_ai_planned_steps(initial_state)
            is_passed = final_state.get("is_complete", False)

            if not is_passed:
                _attach_debug_artifacts()
                if final_state.get("error_message"):
                    allure.attach(
                        final_state["error_message"],
                        name="Execution Error",
                        attachment_type=AttachmentType.TEXT
                    )

        if not is_passed:
            _attach_debug_artifacts()

        print(f"✅ 用例 '{test_case['name']}' 执行完毕。状态: {'PASSED' if is_passed else 'FAILED'}")

    except Exception as e:
        allure.attach(
            traceback.format_exc(),
            name="Exception Traceback",
            attachment_type=AttachmentType.TEXT
        )
        _attach_debug_artifacts()
        print(f"❌ 用例 '{test_case['name']}' 执行出错: {repr(e)}")
        raise

def reset_app():
    """重置被测应用：终止并重新激活"""
    with allure.step("🔄 重置被测应用 (Terminate & Activate)"):
        try:
            print(f"🔄 正在重置应用: {settings.APP_PACKAGE}")
            driver_manager.driver.terminate_app(settings.APP_PACKAGE)
            driver_manager.driver.activate_app(settings.APP_PACKAGE)
            print("✅ 应用已成功重置！")
        except Exception as reset_err:
            print(f"⚠️ 重置应用时发生错误: {reset_err}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行移动端AI自动化测试用例 (Allure版)")
    parser.add_argument("--cases", type=str, default="test_cases", help="测试用例目录路径")
    args = parser.parse_args()

    print("🚀 启动AI自动化测试执行器 (Allure Report)...")

    test_cases = []
    try:
        test_cases = load_test_cases(args.cases)
        if not test_cases:
            print("⚠️ 未找到任何测试用例。")
            exit(1)

        total = len(test_cases)
        for idx, case in enumerate(test_cases):
            run_single_test_case(case)

            # ✅ 关键逻辑：如果不是最后一个用例，则重置App
            if idx < total - 1:
                reset_app()
            else:
                print("🏁 所有用例已执行完毕，跳过最后的App重置。")

        print("\n✅ 所有用例执行完毕。")
        print("📊 要查看Allure报告，请在项目根目录运行:")
        print("   allure serve allure-results")

    except KeyboardInterrupt:
        print("\n🛑 用户中断了测试执行。")
        # 可选：在这里也可以调用 reset_app() 做清理，但通常不需要
        raise
    except Exception as e:
        print(f"💥 主流程发生未预期错误: {e}")
        # 如果已经跑了一些用例，也可以选择重置，但非必须
        raise
    finally:
        try:
            if driver_manager._driver is not None:
                driver_manager._driver.quit()
                print("👋 Appium Driver 已关闭")
        except Exception as e:
            print(f"⚠️ 关闭 driver 失败: {repr(e)}")