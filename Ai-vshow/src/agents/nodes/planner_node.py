# src/agents/nodes/planner_node.py
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
请严格遵循以下规则：

1. **规划模式**:
   - 当收到一个新任务时，请一次性生成一个完整的、详细的、按顺序执行的操作计划。
   - 计划必须是一个 JSON 数组，每个元素代表一个操作步骤。
   - 操作类型包括: "click_text", "click_id", "click_xpath", "click_coordinate", "click_bounds", "type_text", "swipe", "back", "wait", "done"。
   - 示例输出: 
     [
        {"type": "click_text", "value": "直播"},
        {"type": "wait", "value": "2"},
        {"type": "click_id", "value": "com.example.app:id/start_btn"},
        {"type": "done", "value": ""}
     ]

2. **重规划模式**:
   - 如果被告知某个操作失败，请根据当前屏幕截图和UI元素，重新规划从该点开始的剩余操作。
   - 同样输出一个 JSON 数组。

3. **注意事项**:
   - 优先使用ID (`resource-id`)，其次使用文本 (`text`)，然后是xpath等。
   - 对于输入操作，请确保先点击输入框再输入。
   - "wait" 操作的 value 是秒数，用于等待页面加载。
   - 如果任务已完成，最后一个操作必须是 "done"。
   - 只能返回一个 JSON 数组，不要返回任何其他文字、解释或 Markdown。
"""


def safe_extract_text_content(content) -> str:
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


def parse_llm_plan(raw_text: str) -> List[Dict[str, Any]]:
    text = (raw_text or "").strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*``` $ ", "", text)
    try:
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("LLM 应该返回一个 JSON 数组")
        for item in data:
            if "type" not in item or "value" not in item:
                raise ValueError("数组中的每个对象必须包含 type 和 value")
        return data
    except Exception as e:
        match = re.search(r"  $ .* $  ", text, flags=re.S)
        if not match:
            raise ValueError(f"无法从 LLM 输出中提取 JSON 数组: {text}")
        data = json.loads(match.group(0))
        if not isinstance(data, list):
            raise ValueError("提取的内容不是一个数组")
        for item in data:
            if "type" not in item or "value" not in item:
                raise ValueError("数组中的每个对象必须包含 type 和 value")
        return data


def llm_planner(state: Dict[str, Any]) -> dict:
    print("🧠 LLM 正在规划整个任务...")
    if not state.get("screenshot_path"):
        return {
            "planned_actions": [],
            "error_message": "error: no screenshot",
            "history": state["history"] + ["LLM skipped: no screenshot"]
        }

    content = None
    try:
        llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0)
        base64_image = compress_image_to_base64(state["screenshot_path"])
        ui_elements = state.get("ui_elements", [])[:100]

        context = f"任务: {state['task']}\n"
        if state.get('error_message'):
            context += f"上一步操作失败: {state['error_message']}\n现在需要重新规划。\n"
        context += "请生成一个完整的操作计划。"

        messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=[
                {
                    "type": "text",
                    "text": context + f"\n\n当前UI元素:\n{json.dumps(ui_elements, ensure_ascii=False, indent=2)}"
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
        content = response.content
        print("💬 LLM 原始回复:", content)
        content_text = safe_extract_text_content(content)
        planned_actions = parse_llm_plan(content_text)
        print(f"✅ 解析出的动作计划: {planned_actions}")
        return {
            "planned_actions": planned_actions,
            "error_message": None
        }

    except Exception as e:
        print(f"❌ LLM 规划调用或解析失败: {repr(e)}")
        print("🔍 原始 content:", content)
        traceback.print_exc()

        try:
            print("🔁 尝试进行一次兜底重试...")
            ui_elements = state.get("ui_elements", [])[:40]
            retry_context = f"任务: {state['task']}\n"
            if state.get('error_message'):
                retry_context += f"上一步操作失败: {state['error_message']}\n"
            retry_context += "你上一次输出不符合要求。现在只允许输出一个合法的 JSON 数组。"

            retry_messages = [
                SystemMessage(content=PLANNER_SYSTEM_PROMPT),
                HumanMessage(content=[
                    {"type": "text",
                     "text": retry_context + f"\n\n当前UI元素:\n{json.dumps(ui_elements, ensure_ascii=False)}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ])
            ]
            retry_resp = llm.invoke(retry_messages)
            retry_text = safe_extract_text_content(retry_resp.content)
            planned_actions = parse_llm_plan(retry_text)
            print(f"✅ 兜底重试成功，动作计划: {planned_actions}")
            return {"planned_actions": planned_actions, "error_message": None}
        except Exception as retry_e:
            print(f"❌ 兜底重试仍失败: {repr(retry_e)}")
            traceback.print_exc()
            return {
                "planned_actions": [],
                "error_message": f"LLM planning error: {repr(e)}",
                "history": state["history"] + [f"LLM planning error: {repr(e)}"]
            }