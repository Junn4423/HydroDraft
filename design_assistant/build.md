# HydroDraft - Build Instructions

## Yêu cầu hệ thống

- Python 3.10+ 
- Node.js 18+ (cho frontend build)
- Windows 10/11

## Bước 1: Chuẩn bị môi trường

```powershell
# Clone hoặc mở thư mục project
cd d:\HydroDraft\design_assistant

# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
.\venv\Scripts\Activate.ps1

# Cài đặt dependencies
pip install -r backend\requirements.txt
```

## Bước 2: Build Frontend (React)

```powershell
# Di chuyển vào thư mục frontend
cd frontend

# Cài đặt npm packages
npm install

# Build production
npm run build

# Copy build sang backend/static
xcopy /E /I /Y build ..\backend\static
```

## Bước 3: Test chạy trực tiếp

```powershell
# Quay lại thư mục backend
cd ..\backend

# Chạy server
python main.py
```

Trình duyệt sẽ tự động mở tại http://127.0.0.1:8000

## Bước 4: Build Executable

```powershell
# Quay lại thư mục gốc
cd ..

# Build với PyInstaller
pyinstaller hydrodraft.spec --clean

# Executable sẽ nằm trong thư mục dist/
# dist\HydroDraft.exe
```

## Bước 5: Test Executable

```powershell
# Chạy executable
.\dist\HydroDraft.exe
```

## Cấu trúc sau khi build

```
dist/
└── HydroDraft.exe     # Single executable (~50-100MB)
```

Khi chạy, HydroDraft sẽ tự động:
1. Tạo thư mục `data/` với database `design_data.db`
2. Tạo thư mục `outputs/` cho file xuất
3. Mở trình duyệt mặc định

## Gỡ lỗi

### Lỗi "Module not found"
Thêm module vào `hiddenimports` trong `hydrodraft.spec`

### Lỗi database
Xóa file `data/design_data.db` để tạo lại

### Lỗi templates/rules không load
Kiểm tra `datas` trong `hydrodraft.spec` đã include đúng path

## Development Mode

Để chạy trong development mode với hot-reload:

```powershell
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 - Frontend
cd frontend
npm start
```

## Tùy chỉnh cấu hình

Tạo file `.env` trong thư mục backend:

```env
DEBUG=true
HOST=127.0.0.1
PORT=8000
AUTO_OPEN_BROWSER=true
```

## Kiểm tra hệ thống

Sau khi chạy, kiểm tra:
- http://127.0.0.1:8000/health - Health check
- http://127.0.0.1:8000/docs - API Documentation
- http://127.0.0.1:8000/api/v1/system/info - System info
