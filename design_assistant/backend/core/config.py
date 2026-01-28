"""
Cấu hình hệ thống HydroDraft
Offline-first configuration
"""

from pydantic_settings import BaseSettings
from typing import List
import os
import sys
from pathlib import Path


def get_base_path() -> Path:
    """Lấy đường dẫn gốc của ứng dụng (hỗ trợ cả dev và PyInstaller)"""
    if getattr(sys, 'frozen', False):
        # Chạy từ PyInstaller executable
        return Path(sys.executable).parent
    else:
        # Chạy từ source
        return Path(__file__).parent.parent


BASE_PATH = get_base_path()


class Settings(BaseSettings):
    """Cấu hình ứng dụng"""
    
    # Thông tin ứng dụng
    APP_NAME: str = "HydroDraft"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    
    # Thư mục lưu trữ (relative to BASE_PATH)
    DATA_DIR: str = str(BASE_PATH / "data")
    OUTPUT_DIR: str = str(BASE_PATH / "outputs")
    TEMPLATE_DIR: str = str(BASE_PATH / "templates")
    RULES_DIR: str = str(BASE_PATH / "rules" / "definitions")
    TEMP_DIR: str = str(BASE_PATH / "temp")
    STATIC_DIR: str = str(BASE_PATH / "static")  # React build
    
    # Giới hạn
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    MAX_CONCURRENT_JOBS: int = 10
    
    # Chuẩn layer CAD
    LAYER_PREFIXES: dict = {
        "structure": "STR_",
        "pipe": "PIPE_",
        "dimension": "DIM_",
        "text": "TEXT_",
        "water": "WATER_",
        "electrical": "ELEC_",
        "foundation": "FOUND_"
    }
    
    # Auto-open browser on startup
    AUTO_OPEN_BROWSER: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# Tạo thư mục cần thiết
for dir_path in [
    settings.DATA_DIR,
    settings.OUTPUT_DIR,
    settings.TEMPLATE_DIR,
    settings.TEMP_DIR,
]:
    os.makedirs(dir_path, exist_ok=True)
