# src/nodes/executor_node.py
import time
import traceback
from typing import Dict, Any, List, Optional
from ...actions.mobile_actions import perform_single_action
from ...utils.image_processor import compress_image_to_base64
from ...config.settings import settings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import json
import re
from ...drivers.element_handler import extract_ui_elements


def _get_current_ui_elements() -> List[Dict[str, Any]]:
    """
    复用项目中已有的 extract_ui_elements 函数来获取当前UI元素。
    """
    try:
        return extract_ui_elements()
    except Exception as e:
        print(f"⚠️ 调用 extract_ui_elements 失败: {repr(e)}")
        traceback.print_exc()
        return []


def _call_llm_for_recovery(
        error_message: str,
        ui_elements: List[Dict[str, Any]],
        screenshot_path: str,
        next_action: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    当预设动作失败时，调用 LLM 生成修复动作。
    """
    RECOVERY_SYSTEM_PROMPT = """
    你是一个移动应用自动化专家。当前脚本因异常中断，请分析屏幕状态并生成**最少**的动作来清除障碍（如关闭弹窗、点击同意），使得能继续执行下一步的预设动作。

    【重要规则】
    1. **只关注如何恢复**，不要尝试完成整个任务。
    2. **不要返回** 'done' 或任何与原始任务直接相关的动作（如 click_id(openLive)）。
    3. 优先处理弹窗、权限请求、更新提示等遮挡物。
    4. 如果无法确定如何恢复，请返回一个空数组 []。
    5. 只返回纯 JSON 数组，不要解释。
    """

    try:
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )

        # 构建上下文
        context = f"【错误信息】: {error_message}\n"
        context += f"【下一步预设动作】: {next_action}\n"
        context += f"【当前UI元素】: {json.dumps(ui_elements[:20], ensure_ascii=False)}\n"
        context += "请返回用于恢复的JSON动作数组（例如关闭弹窗）。如果无需恢复，请返回[]。"

        # 尝试多模态
        base64_image = compress_image_to_base64(screenshot_path)
        messages = [
            SystemMessage(content=RECOVERY_SYSTEM_PROMPT),
            HumanMessage(content=[
                {"type": "text", "text": context},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
            ])
        ]
        response = llm.invoke(messages)
        raw_text = response.content if isinstance(response.content, str) else str(response.content)

        # 解析响应
        raw_text = re.sub(r"```json\s*|\s*```", "", raw_text, flags=re.IGNORECASE)
        try:
            recovery_actions = json.loads(raw_text)
            if isinstance(recovery_actions, list):
                return recovery_actions
        except json.JSONDecodeError:
            pass

        print(f"⚠️ LLM 恢复动作解析失败，原始响应: {raw_text}")
        return []

    except Exception as e:
        print(f"❌ 调用 LLM 进行恢复失败: {repr(e)}")
        traceback.print_exc()
        return []


def execute_planned_action(state: Dict[str, Any]) -> dict:
    """
    执行器节点：增强版，支持预设动作序列。
    """
    from ...drivers.appium_driver import driver_manager
    driver = driver_manager.driver

    print("🤖 执行器节点被调用")

    # --- 新增逻辑：检查是否存在预设动作 ---
    test_case = state.get("test_case", {})
    predefined_actions = test_case.get("predefined_actions", [])

    if predefined_actions:
        return _execute_predefined_actions(driver, state, predefined_actions)
    else:
        # --- 回退到原有的 LLM 规划执行逻辑 ---
        return _execute_llm_planned_actions(state)


def _execute_llm_planned_actions(state: Dict[str, Any]) -> dict:
    """原有的 LLM 规划动作执行逻辑（保持不变）"""
    history = state.get("history", []) or []
    planned_actions = state.get("planned_actions", []) or []
    current_index = state.get("current_step_index", 0)
    executed_actions = state.get("executed_actions", []) or []
    step_count = state.get("step_count", 0)
    max_steps = state.get("max_steps", 10)
    error_message = None
    is_complete = False

    if not planned_actions or current_index >= len(planned_actions):
        print("⚠️ 没有可执行的动作或已执行完毕")
        return {
            "executed_actions": executed_actions,
            "current_step_index": current_index,
            "step_count": step_count,
            "error_message": error_message,
            "is_complete": is_complete,
            "history": history + ["No actions to execute"]
        }

    action = planned_actions[current_index]
    print(f"🤖 第 {current_index + 1} 步，准备执行动作: {action['type']} - {action['value']}")
    try:
        result = perform_single_action(action)
        print(f"   -> 动作执行成功: {result}")
        executed_actions.append(action)
        step_count += 1
        current_index += 1
        if action.get("type") == "done":
            is_complete = True
            print("✅ 检测到 'done' 动作，任务标记为完成")
    except Exception as e:
        error_msg = f"{action['type']}({action['value']}) -> {repr(e)}"
        print(f"❌ 执行动作失败: {error_msg}")
        error_message = error_msg

    return {
        "executed_actions": executed_actions,
        "current_step_index": current_index,
        "step_count": step_count,
        "error_message": error_message,
        "is_complete": is_complete,
        "history": history + [f"Executed: {action}"]
    }


def _execute_predefined_actions(
        driver,
        state: Dict[str, Any],
        predefined_actions: List[Dict[str, Any]]
) -> dict:
    """执行预设动作序列的核心逻辑"""
    history = state.get("history", []) or []
    executed_actions = state.get("executed_actions", []) or []
    step_count = state.get("step_count", 0)
    max_steps = state.get("max_steps", 10)
    current_index = len(executed_actions)  # 从已执行的动作之后开始
    error_message = None
    is_complete = False

    # 如果所有预设动作都已执行完毕
    if current_index >= len(predefined_actions):
        is_complete = True
        print("✅ 所有预设动作已执行完毕")
        return {
            "executed_actions": executed_actions,
            "current_step_index": current_index,
            "step_count": step_count,
            "error_message": error_message,
            "is_complete": is_complete,
            "history": history + ["Predefined actions completed"]
        }

    action = predefined_actions[current_index]
    print(f"🤖 (预设模式) 第 {current_index + 1} 步，准备执行动作: {action['type']} - {action['value']}")

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            result = perform_single_action(action)
            print(f"   -> 动作执行成功: {result}")
            executed_actions.append(action)
            step_count += 1

            # 如果是最后一个动作，标记为完成
            if current_index + 1 == len(predefined_actions):
                is_complete = True

            return {
                "executed_actions": executed_actions,
                "current_step_index": current_index + 1,
                "step_count": step_count,
                "error_message": error_message,
                "is_complete": is_complete,
                "history": history + [f"Executed (Predefined): {action}"]
            }

        except Exception as e:
            error_msg = f"{action['type']}({action['value']}) -> {repr(e)}"
            print(f"   ❌ 尝试 {attempt + 1}/{max_retries + 1} 失败: {error_msg}")

            if attempt < max_retries:
                # --- 调用 LLM 进行恢复 ---
                print("   🧠 调用 LLM 分析异常并生成修复动作...")
                ui_elements = _get_current_ui_elements(driver)
                screenshot_path = settings.CURRENT_SCREEN_PATH

                repair_actions = _call_llm_for_recovery(
                    error_message=error_msg,
                    ui_elements=ui_elements,
                    screenshot_path=screenshot_path,
                    next_action=action
                )

                if repair_actions:
                    print(f"   🛠️ 执行 {len(repair_actions)} 个修复动作:")
                    for ra in repair_actions:
                        print(f"      - {ra['type']}: '{ra['value']}'")
                        try:
                            perform_single_action(ra)
                        except Exception as re:
                            print(f"        ⚠️ 修复动作失败: {re}")
                    # 修复后，等待一下再重试
                    time.sleep(1)
                else:
                    print("   💡 LLM 未提供有效修复方案，稍后重试...")
                    time.sleep(2)
            else:
                # 所有重试都失败了
                error_message = error_msg
                print("   💥 所有重试均失败，终止执行。")
                break

    return {
        "executed_actions": executed_actions,
        "current_step_index": current_index,  # 保持索引不变，表示此步未完成
        "step_count": step_count,
        "error_message": error_message,
        "is_complete": is_complete,
        "history": history + [f"Failed after retries: {action}"]
    }