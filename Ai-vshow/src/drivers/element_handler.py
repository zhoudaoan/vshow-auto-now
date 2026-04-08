# src/drivers/element_handler.py
import re
import traceback
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from ..config.settings import settings
from ..drivers.appium_driver import driver_manager
import time

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

def normalize_text(text: str) -> str:
    return (text or "").strip()

def extract_ui_elements() -> List[Dict[str, Any]]:
    drv = driver_manager.driver
    elements: List[Dict[str, Any]] = []
    try:
        source = drv.page_source
        with open(settings.CURRENT_PAGE_SOURCE_PATH, "w", encoding="utf-8") as f:
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

def try_click_text_once(text: str) -> bool:
    drv = driver_manager.driver
    selectors = [
        f'new UiSelector().text("{text}")',
        f'new UiSelector().textContains("{text}")',
        f'new UiSelector().description("{text}")',
        f'new UiSelector().descriptionContains("{text}")',
    ]
    for sel in selectors:
        try:
            drv.find_element("android uiautomator", sel).click()
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