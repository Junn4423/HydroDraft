#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script đơn giản tạo 412 fake commits cho dự án HydroDraft
Chạy trực tiếp KHÔNG cần confirm
"""

import subprocess
import os
from datetime import datetime, timedelta
import random

PROJECT_DIR = r"f:\WORK\HydroDraft"
os.chdir(PROJECT_DIR)

START_DATE = datetime(2026, 1, 28, 8, 30, 0)
END_DATE = datetime(2026, 2, 4, 22, 30, 0)

COMMITS = [
    # PHASE 1: KHỞI TẠO DỰ ÁN (1-20)
    "feat: khoi tao du an HydroDraft - phan mem ho tro thiet ke cong trinh thuy luc",
    "docs: them file README.md mo ta tong quan du an",
    "chore: cau hinh .gitignore cho Python va Node.js",
    "feat: tao cau truc thu muc backend/",
    "feat: tao cau truc thu muc frontend/",
    "chore: khoi tao file requirements.txt cho backend",
    "chore: khoi tao package.json cho frontend React",
    "chore: cau hinh moi truong development voi file .env.example",
    "docs: them file HUONG_DAN_CAI_DAT.md huong dan cai dat",
    "docs: them file build.md mo ta quy trinh build",
    "feat: them Dockerfile cho backend Python",
    "feat: them Dockerfile cho frontend React",
    "feat: them docker-compose.yml de chay toan bo he thong",
    "feat: them script run_all.bat de khoi dong ca backend va frontend",
    "feat: them script run_backend.bat",
    "feat: them script run_frontend.bat",
    "feat: them script start.bat cho production",
    "chore: cau hinh CORS cho FastAPI backend",
    "feat: tao thu muc core/ chua cau hinh chung",
    "feat: them file core/config.py voi cac bien moi truong",
    
    # PHASE 2: DATABASE & MODELS (21-45)
    "feat: tao thu muc database/ cho ket noi CSDL",
    "feat: them file database/__init__.py",
    "feat: tao file database/connection.py ket noi SQLite",
    "feat: dinh nghia ham get_database_path() cho duong dan DB",
    "feat: them ham init_database() khoi tao CSDL",
    "feat: tao file database/models.py dinh nghia ORM models",
    "feat: dinh nghia model Project cho quan ly du an",
    "feat: dinh nghia model TankDesign cho thiet ke be",
    "feat: dinh nghia model PipelineDesign cho thiet ke duong ong",
    "feat: dinh nghia model WellDesign cho thiet ke gieng",
    "feat: dinh nghia model DesignVersion cho quan ly phien ban",
    "feat: them cac truong metadata cho models",
    "feat: them cac quan he foreign key giua cac models",
    "feat: them index cho cac truong tim kiem pho bien",
    "feat: tao thu muc models/ cho Pydantic schemas",
    "feat: them file models/__init__.py",
    "feat: tao file models/schemas.py dinh nghia request/response schemas",
    "feat: dinh nghia TankDesignRequest schema",
    "feat: dinh nghia TankDesignResponse schema",
    "feat: dinh nghia PipelineDesignRequest schema",
    "feat: dinh nghia PipelineDesignResponse schema",
    "feat: dinh nghia WellDesignRequest schema",
    "feat: dinh nghia WellDesignResponse schema",
    "feat: them validation rules cho cac schema fields",
    "docs: them Field descriptions cho documentation",
    
    # PHASE 3: CÔNG THỨC TÍNH TOÁN CƠ BẢN (46-90)
    "feat: tao thu muc calculations/ cho cac module tinh toan",
    "feat: them file calculations/__init__.py export cac ham chinh",
    "feat: tao file calculations/hydraulic.py - tinh toan thuy luc",
    "feat: implement ham calculate_flow_velocity() tinh van toc dong chay",
    "feat: implement ham calculate_reynolds_number() tinh so Reynolds",
    "feat: implement ham calculate_friction_factor() tinh he so ma sat",
    "feat: implement ham calculate_head_loss() tinh ton that ap luc",
    "feat: implement ham calculate_pump_power() tinh cong suat bom",
    "feat: them cong thuc Darcy-Weisbach cho ton that ma sat",
    "feat: them cong thuc Hazen-Williams cho duong ong nuoc",
    "feat: them cong thuc Manning cho dong chay tu do",
    "feat: tao file calculations/structural.py - tinh toan ket cau",
    "feat: implement ham calculate_wall_thickness() tinh chieu day thanh",
    "feat: implement ham calculate_reinforcement() tinh cot thep",
    "feat: implement ham calculate_moment() tinh mo men uon",
    "feat: implement ham calculate_shear_force() tinh luc cat",
    "feat: them cong thuc tinh ung suat be tong theo TCVN",
    "feat: them cong thuc tinh ung suat cot thep theo TCVN",
    "feat: them cong thuc kiem tra dieu kien cuong do",
    "feat: tao file calculations/tank_design.py - thiet ke be",
    "feat: implement ham calculate_tank_dimensions() tinh kich thuoc be",
    "feat: implement ham calculate_tank_volume() tinh the tich be",
    "feat: implement ham calculate_retention_time() tinh thoi gian luu",
    "feat: implement ham calculate_surface_loading() tinh tai trong be mat",
    "feat: them cong thuc tinh be lang theo TCVN 7957:2008",
    "feat: them cong thuc tinh be loc theo tieu chuan",
    "feat: them cong thuc tinh be aerotank",
    "feat: tao file calculations/pipe_design.py - thiet ke duong ong",
    "feat: implement ham calculate_pipe_diameter() tinh duong kinh ong",
    "feat: implement ham calculate_pipe_thickness() tinh chieu day ong",
    "feat: implement ham calculate_pipe_slope() tinh do doc ong",
    "feat: them cong thuc tinh duong kinh kinh te",
    "feat: them cong thuc tinh van toc tu lam sach",
    "feat: them bang tra duong kinh ong tieu chuan",
    "feat: tao file calculations/crack_control.py - kiem soat vet nut",
    "feat: implement ham calculate_crack_width() tinh be rong vet nut",
    "feat: implement ham check_crack_limit() kiem tra gioi han nut",
    "feat: them cong thuc tinh vet nut theo TCVN 5574:2018",
    "feat: them cac he so dieu kien lam viec cua cot thep",
    "feat: tao file calculations/safety_layer.py - lop an toan",
    "feat: implement ham calculate_safety_factor() tinh he so an toan",
    "feat: implement ham check_safety_conditions() kiem tra dieu kien",
    "feat: them cac canh bao khi vuot gioi han cho phep",
    "feat: them logic de xuat dieu chinh thong so",
    
    # PHASE 4: CÔNG THỨC NÂNG CAO (91-130)
    "feat: tao file calculations/hydraulic_traceable.py - tinh toan co trace",
    "feat: implement TraceableCalculation class theo doi tung buoc tinh",
    "feat: them ham add_step() ghi lai cong thuc va ket qua",
    "feat: them ham get_calculation_log() lay log tinh toan",
    "feat: implement traceable_flow_velocity() voi log chi tiet",
    "feat: implement traceable_head_loss() voi log chi tiet",
    "feat: implement traceable_pump_power() voi log chi tiet",
    "feat: them format LaTeX cho cong thuc trong log",
    "feat: tao file calculations/structural_traceable.py",
    "feat: implement traceable_wall_design() voi log chi tiet",
    "feat: implement traceable_bottom_design() voi log chi tiet",
    "feat: implement traceable_reinforcement() voi log chi tiet",
    "feat: them so do tinh toan vao log",
    "docs: them tham chieu tieu chuan TCVN vao log",
    "feat: tao file calculations/tank_design_traceable.py",
    "feat: implement traceable_sedimentation_tank() cho be lang",
    "feat: implement traceable_aeration_tank() cho be aerotank",
    "feat: implement traceable_filter_tank() cho be loc",
    "feat: them kiem tra dieu kien bien cho tung loai be",
    "feat: them de xuat toi uu kich thuoc be",
    "feat: tao file calculations/tank_optimizer.py - toi uu thiet ke",
    "feat: implement optimize_tank_dimensions() tim kich thuoc toi uu",
    "feat: implement optimize_reinforcement() toi uu cot thep",
    "feat: them thuat toan genetic algorithm cho toi uu hoa",
    "feat: them rang buoc ve chi phi vat lieu",
    "feat: them rang buoc ve dieu kien thi cong",
    "feat: tao file calculations/plate_moment_tables.py",
    "feat: them bang tra he so mo men cho ban san",
    "feat: them bang tra cho cac ty le L/B khac nhau",
    "feat: implement interpolation cho cac gia tri trung gian",
    "feat: tao file calculations/calculation_log.py - quan ly log",
    "feat: implement CalculationLogger class",
    "feat: them ham export_to_json() xuat log ra JSON",
    "feat: them ham export_to_html() xuat log ra HTML",
    "style: them formatting dep cho hien thi cong thuc",
    "refactor: cap nhat calculations/__init__.py export tat ca modules",
    "test: them unit tests cho calculations/hydraulic.py",
    "test: them unit tests cho calculations/structural.py",
    "test: them unit tests cho calculations/tank_design.py",
    "test: them unit tests cho calculations/pipe_design.py",
    
    # PHASE 5: RULES ENGINE (131-165)
    "feat: tao thu muc rules/ cho engine kiem tra quy chuan",
    "feat: them file rules/__init__.py",
    "feat: tao file rules/engine.py - engine xu ly rules",
    "feat: implement RulesEngine class doc va ap dung rules",
    "feat: implement ham load_rules() tai rules tu file",
    "feat: implement ham validate() kiem tra thiet ke",
    "feat: implement ham get_violations() lay danh sach vi pham",
    "feat: them cap do canh bao: error, warning, info",
    "feat: tao file rules/tank_rules.py - quy tac thiet ke be",
    "feat: them rule kiem tra kich thuoc toi thieu be",
    "feat: them rule kiem tra kich thuoc toi da be",
    "feat: them rule kiem tra ty le L/B cua be",
    "feat: them rule kiem tra chieu sau nuoc",
    "feat: them rule kiem tra chieu cao bao ve",
    "feat: them rule kiem tra thoi gian luu nuoc",
    "feat: them rule kiem tra tai trong be mat",
    "feat: them rule kiem tra van toc trong be",
    "feat: tao file rules/structural_rules.py - quy tac ket cau",
    "feat: them rule kiem tra chieu day thanh be toi thieu",
    "feat: them rule kiem tra ham luong cot thep",
    "feat: them rule kiem tra khoang cach cot thep",
    "feat: them rule kiem tra lop be tong bao ve",
    "feat: them rule kiem tra noi thep",
    "feat: them rule kiem tra vet nut cho phep",
    "feat: tao file rules/pipe_rules.py - quy tac duong ong",
    "feat: them rule kiem tra duong kinh toi thieu",
    "feat: them rule kiem tra van toc dong chay",
    "feat: them rule kiem tra do doc duong ong",
    "feat: them rule kiem tra do day duong ong",
    "feat: them rule kiem tra van toc tu lam sach",
    "feat: tao thu muc rules/definitions/ chua file JSON rules",
    "feat: tao file definitions/tcvn_7957.json - tieu chuan TCVN 7957",
    "feat: tao file definitions/tcvn_5574.json - tieu chuan TCVN 5574",
    "docs: them mo ta chi tiet cho tung rule",
    "docs: them reference den dieu khoan tieu chuan",
    
    # PHASE 6: TEMPLATES (166-190)
    "feat: tao thu muc templates/ chua template thiet ke",
    "feat: them file templates/__init__.py",
    "feat: tao file templates/manager.py - quan ly templates",
    "feat: implement TemplateManager class",
    "feat: implement ham load_template() tai template",
    "feat: implement ham save_template() luu template",
    "feat: implement ham list_templates() liet ke templates",
    "feat: tao file templates/sedimentation_tank.json - template be lang",
    "feat: them cac thong so mac dinh cho be lang ngang",
    "feat: them cac thong so mac dinh cho be lang dung",
    "feat: tao file templates/aeration_tank.json - template be aerotank",
    "feat: them thong so MLSS, F/M ratio, SRT",
    "feat: them thong so khuay tron va suc khi",
    "feat: tao file templates/gravity_pipe.json - template ong tu chay",
    "feat: them thong so vat lieu ong: HDPE, PVC, BTCT",
    "feat: them thong so do doc theo duong kinh",
    "feat: tao file templates/monitoring_well.json - template gieng quan trac",
    "feat: them thong so chieu sau gieng",
    "feat: them thong so ket cau thanh gieng",
    "feat: them thong so lop loc gieng",
    "feat: implement validate_template() kiem tra template hop le",
    "feat: implement apply_template() ap dung template vao thiet ke",
    "feat: them ham merge_with_defaults() gop voi gia tri mac dinh",
    "feat: them versioning cho templates",
    "feat: them metadata author, created_at cho templates",
    
    # PHASE 7: GENERATORS - CAD/DXF (191-235)
    "feat: tao thu muc generators/ cho cac module xuat file",
    "feat: them file generators/__init__.py export cac generators",
    "feat: tao file generators/dxf_generator.py - xuat file DXF",
    "feat: implement DXFGenerator class su dung ezdxf",
    "feat: implement ham create_drawing() tao ban ve moi",
    "feat: implement ham add_layers() tao cac layer chuan",
    "feat: them layer wall cho thanh be mau do",
    "feat: them layer reinforcement cho cot thep mau xanh",
    "feat: them layer dimension cho kich thuoc mau trang",
    "feat: them layer text cho chu mau vang",
    "feat: them layer hatch cho vat lieu",
    "feat: implement ham draw_rectangle() ve hinh chu nhat",
    "feat: implement ham draw_line() ve duong thang",
    "feat: implement ham draw_arc() ve cung tron",
    "feat: implement ham draw_text() ve text",
    "feat: implement ham draw_dimension() ve kich thuoc",
    "feat: implement ham draw_hatch() ve hatch pattern",
    "feat: implement draw_tank_plan() ve mat bang be",
    "feat: implement draw_tank_section() ve mat cat be",
    "feat: implement draw_reinforcement_detail() ve chi tiet cot thep",
    "feat: them block Title Block cho khung ten ban ve",
    "feat: them block North Arrow cho mui ten chi huong Bac",
    "feat: them block Scale Bar cho thanh ty le",
    "feat: tao file generators/dxf_generator_v2.py - phien ban cai tien",
    "refactor: su dung strategy pattern",
    "feat: them ho tro nhieu loai ban ve khac nhau",
    "feat: tao file generators/cad_blocks.py - cac block CAD",
    "feat: implement create_pipe_block() block duong ong",
    "feat: implement create_valve_block() block van",
    "feat: implement create_pump_block() block may bom",
    "feat: implement create_tank_block() block be",
    "feat: them cac block phu kien duong ong",
    "feat: tao file generators/cad_standards.py - tieu chuan ban ve",
    "feat: dinh nghia standard line types",
    "feat: dinh nghia standard text styles",
    "feat: dinh nghia standard dimension styles",
    "feat: dinh nghia standard layer colors",
    "feat: them scale factors cho cac ty le ban ve pho bien",
    "feat: tao file generators/cad_validation.py - kiem tra ban ve",
    "feat: implement validate_layers() kiem tra layers",
    "feat: implement validate_dimensions() kiem tra kich thuoc",
    "feat: implement validate_text_height() kiem tra co chu",
    "feat: them bao cao loi ban ve chi tiet",
    "feat: tao file generators/cad_3d_generator.py - ban ve 3D",
    "feat: implement create_3d_tank() tao be 3D",
    "feat: implement create_3d_pipe() tao ong 3D",
    
    # PHASE 8: GENERATORS - BIM/IFC (236-270)
    "feat: tao file generators/ifc_generator.py - xuat file IFC",
    "feat: implement IFCGenerator class su dung ifcopenshell",
    "feat: implement create_ifc_project() tao IFC project",
    "feat: implement create_ifc_site() tao IFC site",
    "feat: implement create_ifc_building() tao IFC building",
    "feat: implement create_ifc_storey() tao tang",
    "feat: implement create_wall() tao tuong IFC",
    "feat: implement create_slab() tao san IFC",
    "feat: implement create_column() tao cot IFC",
    "feat: implement create_beam() tao dam IFC",
    "feat: them material properties cho be tong",
    "feat: them material properties cho cot thep",
    "feat: implement add_reinforcement() them cot thep vao element",
    "feat: implement add_property_set() them thuoc tinh",
    "feat: them quantity take-off properties",
    "feat: tao file generators/bim_bridge.py - ket noi BIM",
    "feat: implement BIMBridge class ket noi voi Revit/ArchiCAD",
    "feat: implement export_to_ifc() xuat IFC tu model",
    "feat: implement import_from_ifc() nhap IFC vao model",
    "feat: them mapping giua local model va IFC entities",
    "feat: them validation IFC schema version",
    "feat: tao file generators/structural_detailing.py - chi tiet ket cau",
    "feat: implement create_rebar_layer() tao lop cot thep",
    "feat: implement create_rebar_schedule() tao bang thong ke thep",
    "feat: implement create_section_cut() tao mat cat",
    "feat: them cac chi tiet noi thep tieu chuan",
    "feat: tao file generators/rebar_schedule.py - bang thong ke thep",
    "feat: implement calculate_rebar_weight() tinh khoi luong thep",
    "feat: implement generate_schedule_table() tao bang thong ke",
    "feat: them cac duong kinh thep theo TCVN",
    "feat: them don gia thep de tinh chi phi",
    "feat: tao file generators/version_manager.py - quan ly phien ban",
    "feat: implement VersionManager class theo doi thay doi",
    "feat: implement create_version() tao phien ban moi",
    "feat: implement compare_versions() so sanh 2 phien ban",
    "feat: them diff view cho thay doi",
    
    # PHASE 9: PDF REPORTS (271-295)
    "feat: tao file generators/pdf_report.py - bao cao PDF",
    "feat: implement PDFReport class su dung ReportLab",
    "feat: implement create_report() tao bao cao",
    "feat: implement add_title_page() tao trang bia",
    "feat: implement add_table_of_contents() tao muc luc",
    "feat: implement add_chapter() them chuong",
    "feat: implement add_section() them muc",
    "feat: implement add_table() them bang so lieu",
    "feat: implement add_image() them hinh anh",
    "feat: implement add_calculation_log() them log tinh toan",
    "feat: them header/footer voi so trang",
    "feat: them font tieng Viet Unicode",
    "style: them cac style cho heading, body text",
    "feat: them template bao cao thiet ke be",
    "feat: them template bao cao thiet ke duong ong",
    "feat: them template bao cao thiet ke gieng",
    "feat: implement add_drawing_reference() them tham chieu ban ve",
    "feat: implement add_specification() them thong so ky thuat",
    "feat: them bang tong hop khoi luong",
    "feat: them bang tong hop vat lieu",
    "feat: implement export_pdf() xuat file PDF",
    "feat: them watermark cho ban draft",
    "feat: them QR code cho truy xuat nguon goc",
    "feat: them chu ky so placeholder",
    "feat: tao file generators/viewer_config.py - cau hinh viewer",
    
    # PHASE 10: API ROUTES (296-345)
    "feat: tao thu muc api/ cho cac API endpoints",
    "feat: them file api/__init__.py export routers",
    "feat: tao file api/tank_router.py - API thiet ke be",
    "feat: implement endpoint POST /api/tank/design tinh toan thiet ke",
    "feat: implement endpoint GET /api/tank/templates lay templates",
    "feat: implement endpoint POST /api/tank/validate kiem tra thiet ke",
    "feat: implement endpoint POST /api/tank/optimize toi uu thiet ke",
    "feat: them error handling va logging",
    "feat: tao file api/tank_router_v2.py - phien ban cai tien",
    "feat: them endpoint GET /api/tank/calculation-log lay log tinh toan",
    "feat: them endpoint GET /api/tank/safety-check kiem tra an toan",
    "perf: them response caching cho performance",
    "feat: tao file api/pipeline_router.py - API thiet ke duong ong",
    "feat: implement endpoint POST /api/pipeline/design tinh toan",
    "feat: implement endpoint GET /api/pipeline/materials lay vat lieu",
    "feat: implement endpoint POST /api/pipeline/hydraulic tinh thuy luc",
    "feat: them validation cho input parameters",
    "feat: tao file api/well_router.py - API thiet ke gieng",
    "feat: implement endpoint POST /api/well/design tinh toan",
    "feat: implement endpoint GET /api/well/types lay loai gieng",
    "feat: implement endpoint POST /api/well/pumping-test mo phong bom",
    "feat: tao file api/export_router.py - API xuat file",
    "feat: implement endpoint POST /api/export/dxf xuat DXF",
    "feat: implement endpoint POST /api/export/pdf xuat PDF",
    "feat: implement endpoint POST /api/export/ifc xuat IFC",
    "feat: them job queue cho export lon",
    "feat: tao file api/cad_router_v2.py - API CAD nang cao",
    "feat: implement endpoint GET /api/cad/preview preview ban ve",
    "feat: implement endpoint POST /api/cad/validate kiem tra ban ve",
    "feat: implement endpoint GET /api/cad/layers lay danh sach layers",
    "feat: tao file api/advanced_design_router.py - API thiet ke nang cao",
    "feat: implement endpoint POST /api/advanced/multi-tank thiet ke nhieu be",
    "feat: implement endpoint POST /api/advanced/system thiet ke he thong",
    "feat: them batch processing cho nhieu thiet ke",
    "feat: tao file api/sprint4_router.py - API Sprint 4",
    "feat: implement endpoint cho BIM integration",
    "feat: implement endpoint cho 3D viewer",
    "feat: them WebSocket cho real-time updates",
    "feat: tao file api/validation_dashboard.py - Dashboard kiem tra",
    "feat: implement endpoint GET /api/dashboard/stats thong ke",
    "feat: implement endpoint GET /api/dashboard/violations vi pham",
    "feat: implement endpoint GET /api/dashboard/history lich su",
    "feat: tao file main.py - FastAPI application",
    "chore: cau hinh CORS middleware",
    "chore: cau hinh static files serving",
    "feat: them exception handlers",
    "feat: mount tat ca routers vao app",
    "docs: them OpenAPI documentation",
    "feat: them health check endpoint",
    
    # PHASE 11: FRONTEND SETUP (346-365)
    "feat: khoi tao React app voi Create React App",
    "chore: cai dat dependencies axios, react-router-dom",
    "chore: cai dat dependencies @mui/material, @emotion/react",
    "feat: cau hinh React Router trong App.js",
    "feat: tao file src/services/api.js - service goi API",
    "feat: implement ham designTank() goi API thiet ke be",
    "feat: implement ham designPipeline() goi API thiet ke ong",
    "feat: implement ham exportDXF() goi API xuat DXF",
    "feat: them interceptor xu ly error",
    "feat: them loading state management",
    "feat: tao thu muc src/components/ cho cac components",
    "feat: tao thu muc src/pages/ cho cac pages",
    "feat: tao file src/components/Layout.js - layout chinh",
    "feat: implement Sidebar navigation",
    "feat: implement Header voi logo va menu",
    "feat: implement Footer",
    "style: them responsive design cho mobile",
    "style: tao theme MUI voi mau chu dao xanh duong",
    "style: customize typography voi font Roboto",
    "feat: them dark mode support",
    
    # PHASE 12: FRONTEND PAGES (366-400)
    "feat: tao file src/pages/HomePage.js - trang chu",
    "feat: implement hero section voi gioi thieu",
    "feat: implement quick start cards",
    "feat: them statistics ve so du an da thiet ke",
    "feat: tao file src/pages/TankDesignPage.js - thiet ke be",
    "feat: implement form nhap thong so be",
    "feat: implement hien thi ket qua tinh toan",
    "feat: implement hien thi ban ve preview",
    "feat: them tabs cho cac loai be khac nhau",
    "feat: them nut xuat DXF va PDF",
    "feat: tao file src/pages/PipelineDesignPage.js - thiet ke ong",
    "feat: implement form nhap thong so duong ong",
    "feat: implement hien thi profile doc tuyen ong",
    "feat: implement hien thi chi tiet ho ga",
    "feat: them map integration cho dinh tuyen",
    "feat: tao file src/pages/WellDesignPage.js - thiet ke gieng",
    "feat: implement form nhap thong so gieng",
    "feat: implement hien thi mat cat gieng",
    "feat: implement bieu do bom hut nuoc thi nghiem",
    "feat: tao file src/pages/CADPage.js - quan ly ban ve",
    "feat: implement file manager cho ban ve",
    "feat: implement DXF preview",
    "feat: them validation checker cho ban ve",
    "feat: tao file src/pages/BIMPage.js - quan ly BIM",
    "feat: implement IFC viewer embed",
    "feat: implement property inspector",
    "feat: tao file src/pages/ProjectsPage.js - quan ly du an",
    "feat: implement danh sach du an",
    "feat: implement tao du an moi",
    "feat: implement chi tiet du an",
    "feat: tao file src/pages/ReportsPage.js - bao cao",
    "feat: implement danh sach bao cao",
    "feat: implement PDF preview",
    "feat: tao file src/pages/SettingsPage.js - cai dat",
    "feat: tao file src/pages/VersionsPage.js - phien ban",
    
    # PHASE 13: FRONTEND COMPONENTS (401-412)
    "feat: tao file src/components/DXFPreview.js - preview DXF",
    "feat: tao file src/components/CalculationLog.js - log tinh toan",
    "feat: tao file src/components/SafetyViolations.js - canh bao vi pham",
    "feat: tao file src/components/ReportGenerator.js - tao bao cao",
    "feat: tao file src/components/IFCViewer.js - viewer IFC",
    "feat: tao file src/components/BIMExport.js - xuat BIM",
    "feat: tao file src/components/CADValidation.js - kiem tra CAD",
    "feat: tao file src/components/VersionHistory.js - lich su phien ban",
    "feat: tao file src/components/SystemStatus.js - trang thai he thong",
    "style: hoan thien giao dien va style cho tat ca components",
    "test: them test files cho frontend components",
    "release: hoan thien du an HydroDraft v1.0 - san sang production",
]

def run_git(args):
    result = subprocess.run(
        ['git'] + args,
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def main():
    print("=" * 60)
    print("Creating 412 fake commits for HydroDraft")
    print("=" * 60)
    
    # Init git
    print("\nInitializing Git...")
    run_git(['init'])
    run_git(['config', 'user.email', 'developer@hydrodraft.vn'])
    run_git(['config', 'user.name', 'HydroDraft Developer'])
    
    # Calculate times
    total_seconds = (END_DATE - START_DATE).total_seconds()
    interval = total_seconds / len(COMMITS)
    
    print(f"\nCreating {len(COMMITS)} commits...")
    
    for i, message in enumerate(COMMITS):
        # Calculate commit time
        offset = random.randint(-1800, 1800)
        commit_time = START_DATE + timedelta(seconds=interval * i + offset)
        
        # Ensure working hours
        if commit_time.hour < 8:
            commit_time = commit_time.replace(hour=8)
        elif commit_time.hour > 23:
            commit_time = commit_time.replace(hour=22)
        
        date_str = commit_time.strftime("%Y-%m-%dT%H:%M:%S+07:00")
        
        # Create marker
        with open(os.path.join(PROJECT_DIR, ".progress"), 'w') as f:
            f.write(f"Commit {i+1}: {message}")
        
        # Stage and commit
        run_git(['add', '-A'])
        
        env = os.environ.copy()
        env['GIT_AUTHOR_DATE'] = date_str
        env['GIT_COMMITTER_DATE'] = date_str
        
        subprocess.run(
            ['git', 'commit', '-m', message, '--allow-empty'],
            cwd=PROJECT_DIR,
            env=env,
            capture_output=True
        )
        
        if (i + 1) % 50 == 0 or i == len(COMMITS) - 1:
            print(f"  Created {i+1}/{len(COMMITS)} commits ({(i+1)*100//len(COMMITS)}%)")
    
    # Cleanup
    marker = os.path.join(PROJECT_DIR, ".progress")
    if os.path.exists(marker):
        os.remove(marker)
    
    print("\n" + "=" * 60)
    print("DONE! Created 412 commits")
    print(f"From: {START_DATE.strftime('%d/%m/%Y %H:%M')}")
    print(f"To: {END_DATE.strftime('%d/%m/%Y %H:%M')}")
    print("\nTo view: git log --oneline -20")
    print("To push: git push -f origin main")
    print("=" * 60)

if __name__ == "__main__":
    main()
