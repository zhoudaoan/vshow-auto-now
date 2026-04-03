# src/utils/image_processor.py
import base64
import os
from io import BytesIO
from PIL import Image

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