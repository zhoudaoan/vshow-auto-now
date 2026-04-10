from typing import List, Dict, Any, Tuple


def _extract_texts(ui_elements: List[Dict[str, Any]]) -> List[str]:
    texts = []

    for el in ui_elements or []:
        for key in ["text", "content-desc", "content_desc", "resource-id", "resource_id"]:
            value = el.get(key)
            if value:
                texts.append(str(value))

    return texts


def verify_live_task_progress(
    task: str,
    ui_elements: List[Dict[str, Any]],
    live_started: bool = False,
    live_ended: bool = False,
) -> Tuple[bool, bool, bool, str]:
    """
    返回:
    (
        new_live_started,
        new_live_ended,
        is_task_complete,
        reason
    )
    """
    if "直播" not in (task or ""):
        return live_started, live_ended, False, "非直播任务，未启用直播验证器"

    texts = _extract_texts(ui_elements)
    merged_text = " | ".join(texts)

    started_keywords = [
        "结束直播",
        "直播中",
        "正在直播",
        "已开播",
        "直播时长",
        "在线人数",
        "观众",
    ]

    ended_keywords = [
        "开始直播",
        "去开播",
        "开启直播",
        "我要开播",
        "开直播",
    ]

    detected_started = any(k in merged_text for k in started_keywords)
    detected_ended = any(k in merged_text for k in ended_keywords)

    new_live_started = live_started or detected_started
    new_live_ended = live_ended

    if new_live_started and detected_ended:
        if not any(k in merged_text for k in ["结束直播", "直播中", "正在直播", "已开播"]):
            new_live_ended = True

    is_task_complete = new_live_started and new_live_ended

    if is_task_complete:
        reason = "已检测到：成功开播，并且已回到可开播状态，判定直播任务完成"
    elif new_live_started:
        reason = "已检测到开播成功，但尚未确认结束直播"
    else:
        reason = "尚未检测到开播成功"

    return new_live_started, new_live_ended, is_task_complete, reason
