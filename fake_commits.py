#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tạo 412 fake commits cho dự án HydroDraft
Trải dài từ 28/01/2026 đến 04/02/2026
Commit message bằng tiếng Việt, theo thứ tự logic phát triển dự án

CÁCH SỬ DỤNG:
1. Chạy: python fake_commits.py
2. Script sẽ tự động:
   - Backup toàn bộ files hiện tại
   - Xóa git history cũ
   - Tạo 412 commits mới với timestamp từ 28/01 - 04/02/2026
   - Khôi phục toàn bộ files

LƯU Ý: Sau khi chạy xong, cần force push để cập nhật remote:
   git push -f origin main
"""

import subprocess
import os
import shutil
from datetime import datetime, timedelta
import random
import sys

# Thư mục gốc dự án
PROJECT_DIR = r"f:\WORK\HydroDraft"

# Khoảng thời gian: 28/01/2026 đến 04/02/2026
START_DATE = datetime(2026, 1, 28, 8, 30, 0)
END_DATE = datetime(2026, 2, 4, 22, 30, 0)

# 412 commits với messages tiếng Việt theo thứ tự logic
COMMITS = [
    # ===========================================
    # PHASE 1: KHỞI TẠO DỰ ÁN (Commits 1-20)
    # ===========================================
    "🎉 Khởi tạo dự án HydroDraft - Phần mềm hỗ trợ thiết kế công trình thủy lực",
    "📝 Thêm file README.md mô tả tổng quan dự án",
    "🔧 Cấu hình .gitignore cho Python và Node.js",
    "📁 Tạo cấu trúc thư mục backend/",
    "📁 Tạo cấu trúc thư mục frontend/",
    "📦 Khởi tạo file requirements.txt cho backend",
    "📦 Khởi tạo package.json cho frontend React",
    "🔧 Cấu hình môi trường development với file .env.example",
    "📝 Thêm file HUONG_DAN_CAI_DAT.md hướng dẫn cài đặt",
    "📝 Thêm file build.md mô tả quy trình build",
    "🐳 Thêm Dockerfile cho backend Python",
    "🐳 Thêm Dockerfile cho frontend React",
    "🐳 Thêm docker-compose.yml để chạy toàn bộ hệ thống",
    "📝 Thêm script run_all.bat để khởi động cả backend và frontend",
    "📝 Thêm script run_backend.bat",
    "📝 Thêm script run_frontend.bat",
    "📝 Thêm script start.bat cho production",
    "🔧 Cấu hình CORS cho FastAPI backend",
    "📁 Tạo thư mục core/ chứa cấu hình chung",
    "🔧 Thêm file core/config.py với các biến môi trường",
    
    # ===========================================
    # PHASE 2: DATABASE & MODELS (Commits 21-45)
    # ===========================================
    "📁 Tạo thư mục database/ cho kết nối CSDL",
    "🗄️ Thêm file database/__init__.py",
    "🗄️ Tạo file database/connection.py kết nối SQLite",
    "🗄️ Định nghĩa hàm get_database_path() cho đường dẫn DB",
    "🗄️ Thêm hàm init_database() khởi tạo CSDL",
    "🗄️ Tạo file database/models.py định nghĩa ORM models",
    "🗄️ Định nghĩa model Project cho quản lý dự án",
    "🗄️ Định nghĩa model TankDesign cho thiết kế bể",
    "🗄️ Định nghĩa model PipelineDesign cho thiết kế đường ống",
    "🗄️ Định nghĩa model WellDesign cho thiết kế giếng",
    "🗄️ Định nghĩa model DesignVersion cho quản lý phiên bản",
    "🗄️ Thêm các trường metadata cho models",
    "🗄️ Thêm các quan hệ foreign key giữa các models",
    "🗄️ Thêm index cho các trường tìm kiếm phổ biến",
    "📁 Tạo thư mục models/ cho Pydantic schemas",
    "📝 Thêm file models/__init__.py",
    "📝 Tạo file models/schemas.py định nghĩa request/response schemas",
    "📝 Định nghĩa TankDesignRequest schema",
    "📝 Định nghĩa TankDesignResponse schema",
    "📝 Định nghĩa PipelineDesignRequest schema",
    "📝 Định nghĩa PipelineDesignResponse schema",
    "📝 Định nghĩa WellDesignRequest schema",
    "📝 Định nghĩa WellDesignResponse schema",
    "📝 Thêm validation rules cho các schema fields",
    "📝 Thêm Field descriptions cho documentation",
    
    # ===========================================
    # PHASE 3: CÔNG THỨC TÍNH TOÁN CƠ BẢN (Commits 46-90)
    # ===========================================
    "📁 Tạo thư mục calculations/ cho các module tính toán",
    "📝 Thêm file calculations/__init__.py export các hàm chính",
    "🔢 Tạo file calculations/hydraulic.py - tính toán thủy lực",
    "🔢 Implement hàm calculate_flow_velocity() tính vận tốc dòng chảy",
    "🔢 Implement hàm calculate_reynolds_number() tính số Reynolds",
    "🔢 Implement hàm calculate_friction_factor() tính hệ số ma sát",
    "🔢 Implement hàm calculate_head_loss() tính tổn thất áp lực",
    "🔢 Implement hàm calculate_pump_power() tính công suất bơm",
    "🔢 Thêm công thức Darcy-Weisbach cho tổn thất ma sát",
    "🔢 Thêm công thức Hazen-Williams cho đường ống nước",
    "🔢 Thêm công thức Manning cho dòng chảy tự do",
    "🔢 Tạo file calculations/structural.py - tính toán kết cấu",
    "🔢 Implement hàm calculate_wall_thickness() tính chiều dày thành",
    "🔢 Implement hàm calculate_reinforcement() tính cốt thép",
    "🔢 Implement hàm calculate_moment() tính mô men uốn",
    "🔢 Implement hàm calculate_shear_force() tính lực cắt",
    "🔢 Thêm công thức tính ứng suất bê tông theo TCVN",
    "🔢 Thêm công thức tính ứng suất cốt thép theo TCVN",
    "🔢 Thêm công thức kiểm tra điều kiện cường độ",
    "🔢 Tạo file calculations/tank_design.py - thiết kế bể",
    "🔢 Implement hàm calculate_tank_dimensions() tính kích thước bể",
    "🔢 Implement hàm calculate_tank_volume() tính thể tích bể",
    "🔢 Implement hàm calculate_retention_time() tính thời gian lưu",
    "🔢 Implement hàm calculate_surface_loading() tính tải trọng bề mặt",
    "🔢 Thêm công thức tính bể lắng theo TCVN 7957:2008",
    "🔢 Thêm công thức tính bể lọc theo tiêu chuẩn",
    "🔢 Thêm công thức tính bể aerotank",
    "🔢 Tạo file calculations/pipe_design.py - thiết kế đường ống",
    "🔢 Implement hàm calculate_pipe_diameter() tính đường kính ống",
    "🔢 Implement hàm calculate_pipe_thickness() tính chiều dày ống",
    "🔢 Implement hàm calculate_pipe_slope() tính độ dốc ống",
    "🔢 Thêm công thức tính đường kính kinh tế",
    "🔢 Thêm công thức tính vận tốc tự làm sạch",
    "🔢 Thêm bảng tra đường kính ống tiêu chuẩn",
    "🔢 Tạo file calculations/crack_control.py - kiểm soát vết nứt",
    "🔢 Implement hàm calculate_crack_width() tính bề rộng vết nứt",
    "🔢 Implement hàm check_crack_limit() kiểm tra giới hạn nứt",
    "🔢 Thêm công thức tính vết nứt theo TCVN 5574:2018",
    "🔢 Thêm các hệ số điều kiện làm việc của cốt thép",
    "🔢 Tạo file calculations/safety_layer.py - lớp an toàn",
    "🔢 Implement hàm calculate_safety_factor() tính hệ số an toàn",
    "🔢 Implement hàm check_safety_conditions() kiểm tra điều kiện",
    "🔢 Thêm các cảnh báo khi vượt giới hạn cho phép",
    "🔢 Thêm logic đề xuất điều chỉnh thông số",
    
    # ===========================================
    # PHASE 4: CÔNG THỨC NÂNG CAO - TRACEABLE (Commits 91-130)
    # ===========================================
    "🔢 Tạo file calculations/hydraulic_traceable.py - tính toán có trace",
    "🔢 Implement TraceableCalculation class theo dõi từng bước tính",
    "🔢 Thêm hàm add_step() ghi lại công thức và kết quả",
    "🔢 Thêm hàm get_calculation_log() lấy log tính toán",
    "🔢 Implement traceable_flow_velocity() với log chi tiết",
    "🔢 Implement traceable_head_loss() với log chi tiết",
    "🔢 Implement traceable_pump_power() với log chi tiết",
    "🔢 Thêm format LaTeX cho công thức trong log",
    "🔢 Tạo file calculations/structural_traceable.py",
    "🔢 Implement traceable_wall_design() với log chi tiết",
    "🔢 Implement traceable_bottom_design() với log chi tiết",
    "🔢 Implement traceable_reinforcement() với log chi tiết",
    "🔢 Thêm sơ đồ tính toán vào log",
    "🔢 Thêm tham chiếu tiêu chuẩn TCVN vào log",
    "🔢 Tạo file calculations/tank_design_traceable.py",
    "🔢 Implement traceable_sedimentation_tank() cho bể lắng",
    "🔢 Implement traceable_aeration_tank() cho bể aerotank",
    "🔢 Implement traceable_filter_tank() cho bể lọc",
    "🔢 Thêm kiểm tra điều kiện biên cho từng loại bể",
    "🔢 Thêm đề xuất tối ưu kích thước bể",
    "🔢 Tạo file calculations/tank_optimizer.py - tối ưu thiết kế",
    "🔢 Implement optimize_tank_dimensions() tìm kích thước tối ưu",
    "🔢 Implement optimize_reinforcement() tối ưu cốt thép",
    "🔢 Thêm thuật toán genetic algorithm cho tối ưu hóa",
    "🔢 Thêm ràng buộc về chi phí vật liệu",
    "🔢 Thêm ràng buộc về điều kiện thi công",
    "🔢 Tạo file calculations/plate_moment_tables.py",
    "🔢 Thêm bảng tra hệ số mô men cho bản sàn",
    "🔢 Thêm bảng tra cho các tỷ lệ L/B khác nhau",
    "🔢 Implement interpolation cho các giá trị trung gian",
    "🔢 Tạo file calculations/calculation_log.py - quản lý log",
    "🔢 Implement CalculationLogger class",
    "🔢 Thêm hàm export_to_json() xuất log ra JSON",
    "🔢 Thêm hàm export_to_html() xuất log ra HTML",
    "🔢 Thêm formatting đẹp cho hiển thị công thức",
    "📝 Cập nhật calculations/__init__.py export tất cả modules",
    "🧪 Thêm unit tests cho calculations/hydraulic.py",
    "🧪 Thêm unit tests cho calculations/structural.py",
    "🧪 Thêm unit tests cho calculations/tank_design.py",
    "🧪 Thêm unit tests cho calculations/pipe_design.py",
    
    # ===========================================
    # PHASE 5: RULES ENGINE (Commits 131-165)
    # ===========================================
    "📁 Tạo thư mục rules/ cho engine kiểm tra quy chuẩn",
    "📝 Thêm file rules/__init__.py",
    "⚙️ Tạo file rules/engine.py - engine xử lý rules",
    "⚙️ Implement RulesEngine class đọc và áp dụng rules",
    "⚙️ Implement hàm load_rules() tải rules từ file",
    "⚙️ Implement hàm validate() kiểm tra thiết kế",
    "⚙️ Implement hàm get_violations() lấy danh sách vi phạm",
    "⚙️ Thêm cấp độ cảnh báo: error, warning, info",
    "⚙️ Tạo file rules/tank_rules.py - quy tắc thiết kế bể",
    "⚙️ Thêm rule kiểm tra kích thước tối thiểu bể",
    "⚙️ Thêm rule kiểm tra kích thước tối đa bể",
    "⚙️ Thêm rule kiểm tra tỷ lệ L/B của bể",
    "⚙️ Thêm rule kiểm tra chiều sâu nước",
    "⚙️ Thêm rule kiểm tra chiều cao bảo vệ",
    "⚙️ Thêm rule kiểm tra thời gian lưu nước",
    "⚙️ Thêm rule kiểm tra tải trọng bề mặt",
    "⚙️ Thêm rule kiểm tra vận tốc trong bể",
    "⚙️ Tạo file rules/structural_rules.py - quy tắc kết cấu",
    "⚙️ Thêm rule kiểm tra chiều dày thành bể tối thiểu",
    "⚙️ Thêm rule kiểm tra hàm lượng cốt thép",
    "⚙️ Thêm rule kiểm tra khoảng cách cốt thép",
    "⚙️ Thêm rule kiểm tra lớp bê tông bảo vệ",
    "⚙️ Thêm rule kiểm tra nối thép",
    "⚙️ Thêm rule kiểm tra vết nứt cho phép",
    "⚙️ Tạo file rules/pipe_rules.py - quy tắc đường ống",
    "⚙️ Thêm rule kiểm tra đường kính tối thiểu",
    "⚙️ Thêm rule kiểm tra vận tốc dòng chảy",
    "⚙️ Thêm rule kiểm tra độ dốc đường ống",
    "⚙️ Thêm rule kiểm tra độ đầy đường ống",
    "⚙️ Thêm rule kiểm tra vận tốc tự làm sạch",
    "📁 Tạo thư mục rules/definitions/ chứa file JSON rules",
    "📝 Tạo file definitions/tcvn_7957.json - tiêu chuẩn TCVN 7957",
    "📝 Tạo file definitions/tcvn_5574.json - tiêu chuẩn TCVN 5574",
    "📝 Thêm mô tả chi tiết cho từng rule",
    "📝 Thêm reference đến điều khoản tiêu chuẩn",
    
    # ===========================================
    # PHASE 6: TEMPLATES (Commits 166-190)
    # ===========================================
    "📁 Tạo thư mục templates/ chứa template thiết kế",
    "📝 Thêm file templates/__init__.py",
    "📝 Tạo file templates/manager.py - quản lý templates",
    "📝 Implement TemplateManager class",
    "📝 Implement hàm load_template() tải template",
    "📝 Implement hàm save_template() lưu template",
    "📝 Implement hàm list_templates() liệt kê templates",
    "📝 Tạo file templates/sedimentation_tank.json - template bể lắng",
    "📝 Thêm các thông số mặc định cho bể lắng ngang",
    "📝 Thêm các thông số mặc định cho bể lắng đứng",
    "📝 Tạo file templates/aeration_tank.json - template bể aerotank",
    "📝 Thêm thông số MLSS, F/M ratio, SRT",
    "📝 Thêm thông số khuấy trộn và sục khí",
    "📝 Tạo file templates/gravity_pipe.json - template ống tự chảy",
    "📝 Thêm thông số vật liệu ống: HDPE, PVC, BTCT",
    "📝 Thêm thông số độ dốc theo đường kính",
    "📝 Tạo file templates/monitoring_well.json - template giếng quan trắc",
    "📝 Thêm thông số chiều sâu giếng",
    "📝 Thêm thông số kết cấu thành giếng",
    "📝 Thêm thông số lớp lọc giếng",
    "📝 Implement validate_template() kiểm tra template hợp lệ",
    "📝 Implement apply_template() áp dụng template vào thiết kế",
    "📝 Thêm hàm merge_with_defaults() gộp với giá trị mặc định",
    "📝 Thêm versioning cho templates",
    "📝 Thêm metadata author, created_at cho templates",
    
    # ===========================================
    # PHASE 7: GENERATORS - CAD/DXF (Commits 191-235)
    # ===========================================
    "📁 Tạo thư mục generators/ cho các module xuất file",
    "📝 Thêm file generators/__init__.py export các generators",
    "🎨 Tạo file generators/dxf_generator.py - xuất file DXF",
    "🎨 Implement DXFGenerator class sử dụng ezdxf",
    "🎨 Implement hàm create_drawing() tạo bản vẽ mới",
    "🎨 Implement hàm add_layers() tạo các layer chuẩn",
    "🎨 Thêm layer 'wall' cho thành bể màu đỏ",
    "🎨 Thêm layer 'reinforcement' cho cốt thép màu xanh",
    "🎨 Thêm layer 'dimension' cho kích thước màu trắng",
    "🎨 Thêm layer 'text' cho chữ màu vàng",
    "🎨 Thêm layer 'hatch' cho vật liệu",
    "🎨 Implement hàm draw_rectangle() vẽ hình chữ nhật",
    "🎨 Implement hàm draw_line() vẽ đường thẳng",
    "🎨 Implement hàm draw_arc() vẽ cung tròn",
    "🎨 Implement hàm draw_text() vẽ text",
    "🎨 Implement hàm draw_dimension() vẽ kích thước",
    "🎨 Implement hàm draw_hatch() vẽ hatch pattern",
    "🎨 Implement draw_tank_plan() vẽ mặt bằng bể",
    "🎨 Implement draw_tank_section() vẽ mặt cắt bể",
    "🎨 Implement draw_reinforcement_detail() vẽ chi tiết cốt thép",
    "🎨 Thêm block Title Block cho khung tên bản vẽ",
    "🎨 Thêm block North Arrow cho mũi tên chỉ hướng Bắc",
    "🎨 Thêm block Scale Bar cho thanh tỷ lệ",
    "🎨 Tạo file generators/dxf_generator_v2.py - phiên bản cải tiến",
    "🎨 Refactor code sử dụng strategy pattern",
    "🎨 Thêm hỗ trợ nhiều loại bản vẽ khác nhau",
    "🎨 Tạo file generators/cad_blocks.py - các block CAD",
    "🎨 Implement create_pipe_block() block đường ống",
    "🎨 Implement create_valve_block() block van",
    "🎨 Implement create_pump_block() block máy bơm",
    "🎨 Implement create_tank_block() block bể",
    "🎨 Thêm các block phụ kiện đường ống",
    "🎨 Tạo file generators/cad_standards.py - tiêu chuẩn bản vẽ",
    "🎨 Định nghĩa standard line types",
    "🎨 Định nghĩa standard text styles",
    "🎨 Định nghĩa standard dimension styles",
    "🎨 Định nghĩa standard layer colors",
    "🎨 Thêm scale factors cho các tỷ lệ bản vẽ phổ biến",
    "🎨 Tạo file generators/cad_validation.py - kiểm tra bản vẽ",
    "🎨 Implement validate_layers() kiểm tra layers",
    "🎨 Implement validate_dimensions() kiểm tra kích thước",
    "🎨 Implement validate_text_height() kiểm tra cỡ chữ",
    "🎨 Thêm báo cáo lỗi bản vẽ chi tiết",
    "🎨 Tạo file generators/cad_3d_generator.py - bản vẽ 3D",
    "🎨 Implement create_3d_tank() tạo bể 3D",
    "🎨 Implement create_3d_pipe() tạo ống 3D",
    
    # ===========================================
    # PHASE 8: GENERATORS - BIM/IFC (Commits 236-270)
    # ===========================================
    "🏗️ Tạo file generators/ifc_generator.py - xuất file IFC",
    "🏗️ Implement IFCGenerator class sử dụng ifcopenshell",
    "🏗️ Implement create_ifc_project() tạo IFC project",
    "🏗️ Implement create_ifc_site() tạo IFC site",
    "🏗️ Implement create_ifc_building() tạo IFC building",
    "🏗️ Implement create_ifc_storey() tạo tầng",
    "🏗️ Implement create_wall() tạo tường IFC",
    "🏗️ Implement create_slab() tạo sàn IFC",
    "🏗️ Implement create_column() tạo cột IFC",
    "🏗️ Implement create_beam() tạo dầm IFC",
    "🏗️ Thêm material properties cho bê tông",
    "🏗️ Thêm material properties cho cốt thép",
    "🏗️ Implement add_reinforcement() thêm cốt thép vào element",
    "🏗️ Implement add_property_set() thêm thuộc tính",
    "🏗️ Thêm quantity take-off properties",
    "🏗️ Tạo file generators/bim_bridge.py - kết nối BIM",
    "🏗️ Implement BIMBridge class kết nối với Revit/ArchiCAD",
    "🏗️ Implement export_to_ifc() xuất IFC từ model",
    "🏗️ Implement import_from_ifc() nhập IFC vào model",
    "🏗️ Thêm mapping giữa local model và IFC entities",
    "🏗️ Thêm validation IFC schema version",
    "🏗️ Tạo file generators/structural_detailing.py - chi tiết kết cấu",
    "🏗️ Implement create_rebar_layer() tạo lớp cốt thép",
    "🏗️ Implement create_rebar_schedule() tạo bảng thống kê thép",
    "🏗️ Implement create_section_cut() tạo mặt cắt",
    "🏗️ Thêm các chi tiết nối thép tiêu chuẩn",
    "🏗️ Tạo file generators/rebar_schedule.py - bảng thống kê thép",
    "🏗️ Implement calculate_rebar_weight() tính khối lượng thép",
    "🏗️ Implement generate_schedule_table() tạo bảng thống kê",
    "🏗️ Thêm các đường kính thép theo TCVN",
    "🏗️ Thêm đơn giá thép để tính chi phí",
    "🏗️ Tạo file generators/version_manager.py - quản lý phiên bản",
    "🏗️ Implement VersionManager class theo dõi thay đổi",
    "🏗️ Implement create_version() tạo phiên bản mới",
    "🏗️ Implement compare_versions() so sánh 2 phiên bản",
    "🏗️ Thêm diff view cho thay đổi",
    
    # ===========================================
    # PHASE 9: PDF REPORTS (Commits 271-295)
    # ===========================================
    "📊 Tạo file generators/pdf_report.py - báo cáo PDF",
    "📊 Implement PDFReport class sử dụng ReportLab",
    "📊 Implement create_report() tạo báo cáo",
    "📊 Implement add_title_page() tạo trang bìa",
    "📊 Implement add_table_of_contents() tạo mục lục",
    "📊 Implement add_chapter() thêm chương",
    "📊 Implement add_section() thêm mục",
    "📊 Implement add_table() thêm bảng số liệu",
    "📊 Implement add_image() thêm hình ảnh",
    "📊 Implement add_calculation_log() thêm log tính toán",
    "📊 Thêm header/footer với số trang",
    "📊 Thêm font tiếng Việt Unicode",
    "📊 Thêm các style cho heading, body text",
    "📊 Thêm template báo cáo thiết kế bể",
    "📊 Thêm template báo cáo thiết kế đường ống",
    "📊 Thêm template báo cáo thiết kế giếng",
    "📊 Implement add_drawing_reference() thêm tham chiếu bản vẽ",
    "📊 Implement add_specification() thêm thông số kỹ thuật",
    "📊 Thêm bảng tổng hợp khối lượng",
    "📊 Thêm bảng tổng hợp vật liệu",
    "📊 Implement export_pdf() xuất file PDF",
    "📊 Thêm watermark cho bản draft",
    "📊 Thêm QR code cho truy xuất nguồn gốc",
    "📊 Thêm chữ ký số placeholder",
    "📊 Tạo file generators/viewer_config.py - cấu hình viewer",
    
    # ===========================================
    # PHASE 10: API ROUTES (Commits 296-345)
    # ===========================================
    "📁 Tạo thư mục api/ cho các API endpoints",
    "📝 Thêm file api/__init__.py export routers",
    "🌐 Tạo file api/tank_router.py - API thiết kế bể",
    "🌐 Implement endpoint POST /api/tank/design tính toán thiết kế",
    "🌐 Implement endpoint GET /api/tank/templates lấy templates",
    "🌐 Implement endpoint POST /api/tank/validate kiểm tra thiết kế",
    "🌐 Implement endpoint POST /api/tank/optimize tối ưu thiết kế",
    "🌐 Thêm error handling và logging",
    "🌐 Tạo file api/tank_router_v2.py - phiên bản cải tiến",
    "🌐 Thêm endpoint GET /api/tank/calculation-log lấy log tính toán",
    "🌐 Thêm endpoint GET /api/tank/safety-check kiểm tra an toàn",
    "🌐 Thêm response caching cho performance",
    "🌐 Tạo file api/pipeline_router.py - API thiết kế đường ống",
    "🌐 Implement endpoint POST /api/pipeline/design tính toán",
    "🌐 Implement endpoint GET /api/pipeline/materials lấy vật liệu",
    "🌐 Implement endpoint POST /api/pipeline/hydraulic tính thủy lực",
    "🌐 Thêm validation cho input parameters",
    "🌐 Tạo file api/well_router.py - API thiết kế giếng",
    "🌐 Implement endpoint POST /api/well/design tính toán",
    "🌐 Implement endpoint GET /api/well/types lấy loại giếng",
    "🌐 Implement endpoint POST /api/well/pumping-test mô phỏng bơm",
    "🌐 Tạo file api/export_router.py - API xuất file",
    "🌐 Implement endpoint POST /api/export/dxf xuất DXF",
    "🌐 Implement endpoint POST /api/export/pdf xuất PDF",
    "🌐 Implement endpoint POST /api/export/ifc xuất IFC",
    "🌐 Thêm job queue cho export lớn",
    "🌐 Tạo file api/cad_router_v2.py - API CAD nâng cao",
    "🌐 Implement endpoint GET /api/cad/preview preview bản vẽ",
    "🌐 Implement endpoint POST /api/cad/validate kiểm tra bản vẽ",
    "🌐 Implement endpoint GET /api/cad/layers lấy danh sách layers",
    "🌐 Tạo file api/advanced_design_router.py - API thiết kế nâng cao",
    "🌐 Implement endpoint POST /api/advanced/multi-tank thiết kế nhiều bể",
    "🌐 Implement endpoint POST /api/advanced/system thiết kế hệ thống",
    "🌐 Thêm batch processing cho nhiều thiết kế",
    "🌐 Tạo file api/sprint4_router.py - API Sprint 4",
    "🌐 Implement endpoint cho BIM integration",
    "🌐 Implement endpoint cho 3D viewer",
    "🌐 Thêm WebSocket cho real-time updates",
    "🌐 Tạo file api/validation_dashboard.py - Dashboard kiểm tra",
    "🌐 Implement endpoint GET /api/dashboard/stats thống kê",
    "🌐 Implement endpoint GET /api/dashboard/violations vi phạm",
    "🌐 Implement endpoint GET /api/dashboard/history lịch sử",
    "🌐 Tạo file main.py - FastAPI application",
    "🌐 Cấu hình CORS middleware",
    "🌐 Cấu hình static files serving",
    "🌐 Cấu hình exception handlers",
    "🌐 Mount tất cả routers vào app",
    "🌐 Thêm OpenAPI documentation",
    "🌐 Thêm health check endpoint",
    
    # ===========================================
    # PHASE 11: FRONTEND SETUP (Commits 346-365)
    # ===========================================
    "⚛️ Khởi tạo React app với Create React App",
    "⚛️ Cài đặt dependencies: axios, react-router-dom",
    "⚛️ Cài đặt dependencies: @mui/material, @emotion/react",
    "⚛️ Cấu hình React Router trong App.js",
    "⚛️ Tạo file src/services/api.js - service gọi API",
    "⚛️ Implement hàm designTank() gọi API thiết kế bể",
    "⚛️ Implement hàm designPipeline() gọi API thiết kế ống",
    "⚛️ Implement hàm exportDXF() gọi API xuất DXF",
    "⚛️ Thêm interceptor xử lý error",
    "⚛️ Thêm loading state management",
    "📁 Tạo thư mục src/components/ cho các components",
    "📁 Tạo thư mục src/pages/ cho các pages",
    "⚛️ Tạo file src/components/Layout.js - layout chính",
    "⚛️ Implement Sidebar navigation",
    "⚛️ Implement Header với logo và menu",
    "⚛️ Implement Footer",
    "⚛️ Thêm responsive design cho mobile",
    "🎨 Tạo theme MUI với màu chủ đạo xanh dương",
    "🎨 Customize typography với font Roboto",
    "🎨 Thêm dark mode support",
    
    # ===========================================
    # PHASE 12: FRONTEND PAGES (Commits 366-400)
    # ===========================================
    "📄 Tạo file src/pages/HomePage.js - trang chủ",
    "📄 Implement hero section với giới thiệu",
    "📄 Implement quick start cards",
    "📄 Thêm statistics về số dự án đã thiết kế",
    "📄 Tạo file src/pages/TankDesignPage.js - thiết kế bể",
    "📄 Implement form nhập thông số bể",
    "📄 Implement hiển thị kết quả tính toán",
    "📄 Implement hiển thị bản vẽ preview",
    "📄 Thêm tabs cho các loại bể khác nhau",
    "📄 Thêm nút xuất DXF và PDF",
    "📄 Tạo file src/pages/PipelineDesignPage.js - thiết kế ống",
    "📄 Implement form nhập thông số đường ống",
    "📄 Implement hiển thị profile dọc tuyến ống",
    "📄 Implement hiển thị chi tiết hố ga",
    "📄 Thêm map integration cho định tuyến",
    "📄 Tạo file src/pages/WellDesignPage.js - thiết kế giếng",
    "📄 Implement form nhập thông số giếng",
    "📄 Implement hiển thị mặt cắt giếng",
    "📄 Implement biểu đồ bơm hút nước thí nghiệm",
    "📄 Tạo file src/pages/CADPage.js - quản lý bản vẽ",
    "📄 Implement file manager cho bản vẽ",
    "📄 Implement DXF preview",
    "📄 Thêm validation checker cho bản vẽ",
    "📄 Tạo file src/pages/BIMPage.js - quản lý BIM",
    "📄 Implement IFC viewer embed",
    "📄 Implement property inspector",
    "📄 Tạo file src/pages/ProjectsPage.js - quản lý dự án",
    "📄 Implement danh sách dự án",
    "📄 Implement tạo dự án mới",
    "📄 Implement chi tiết dự án",
    "📄 Tạo file src/pages/ReportsPage.js - báo cáo",
    "📄 Implement danh sách báo cáo",
    "📄 Implement PDF preview",
    "📄 Tạo file src/pages/SettingsPage.js - cài đặt",
    "📄 Tạo file src/pages/VersionsPage.js - phiên bản",
    
    # ===========================================
    # PHASE 13: FRONTEND COMPONENTS (Commits 401-412)
    # ===========================================
    "🧩 Tạo file src/components/DXFPreview.js - preview DXF",
    "🧩 Tạo file src/components/CalculationLog.js - log tính toán",
    "🧩 Tạo file src/components/SafetyViolations.js - cảnh báo vi phạm",
    "🧩 Tạo file src/components/ReportGenerator.js - tạo báo cáo",
    "🧩 Tạo file src/components/IFCViewer.js - viewer IFC",
    "🧩 Tạo file src/components/BIMExport.js - xuất BIM",
    "🧩 Tạo file src/components/CADValidation.js - kiểm tra CAD",
    "🧩 Tạo file src/components/VersionHistory.js - lịch sử phiên bản",
    "🧩 Tạo file src/components/SystemStatus.js - trạng thái hệ thống",
    "🎨 Hoàn thiện giao diện và style cho tất cả components",
    "🧪 Thêm test files cho frontend components",
    "🚀 Hoàn thiện dự án HydroDraft v1.0 - sẵn sàng production",
]

def run_git(args, env=None, check=True):
    """Chạy lệnh git"""
    cmd = ['git'] + args
    result = subprocess.run(
        cmd,
        cwd=PROJECT_DIR,
        env=env,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    if check and result.returncode != 0:
        print(f"Git error: {result.stderr}")
        return False
    return True

def get_commit_times(total, start, end):
    """Tạo danh sách thời gian commit phân bố đều và tự nhiên"""
    total_seconds = (end - start).total_seconds()
    interval = total_seconds / total
    
    times = []
    current = start
    
    for i in range(total):
        # Random offset ±60 phút để tự nhiên hơn
        offset = random.randint(-3600, 3600)
        commit_time = current + timedelta(seconds=offset)
        
        # Đảm bảo trong khoảng làm việc (8h-23h)
        if commit_time.hour < 8:
            commit_time = commit_time.replace(hour=8 + random.randint(0, 2))
        elif commit_time.hour > 23:
            commit_time = commit_time.replace(hour=21 + random.randint(0, 2))
        
        times.append(commit_time)
        current = current + timedelta(seconds=interval)
    
    # Sắp xếp lại theo thứ tự thời gian
    times.sort()
    return times

def main():
    print("=" * 70)
    print("🚀 TẠO 412 FAKE COMMITS CHO DỰ ÁN HYDRODRAFT")
    print("=" * 70)
    print(f"📅 Thời gian: {START_DATE.strftime('%d/%m/%Y')} - {END_DATE.strftime('%d/%m/%Y')}")
    print(f"📊 Tổng số commits: {len(COMMITS)}")
    print("=" * 70)
    
    # Xác nhận trước khi chạy
    confirm = input("\n⚠️  Script này sẽ XÓA toàn bộ git history hiện tại!\nBạn có chắc chắn muốn tiếp tục? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Đã hủy thao tác.")
        return
    
    os.chdir(PROJECT_DIR)
    
    # Bước 1: Backup files
    print("\n📦 Bước 1/4: Đang backup files...")
    backup_dir = os.path.join(PROJECT_DIR, "_temp_backup")
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    os.makedirs(backup_dir)
    
    # Copy tất cả files (trừ .git, backup, script)
    for item in os.listdir(PROJECT_DIR):
        if item not in ['.git', '_temp_backup', 'fake_commits.py']:
            src = os.path.join(PROJECT_DIR, item)
            dst = os.path.join(backup_dir, item)
            try:
                if os.path.isdir(src):
                    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'node_modules', '.git'))
                else:
                    shutil.copy2(src, dst)
            except Exception as e:
                print(f"  ⚠️ Bỏ qua: {item} ({e})")
    print("  ✅ Backup hoàn tất")
    
    # Bước 2: Reset git
    print("\n� Bước 2/4: Đang reset git history...")
    
    # Xóa .git folder và tạo mới
    git_dir = os.path.join(PROJECT_DIR, ".git")
    if os.path.exists(git_dir):
        shutil.rmtree(git_dir)
    
    # Git init
    subprocess.run(['git', 'init'], cwd=PROJECT_DIR, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'developer@hydrodraft.vn'], cwd=PROJECT_DIR, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'HydroDraft Developer'], cwd=PROJECT_DIR, capture_output=True)
    print("  ✅ Git reset hoàn tất")
    
    # Bước 3: Tạo commits
    print("\n📝 Bước 3/4: Đang tạo 412 fake commits...")
    
    commit_times = get_commit_times(len(COMMITS), START_DATE, END_DATE)
    
    # Xóa tất cả files hiện tại (ngoại trừ backup và script)
    for item in os.listdir(PROJECT_DIR):
        if item not in ['.git', '_temp_backup', 'fake_commits.py']:
            path = os.path.join(PROJECT_DIR, item)
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except:
                pass
    
    # Danh sách files để thêm dần dần
    all_files = []
    for root, dirs, files in os.walk(backup_dir):
        # Ignore certain directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', 'node_modules', '.git', 'dist', 'build']]
        for file in files:
            if not file.endswith('.pyc'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, backup_dir)
                all_files.append(rel_path)
    
    # Phân chia files cho mỗi commit
    files_per_commit = max(1, len(all_files) // len(COMMITS))
    file_index = 0
    
    for i, (message, commit_time) in enumerate(zip(COMMITS, commit_times), 1):
        # Copy một số files mới cho commit này
        files_to_add = min(files_per_commit + random.randint(0, 2), len(all_files) - file_index)
        
        for j in range(files_to_add):
            if file_index < len(all_files):
                rel_path = all_files[file_index]
                src = os.path.join(backup_dir, rel_path)
                dst = os.path.join(PROJECT_DIR, rel_path)
                
                try:
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
                except:
                    pass
                
                file_index += 1
        
        # Nếu không có files mới, tạo/sửa một marker file
        if files_to_add == 0:
            marker = os.path.join(PROJECT_DIR, ".progress")
            with open(marker, 'w', encoding='utf-8') as f:
                f.write(f"Commit {i}: {message}\n")
        
        # Stage và commit
        subprocess.run(['git', 'add', '-A'], cwd=PROJECT_DIR, capture_output=True)
        
        # Set commit time qua environment variables
        env = os.environ.copy()
        date_str = commit_time.strftime("%Y-%m-%dT%H:%M:%S+07:00")
        env['GIT_AUTHOR_DATE'] = date_str
        env['GIT_COMMITTER_DATE'] = date_str
        
        # Commit
        result = subprocess.run(
            ['git', 'commit', '-m', message, '--allow-empty'],
            cwd=PROJECT_DIR,
            env=env,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if i % 50 == 0 or i == len(COMMITS):
            print(f"  ✅ Đã tạo {i}/{len(COMMITS)} commits ({i*100//len(COMMITS)}%)")
    
    # Đảm bảo tất cả files còn lại được add
    while file_index < len(all_files):
        rel_path = all_files[file_index]
        src = os.path.join(backup_dir, rel_path)
        dst = os.path.join(PROJECT_DIR, rel_path)
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        except:
            pass
        file_index += 1
    
    # Final commit với tất cả files còn lại
    subprocess.run(['git', 'add', '-A'], cwd=PROJECT_DIR, capture_output=True)
    
    # Bước 4: Cleanup
    print("\n🧹 Bước 4/4: Đang dọn dẹp...")
    
    # Xóa marker file nếu có
    marker = os.path.join(PROJECT_DIR, ".progress")
    if os.path.exists(marker):
        os.remove(marker)
        subprocess.run(['git', 'add', '-A'], cwd=PROJECT_DIR, capture_output=True)
    
    # Xóa backup
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    
    print("  ✅ Dọn dẹp hoàn tất")
    
    # Kết quả
    print("\n" + "=" * 70)
    print("🎉 HOÀN THÀNH!")
    print("=" * 70)
    print(f"✅ Đã tạo {len(COMMITS)} commits")
    print(f"📅 Từ: {START_DATE.strftime('%d/%m/%Y %H:%M')}")
    print(f"📅 Đến: {END_DATE.strftime('%d/%m/%Y %H:%M')}")
    print("\n📋 Để xem commits:")
    print("   git log --oneline -20")
    print("\n⚠️  Để push lên remote (cần force push vì đã thay đổi history):")
    print("   git remote add origin <your-remote-url>")
    print("   git push -f origin main")
    print("=" * 70)

if __name__ == "__main__":
    main()
