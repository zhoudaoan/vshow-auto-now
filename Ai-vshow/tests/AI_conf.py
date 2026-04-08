import base64
import json
import os
import re
import time
import traceback
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

from PIL import Image
from dotenv import load_dotenv
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

load_dotenv()


# =========================
# 1. 状态定义 (已优化)
# =========================
class AgentState(TypedDict):
    task: str
    history: List[str]
    screenshot_path: str
    page_source_path: str
    ui_elements: List[Dict[str, Any]]
    # --- 新增字段 ---
    planned_actions: List[Dict[str, Any]]  # 存储AI规划的动作列表
    executed_actions: List[Dict[str, Any]]  # 记录已成功执行的动作
    error_message: Optional[str]  # 记录执行或规划时的错误
    is_complete: bool
    step_count: int
    max_steps: int


# =========================
# 2. 全局配置 (完全保留)
# =========================
BASE_DIR = Path(__file__).resolve().parent
CURRENT_SCREEN_PATH = str(BASE_DIR / "current_screen.png")
STARTUP_DEBUG_SCREEN_PATH = str(BASE_DIR / "startup_debug.png")
CURRENT_PAGE_SOURCE_PATH = str(BASE_DIR / "current_page_source.xml")
STARTUP_PAGE_SOURCE_PATH = str(BASE_DIR / "startup_page_source.xml")

APPIUM_SERVER_URL = os.getenv("APPIUM_SERVER_URL", "http://localhost:4723")
ANDROID_DEVICE_NAME = os.getenv("ANDROID_DEVICE_NAME", "5e0c4268")
APP_PACKAGE = os.getenv("APP_PACKAGE", "com.baitu.qingshu")
APP_ACTIVITY = os.getenv("APP_ACTIVITY", "com.androidrtc.chat.DefaultIconAlias")
HOME_READY_ID = os.getenv("HOME_READY_ID", "com.baitu.qingshu:id/navLive")
DEFAULT_TASK = os.getenv("DEFAULT_TASK", "点击新人按钮")

driver = None


# =========================
# 3. Driver 初始化 (完全保留)
# =========================
def build_options() -> UiAutomator2Options:
    options = UiAutomator2Options()
    options.automation_name = "UiAutomator2"
    options.platform_name = "Android"
    options.device_name = ANDROID_DEVICE_NAME
    options.app_package = APP_PACKAGE
    options.app_activity = APP_ACTIVITY
    options.no_reset = True
    options.auto_grant_permissions = True
    options.new_command_timeout = 600
    return options


def save_page_source(drv, path: str):
    try:
        source = drv.page_source
        with open(path, "w", encoding="utf-8") as f:
            f.write(source)
        print(f"🧾 已保存 page_source: {path}")
    except Exception as e:
        print(f"⚠️ 保存 page_source 失败: {repr(e)}")


def get_driver():
    try:
        options = build_options()
        drv = webdriver.Remote(APPIUM_SERVER_URL, options=options)
        print("✅ Appium Session 创建成功")

        try:
            WebDriverWait(drv, 20).until(
                EC.presence_of_element_located((AppiumBy.ID, HOME_READY_ID))
            )
            print("✅ 已进入首页")
        except Exception as e:
            print(f"⚠️ 首页校验失败，但 driver 仍可用: {repr(e)}")

        # 调试信息输出
        try:
            print("current_package:", drv.current_package)
        except Exception:
            pass
        try:
            print("current_activity:", drv.current_activity)
        except Exception:
            pass
        try:
            drv.get_screenshot_as_file(STARTUP_DEBUG_SCREEN_PATH)
            print(f"📷 已保存启动截图: {STARTUP_DEBUG_SCREEN_PATH}")
        except Exception as se:
            print(f"⚠️ 保存启动截图失败: {repr(se)}")

        save_page_source(drv, STARTUP_PAGE_SOURCE_PATH)
        return drv

    except Exception as e:
        print(f"❌ Driver 初始化失败: {repr(e)}")
        traceback.print_exc()
        return None


def ensure_driver():
    global driver
    if driver is None:
        driver = get_driver()
        if driver is None:
            raise RuntimeError("driver 初始化失败")
    return driver


# =========================
# 4. 通用工具 (完全保留)
# =========================
def parse_bounds(bounds: str) -> Optional[Dict[str, int]]:
    match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds or "")
    if not match:
        return None
    x1, y1, x2, y2 = map(int, match.groups())
    return {
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "center_x": (x1 + x2) // 2,
        "center_y": (y1 + y2) // 2,
    }


def compress_image_to_base64(image_path: str, max_size=(1024, 1024)) -> str:
    if not image_path or not os.path.isfile(image_path):
        raise FileNotFoundError(f"图片不存在: {image_path}")
    try:
        with Image.open(image_path) as img:
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")
            img.thumbnail(max_size)
            buffer = BytesIO()
            img.save(buffer, format="PNG", optimize=True)
            return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"处理图片失败: {repr(e)}") from e


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


