# src/agents/nodes/planner_node.py
import json
import re
import traceback
from typing import Dict, Any, List, Union
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from ...config.settings import settings
from ...utils.image_processor import compress_image_to_base64
from pydantic import BaseModel, Field

# ---系统提示词 ---
PLANNER_SYSTEM_PROMPT = """
你是一个 JSON 输出工具。你的唯一任务是根据输入生成一个操作计划数组。
你必须且只能输出一个 JSON 数组，格式如下：
[{"type": "click_id", "value": "..."}, {"type": "wait", "value": "2"}]

可用的操作类型有: click_text, click_id, click_xpath, click_coordinate, click_bounds, type_text, swipe, back, wait, done.
不要输出任何其他文字、解释、Markdown 或代码块。只输出 JSON。
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
    # 移除可能的 Markdown 代码块标记
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

    try:
        # --- 创建 LLM 实例 ---
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )

        # --- 定义 JSON Schema ---

        class ActionStep(BaseModel):
            type: str = Field(..., description="操作类型")
            value: Union[str, dict] = Field(..., description="操作值")

        class ActionPlan(BaseModel):
            steps: list[ActionStep] = Field(..., description="操作步骤列表")

        # --- 准备消息 ---
        base64_image = compress_image_to_base64(state["screenshot_path"])
        ui_elements = state.get("ui_elements", [])[:100]

        context = f"任务: {state['task']}\n"
        if state.get('error_message'):
            context += f"上一步操作失败: {state['error_message']}\n现在需要重新规划。\n"
        context += "请生成一个完整的操作计划。"

        messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=[
                {"type": "text",
                 "text": context + f"\n\n当前UI元素:\n{json.dumps(ui_elements, ensure_ascii=False, indent=2)}"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
            ])
        ]

        # --- 强制结构化输出 ---
        structured_llm = llm.with_structured_output(ActionPlan)
        response_obj = structured_llm.invoke(messages)

        planned_actions = [{"type": step.type, "value": step.value} for step in response_obj.steps]
        print(f"✅ 解析出的动作计划: {planned_actions}")
        return {"planned_actions": planned_actions, "error_message": None}

    except Exception as e:
        print(f"❌ LLM 规划调用或解析失败: {repr(e)}")
        traceback.print_exc()
        return {
            "planned_actions": [],
            "error_message": f"LLM planning error: {repr(e)}",
        }