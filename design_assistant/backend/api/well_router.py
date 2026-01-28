"""
API Router - Well Design Endpoints

Các endpoint thiết kế giếng:
- POST /design/well - Thiết kế giếng quan trắc
- GET /design/well/templates - Mẫu thiết kế giếng
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

from models.schemas import WellInput, WellType
from templates.manager import TemplateManager
from generators.dxf_generator import DXFGenerator

router = APIRouter(prefix="/design/well", tags=["Well Design"])

# Khởi tạo services
template_manager = TemplateManager()


class WellMaterial(str, Enum):
    """Vật liệu ống giếng"""
    PVC = "PVC"
    HDPE = "HDPE"
    STAINLESS = "Stainless_steel"


class WellDesignRequest(BaseModel):
    """Request model cho thiết kế giếng"""
    
    # Thông tin cơ bản
    project_name: str = Field(..., description="Tên dự án")
    well_name: str = Field(..., description="Tên/ký hiệu giếng")
    well_type: WellType = Field(..., description="Loại giếng")
    
    # Vị trí
    x_coordinate: float = Field(..., description="Tọa độ X (m)")
    y_coordinate: float = Field(..., description="Tọa độ Y (m)")
    ground_level: float = Field(..., description="Cao độ mặt đất (m)")
    
    # Thông số thiết kế
    total_depth: float = Field(..., gt=0, description="Tổng chiều sâu (m)")
    casing_diameter: float = Field(110, gt=0, description="Đường kính ống chống (mm)")
    casing_material: WellMaterial = Field(WellMaterial.PVC, description="Vật liệu ống")
    
    # Ống lọc
    screen_top: Optional[float] = Field(None, description="Đỉnh ống lọc (m dưới mặt đất)")
    screen_bottom: Optional[float] = Field(None, description="Đáy ống lọc (m dưới mặt đất)")
    screen_slot_size: float = Field(0.5, description="Kích thước khe (mm)")
    
    # Lớp địa chất (tùy chọn)
    geology: Optional[List[dict]] = Field(None, description="Cột địa tầng")
    
    # Output
    generate_drawing: bool = Field(True, description="Tạo bản vẽ CAD")


class WellDesignResponse(BaseModel):
    """Response model cho thiết kế giếng"""
    
    job_id: str
    status: str
    
    # Thông số thiết kế
    design: dict
    
    # Cấu trúc giếng
    structure: dict
    
    # Vật liệu
    materials: dict
    
    # Quy trình thi công
    construction_steps: List[str]
    
    # Validation
    validation: dict
    
    # Files
    drawing_file: Optional[str] = None


@router.post("/", response_model=WellDesignResponse)
async def design_well(
    request: WellDesignRequest,
    background_tasks: BackgroundTasks
):
    """
    Thiết kế giếng quan trắc
    
    Quy trình:
    1. Validate input
    2. Thiết kế cấu trúc giếng
    3. Chọn vật liệu
    4. Lập quy trình thi công
    5. Tạo bản vẽ
    """
    import uuid
    
    job_id = str(uuid.uuid4())[:8]
    
    try:
        # 1. Tính toán các thông số
        screen_length = 0
        if request.screen_top and request.screen_bottom:
            screen_length = request.screen_bottom - request.screen_top
        else:
            # Mặc định: 30% chiều sâu là ống lọc
            screen_length = request.total_depth * 0.3
            request.screen_bottom = request.total_depth
            request.screen_top = request.total_depth - screen_length
        
        # Đường kính lỗ khoan
        borehole_diameter = request.casing_diameter + 100  # +100mm cho sỏi lọc
        
        # 2. Cấu trúc giếng
        structure = {
            "protective_casing": {
                "depth_above_ground": 0.5,
                "depth_below_ground": 0.3,
                "diameter": request.casing_diameter + 50
            },
            "casing": {
                "depth_from": 0,
                "depth_to": request.screen_top,
                "diameter": request.casing_diameter,
                "material": request.casing_material.value
            },
            "screen": {
                "depth_from": request.screen_top,
                "depth_to": request.screen_bottom,
                "length": screen_length,
                "diameter": request.casing_diameter,
                "slot_size": request.screen_slot_size
            },
            "gravel_pack": {
                "depth_from": request.screen_top - 1.0,
                "depth_to": request.total_depth,
                "thickness": (borehole_diameter - request.casing_diameter) / 2,
                "grain_size": f"{request.screen_slot_size * 4}-{request.screen_slot_size * 6} mm"
            },
            "bentonite_seal": {
                "depth_from": request.screen_top - 2.0,
                "depth_to": request.screen_top - 1.0,
                "thickness": 1.0
            },
            "grout_seal": {
                "depth_from": 0.3,
                "depth_to": request.screen_top - 2.0
            },
            "bottom_cap": {
                "depth": request.total_depth
            }
        }
        
        # 3. Vật liệu
        materials = {
            "casing": {
                "material": request.casing_material.value,
                "diameter": request.casing_diameter,
                "length": round(request.total_depth + 0.5, 1),  # +0.5 cho phần trên mặt đất
                "unit": "m"
            },
            "screen": {
                "material": request.casing_material.value,
                "diameter": request.casing_diameter,
                "length": round(screen_length, 1),
                "slot_size": request.screen_slot_size,
                "unit": "m"
            },
            "gravel": {
                "volume": round(
                    3.14159 * ((borehole_diameter/1000)**2 - (request.casing_diameter/1000)**2) / 4 
                    * (screen_length + 1) * 1.2,  # +1m đệm, *1.2 hệ số dư
                    2
                ),
                "unit": "m³"
            },
            "bentonite": {
                "quantity": round(
                    3.14159 * (borehole_diameter/1000)**2 / 4 * 1.0 * 50,  # 50 kg/m³
                    1
                ),
                "unit": "kg"
            },
            "cement": {
                "quantity": round(
                    3.14159 * ((borehole_diameter/1000)**2 - (request.casing_diameter/1000)**2) / 4 
                    * (request.screen_top - 2.3) * 400,  # 400 kg/m³
                    1
                ),
                "unit": "kg"
            }
        }
        
        # 4. Quy trình thi công
        construction_steps = [
            f"1. Khoan tạo lỗ đường kính {borehole_diameter}mm đến độ sâu {request.total_depth}m",
            "2. Làm sạch lỗ khoan bằng phương pháp bơm rửa tuần hoàn",
            f"3. Hạ ống chống và ống lọc {request.casing_material.value} Ø{request.casing_diameter}mm",
            "4. Đổ sỏi lọc từ đáy đến cao độ trên đỉnh ống lọc 1m",
            "5. Đặt nút bentonite dày 1m trên lớp sỏi",
            "6. Trám vữa xi măng-bentonite từ dưới lên bằng ống tremie",
            "7. Phát triển giếng bằng phương pháp bơm khí nén/bơm hút xả",
            "8. Lắp đặt ống bảo vệ và nắp khóa",
            "9. Đo mực nước tĩnh và lấy mẫu nước ban đầu"
        ]
        
        # 5. Validation
        validation = {"valid": True, "errors": [], "warnings": []}
        
        # Kiểm tra tỷ lệ chiều dài ống lọc
        screen_ratio = screen_length / request.total_depth
        if screen_ratio < 0.2:
            validation["warnings"].append(
                f"Tỷ lệ ống lọc {screen_ratio:.0%} < 20% có thể không đủ"
            )
        if screen_ratio > 0.5:
            validation["warnings"].append(
                f"Tỷ lệ ống lọc {screen_ratio:.0%} > 50% có thể gây xâm nhập nước tầng khác"
            )
        
        # Kiểm tra chiều sâu
        if request.total_depth > 100 and request.casing_material == WellMaterial.PVC:
            validation["warnings"].append(
                "Ống PVC không khuyến nghị cho giếng sâu > 100m"
            )
        
        # 6. Tạo bản vẽ
        drawing_file = None
        if request.generate_drawing:
            dxf_gen = DXFGenerator(output_dir=f"./outputs/{job_id}")
            
            # Vẽ mặt cắt giếng
            dxf_gen.draw_well_section(
                total_depth=request.total_depth,
                casing_diameter=request.casing_diameter,
                borehole_diameter=borehole_diameter,
                screen_top=request.screen_top,
                screen_bottom=request.screen_bottom,
                grout_depth=structure["grout_seal"]["depth_to"],
                bentonite_top=structure["bentonite_seal"]["depth_from"],
                bentonite_bottom=structure["bentonite_seal"]["depth_to"],
                gravel_top=structure["gravel_pack"]["depth_from"],
                ground_level=request.ground_level,
                protective_height=structure["protective_casing"]["depth_above_ground"],
                geology=request.geology,
                origin=(0, 0),
                scale=10.0  # Tỷ lệ 1:100
            )
            
            # Vẽ mặt bằng giếng
            dxf_gen.draw_well_plan(
                casing_diameter=request.casing_diameter,
                borehole_diameter=borehole_diameter,
                protective_diameter=structure["protective_casing"]["diameter"],
                origin=(5, 0),  # Đặt cạnh mặt cắt
                scale=10.0
            )
            
            dxf_gen.add_title_block(
                project_name=request.project_name,
                drawing_title=f"GIẾNG QUAN TRẮC {request.well_name}",
                scale="1:100",
                drawn_by="HydroDraft"
            )
            
            drawing_file = dxf_gen.save(f"well_{request.well_name}")
        
        # 7. Response
        return WellDesignResponse(
            job_id=job_id,
            status="completed" if validation["valid"] else "warning",
            design={
                "well_type": request.well_type.value,
                "total_depth": request.total_depth,
                "casing_diameter": request.casing_diameter,
                "borehole_diameter": borehole_diameter,
                "screen_length": round(screen_length, 1),
                "coordinates": {
                    "x": request.x_coordinate,
                    "y": request.y_coordinate,
                    "ground_level": request.ground_level
                }
            },
            structure=structure,
            materials=materials,
            construction_steps=construction_steps,
            validation=validation,
            drawing_file=drawing_file
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi thiết kế: {str(e)}")


@router.get("/templates")
async def get_well_template():
    """Lấy template giếng quan trắc"""
    template = template_manager.get_template("WELL_MON_001")
    if not template:
        raise HTTPException(status_code=404, detail="Template không tồn tại")
    return template


@router.get("/standard-diameters")
async def get_standard_casing_diameters():
    """Lấy đường kính ống chống tiêu chuẩn"""
    return {
        "diameters": [50, 60, 75, 90, 110, 125, 160, 200],
        "unit": "mm",
        "recommended": {
            "shallow": 50,
            "medium": 110,
            "deep": 160
        }
    }


@router.get("/materials")
async def get_casing_materials():
    """Lấy thông tin vật liệu ống giếng"""
    return {
        "materials": [
            {
                "code": "PVC",
                "name": "PVC-U",
                "max_depth": 100,
                "advantages": ["Giá rẻ", "Dễ thi công", "Không gỉ"],
                "disadvantages": ["Dễ vỡ", "Không chịu nhiệt"]
            },
            {
                "code": "HDPE",
                "name": "HDPE",
                "max_depth": 150,
                "advantages": ["Dẻo dai", "Chống ăn mòn", "Nhẹ"],
                "disadvantages": ["Cần thiết bị hàn nhiệt"]
            },
            {
                "code": "Stainless_steel",
                "name": "Thép không gỉ",
                "max_depth": 300,
                "advantages": ["Bền", "Chịu áp tốt", "Tuổi thọ cao"],
                "disadvantages": ["Giá cao", "Nặng"]
            }
        ]
    }