def normalize_text(text: str) -> str:
    return (text or "").strip()


# =========================
# 5. 页面元素提取 (完全保留)
# =========================
def extract_ui_elements() -> List[Dict[str, Any]]:
    drv = ensure_driver()
    elements: List[Dict[str, Any]] = []
    try:
        source = drv.page_source
        with open(CURRENT_PAGE_SOURCE_PATH, "w", encoding="utf-8") as f:
            f.write(source)
        root = ET.fromstring(source)
        for node in root.iter():
            text = normalize_text(node.attrib.get("text", ""))
            resource_id = normalize_text(node.attrib.get("resource-id", ""))
            content_desc = normalize_text(node.attrib.get("content-desc", ""))
            bounds = normalize_text(node.attrib.get("bounds", ""))
            clickable = normalize_text(node.attrib.get("clickable", ""))
            enabled = normalize_text(node.attrib.get("enabled", ""))
            displayed = normalize_text(node.attrib.get("displayed", ""))
            class_name = normalize_text(node.attrib.get("class", ""))

            if not (text or resource_id or content_desc):
                continue

            item: Dict[str, Any] = {
                "text": text,
                "resource_id": resource_id,
                "content_desc": content_desc,
                "bounds": bounds,
                "clickable": clickable,
                "enabled": enabled,
                "displayed": displayed,
                "class": class_name,
            }
            parsed = parse_bounds(bounds)
            if parsed:
                item.update(parsed)
            elements.append(item)
        print(f"🧩 已提取 UI 元素: {len(elements)} 个")
        return elements
    except Exception as e:
        print(f"❌ 提取 UI 元素失败: {repr(e)}")
        traceback.print_exc()
        return []


# =========================
# 6. 弹窗处理 (完全保留)
# =========================
def try_click_text_once(text: str) -> bool:
    drv = ensure_driver()
    selectors = [
        f'new UiSelector().text("{text}")',
        f'new UiSelector().textContains("{text}")',
        f'new UiSelector().description("{text}")',
        f'new UiSelector().descriptionContains("{text}")',
    ]
    for sel in selectors:
        try:
            drv.find_element(AppiumBy.ANDROID_UIAUTOMATOR, sel).click()
            print(f"✅ 已点击弹窗元素: {text}")
            return True
        except Exception:
            pass
    return False


def dismiss_common_popups(max_rounds: int = 3):
    popup_texts = [
        "允许", "始终允许", "仅在使用中允许", "同意", "我知道了", "跳过", "以后再说",
        "暂不", "取消", "关闭", "好的", "下次再说", "立即体验", "继续", "进入应用"
    ]
    for _ in range(max_rounds):
        clicked_any = False
        for text in popup_texts:
            if try_click_text_once(text):
                clicked_any = True
                time.sleep(1)
        if not clicked_any:
            break


# =========================
# 7. 截图节点 (完全保留)
# =========================
def take_screenshot(state: AgentState) -> dict:
    print("📸 正在截取屏幕...")
    try:
        drv = ensure_driver()
        dismiss_common_popups(max_rounds=2)
        drv.get_screenshot_as_file(CURRENT_SCREEN_PATH)
        ui_elements = extract_ui_elements()
        print(f"✅ 截图保存至: {CURRENT_SCREEN_PATH}")
        return {
            "screenshot_path": CURRENT_SCREEN_PATH,
            "page_source_path": CURRENT_PAGE_SOURCE_PATH,
            "ui_elements": ui_elements,
            "error_message": None  # 清除可能的旧错误
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


# =========================
# 8. 执行动作工具 (完全保留)
# =========================
def click_by_text(text: str) -> bool:
    drv = ensure_driver()
    selectors = [
        f'new UiSelector().text("{text}")',
        f'new UiSelector().textContains("{text}")',
        f'new UiSelector().description("{text}")',
        f'new UiSelector().descriptionContains("{text}")',
    ]
    for sel in selectors:
        try:
            drv.find_element(AppiumBy.ANDROID_UIAUTOMATOR, sel).click()
            return True
        except Exception:
            pass
    return False


def click_by_id(resource_id: str):
    drv = ensure_driver()
    drv.find_element(AppiumBy.ID, resource_id).click()


def click_by_xpath(xpath: str):
    drv = ensure_driver()
    drv.find_element(AppiumBy.XPATH, xpath).click()


def click_by_coordinate(x: int, y: int):
    drv = ensure_driver()
    drv.execute_script("mobile: clickGesture", {"x": int(x), "y": int(y)})


def click_center_of_bounds(bounds: str):
    parsed = parse_bounds(bounds)
    if not parsed:
        raise ValueError(f"非法 bounds: {bounds}")
    click_by_coordinate(parsed["center_x"], parsed["center_y"])


def do_swipe(direction: str):
    drv = ensure_driver()
    size = drv.get_window_size()
    width = size["width"]
    height = size["height"]
    drv.execute_script(
        "mobile: swipeGesture",
        {
            "left": int(width * 0.1),
            "top": int(height * 0.1),
            "width": int(width * 0.8),
            "height": int(height * 0.8),
            "direction": direction,
            "percent": 0.7
        }
    )


def press_back():
    ensure_driver().back()


def try_focus_and_type(text: str):
    drv = ensure_driver()
    try:
        el = drv.switch_to.active_element
        el.send_keys(text)
        return
    except Exception:
        pass

    editable_classes = ["android.widget.EditText"]
    for class_name in editable_classes:
        try:
            el = drv.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().className("{class_name}")'
            )
            el.click()
            time.sleep(0.5)
            el.send_keys(text)
            return
        except Exception:
            pass
    raise RuntimeError("未找到可输入的输入框")


