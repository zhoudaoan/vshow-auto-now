
import allure
from contextlib import contextmanager
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

class AllureStep:

    @staticmethod
    @contextmanager
    def allure_step(name: str, driver=None):
        """
        静态方法版 allure_step，支持传入 driver
        """
        with allure.step(name):
            yield
            if driver:
                try:
                    png_data = driver.get_screenshot_as_png()
                    # 压缩图片（可选）
                    img = Image.open(io.BytesIO(png_data))
                    img.thumbnail((800, 600))  # 缩小尺寸加快加载
                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    buf.seek(0)
                    allure.attach(png_data, name=f"{name}_截图", attachment_type=allure.attachment_type.PNG)
                except Exception as e:
                    logger.warning(f"⚠️ 截图失败（可能设置了 FLAG_SECURE）: {e}")
                    allure.attach(
                        body="无法截图：当前页面设置了 FLAG_SECURE（防截屏）",
                        name=f"{name}_截图",
                        attachment_type=allure.attachment_type.TEXT
                    )