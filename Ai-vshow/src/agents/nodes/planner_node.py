import json
import re
import traceback
from typing import Dict, Any, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ...config.settings import settings
from ...utils.image_processor import compress_image_to_base64


PLANNER_SYSTEM_PROMPT = """
你是一个专业的移动应用自动化专家。你的任务是帮助用户完成在手机上的操作。

【重要规则】
1. 应用包名必须是：com.baitu.qingshu
2. 只能使用我提供的“当前屏幕可用元素”中的信息，不要编造不存在的元素
3. 优先使用 resource-id，其次 text，再其次 bounds / xpath
4. 页面切换至少等待3秒，弹窗出现至少等待2秒
5. 如果检测到弹窗，优先关闭弹窗，再继续原任务
6. 如果当前页面无法直接完成任务，请给出最合理的下一步操作
7. 只返回纯 JSON 数组，不要解释，不要注释，不要 Markdown，不要代码块
8. 只有在你能确认整个任务已经完成时，才允许输出 done
9. 如果当前只是任务执行中的中间页面，不要输出 done

【动作类型】
- click_id: 点击指定resource-id的元素
- click_text: 点击指定文本的元素
- click_xpath: 点击指定xpath的元素
- click_coordinate: 点击指定坐标，value格式如 {"x":100,"y":200}
- click_bounds: 点击指定bounds的中心，value格式如 "[0,0][100,100]"
- type_text: 输入文本
- swipe: 滑动，value 只能是 up/down/left/right
- back: 返回
- wait: 等待指定秒数
- done: 任务完成

【输出要求】
1. 必须返回 JSON 数组
2. 每个元素必须包含 type 和 value
3. 不要输出数组以外的任何内容
4. 如果任务已经完成，请返回 [{"type":"done","value":""}]

【输出格式示例】
[
  {"type": "click_id", "value": "com.baitu.qingshu:id/navLive"},
  {"type": "wait", "value": "3"},
  {"type": "click_text", "value": "开始直播"}
]
"""


