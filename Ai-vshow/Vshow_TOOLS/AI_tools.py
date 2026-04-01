import base64
import io
from typing import Annotated, TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from appium import webdriver
from appium.options.android import UiAutomator2Options
from PIL import Image
from dotenv import load_dotenv
load_dotenv()

# --- 1. 定义状态结构 ---
class AgentState(TypedDict):
    task: str  # 用户的目标 (例如："打开微信，给文件传输助手发一条消息：测试")
    history: List[str]  # 操作历史记录
    screenshot_path: str  # 当前截图路径
    current_action: Dict  # LLM决定的下一个动作
    is_complete: bool  # 任务是否完成


# --- 2. 初始化 Appium 驱动 ---
def get_driver():
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = "5e0c4268"  # 替换为你的设备
    options.app_package = "com.baitu.qingshu"  # 初始包名，可动态变化
    options.app_activity = "com.androidrtc.chat.DefaultIconAlias"
    driver = webdriver.Remote("http://localhost:4723", options=options)
    return driver


driver = get_driver()


# --- 3. 定义工具函数 ---

def take_screenshot(state: AgentState) -> dict:
    """截取屏幕并保存，返回图片路径"""
    path = "current_screen.png"
    driver.get_screenshot_as_file(path)
    return {"screenshot_path": path}


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def execute_action(state: AgentState) -> dict:
    """根据LLM的决策执行具体操作"""
    action = state["current_action"]
    action_type = action.get("type")
    value = action.get("value")

    print(f"🤖 执行动作: {action_type} - {value}")

    try:
        if action_type == "click_text":
            # 简单示例：通过文本查找元素并点击 (实际生产环境建议结合坐标或Accessibility ID)
            el = driver.find_element(by="accessibility id", value=value)  # 或用 xpath
            el.click()
        elif action_type == "click_coordinate":
            # 点击坐标 {'x': 100, 'y': 200}
            driver.tap([(value['x'], value['y'])])
        elif action_type == "type_text":
            # 输入文本
            el = driver.switch_to.active_element  # 获取当前焦点
            el.send_keys(value)
        elif action_type == "swipe":
            # 滑动
            size = driver.get_window_size()
            start_x = size['width'] // 2
            start_y = int(size['height'] * 0.8)
            end_y = int(size['height'] * 0.2)
            driver.swipe(start_x, start_y, start_x, end_y, 1000)
        elif action_type == "done":
            return {"is_complete": True}

        # 更新历史
        new_history = state["history"] + [f"Executed: {action_type}({value})"]
        return {"history": new_history}
    except Exception as e:
        return {"history": state["history"] + [f"Error executing {action_type}: {str(e)}"]}


# --- 4. 定义 LLM 节点 (大脑) ---

# 初始化模型 (以 GPT-4o 为例，Qwen-VL 类似，只需更换 endpoint 和 model name)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

SYSTEM_PROMPT = """
你是一个移动端自动化专家。你的任务是操作安卓手机完成用户目标。
你将收到一张当前的手机屏幕截图和用户的任务目标。
请分析屏幕内容，决定下一步操作。

可用的动作类型 (必须以 JSON 格式返回):
1. {"type": "click_text", "value": "按钮上的文字"} (优先使用)
2. {"type": "click_coordinate", "value": {"x": 100, "y": 200}} (当没有文字时使用坐标)
3. {"type": "type_text", "value": "要输入的文本"}
4. {"type": "swipe", "value": "up"} (向上滑动寻找更多内容)
5. {"type": "done", "value": "任务已完成"}

注意：
- 如果任务已完成，必须返回 type: done。
- 不要解释，只返回纯 JSON。
- 如果找不到元素，尝试滑动。
"""


def llm_node(state: AgentState) -> dict:
    # 编码图片
    base64_image = encode_image(state["screenshot_path"])

    # 构建提示词
    user_content = [
        {"type": "text",
         "text": f"任务目标: {state['task']}\n历史操作: {state['history'][-3:]}\n请分析截图并给出下一步操作。"},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
    ]

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_content)
    ]

    # 调用模型
    response = llm.invoke(messages)
    content = response.content

    # 简单的清洗，防止模型输出 Markdown 代码块标记
    import json
    import re
    clean_json = re.sub(r'```json\s*|\s*```', '', content).strip()

    try:
        action_dict = json.loads(clean_json)
        return {"current_action": action_dict}
    except Exception as e:
        # 解析失败的处理逻辑
        print(f"LLM 输出解析失败: {content}")
        return {"current_action": {"type": "done", "value": "error"}}


# --- 5. 构建 LangGraph 工作流 ---

workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("screenshot", take_screenshot)
workflow.add_node("think", llm_node)
workflow.add_node("act", execute_action)

# 定义边 (流程控制)
workflow.set_entry_point("screenshot")  # 从截图开始

workflow.add_edge("screenshot", "think")  # 截图 -> 思考
workflow.add_edge("think", "act")  # 思考 -> 执行


# 执行后判断是否结束
def should_continue(state: AgentState):
    if state.get("is_complete") or state["current_action"].get("type") == "done":
        return END
    else:
        return "screenshot"  # 未完成则回到截图步骤，形成闭环


workflow.add_conditional_edges(
    "act",
    should_continue
)

app = workflow.compile()

# --- 6. 运行 ---
if __name__ == "__main__":
    initial_state = {
        "task": "打开poppo,点击live，在点击开始直播按钮，进去后截图，最后退出直播间",
        "history": [],
        "screenshot_path": "",
        "current_action": {},
        "is_complete": False
    }

    print("🚀 智能体启动...")
    final_state = app.invoke(initial_state)
    print("✅ 任务结束。历史操作:", final_state["history"])
    driver.quit()