# =========================
# 9. 动作执行节点 (已优化)
# =========================
def execute_planned_action(state: AgentState) -> dict:
    """执行计划中的下一个动作。"""
    planned_actions = state.get('planned_actions', [])
    executed_count = len(state.get('executed_actions', []))
    step_count = executed_count + 1

    if executed_count >= len(planned_actions):
        return {
            "error_message": "没有更多计划动作可执行。",
            "step_count": step_count
        }

    next_action = planned_actions[executed_count]
    action_type = next_action.get("type")
    value = next_action.get("value")
    print(f"🤖 第 {step_count} 步，准备执行动作: {action_type} - {value}")

    try:
        time.sleep(1)
        if action_type == "click_text":
            if not value:
                raise ValueError("click_text 缺少 value")
            print(f" -> 点击文本: {value}")
            ok = click_by_text(str(value))
            if not ok:
                raise RuntimeError(f"未找到文本元素: {value}")

        elif action_type == "click_id":
            if not value:
                raise ValueError("click_id 缺少 value")
            print(f" -> 点击 resource-id: {value}")
            click_by_id(str(value))

        elif action_type == "click_xpath":
            if not value:
                raise ValueError("click_xpath 缺少 value")
            print(f" -> 点击 xpath: {value}")
            click_by_xpath(str(value))

        elif action_type == "click_coordinate":
            if not isinstance(value, dict) or "x" not in value or "y" not in value:
                raise ValueError("click_coordinate 的 value 必须包含 x/y")
            x, y = int(value["x"]), int(value["y"])
            print(f" -> 点击坐标: ({x}, {y})")
            click_by_coordinate(x, y)

        elif action_type == "click_bounds":
            if not value:
                raise ValueError("click_bounds 缺少 value")
            print(f" -> 点击 bounds 中心: {value}")
            click_center_of_bounds(str(value))

        elif action_type == "type_text":
            if value is None:
                raise ValueError("type_text 缺少 value")
            print(f" -> 输入文本: {value}")
            try_focus_and_type(str(value))

        elif action_type == "swipe":
            if value not in ["up", "down", "left", "right"]:
                raise ValueError("swipe 的 value 必须是 up/down/left/right")
            print(f" -> 执行滑动: {value}")
            do_swipe(str(value))

        elif action_type == "back":
            print(" -> 执行返回")
            press_back()

        elif action_type == "wait":
            seconds = int(value) if value else 2
            print(f" -> 等待 {seconds} 秒")
            time.sleep(seconds)

        elif action_type == "done":
            print("✅ 任务标记为完成")
            return {
                "is_complete": True,
                "executed_actions": state.get('executed_actions', []) + [next_action],
                "step_count": step_count,
                "history": state["history"] + [f"Done: {value}"]
            }

        else:
            raise ValueError(f"未知动作类型: {action_type}")

        # 记录成功执行的动作
        new_executed = state.get('executed_actions', []) + [next_action]
        return {
            "executed_actions": new_executed,
            "history": state["history"] + [f"Executed: {action_type}({value})"],
            "step_count": step_count,
            "error_message": None
        }

    except Exception as e:
        error_msg = f"执行动作失败: {action_type}({value}) -> {repr(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return {
            "history": state["history"] + [error_msg],
            "step_count": step_count,
            "error_message": error_msg
        }


# =========================
# 10. LLM 配置 (完全保留)
# =========================
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o"),
    temperature=0
)

# --- 优化后的 SYSTEM_PROMPT ---
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


# =========================
# 11. LLM 响应解析 (已优化)
# =========================
def parse_llm_plan(raw_text: str) -> List[Dict[str, Any]]:
    text = (raw_text or "").strip()
    # 移除可能的 Markdown 代码块
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
        # 尝试从文本中提取 JSON 数组
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


