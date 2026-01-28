# HUONG DAN CAI DAT VA CHAY UNG DUNG DESIGN ASSISTANT

## Yeu cau he thong

### Phan mem can thiet
- Python 3.10 tro len (khuyen nghi su dung Anaconda)
- Node.js 18 tro len
- MySQL (khuyen nghi su dung Laragon tren Windows)
- Git (tuy chon)

### Thong so toi thieu
- RAM: 4GB tro len
- O cung: 2GB trong
- HDH: Windows 10/11, macOS, hoac Linux

---

## Buoc 1: Cai dat MySQL (Laragon)

### 1.1. Tai va cai Laragon
- Tai tu: https://laragon.org/download/
- Chon phien ban "Laragon Full" de co MySQL san

### 1.2. Khoi dong Laragon
- Mo Laragon
- Click "Start All" de khoi dong MySQL

### 1.3. Tao database
- Mo Terminal trong Laragon (click nut "Terminal")
- Chay lenh:
```bash
mysql -u root
```

- Trong MySQL console, chay:
```sql
CREATE DATABASE design_assistant CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

---

## Buoc 2: Cai dat Backend (Python)

### 2.1. Mo terminal tai thu muc du an
```bash
cd D:\HydroDraft\design_assistant\backend
```

### 2.2. Tao moi truong ao (khuyen nghi)

**Cach 1: Su dung Anaconda**
```bash
conda create -n design_assistant python=3.10
conda activate design_assistant
```

**Cach 2: Su dung venv**
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2.3. Cai dat cac thu vien
```bash
pip install -r requirements.txt
```

Hoac cai thu cong:
```bash
pip install fastapi uvicorn pydantic pydantic-settings sqlalchemy[asyncio] aiomysql pymysql greenlet ezdxf numpy scipy python-multipart python-dotenv
```

### 2.4. Cau hinh ket noi database (tuy chon)
Tao file `.env` trong thu muc `backend`:
```
DATABASE_URL=mysql+aiomysql://root:@127.0.0.1:3306/design_assistant
DEBUG=true
```

Luu y: 
- Neu MySQL co mat khau, thay `root:@` thanh `root:matkhau@`
- Mac dinh Laragon MySQL khong co mat khau

---

## Buoc 3: Cai dat Frontend (React)

### 3.1. Mo terminal tai thu muc frontend
```bash
cd D:\HydroDraft\design_assistant\frontend
```

### 3.2. Cai dat cac package
```bash
npm install
```

---

## Buoc 4: Chay ung dung

### 4.1. Dam bao Laragon da khoi dong MySQL

### 4.2. Chay Backend
Mo terminal 1:
```bash
cd D:\HydroDraft\design_assistant\backend

# Neu dung Anaconda:
conda activate design_assistant
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Hoac chi dinh duong dan Python cu the:
D:\anacoda\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Khi thanh cong se thay:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
Database da duoc khoi tao
Design Assistant da khoi dong!
```

### 4.3. Chay Frontend
Mo terminal 2:
```bash
cd D:\HydroDraft\design_assistant\frontend
npm start
```

Trinh duyet se tu dong mo tai http://localhost:3000

---

## Buoc 5: Su dung ung dung

### Truy cap
- **Giao dien web**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs

### Cac chuc nang chinh
1. **Thiet ke Be** - Tinh toan va tao ban ve be lang, be chua, be dieu hoa
2. **Thiet ke Duong ong** - Thiet ke tuyen ong tu chay va co ap
3. **Thiet ke Gieng** - Thiet ke gieng quan trac

---

## Xu ly loi thuong gap

### Loi 1: "ModuleNotFoundError: No module named 'sqlalchemy'"
**Nguyen nhan**: Chua cai dat thu vien hoac dang dung sai moi truong Python
**Cach xu ly**:
```bash
pip install sqlalchemy[asyncio] aiomysql
```
Hoac dam bao dang dung dung moi truong Anaconda:
```bash
conda activate design_assistant
```

### Loi 2: "Can't connect to MySQL server"
**Nguyen nhan**: MySQL chua khoi dong hoac sai thong tin ket noi
**Cach xu ly**:
- Dam bao Laragon da khoi dong va MySQL dang chay (icon MySQL xanh)
- Kiem tra database `design_assistant` da duoc tao
- Kiem tra file `.env` co dung thong tin

### Loi 3: "Error loading ASGI app. Could not import module 'main'"
**Nguyen nhan**: Chua cd vao thu muc backend
**Cach xu ly**:
```bash
cd D:\HydroDraft\design_assistant\backend
python -m uvicorn main:app --reload
```

### Loi 4: "npm ERR! code ENOENT"
**Nguyen nhan**: Chua cai dat Node.js hoac chua chay npm install
**Cach xu ly**:
- Cai Node.js tu https://nodejs.org/
- Chay `npm install` trong thu muc frontend

### Loi 5: Canh bao "pythonOCC khong duoc cai dat"
**Nguyen nhan**: Day chi la canh bao, khong anh huong chuc nang chinh
**Cach xu ly** (tuy chon - neu can xuat 3D):
```bash
conda install -c conda-forge pythonocc-core
```

---

## Cau truc thu muc

```
design_assistant/
|-- backend/                 # Ma nguon Backend (Python/FastAPI)
|   |-- api/                # Cac API endpoint
|   |-- calculations/       # Logic tinh toan thiet ke
|   |-- database/           # Ket noi va model database
|   |-- generators/         # Tao file DXF/IFC
|   |-- rules/              # Quy tac thiet ke
|   |-- templates/          # Template thiet ke
|   |-- main.py            # Entry point
|   |-- requirements.txt   # Cac thu vien can thiet
|
|-- frontend/               # Ma nguon Frontend (React)
|   |-- src/
|   |   |-- pages/         # Cac trang giao dien
|   |   |-- components/    # Component dung chung
|   |-- package.json       # Cau hinh npm
|
|-- outputs/                # Thu muc xuat file
```

---

## Lien he ho tro

Neu gap van de, vui long kiem tra:
1. Log cua backend trong terminal
2. Console cua trinh duyet (F12 -> Console)
3. API response tai http://localhost:8000/docs

---

## Phien ban

- Backend: FastAPI 0.109+
- Frontend: React 18
- Database: MySQL 8.0+ (Laragon)
- Python: 3.10+
- Node.js: 18+
