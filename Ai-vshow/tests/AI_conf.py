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
# 1. 状态定义 (Reactive Mode)
# =========================
class AgentState(TypedDict):
    task: str
    history: List[str]
    screenshot_path: str
    page_source_path: str
    ui_elements: List[Dict[str, Any]]
    # --- 新增字段 ---
    planned_actions: List[Dict[str, Any]]  # 存储AI规划的动作列表 (现在通常只有1-2个)
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
VSHOW_READY_ID = os.getenv("HOME_READY_ID", "com.baitu.qingshu:id/navLive")
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
                EC.presence_of_element_located((AppiumBy.ID, VSHOW_READY_ID))
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
    global driver
    # ⭐ 检查 Driver 是否可用
    if driver is None:
        print("⚠️ Driver 不可用，跳过弹窗处理")
        return

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
# 9. 动作执行节点 (Reactive Mode - Simplified)
# =========================
def execute_planned_action(state: AgentState) -> dict:
    """执行计划中的第一个（也是唯一一个）动作。"""
    planned_actions = state.get('planned_actions', [])
    executed_count = len(state.get('executed_actions', []))
    step_count = executed_count + 1

    if not planned_actions:
        return {
            "error_message": "没有计划动作可执行。",
            "step_count": step_count
        }

    # 在 Reactive 模式下，我们只执行列表中的第一个动作
    next_action = planned_actions[0]
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
            time.sleep(3)

        elif action_type == "click_id":
            if not value:
                raise ValueError("click_id 缺少 value")
            print(f" -> 点击 resource-id: {value}")
            click_by_id(str(value))
            time.sleep(3)

        elif action_type == "click_xpath":
            if not value:
                raise ValueError("click_xpath 缺少 value")
            print(f" -> 点击 xpath: {value}")
            click_by_xpath(str(value))
            time.sleep(3)

        elif action_type == "click_coordinate":
            if not isinstance(value, dict) or "x" not in value or "y" not in value:
                raise ValueError("click_coordinate 的 value 必须包含 x/y")
            x, y = int(value["x"]), int(value["y"])
            print(f" -> 点击坐标: ({x}, {y})")
            click_by_coordinate(x, y)
            time.sleep(3)

        elif action_type == "click_bounds":
            if not value:
                raise ValueError("click_bounds 缺少 value")
            print(f" -> 点击 bounds 中心: {value}")
            click_center_of_bounds(str(value))
            time.sleep(3)

        elif action_type == "type_text":
            if value is None:
                raise ValueError("type_text 缺少 value")
            print(f" -> 输入文本: {value}")
            try_focus_and_type(str(value))
            time.sleep(2)

        elif action_type == "swipe":
            if value not in ["up", "down", "left", "right"]:
                raise ValueError("swipe 的 value 必须是 up/down/left/right")
            print(f" -> 执行滑动: {value}")
            do_swipe(str(value))
            time.sleep(2)

        elif action_type == "back":
            print(" -> 执行返回")
            press_back()
            time.sleep(2)

        elif action_type == "wait":
            seconds = int(value) if value else 2
            actual_wait = max(2, seconds)
            print(f" -> 等待 {actual_wait} 秒")
            time.sleep(actual_wait)

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

# --- 优化后的 SYSTEM_PROMPT (Reactive Mode) ---
PLANNER_SYSTEM_PROMPT = """
你是一个专业的移动应用自动化专家。你的任务是帮助用户完成在手机上的操作。
请严格遵循以下规则：

【重要规则】
1. **每次只生成 1 到 2 个动作**（例如：点击某个按钮 + 等待 2~3 秒）。不要试图规划完整流程。
2. 应用包名必须是：com.baitu.qingshu。
3. 只能使用我提供的“当前屏幕可用元素”中的信息，不要编造不存在的元素。
4. 优先使用 resource-id，其次 text，再其次 bounds / xpath。
5. 页面切换至少等待3秒，弹窗出现至少等待2秒。
6. 如果检测到弹窗，优先关闭弹窗，再继续原任务。
7. ❌ **绝对不允许输出 {"type": "done", ...}**。
8. 是否完成任务由系统判断，你只需推进流程。

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

【输出要求】
1. 必须返回 JSON 数组
2. 每个元素必须包含 type 和 value
3. 不要输出数组以外的任何内容

【输出格式示例】
[
  {"type": "click_id", "value": "com.baitu.qingshu:id/navLive"},
  {"type": "wait", "value": "3"}
]
"""

# =========================
# 11. LLM 响应解析 (已优化)
# =========================
import re