# =========================
# 12. LLM 规划器节点 (核心新增)
# =========================
def llm_planner(state: AgentState) -> dict:
    print("🧠 LLM 正在规划整个任务...")
    if not state.get("screenshot_path"):
        return {
            "planned_actions": [],
            "error_message": "error: no screenshot",
            "history": state["history"] + ["LLM skipped: no screenshot"]
        }

    content = None
    try:
        base64_image = compress_image_to_base64(state["screenshot_path"])
        ui_elements = state.get("ui_elements", [])[:100]

        # 构建上下文
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

        # 自动兜底一次
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


# =========================
# 13. LangGraph 工作流 (已重构)
# =========================
def should_continue_or_replan(state: AgentState):
    """决定下一步是继续执行、结束还是需要重规划。"""
    error = state.get('error_message')
    planned_actions = state.get('planned_actions', [])
    executed_count = len(state.get('executed_actions', []))
    step_count = state.get('step_count', 0)
    max_steps = state.get('max_steps', 10)

    # 检查步数限制
    if step_count >= max_steps:
        print(f"🛑 达到最大步数限制: {max_steps}")
        return "end"

    # 如果有错误，需要重规划
    if error:
        print("🔄 检测到执行错误，触发重规划流程")
        return "replan"

    # 如果所有动作都执行完了
    if executed_count >= len(planned_actions):
        last_action = planned_actions[-1] if planned_actions else {}
        if last_action.get('type') == 'done':
            print("🏁 检测到结束条件，终止循环")
            return "end"
        else:
            print("🏁 所有计划动作已执行完毕")
            return "end"

    # 否则，继续执行下一个动作
    print("➡️ 继续执行下一个计划动作")
    return "continue"


# 构建新的工作流
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("initial_screenshot", take_screenshot)
workflow.add_node("plan", llm_planner)
workflow.add_node("execute", execute_planned_action)
workflow.add_node("re_screenshot", take_screenshot)
workflow.add_node("replan", llm_planner)

# 设置入口
workflow.set_entry_point("initial_screenshot")
workflow.add_edge("initial_screenshot", "plan")

# 主执行循环
workflow.add_edge("plan", "execute")
workflow.add_conditional_edges(
    "execute",
    should_continue_or_replan,
    {
        "continue": "execute",  # 继续执行下一个动作
        "replan": "re_screenshot",  # 出错，重新截图并规划
        "end": END
    }
)

# 重规划路径
workflow.add_edge("re_screenshot", "replan")
workflow.add_edge("replan", "execute")  # 重规划后，回到执行节点

app = workflow.compile()


# =========================
# 14. 调试辅助 (完全保留)
# =========================
def print_top_ui_elements(elements: List[Dict[str, Any]], limit: int = 20):
    print(f"🔎 当前 UI 元素（最多显示 {limit} 个）:")
    for i, item in enumerate(elements[:limit], start=1):
        print(
            f"[{i}] text={item.get('text', '')!r}, "
            f"id={item.get('resource_id', '')!r}, "
            f"desc={item.get('content_desc', '')!r}, "
            f"bounds={item.get('bounds', '')!r}, "
            f"clickable={item.get('clickable', '')!r}"
        )


def debug_dump_current_screen():
    try:
        drv = ensure_driver()
        drv.get_screenshot_as_file(CURRENT_SCREEN_PATH)
        save_page_source(drv, CURRENT_PAGE_SOURCE_PATH)
        elements = extract_ui_elements()

        print(f"📷 当前截图: {CURRENT_SCREEN_PATH}")
        print(f"🧾 当前页面源码: {CURRENT_PAGE_SOURCE_PATH}")
        print_top_ui_elements(elements, limit=30)

    except Exception as e:
        print(f"❌ debug_dump_current_screen 失败: {repr(e)}")
        traceback.print_exc()


# =========================
# 15. 主程序 (微调以适应新状态)
# =========================
if __name__ == "__main__":
    # task = input(f"请输入任务（直接回车则使用默认任务: {DEFAULT_TASK}）: ").strip()
    task = "点击当前页面的live按钮，再接着点击开始直播按钮，播10s钟，先点击关闭直播间在点击弹窗确认按钮"

    if not task:
        task = DEFAULT_TASK

    initial_state: AgentState = {
        "task": task,
        "history": [],
        "screenshot_path": "",
        "page_source_path": "",
        "ui_elements": [],
        # --- 初始化新增字段 ---
        "planned_actions": [],
        "executed_actions": [],
        "error_message": None,
        # ----------------------
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
            if driver is not None:
                driver.quit()
                print("👋 Driver 已关闭")
        except Exception as e:
            print(f"⚠️ 关闭 driver 失败: {repr(e)}")