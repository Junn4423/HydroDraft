"""
HydroDraft - Professional Engineering Platform
Main Application Entry Point

Từ Thông số Kỹ thuật → Tính toán Thiết kế → Bản vẽ CAD/BIM
Standalone offline-first desktop application với native window
"""

import os
import sys
import threading
import logging
import multiprocessing
from pathlib import Path

# Fix for PyInstaller with console=False: sys.stdout/stderr may be None
# This must be done BEFORE importing uvicorn
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn

from api import tank_router, pipeline_router, well_router, export_router
from api.tank_router_v2 import router as tank_router_v2
from api.cad_router_v2 import router as cad_router_v2
from api.sprint4_router import router as sprint4_router
from api.advanced_design_router import router as advanced_design_router
from database.connection import init_db, close_db, get_db_info
from core.config import settings, BASE_PATH

# Desktop mode with pywebview
DESKTOP_MODE = True
try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    print("Warning: pywebview not installed. Running in browser mode.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời ứng dụng"""
    # Khởi tạo kết nối database
    await init_db()
    
    db_info = get_db_info()
    print(
        """
============================================================
HydroDraft {version}
Professional Engineering Design Platform
Database: {db_path}
Server: http://{host}:{port}
Mode: {mode}
============================================================
""".format(
            version=settings.APP_VERSION,
            db_path=db_info['path'],
            host=settings.HOST,
            port=settings.PORT,
            mode="Desktop App" if (DESKTOP_MODE and WEBVIEW_AVAILABLE) else "Browser"
        )
    )
    
    yield
    
    # Đóng kết nối database
    await close_db()
    print("HydroDraft stopped")


app = FastAPI(
    title="HydroDraft - Professional Engineering Platform",
    description="""
    ## Hệ thống Tự động hóa Thiết kế Hạ tầng Môi trường
    
    ### Chức năng chính:
    - 🏗️ Thiết kế Bể (Lắng, Lọc, Chứa, Điều hòa)
    - 🔧 Thiết kế Mạng lưới Đường ống
    - 💧 Thiết kế Mạng lưới Giếng quan trắc
    - 📐 Xuất bản vẽ CAD 2D/3D
    - 📊 Xuất mô hình BIM (IFC)
    - 📋 Tạo báo cáo kỹ thuật
    - 🔄 Version control cho thiết kế
    
    ### Tiêu chuẩn:
    - TCVN 7957:2008
    - QCVN 14:2008/BTNMT
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các router
app.include_router(tank_router, prefix="/api/v1", tags=["Thiết kế Bể"])
app.include_router(tank_router_v2, prefix="/api/v1", tags=["Thiết kế Bể V2 - Traceable"])
app.include_router(cad_router_v2, tags=["CAD V2 - Professional"])
app.include_router(sprint4_router, tags=["Sprint 4 - BIM & Enterprise"])
app.include_router(advanced_design_router, tags=["Advanced Design - PCA/Crack/Optimizer"])
app.include_router(pipeline_router, prefix="/api/v1", tags=["Thiết kế Đường ống"])
app.include_router(well_router, prefix="/api/v1", tags=["Thiết kế Giếng"])
app.include_router(export_router, prefix="/api/v1", tags=["Xuất file"])

# Mount static files (React build) nếu tồn tại
static_dir = Path(settings.STATIC_DIR)
if static_dir.exists() and (static_dir / "index.html").exists():
    app.mount("/static", StaticFiles(directory=str(static_dir / "static")), name="static")
    
    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        """Serve React frontend"""
        return FileResponse(str(static_dir / "index.html"))
    
    # Catch-all route for React Router
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Serve SPA for client-side routing"""
        # Nếu là API request, skip
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi"):
            return None
        
        # Kiểm tra nếu là static file
        file_path = static_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        
        # Trả về index.html cho React Router
        return FileResponse(str(static_dir / "index.html"))
else:
    @app.get("/", tags=["Trang chủ"])
    async def root():
        """Trang chủ API (khi không có frontend build)"""
        return {
            "message": "Chào mừng đến với HydroDraft",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "status": "Đang hoạt động",
            "note": "Frontend chưa được build. Truy cập /docs để sử dụng API."
        }


@app.get("/health", tags=["Hệ thống"])
@app.get("/api/v1/health", tags=["Hệ thống"])
async def health_check():
    """Kiểm tra trạng thái hệ thống"""
    from database.connection import check_db_connection
    
    db_connected = False
    try:
        db_connected = await check_db_connection()
    except:
        pass
    
    db_info = get_db_info()
    
    return {
        "status": "healthy",
        "message": "Hệ thống hoạt động bình thường",
        "version": settings.APP_VERSION,
        "database": {
            "connected": db_connected,
            "path": db_info["path"],
            "size_mb": db_info["size_mb"]
        },
        "services": {
            "api": True,
            "database": db_connected,
        }
    }


@app.get("/api/v1/system/info", tags=["Hệ thống"])
async def system_info():
    """Thông tin chi tiết hệ thống"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": get_db_info(),
        "paths": {
            "base": str(BASE_PATH),
            "data": settings.DATA_DIR,
            "outputs": settings.OUTPUT_DIR,
            "templates": settings.TEMPLATE_DIR,
        },
        "is_packaged": getattr(sys, 'frozen', False),
    }


def run_server():
    """Chạy uvicorn server"""
    is_frozen = getattr(sys, 'frozen', False)
    
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(levelname)s: %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
        },
    }
    
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
        log_config=log_config if is_frozen else None,
    )


def create_desktop_window():
    """Tạo native desktop window với pywebview"""
    import time
    
    # Đợi server khởi động
    time.sleep(2)
    
    url = f"http://{settings.HOST}:{settings.PORT}"
    
    # Tạo window với các tùy chọn
    window = webview.create_window(
        title=f"HydroDraft v{settings.APP_VERSION} - Professional Engineering Platform",
        url=url,
        width=1400,
        height=900,
        min_size=(1200, 700),
        resizable=True,
        fullscreen=False,
        frameless=False,
        easy_drag=False,
        text_select=True,
        confirm_close=True,
        background_color='#1a365d'
    )
    
    # Bắt đầu pywebview event loop
    webview.start(
        gui='edgechromium',  # Sử dụng Edge Chromium trên Windows
        debug=not getattr(sys, 'frozen', False)
    )


def main():
    """Entry point cho ứng dụng"""
    print(f"Starting HydroDraft v{settings.APP_VERSION}...")
    
    is_frozen = getattr(sys, 'frozen', False)
    
    # Desktop mode với pywebview
    if DESKTOP_MODE and WEBVIEW_AVAILABLE:
        print("Running in Desktop Mode (Native Window)...")
        
        # Chạy server trong thread riêng
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Tạo desktop window (blocking)
        create_desktop_window()
        
        print("Desktop window closed. Shutting down...")
        sys.exit(0)
    else:
        # Browser mode (fallback)
        print("Running in Browser Mode...")
        import webbrowser
        
        def open_browser():
            import time
            time.sleep(1.5)
            url = f"http://{settings.HOST}:{settings.PORT}"
            print(f"Opening browser: {url}")
            try:
                webbrowser.open(url, new=2)
            except Exception as e:
                print(f"Could not open browser: {e}")
        
        if settings.AUTO_OPEN_BROWSER:
            threading.Thread(target=open_browser, daemon=True).start()
        
        run_server()


if __name__ == "__main__":
    # Cần multiprocessing freeze_support cho PyInstaller
    multiprocessing.freeze_support()
    main()
