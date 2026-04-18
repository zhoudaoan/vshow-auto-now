# src/agents/workflow.py
from typing import TypedDict, Annotated, List, Literal, Dict, Any
from langgraph.graph import StateGraph, START
from langgraph.constants import END as GRAPH_END
import operator

# 正确导入实际存在的函数名
from .nodes.screenshot_node import take_screenshot
from .nodes.planner_node import llm_planner
from .nodes.executor_node import execute_planned_action


class WorkflowState(TypedDict):
    original_task: str
    current_screen: str
    page_source: str
    planned_actions: List[Dict[str, str]]
    executed_actions: Annotated[List[Dict[str, str]], operator.add]
    error_message: str
    step_count: int
    max_steps: int
    task_completed: bool
    # 从您的节点函数中提取的其他必要字段
    screenshot_path: str
    ui_elements: List[Dict[str, Any]]
    current_step_index: int
    history: List[str]
    live_started: bool
    live_ended: bool
    is_complete: bool


def check_completion(state: WorkflowState) -> Literal["take_screenshot", "__end__"]:
    """
    智能结束判断：执行完positiveButton后立即结束
    """
    # 安全兜底：超过最大步数强制结束
    if state.get("step_count", 0) >= state.get("max_steps", 20):
        return "__end__"

    # 检查是否已标记任务完成
    if state.get("is_complete", False):
        return "__end__"

    # 提取所有已点击的元素ID
    clicked_ids = []
    for action in state.get("executed_actions", []):
        if action.get("type") == "click_id":
            clicked_ids.append(action.get("value", ""))

    # 直播任务完成的关键标识
    REQUIRED_FINAL_IDS = [
        "com.baitu.qingshu:id/liveClose",
        "com.baitu.qingshu:id/positiveButton"
    ]

    # 如果两个关键按钮都已点击，立即结束
    if all(target_id in clicked_ids for target_id in REQUIRED_FINAL_IDS):
        return "__end__"

    # 否则继续流程
    return "take_screenshot"


def create_workflow():
    workflow = StateGraph(WorkflowState)

    # 注册节点（使用实际的函数名）
    workflow.add_node("take_screenshot", take_screenshot)
    workflow.add_node("llm_planner", llm_planner)
    workflow.add_node("execute_planned_action", execute_planned_action)

    # 起始点
    workflow.add_edge(START, "take_screenshot")

    # 主循环：截图 → 规划 → 执行 → (检查结束条件)
    workflow.add_edge("take_screenshot", "llm_planner")
    workflow.add_edge("llm_planner", "execute_planned_action")
    workflow.add_conditional_edges(
        "execute_planned_action",
        check_completion,
        {
            "take_screenshot": "take_screenshot",
            "__end__": GRAPH_END
        }
    )

    return workflow.compile()


# 创建全局工作流实例
app = create_workflow()