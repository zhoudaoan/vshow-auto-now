# src/agents/state.py
from typing import TypedDict, List, Dict, Any, Optional

class TestCaseConfig(TypedDict):
    name: str
    description: str
    task: str
    max_steps: int
    timeout_seconds: int

class AgentState(TypedDict):
    task: str
    history: List[str]
    screenshot_path: str
    page_source_path: str
    ui_elements: List[Dict[str, Any]]
    planned_actions: List[Dict[str, Any]]
    executed_actions: List[Dict[str, Any]]
    error_message: Optional[str]
    is_complete: bool
    step_count: int
    max_steps: int
    test_case: TestCaseConfig