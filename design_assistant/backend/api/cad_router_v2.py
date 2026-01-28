"""
CAD Router V2 - API endpoints cho Professional CAD

SPRINT 3: PROFESSIONAL CAD
Endpoints:
- POST /api/v1/cad/v2/tank - Vẽ bể chuyên nghiệp
- POST /api/v1/cad/v2/validate - Validate bản vẽ
- GET /api/v1/cad/v2/blocks - Danh sách blocks
- GET /api/v1/cad/v2/layers - Danh sách layers chuẩn
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import uuid
import traceback

from generators import (
    ProfessionalDXFGenerator,
    DrawingMetadata,
    TankDrawingParams,
    DrawingScale,
    CADStandards,
    CADBlockLibrary,
    BlockType,
    ValidationResult,
    create_professional_generator
)


router = APIRouter(prefix="/api/v1/cad/v2", tags=["CAD V2 - Professional"])


# ==========================================
# SCHEMAS
# ==========================================

class TankDrawingRequest(BaseModel):
    """Request vẽ bể"""
    # Project info
    project_name: str = Field(..., description="Tên dự án")
    drawing_title: str = Field(default="MẶT BẰNG VÀ MẶT CẮT BỂ", description="Tiêu đề bản vẽ")
    drawing_number: str = Field(default="TD-01", description="Số hiệu bản vẽ")
    drawn_by: str = Field(default="HydroDraft", description="Người vẽ")
    scale: str = Field(default="1:100", description="Tỷ lệ (1:50, 1:100, 1:200)")
    
    # Tank dimensions (m)
    length: float = Field(..., gt=0, description="Chiều dài trong (m)")
    width: float = Field(..., gt=0, description="Chiều rộng trong (m)")
    water_depth: float = Field(..., gt=0, description="Chiều sâu nước (m)")
    total_depth: float = Field(..., gt=0, description="Tổng chiều sâu (m)")
    wall_thickness: float = Field(default=0.3, gt=0, description="Chiều dày thành (m)")
    bottom_thickness: float = Field(default=0.3, gt=0, description="Chiều dày đáy (m)")
    freeboard: float = Field(default=0.3, gt=0, description="Chiều cao an toàn (m)")
    
    # Pipes (mm)
    inlet_diameter: int = Field(default=200, description="Đường kính ống vào (mm)")
    outlet_diameter: int = Field(default=200, description="Đường kính ống ra (mm)")
    
    # Reinforcement
    main_rebar_dia: int = Field(default=12, description="Đường kính thép chính (mm)")
    main_rebar_spacing: int = Field(default=200, description="Khoảng cách thép chính (mm)")
    dist_rebar_dia: int = Field(default=10, description="Đường kính thép phân bố (mm)")
    dist_rebar_spacing: int = Field(default=250, description="Khoảng cách thép phân bố (mm)")
    cover: float = Field(default=0.03, description="Lớp bảo vệ (m)")
    
    # Levels
    ground_level: float = Field(default=0.0, description="Cao độ mặt đất (m)")
    
    # Options
    include_plan: bool = Field(default=True, description="Bao gồm mặt bằng")
    include_section: bool = Field(default=True, description="Bao gồm mặt cắt")
    include_rebar: bool = Field(default=True, description="Bao gồm chi tiết thép")


class TankDrawingResponse(BaseModel):
    """Response vẽ bể"""
    success: bool
    job_id: str
    file_path: str
    file_name: str
    validation: Dict[str, Any]
    download_url: str
    message: str


class ValidationRequest(BaseModel):
    """Request validate"""
    file_path: str
    drawing_type: str = Field(default="general", description="tank|pipe|well|general")


class ValidationResponse(BaseModel):
    """Response validation"""
    is_valid: bool
    can_export: bool
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues_by_category: Dict[str, int]
    issues: List[Dict[str, Any]]


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def parse_scale(scale_str: str) -> DrawingScale:
    """Parse string tỷ lệ sang DrawingScale"""
    scale_map = {
        "1:1": DrawingScale.SCALE_1_1,
        "1:2": DrawingScale.SCALE_1_2,
        "1:5": DrawingScale.SCALE_1_5,
        "1:10": DrawingScale.SCALE_1_10,
        "1:20": DrawingScale.SCALE_1_20,
        "1:25": DrawingScale.SCALE_1_25,
        "1:50": DrawingScale.SCALE_1_50,
        "1:100": DrawingScale.SCALE_1_100,
        "1:200": DrawingScale.SCALE_1_200,
        "1:250": DrawingScale.SCALE_1_250,
        "1:500": DrawingScale.SCALE_1_500,
        "1:1000": DrawingScale.SCALE_1_1000,
    }
    return scale_map.get(scale_str, DrawingScale.SCALE_1_100)


# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/tank", response_model=TankDrawingResponse)
async def create_tank_drawing(request: TankDrawingRequest):
    """
    Tạo bản vẽ bể chuyên nghiệp
    
    Features:
    - Professional layers & styles (TCVN)
    - Block-based symbols (valves, etc.)
    - Reinforcement detailing
    - Proper dimensions & annotations
    - Validation report
    """
    try:
        job_id = str(uuid.uuid4())[:8]
        output_dir = f"./outputs/{job_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Create generator
        generator = create_professional_generator(output_dir)
        
        # Prepare metadata
        metadata = DrawingMetadata(
            project_name=request.project_name,
            drawing_title=request.drawing_title,
            drawing_number=request.drawing_number,
            scale=parse_scale(request.scale),
            drawn_by=request.drawn_by
        )
        
        # Prepare params
        params = TankDrawingParams(
            length=request.length,
            width=request.width,
            water_depth=request.water_depth,
            total_depth=request.total_depth,
            wall_thickness=request.wall_thickness,
            bottom_thickness=request.bottom_thickness,
            freeboard=request.freeboard,
            inlet_diameter=request.inlet_diameter,
            outlet_diameter=request.outlet_diameter,
            main_rebar_dia=request.main_rebar_dia,
            main_rebar_spacing=request.main_rebar_spacing,
            dist_rebar_dia=request.dist_rebar_dia,
            dist_rebar_spacing=request.dist_rebar_spacing,
            cover=request.cover,
            ground_level=request.ground_level
        )
        
        # Generate drawing
        file_path = generator.draw_tank_complete(
            params=params,
            metadata=metadata,
            include_plan=request.include_plan,
            include_section=request.include_section,
            include_rebar=request.include_rebar
        )
        
        # Get validation result
        validation_result = generator.validate_current_drawing("tank")
        
        file_name = os.path.basename(file_path)
        
        return TankDrawingResponse(
            success=True,
            job_id=job_id,
            file_path=file_path,
            file_name=file_name,
            validation=validation_result.to_dict(),
            download_url=f"/api/v1/cad/v2/download/{job_id}/{file_name}",
            message="Bản vẽ đã được tạo thành công"
        )
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{job_id}/{filename}")
async def download_drawing(job_id: str, filename: str):
    """Download bản vẽ DXF"""
    file_path = f"./outputs/{job_id}/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="application/dxf",
        filename=filename
    )


@router.post("/validate", response_model=ValidationResponse)
async def validate_drawing_endpoint(request: ValidationRequest):
    """
    Validate bản vẽ DXF
    
    Kiểm tra:
    - Missing dimensions
    - Missing annotations
    - Layer standards
    - Scale consistency
    - Block completeness
    """
    try:
        import ezdxf
        from generators.cad_validation import validate_drawing
        
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        doc = ezdxf.readfile(request.file_path)
        result = validate_drawing(doc, request.drawing_type)
        
        return ValidationResponse(
            is_valid=result.is_valid,
            can_export=result.can_export,
            total_issues=result.total_issues,
            issues_by_severity=result.issues_by_severity,
            issues_by_category=result.issues_by_category,
            issues=[i.to_dict() for i in result.issues]
        )
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blocks")
async def list_available_blocks():
    """
    Liệt kê các block có sẵn
    
    Categories:
    - Valves
    - Manholes
    - Pumps
    - Instruments
    - Structural
    - Annotation
    """
    blocks = {
        "valves": [
            {"name": "VALVE_GATE", "description": "Van cổng (Gate Valve)"},
            {"name": "VALVE_CHECK", "description": "Van một chiều (Check Valve)"},
            {"name": "VALVE_BUTTERFLY", "description": "Van bướm (Butterfly Valve)"},
            {"name": "VALVE_BALL", "description": "Van bi (Ball Valve)"},
            {"name": "VALVE_CONTROL", "description": "Van điều khiển (Control Valve)"},
            {"name": "VALVE_RELIEF", "description": "Van xả áp (Relief Valve)"},
        ],
        "manholes": [
            {"name": "MH_CIRCULAR", "description": "Giếng thăm tròn"},
            {"name": "MH_RECT", "description": "Giếng thăm chữ nhật"},
            {"name": "MH_DROP", "description": "Giếng thăm có bậc"},
        ],
        "pumps": [
            {"name": "PUMP_CENTRI", "description": "Bơm ly tâm"},
            {"name": "PUMP_SUBM", "description": "Bơm chìm"},
        ],
        "instruments": [
            {"name": "FLOWMETER", "description": "Đồng hồ đo lưu lượng"},
            {"name": "LEVEL_GAUGE", "description": "Đo mực nước"},
            {"name": "PRESSURE_GAUGE", "description": "Đồng hồ áp suất"},
        ],
        "structural": [
            {"name": "REBAR_SECTION", "description": "Mặt cắt cốt thép"},
            {"name": "REBAR_STIRRUP", "description": "Đai/Thép đai"},
            {"name": "WATERSTOP_PVC", "description": "Waterstop PVC"},
            {"name": "WATERSTOP_RUBBER", "description": "Waterstop cao su"},
        ],
        "annotation": [
            {"name": "ELEVATION_MARK", "description": "Ký hiệu cao độ"},
            {"name": "GRID_AXIS", "description": "Ký hiệu trục"},
            {"name": "SECTION_MARK", "description": "Ký hiệu mặt cắt"},
            {"name": "NORTH_ARROW", "description": "Mũi tên hướng Bắc"},
        ]
    }
    
    return {"blocks": blocks, "total": sum(len(v) for v in blocks.values())}


@router.get("/layers")
async def list_standard_layers():
    """
    Liệt kê các layer tiêu chuẩn (TCVN)
    """
    layers = {
        "structural": [
            {"name": "STR_WALL", "color": 3, "description": "Tường/Thành"},
            {"name": "STR_FOUNDATION", "color": 2, "description": "Móng"},
            {"name": "STR_SLAB", "color": 4, "description": "Sàn/Bản"},
            {"name": "STR_COLUMN", "color": 3, "description": "Cột"},
            {"name": "STR_REBAR", "color": 1, "description": "Cốt thép"},
        ],
        "pipe": [
            {"name": "PIPE_MAIN", "color": 1, "description": "Ống chính"},
            {"name": "PIPE_BRANCH", "color": 6, "description": "Ống nhánh"},
            {"name": "PIPE_GRAVITY", "color": 5, "description": "Ống tự chảy"},
            {"name": "PIPE_PRESSURE", "color": 1, "description": "Ống áp lực"},
        ],
        "equipment": [
            {"name": "EQUIP_VALVE", "color": 1, "description": "Van"},
            {"name": "EQUIP_PUMP", "color": 3, "description": "Bơm"},
            {"name": "EQUIP_INST", "color": 6, "description": "Thiết bị đo"},
        ],
        "annotation": [
            {"name": "ANNO_DIM", "color": 7, "description": "Kích thước"},
            {"name": "ANNO_TEXT", "color": 7, "description": "Văn bản"},
            {"name": "ANNO_LEADER", "color": 7, "description": "Leader"},
            {"name": "ANNO_GRID", "color": 8, "description": "Lưới trục"},
        ],
        "hatch": [
            {"name": "HATCH_CONCRETE", "color": 8, "description": "Bê tông"},
            {"name": "HATCH_SOIL", "color": 33, "description": "Đất"},
            {"name": "HATCH_WATER", "color": 5, "description": "Nước"},
        ]
    }
    
    return {"layers": layers, "standard": "TCVN 8-1:2002"}


@router.get("/dimstyles")
async def list_dimension_styles():
    """
    Liệt kê các DimStyle theo tỷ lệ
    """
    dimstyles = [
        {"name": "DIM_1_1", "scale": "1:1", "text_height": 2.5},
        {"name": "DIM_1_10", "scale": "1:10", "text_height": 2.5},
        {"name": "DIM_1_20", "scale": "1:20", "text_height": 2.5},
        {"name": "DIM_1_25", "scale": "1:25", "text_height": 2.5},
        {"name": "DIM_1_50", "scale": "1:50", "text_height": 2.5},
        {"name": "DIM_1_100", "scale": "1:100", "text_height": 2.5},
        {"name": "DIM_1_200", "scale": "1:200", "text_height": 2.5},
        {"name": "DIM_1_500", "scale": "1:500", "text_height": 2.5},
        {"name": "DIM_ELEVATION", "description": "Cao độ", "prefix": "±"},
        {"name": "DIM_REBAR", "description": "Cốt thép", "prefix": "Ø"},
        {"name": "DIM_DIAMETER", "description": "Đường kính ống", "prefix": "DN"},
    ]
    
    return {"dimstyles": dimstyles, "standard": "ISO 129"}


@router.get("/scales")
async def list_drawing_scales():
    """
    Liệt kê các tỷ lệ bản vẽ tiêu chuẩn
    """
    scales = [
        {"value": "1:1", "usage": "Chi tiết"},
        {"value": "1:2", "usage": "Chi tiết lớn"},
        {"value": "1:5", "usage": "Chi tiết"},
        {"value": "1:10", "usage": "Chi tiết, mặt cắt"},
        {"value": "1:20", "usage": "Mặt cắt kết cấu"},
        {"value": "1:25", "usage": "Mặt cắt"},
        {"value": "1:50", "usage": "Mặt bằng, mặt cắt"},
        {"value": "1:100", "usage": "Mặt bằng chung"},
        {"value": "1:200", "usage": "Mặt bằng tổng thể"},
        {"value": "1:250", "usage": "Mặt bằng tổng thể"},
        {"value": "1:500", "usage": "Quy hoạch"},
        {"value": "1:1000", "usage": "Bình đồ"},
    ]
    
    return {"scales": scales, "recommended": ["1:50", "1:100", "1:200"]}