def safe_extract_text_content(content) -> str:
    """安全提取 LLM 返回的文本内容"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


def validate_actions(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """验证并标准化动作列表"""
    if not isinstance(actions, list):
        raise ValueError("动作计划必须是 JSON 数组")

    normalized = []

    for i, item in enumerate(actions):
        if not isinstance(item, dict):
            raise ValueError(f"第 {i} 个动作不是对象: {item}")

        action_type = item.get("type")
        value = item.get("value", "")

        if not action_type:
            raise ValueError(f"第 {i} 个动作缺少 type: {item}")

        normalized.append({
            "type": str(action_type).strip(),
            "value": value
        })

    return normalized


def parse_llm_plan(raw_text: str) -> List[Dict[str, Any]]:
    """从 LLM 输出中提取结构化动作计划"""
    text = (raw_text or "").strip()

    # 清理 markdown 代码块（修复原始代码中的换行符问题）
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"^```\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*``` $ ", "", text, flags=re.MULTILINE)

    # 尝试直接解析
    try:
        data = json.loads(text)
        return validate_actions(data)
    except Exception:
        pass

    # 从文本中提取 JSON 数组（使用非贪婪匹配更安全）
    match = re.search(r"  $ .*? $  ", text, flags=re.S)
    if match:
        try:
            data = json.loads(match.group(0))
            return validate_actions(data)
        except Exception:
            pass

    raise ValueError(f"无法从 LLM 输出中提取合法 JSON 数组，原始内容: {text}")


def fallback_plan() -> List[Dict[str, Any]]:
    """兜底动作计划：只等待，不直接结束"""
    return [
        {"type": "wait", "value": "2"}
    ]


def build_context(state: Dict[str, Any], ui_elements: List[Dict[str, Any]]) -> str:
    """构建发送给 LLM 的上下文"""
    context = f"任务: {state.get('task', '')}\n"

    if state.get("error_message"):
        context += f"上一步操作失败: {state['error_message']}\n现在需要重新规划。\n"

    started = state.get("live_started", False)
    ended = state.get("live_ended", False)
    context += f"当前任务状态: live_started={started}, live_ended={ended}\n"

    context += "请根据当前页面信息，生成下一组最合理的完整动作。只输出 JSON 数组。\n"
    context += "当前UI元素如下：\n"
    context += json.dumps(ui_elements, ensure_ascii=False, indent=2)

    return context


def build_success_result(planned_actions: List[Dict[str, Any]]) -> dict:
    """构建成功规划结果：不自动追加 done"""
    if not planned_actions:
        planned_actions = fallback_plan()

    print(f"🛠️ build_success_result 最终 planned_actions: {planned_actions}")

    return {
        "planned_actions": planned_actions,
        "current_step_index": 0,
        "executed_actions": [],
        "error_message": None,
        "is_complete": False,
    }


def build_error_result(error: Exception) -> dict:
    """构建失败规划结果"""
    return {
        "planned_actions": fallback_plan(),
        "current_step_index": 0,
        "executed_actions": [],
        "error_message": f"LLM planning error: {repr(error)}",
        "is_complete": False,
    }


def invoke_with_image(llm: ChatOpenAI, context_text: str, base64_image: str) -> str:
    """使用多模态（图像 + 文本）调用 LLM"""
    messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=[
            {
                "type": "text",
                "text": context_text
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }
            }
        ])
    ]

    response = llm.invoke(messages)
    raw_text = response.content

    if isinstance(raw_text, list):
        raw_text = safe_extract_text_content(raw_text)

    return str(raw_text)


def invoke_text_only(llm: ChatOpenAI, context_text: str) -> str:
    """仅使用文本调用 LLM（降级方案）"""
    messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=context_text)
    ]

    response = llm.invoke(messages)
    raw_text = response.content

    if isinstance(raw_text, list):
        raw_text = safe_extract_text_content(raw_text)

    return str(raw_text)


def llm_planner(state: Dict[str, Any]) -> dict:
    """LLM 动作规划器节点（支持多模态 + 文本降级）"""
    print("🧠 LLM 正在规划整个任务...")

    if not state.get("screenshot_path"):
        return {
            "planned_actions": [],
            "current_step_index": 0,
            "executed_actions": [],
            "error_message": "error: no screenshot",
            "is_complete": False,
            "history": state.get("history", []) + ["LLM skipped: no screenshot"]
        }

    history = state.get("history", []) or []

    try:
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            max_retries=2,
        )

        ui_elements = state.get("ui_elements", [])[:30]
        context_text = build_context(state, ui_elements)

        print(f"🧾 发送给 LLM 的 UI 元素数量: {len(ui_elements)}")

        # 第一阶段：多模态
        try:
            base64_image = compress_image_to_base64(state["screenshot_path"])
            print(f"🖼️ base64 图片长度: {len(base64_image)}")
            print("🚀 尝试使用 多模态规划（图片 + UI元素）...")

            raw_text = invoke_with_image(llm, context_text, base64_image)
            print(f"📝 LLM 原始返回（多模态）:\n{raw_text}")

            planned_actions = parse_llm_plan(raw_text)
            print(f"✅ 多模态规划成功: {planned_actions}")
            print(f"🛠️ 准备返回给 workflow 的 planned_actions: {planned_actions}")

            result = build_success_result(planned_actions)
            result["history"] = history + ["LLM 规划成功（多模态）"]
            return result

        except Exception as image_error:
            print(f"⚠️ 多模态规划失败，准备降级到纯文本模式: {repr(image_error)}")
            traceback.print_exc()

            # 第二阶段：纯文本降级
            try:
                print("🚀 尝试使用 纯文本规划（仅UI元素）...")
                raw_text = invoke_text_only(llm, context_text)
                print(f"📝 LLM 原始返回（纯文本）:\n{raw_text}")

                planned_actions = parse_llm_plan(raw_text)
                print(f"✅ 纯文本规划成功: {planned_actions}")
                print(f"🛠️ 准备返回给 workflow 的 planned_actions: {planned_actions}")

                result = build_success_result(planned_actions)
                result["history"] = history + [
                    f"多模态规划失败: {repr(image_error)}",
                    "LLM 规划成功（纯文本降级）"
                ]
                return result

            except Exception as text_error:
                print(f"❌ 纯文本规划也失败: {repr(text_error)}")
                traceback.print_exc()

                result = build_error_result(text_error)
                result["history"] = history + [
                    f"多模态规划失败: {repr(image_error)}",
                    f"纯文本规划失败: {repr(text_error)}",
                    "使用 fallback_plan"
                ]
                return result

    except Exception as e:
        print(f"❌ LLM 初始化或规划流程失败: {repr(e)}")
        traceback.print_exc()

        result = build_error_result(e)
        result["history"] = history + [f"LLM 初始化失败: {repr(e)}"]
        return result