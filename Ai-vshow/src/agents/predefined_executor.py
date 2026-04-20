# src/agents/predefined_executor.py
import time
import traceback
from typing import Dict, Any, List
from ..config.settings import settings
from ..drivers.appium_driver import driver_manager
from ..actions.mobile_actions import perform_single_action
from ..drivers.element_handler import extract_ui_elements
from ..utils.image_processor import compress_image_to_base64
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import json
import re
from ..utils.logger import logger


def _call_llm_for_recovery(
        error_message: str,
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
    2. **不要返回** 'done' 或任何与原始任务直接相关的动作。
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

        ui_elements = extract_ui_elements()
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

        logger.warning(f"⚠️ LLM 恢复动作解析失败，原始响应: {raw_text}")
        return []

    except Exception as e:
        logger.error(f"❌ 调用 LLM 进行恢复失败: {repr(e)}")
        traceback.print_exc()
        return []


def execute_predefined_test_case(test_case: Dict[str, Any]) -> bool:
    """
    执行包含 predefined_actions 的测试用例。
    返回 True 表示成功，False 表示失败。
    """
    predefined_actions = test_case.get("predefined_actions", [])
    max_retries_per_step = 2

    for idx, action in enumerate(predefined_actions):
        act_str = f"{action['type']} → '{action['value']}'"
        logger.info(f"\n🤖 执行步骤 {idx + 1}/{len(predefined_actions)}: {act_str}")

        success = False
        for attempt in range(max_retries_per_step + 1):
            try:
                result = perform_single_action(action)
                logger.info(f"   ✅ 成功: {result}")
                success = True
                break

            except Exception as e:
                error_msg = str(e).replace("\n", " ")
                logger.error(f"   ❌ 失败 (尝试 {attempt + 1}/{max_retries_per_step + 1}): {error_msg}")

                if attempt < max_retries_per_step:
                    logger.info("   🧠 尝试自动恢复（弹窗/遮挡检测）...")
                    driver_manager.driver.get_screenshot_as_file(settings.CURRENT_SCREEN_PATH)

                    repair_actions = _call_llm_for_recovery(
                        error_message=error_msg,
                        screenshot_path=settings.CURRENT_SCREEN_PATH,
                        next_action=action
                    )

                    if repair_actions:
                        logger.info(f"   🛠️ 执行 {len(repair_actions)} 个修复动作:")
                        for ra in repair_actions:
                            logger.info(f"      - {ra['type']}: '{ra['value']}'")
                            try:
                                perform_single_action(ra)
                            except Exception as re:
                                logger.warning(f"        ⚠️ 修复动作失败: {re}")
                        time.sleep(1)
                    else:
                        logger.warning("   💡 无匹配修复方案，稍后重试...")
                        time.sleep(2)
                else:
                    logger.error(f"   💥 步骤 {idx + 1} 彻底失败，终止执行。")
                    return False
    return True