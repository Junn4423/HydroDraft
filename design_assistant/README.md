# Design Assistant - Trợ lý Thiết kế Hạ tầng Môi trường

## 🎯 Giới thiệu

**Design Assistant** là hệ thống tự động hóa thiết kế hạ tầng môi trường, hỗ trợ kỹ sư từ giai đoạn nhập thông số kỹ thuật đến xuất bản vẽ CAD/BIM hoàn chỉnh.

### Quy trình tự động hóa

```
Thông số Kỹ thuật → Tính toán Thiết kế → Xuất Bản vẽ CAD/BIM
```

## 🚀 Tính năng chính

### 1. Thiết kế Bể (Tank Design)
- ✅ Bể lắng sơ cấp/thứ cấp
- ✅ Bể hiếu khí (Aeration tank)
- ✅ Bể chứa/điều hòa
- ✅ Tự động tính toán thủy lực và kết cấu
- ✅ Xuất bản vẽ mặt bằng + mặt cắt

### 2. Thiết kế Đường ống (Pipeline Design)
- ✅ Mạng lưới thoát nước tự chảy
- ✅ Đường ống có áp
- ✅ Thiết kế trắc dọc tự động
- ✅ Bố trí giếng thăm theo quy chuẩn
- ✅ Tính toán thủy lực Manning

### 3. Thiết kế Giếng (Well Design)
- ✅ Giếng quan trắc nước ngầm
- ✅ Thiết kế cấu trúc giếng
- ✅ Chọn vật liệu và kích cỡ ống lọc
- ✅ Lập quy trình thi công

### 4. Xuất file
- ✅ DXF 2D (AutoCAD compatible)
- ✅ STEP 3D (yêu cầu pythonOCC)
- ✅ IFC/BIM (yêu cầu ifcopenshell)
- 🔄 PDF Report (đang phát triển)

## 📋 Tiêu chuẩn áp dụng

- **TCVN 7957:2008** - Thoát nước - Mạng lưới và công trình bên ngoài
- **TCVN 33:2006** - Cấp nước - Mạng lưới đường ống và công trình
- **TCVN 5574:2018** - Kết cấu bê tông và bê tông cốt thép
- **TCVN 9901:2014** - Giếng quan trắc nước dưới đất
- **QCVN 14:2008/BTNMT** - Quy chuẩn kỹ thuật quốc gia về nước thải sinh hoạt

## 🛠️ Công nghệ sử dụng

### Backend
- **FastAPI** - Web framework
- **Pydantic** - Data validation
- **SQLAlchemy** - ORM (async)
- **PostgreSQL** - Database
- **Celery + Redis** - Task queue
- **ezdxf** - 2D CAD generation
- **pythonOCC** - 3D CAD (optional)
- **ifcopenshell** - IFC/BIM (optional)

### Frontend
- **React 18** - UI framework
- **Material-UI** - Component library
- **Axios** - HTTP client
- **Recharts** - Data visualization

## 📦 Cài đặt

### Yêu cầu
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### Cài đặt Backend

```bash
cd backend

# Tạo môi trường ảo
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc: venv\Scripts\activate  # Windows

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy server
uvicorn main:app --reload --port 8000
```

### Cài đặt Frontend

```bash
cd frontend

# Cài đặt dependencies
npm install

# Chạy development server
npm start
```

### Sử dụng Docker

```bash
# Chạy toàn bộ hệ thống
docker-compose up -d

# Xem logs
docker-compose logs -f
```

## 🔧 Cấu hình

### Biến môi trường

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/design_assistant

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]
```

## 📖 API Documentation

Sau khi chạy backend, truy cập:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints chính

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/v1/design/tank/` | Thiết kế bể |
| POST | `/api/v1/design/pipeline/` | Thiết kế đường ống |
| POST | `/api/v1/design/well/` | Thiết kế giếng |
| POST | `/api/v1/export/dxf` | Xuất file DXF |
| POST | `/api/v1/export/ifc` | Xuất file IFC |

## 📁 Cấu trúc thư mục

```
design_assistant/
├── backend/
│   ├── api/                 # API routers
│   ├── calculations/        # Calculation engines
│   ├── core/                # Core config
│   ├── database/            # Database models
│   ├── generators/          # CAD/BIM generators
│   ├── models/              # Pydantic schemas
│   ├── rules/               # Design rules
│   ├── tasks/               # Celery tasks
│   ├── templates/           # Design templates
│   ├── main.py              # Entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── App.js
│   │   └── index.js
│   ├── public/
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 🧪 Testing

```bash
cd backend

# Chạy tests
pytest

# Với coverage
pytest --cov=. --cov-report=html
```

## 🤝 Đóng góp

Mọi đóng góp đều được hoan nghênh! Vui lòng:
1. Fork repository
2. Tạo branch mới (`git checkout -b feature/TinhNangMoi`)
3. Commit changes (`git commit -m 'Thêm tính năng mới'`)
4. Push to branch (`git push origin feature/TinhNangMoi`)
5. Tạo Pull Request

## 📄 License

MIT License - Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

## 📞 Liên hệ

- Email: support@designassistant.vn
- Website: https://designassistant.vn

---

**Design Assistant** - Tự động hóa thiết kế, nâng cao hiệu quả công việc! 🚀
