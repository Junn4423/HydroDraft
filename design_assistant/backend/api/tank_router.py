"""
API Router - Tank Design Endpoints

Các endpoint thiết kế bể:
- POST /design/tank - Thiết kế bể mới
- GET /design/tank/{job_id} - Lấy kết quả thiết kế
- POST /design/tank/calculate - Chỉ tính toán (không lưu)
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
from pydantic import BaseModel, Field

from models.schemas import TankType
from calculations.tank_design import TankDesignCalculator
from rules.tank_rules import TankRules
from generators.dxf_generator import DXFGenerator
from templates.manager import TemplateManager

router = APIRouter(prefix="/design/tank", tags=["Tank Design"])

# Khởi tạo các services
tank_calculator = TankDesignCalculator()
tank_rules = TankRules()
template_manager = TemplateManager()


class TankDesignRequest(BaseModel):
    """Request model cho thiết kế bể"""
    
    # Thông tin cơ bản
    project_name: str = Field(..., description="Tên dự án")
    tank_name: str = Field(..., description="Tên/ký hiệu bể")
    tank_type: TankType = Field(..., description="Loại bể")
    
    # Thông số thiết kế
    flow_rate: float = Field(..., gt=0, description="Lưu lượng thiết kế (m³/ngày)")
    detention_time: Optional[float] = Field(None, ge=0.5, description="Thời gian lưu (giờ)")
    surface_loading_rate: Optional[float] = Field(None, gt=0, description="Tải trọng bề mặt (m³/m².ngày)")
    
    # Kích thước (tùy chọn - nếu đã biết)
    length: Optional[float] = Field(None, gt=0, description="Chiều dài (m)")
    width: Optional[float] = Field(None, gt=0, description="Chiều rộng (m)")
    depth: Optional[float] = Field(None, gt=0, description="Chiều sâu (m)")
    
    # Tùy chọn cấu hình
    number_of_tanks: int = Field(2, ge=1, le=8, description="Số bể")
    length_width_ratio: float = Field(3.0, ge=1.5, le=5.0, description="Tỷ lệ L/W")
    
    # Thông số kết cấu
    wall_thickness: Optional[float] = Field(None, description="Chiều dày thành (m)")
    bottom_thickness: Optional[float] = Field(None, description="Chiều dày đáy (m)")
    concrete_grade: str = Field("B25", description="Mác bê tông")
    
    # Template
    template_id: Optional[str] = Field(None, description="ID template để sử dụng")
    
    # Output options
    generate_drawing: bool = Field(True, description="Tạo bản vẽ CAD")
    generate_report: bool = Field(True, description="Tạo báo cáo")


class TankDesignResponse(BaseModel):
    """Response model cho thiết kế bể"""
    
    job_id: str
    status: str
    
    # Kết quả tính toán
    dimensions: dict
    hydraulic_results: dict
    structural_results: Optional[dict] = None
    
    # Validation
    validation: dict
    warnings: list
    
    # Files
    drawing_file: Optional[str] = None
    report_file: Optional[str] = None
    
    # Khối lượng
    quantities: Optional[dict] = None


@router.post("/", response_model=TankDesignResponse)
async def design_tank(
    request: TankDesignRequest,
    background_tasks: BackgroundTasks
):
    """
    Thiết kế bể xử lý
    
    Quy trình:
    1. Validate input
    2. Áp dụng rules
    3. Tính toán thủy lực
    4. Tính toán kết cấu
    5. Tạo bản vẽ
    6. Xuất báo cáo
    """
    import uuid
    
    job_id = str(uuid.uuid4())[:8]
    
    try:
        # 1. Lấy template nếu có
        template_values = {}
        if request.template_id:
            template_values = template_manager.get_default_values(request.template_id)

        # 2. Chuẩn bị input cho calculator
        design_input = {
            "flow_rate": request.flow_rate,
            "detention_time": request.detention_time or template_values.get("detention_time", 2.0),
            "surface_loading_rate": request.surface_loading_rate or template_values.get("surface_loading_rate", 35),
            "depth": request.depth or template_values.get("depth", 3.0),
            "number_of_tanks": request.number_of_tanks,
        }

        # 3. Tính toán theo loại bể
        if request.tank_type == TankType.SEDIMENTATION:
            calc_result = tank_calculator.design_sedimentation_tank(
                design_flow=design_input["flow_rate"],
                detention_time=design_input["detention_time"],
                surface_loading_rate=design_input["surface_loading_rate"],
                depth=design_input["depth"],
                number_of_tanks=design_input["number_of_tanks"]
            )
        elif request.tank_type == TankType.STORAGE:
            storage_volume = (design_input["flow_rate"] * design_input["detention_time"] / 24) if design_input["detention_time"] else design_input["flow_rate"]
            calc_result = tank_calculator.design_storage_tank(
                storage_volume=storage_volume,
                design_flow=design_input["flow_rate"],
                num_tanks=design_input["number_of_tanks"],
                depth=design_input["depth"]
            )
        else:
            # Mặc định dùng bể điều hòa
            calc_result = tank_calculator.design_buffer_tank(
                peak_flow=design_input["flow_rate"] / 24,
                average_flow=design_input["flow_rate"] / 24,
                buffer_time=design_input["detention_time"]
            )

        dims = calc_result.get("dimensions", {})
        hyd = calc_result.get("hydraulics", {})
        volume = calc_result.get("volume")

        # 4. Validate với rules
        validation_results = TankRules.validate_tank_design(
            request.tank_type.value,
            {
                "retention_time": hyd.get("retention_time"),
                "surface_loading": hyd.get("surface_loading"),
                "velocity": hyd.get("horizontal_velocity"),
                "weir_loading": hyd.get("weir_loading"),
                "length": dims.get("length"),
                "width": dims.get("width"),
                "depth": dims.get("water_depth"),
            }
        )
        validation_dicts = [r.to_dict() for r in validation_results]
        valid = all(r["status"] != "fail" for r in validation_dicts)
        warnings = [r["message"] for r in validation_dicts if r["status"] in ("warning", "fail")]
        warnings.extend(calc_result.get("warnings", []))

        # 5. Kết quả kết cấu (dùng kết quả tính toán có sẵn)
        structural_result = calc_result.get("structure")
        quantities = None
        if structural_result:
            quantities = {
                "concrete": round(structural_result.get("concrete_volume", 0) * request.number_of_tanks, 2),
                "reinforcement": round(structural_result.get("steel_weight", 0) * request.number_of_tanks, 2)
            }

        # 6. Tạo bản vẽ
        drawing_file = None
        struct = calc_result.get("structure", {})
        if request.generate_drawing and valid and dims:
            dxf_gen = DXFGenerator(output_dir=f"./outputs/{job_id}")

            dxf_gen.draw_tank_plan(
                length=dims.get("length", 0),
                width=dims.get("width", 0),
                wall_thickness=dims.get("wall_thickness", request.wall_thickness or 0.25),
                inlet_diameter=struct.get("inlet_diameter", 200),
                outlet_diameter=struct.get("outlet_diameter", 200),
                origin=(0, 0)
            )

            dxf_gen.draw_tank_section(
                length=dims.get("length", 0),
                total_depth=dims.get("total_depth", dims.get("water_depth", 0) + 0.3),
                water_depth=dims.get("water_depth", 0),
                wall_thickness=dims.get("wall_thickness", request.wall_thickness or 0.25),
                bottom_thickness=dims.get("bottom_thickness", request.bottom_thickness or 0.3),
                freeboard=dims.get("freeboard", 0.3),
                origin=(0, -dims.get("total_depth", dims.get("water_depth", 0) + 0.3) - 5)
            )

            dxf_gen.add_title_block(
                project_name=request.project_name,
                drawing_title=f"BỂ {request.tank_name}",
                scale="1:100"
            )

            drawing_file = dxf_gen.save(f"tank_{request.tank_name}")

        # 7. Chuẩn bị response
        response = TankDesignResponse(
            job_id=job_id,
            status="completed" if valid else "warning",
            dimensions={
                "length": round(dims.get("length", 0), 2),
                "width": round(dims.get("width", 0), 2),
                "depth": round(dims.get("water_depth", dims.get("depth", 0) or 0), 2),
                "total_depth": round(dims.get("total_depth", dims.get("water_depth", 0) + dims.get("sludge_depth", 0) + dims.get("freeboard", 0)), 2),
                "number_of_tanks": request.number_of_tanks
            },
            hydraulic_results={
                "volume": volume,
                "retention_time": hyd.get("retention_time"),
                "surface_loading": hyd.get("surface_loading"),
                "weir_loading": hyd.get("weir_loading"),
            },
            structural_results=structural_result,
            validation={
                "valid": valid,
                "results": validation_dicts
            },
            warnings=warnings,
            drawing_file=drawing_file,
            quantities=quantities
        )

        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi thiết kế: {str(e)}")


@router.post("/calculate")
async def calculate_tank(request: TankDesignRequest):
    """
    Chỉ tính toán (không tạo bản vẽ/báo cáo)
    
    Dùng để preview kết quả nhanh
    """
    # Tương tự design_tank nhưng không generate files
    request.generate_drawing = False
    request.generate_report = False
    
    # Gọi lại hàm design với flags đã tắt
    return await design_tank(request, BackgroundTasks())


@router.get("/templates")
async def list_tank_templates():
    """Liệt kê các template bể có sẵn"""
    templates = template_manager.list_templates()
    tank_templates = [
        t for t in templates 
        if t.get("category") in ["sedimentation", "biological", "filtration", "storage"]
    ]
    return {"templates": tank_templates}


@router.get("/templates/{template_id}")
async def get_tank_template(template_id: str):
    """Lấy chi tiết template"""
    template = template_manager.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template không tồn tại")
    return template


@router.get("/rules")
async def get_tank_design_rules():
    """Lấy các quy tắc thiết kế bể"""
    return {
        "design_limits": tank_rules.design_limits,
        "material_properties": tank_rules.material_properties,
        "standards": ["TCVN 7957:2008", "TCVN 5574:2018"]
    }