def parse_llm_plan(text: str) -> List[Dict[str, str]]:
    """从 LLM 输出中提取结构化动作计划"""
    text = re.sub(r'^```(?:json|python|yaml)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()

    try:
        data = json.loads(text)
        return data
    except json.JSONDecodeError as e:
        print(f"❌ 清理后的文本仍无法解析:")
        print(repr(text))
        raise ValueError(f"无法从 LLM 输出中提取 JSON 数组: {e}")


# =========================
# 12. LLM 规划器节点 (Reactive Mode)
# =========================
def llm_planner(state: AgentState) -> dict:
    print("🧠 LLM 正在规划下一步...")
    if not state.get("screenshot_path"):
        return {
            "planned_actions": [{"type": "wait", "value": "2"}],
            "error_message": None,
            "history": state["history"] + ["LLM skipped: no screenshot"]
        }

    try:
        base64_image = compress_image_to_base64(state["screenshot_path"])
        ui_elements = state.get("ui_elements", [])[:100]

        context = f"任务: {state['task']}\n\n"

        if state.get('error_message'):
            context += f"⚠️ 上一步操作失败: {state['error_message']}\n请重新规划下一步。\n"

        # --- 关键：加入业务状态反馈 ---
        live_started = any("直播中" in item.get("text", "") for item in ui_elements)
        live_ended = any("确认" in item.get("text", "") and "弹窗" in str(ui_elements) for item in ui_elements)

        if not live_started:
            context += "📌 当前目标：找到并点击「开播」或「开始直播」按钮。\n"
        elif live_started and not live_ended:
            context += "📌 当前目标：直播已开始，请等待10秒后，找到并点击右上角的「关闭」按钮。\n"
        else:
            context += "📌 所有子任务已完成。\n"

        context += "请根据当前页面，仅输出接下来 1~2 个最合理的动作（不要 done）。\n"
        context += "注意：只使用下面列出的UI元素，不要编造不存在的元素。\n"

        messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=[
                {
                    "type": "text",
                    "text": context + f"\n\n当前屏幕可用元素（共{len(ui_elements)}个）:\n{json.dumps(ui_elements, ensure_ascii=False, indent=2)}"
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
        traceback.print_exc()
        return {
            "planned_actions": [{"type": "wait", "value": "2"}],
            "error_message": f"LLM planning error: {repr(e)}",
            "history": state["history"] + [f"LLM planning error: {repr(e)}"]
        }


# =========================
# 13. 新的决策节点 (Reactive Mode Core)
# =========================
def should_end_or_observe(state: AgentState):
    """决定下一步是结束，还是重新观察（截图）"""
    step_count = state.get('step_count', 0)
    max_steps = state.get('max_steps', 15)  # 增加最大步数以适应更多步骤

    # 条件1: 达到最大步数（防死循环）
    if step_count >= max_steps:
        print(f"🛑 达到最大步数限制: {max_steps}")
        return "end"

    # 条件2: 检查业务目标是否达成 (简单示例)
    executed_actions = state.get('executed_actions', [])
    if len(executed_actions) >= 2:
        last_two = executed_actions[-2:]
        if (any('close' in str(a.get('value', '')) for a in last_two) and
                any('confirm' in str(a.get('value', '')) or '确认' in str(a.get('value', '')) for a in last_two)):
            print("🎯 业务目标达成：检测到关闭和确认操作")
            return "end"

    # 否则，总是需要重新观察
    return "observe"


# =========================
# 14. LangGraph 工作流 (Reactive Mode - New Flow)
# =========================
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("take_screenshot", take_screenshot)
workflow.add_node("plan_next_step", llm_planner)
workflow.add_node("execute_action", execute_planned_action)

# 设置入口
workflow.set_entry_point("take_screenshot")

# 核心循环: observe -> plan -> execute -> decide
workflow.add_edge("take_screenshot", "plan_next_step")
workflow.add_edge("plan_next_step", "execute_action")

workflow.add_conditional_edges(
    "execute_action",
    should_end_or_observe,
    {
        "end": END,
        "observe": "take_screenshot",
    }
)

app = workflow.compile()


# =========================
# 15. 调试辅助 (完全保留)
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
# 16. 主程序 (微调以适应新状态)
# =========================
if __name__ == "__main__":
    task = "进入到首页之后，先点击开播按钮，再点击“开始直播”按钮，播10s钟，点击直播间右上角的关闭按钮，弹出弹窗，在点击弹窗确认按钮"

    if not task:
        task = DEFAULT_TASK

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
        "max_steps": 15,
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