# src/config/settings.py
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Appium 配置
    APPIUM_SERVER_URL: str = "http://localhost:4723"
    ANDROID_DEVICE_NAME: str = "5e0c4268"
    APP_PACKAGE: str = "com.baitu.qingshu"
    APP_ACTIVITY: str = "com.androidrtc.chat.DefaultIconAlias"
    HOME_READY_ID: str = "com.baitu.qingshu:id/navLive"

    # 路径配置
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    CURRENT_SCREEN_PATH: str = str(BASE_DIR / "current_screen.png")
    STARTUP_DEBUG_SCREEN_PATH: str = str(BASE_DIR / "startup_debug.png")
    CURRENT_PAGE_SOURCE_PATH: str = str(BASE_DIR / "current_page_source.xml")
    STARTUP_PAGE_SOURCE_PATH: str = str(BASE_DIR / "startup_page_source.xml")

    # LLM 配置
    OPENAI_MODEL: str = "gpt-4o"
    DEFAULT_TASK: str = "点击新人按钮"

    class Config:
        env_file = ".env"

# 全局实例
settings = Settings()