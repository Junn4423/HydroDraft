"""
API Router - Pipeline Design Endpoints

Các endpoint thiết kế đường ống:
- POST /design/pipeline - Thiết kế tuyến ống mới
- POST /design/pipeline/calculate - Tính toán thủy lực
- GET /design/pipeline/materials - Danh sách vật liệu ống
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

from models.schemas import PipelineInput, MaterialType, PipelineCalculationResult
from calculations.pipe_design import PipeDesignCalculator
from calculations.hydraulic import HydraulicCalculator
from rules.pipe_rules import PipeRules
from rules.engine import RuleStatus
from generators.dxf_generator import DXFGenerator
from templates.manager import TemplateManager

router = APIRouter(prefix="/design/pipeline", tags=["Pipeline Design"])

# Khởi tạo services
pipe_calculator = PipeDesignCalculator()
hydraulic_calculator = HydraulicCalculator()
pipe_rules = PipeRules()
template_manager = TemplateManager()


class PipeType(str, Enum):
    """Loại đường ống"""
    GRAVITY = "gravity"  # Tự chảy
    PRESSURE = "pressure"  # Có áp


class FlowType(str, Enum):
    """Loại dòng chảy"""
    WASTEWATER = "wastewater"  # Nước thải
    STORMWATER = "stormwater"  # Nước mưa
    WATER_SUPPLY = "water_supply"  # Cấp nước


class ManholePoint(BaseModel):
    """Để chứa thông tin điểm giếng thăm"""
    station: float = Field(..., description="Lý trình (m)")
    ground_level: float = Field(..., description="Cao độ mặt đất (m)")
    name: Optional[str] = Field(None, description="Tên/ID giếng")


class PipelineDesignRequest(BaseModel):
    """Request model cho thiết kế tuyến ống"""
    
    # Thông tin cơ bản
    project_name: str = Field(..., description="Tên dự án")
    pipeline_name: str = Field(..., description="Tên/ký hiệu tuyến")
    
    # Loại ống
    pipe_type: PipeType = Field(..., description="Loại ống (tự chảy/có áp)")
    flow_type: FlowType = Field(..., description="Loại dòng chảy")
    
    # Thông số thiết kế
    design_flow: float = Field(..., gt=0, description="Lưu lượng thiết kế (L/s)")
    material: MaterialType = Field(MaterialType.CONCRETE, description="Vật liệu ống")
    
    # Điểm tuyến
    manholes: List[ManholePoint] = Field(..., min_length=2, description="Danh sách giếng thăm")
    
    # Tùy chọn
    min_cover_depth: float = Field(0.7, ge=0.3, description="Chiều sâu lấp tối thiểu (m)")
    max_velocity: Optional[float] = Field(None, description="Vận tốc tối đa (m/s)")
    min_velocity: Optional[float] = Field(None, description="Vận tốc tối thiểu (m/s)")
    
    # Đường kính (nếu đã biết)
    diameter: Optional[float] = Field(None, description="Đường kính ống (mm)")
    
    # Output
    generate_drawing: bool = Field(True, description="Tạo bản vẽ CAD")


class PipeSegmentResult(BaseModel):
    """Kết quả một đoạn ống"""
    segment_id: int
    start_manhole: str
    end_manhole: str
    length: float
    slope: float
    diameter: float
    velocity: float
    flow_capacity: float
    filling_ratio: float
    valid: bool
    warnings: List[str] = []


class PipelineDesignResponse(BaseModel):
    """Response model cho thiết kế tuyến ống"""
    
    job_id: str
    status: str
    
    # Tổng quan
    total_length: float
    number_of_segments: int
    number_of_manholes: int
    
    # Kết quả từng đoạn
    segments: List[PipeSegmentResult]
    
    # Giếng thăm
    manholes: List[dict]
    
    # Validation
    validation: dict
    warnings: List[str]
    
    # Files
    drawing_file: Optional[str] = None


@router.post("/", response_model=PipelineDesignResponse)
async def design_pipeline(
    request: PipelineDesignRequest,
    background_tasks: BackgroundTasks
):
    """
    Thiết kế tuyến đường ống
    
    Quy trình:
    1. Validate input
    2. Thiết kế trắc dọc
    3. Tính toán thủy lực từng đoạn
    4. Bố trí giếng thăm
    5. Tạo bản vẽ
    """
    import uuid
    
    job_id = str(uuid.uuid4())[:8]
    
    try:
        # 1. Chuẩn bị dữ liệu đầu vào
        profile_data = [
            {
                "station": mh.station,
                "ground_level": mh.ground_level,
                "name": mh.name or f"MH{i+1}"
            }
            for i, mh in enumerate(request.manholes)
        ]
        
        # 2. Lấy hệ số nhám
        roughness = pipe_rules.get_manning_n(request.material.value)
        
        # 3. Xác định đường kính
        if request.diameter:
            diameter = request.diameter
        else:
            # Chọn đường kính dựa trên lưu lượng
            diameter = pipe_calculator.select_pipe_diameter(
                flow_rate=request.design_flow,
                slope=0.005,  # Độ dốc ước tính
                roughness=roughness,
                pipe_type=request.pipe_type.value
            )
        
        # 4. Thiết kế theo loại ống
        if request.pipe_type == PipeType.GRAVITY:
            design_result = pipe_calculator.design_gravity_pipe_from_profile(
                flow_rate=request.design_flow,
                profile_data=profile_data,
                pipe_diameter=diameter,
                roughness=roughness,
                min_cover=request.min_cover_depth
            )
        else:
            design_result = pipe_calculator.design_pressure_pipe_from_profile(
                flow_rate=request.design_flow,
                profile_data=profile_data,
                pipe_diameter=diameter,
                roughness=roughness
            )
        
        # 5. Validate từng đoạn
        segments_result = []
        all_warnings = []
        all_valid = True
        
        for i, seg in enumerate(design_result.get("segments", [])):
            # Validate
            velocity_check = pipe_rules.validate_velocity(
                pipe_type=request.flow_type.value,
                velocity=seg["velocity"]
            )

            slope_check = pipe_rules.validate_slope(
                pipe_type=request.pipe_type.value,
                diameter=seg["diameter"],
                slope=seg["slope"] * 1000  # Convert to ‰
            )

            segment_valid = velocity_check.status != RuleStatus.FAIL and slope_check.status != RuleStatus.FAIL
            segment_warnings = []
            if velocity_check.status != RuleStatus.PASS:
                segment_warnings.append(velocity_check.message)
            if slope_check.status != RuleStatus.PASS:
                segment_warnings.append(slope_check.message)

            if not segment_valid:
                all_valid = False
            all_warnings.extend(segment_warnings)

            segments_result.append(PipeSegmentResult(
                segment_id=i + 1,
                start_manhole=seg.get("start_manhole", f"MH{i+1}"),
                end_manhole=seg.get("end_manhole", f"MH{i+2}"),
                length=round(seg["length"], 1),
                slope=round(seg["slope"] * 1000, 2),  # ‰
                diameter=seg["diameter"],
                velocity=round(seg["velocity"], 2),
                flow_capacity=round(seg["capacity"], 1),
                filling_ratio=round(seg.get("filling_ratio", 0.75), 2),
                valid=segment_valid,
                warnings=segment_warnings
            ))
        
        # 6. Bố trí giếng thăm
        manholes_result = design_result.get("manholes", [])
        
        # 7. Tạo bản vẽ
        drawing_file = None
        if request.generate_drawing:
            dxf_gen = DXFGenerator(output_dir=f"./outputs/{job_id}")
            
            # Vẽ trắc dọc
            dxf_gen.draw_pipe_profile(
                segments=[
                    {
                        "diameter": s.diameter,
                        "slope": s.slope,
                        "length": s.length
                    }
                    for s in segments_result
                ],
                manholes=[
                    {
                        "station": mh["station"],
                        "ground_level": mh["ground_level"],
                        "invert_level": mh["invert_level"],
                        "id": mh.get("id", f"MH{i+1}")
                    }
                    for i, mh in enumerate(manholes_result)
                ],
                origin=(0, 0),
                h_scale=1/500,
                v_scale=1/100
            )
            
            dxf_gen.add_title_block(
                project_name=request.project_name,
                drawing_title=f"TRẮC DỌC TUYẾN {request.pipeline_name}",
                scale="1:500/100"
            )
            
            drawing_file = dxf_gen.save(f"pipeline_{request.pipeline_name}")
        
        # 8. Response
        total_length = sum(s.length for s in segments_result)
        
        return PipelineDesignResponse(
            job_id=job_id,
            status="completed" if all_valid else "warning",
            total_length=round(total_length, 1),
            number_of_segments=len(segments_result),
            number_of_manholes=len(manholes_result),
            segments=segments_result,
            manholes=manholes_result,
            validation={"valid": all_valid},
            warnings=list(set(all_warnings)),
            drawing_file=drawing_file
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi thiết kế: {str(e)}")


@router.post("/calculate")
async def calculate_pipe_hydraulics(
    flow_rate: float,
    diameter: float,
    slope: float,
    material: MaterialType = MaterialType.CONCRETE
):
    """
    Tính toán thủy lực nhanh cho một đoạn ống
    
    Args:
        flow_rate: Lưu lượng (L/s)
        diameter: Đường kính (mm)
        slope: Độ dốc (‰)
        material: Vật liệu
    """
    roughness = pipe_rules.get_manning_n(material.value)
    
    # Tính vận tốc và khả năng tải
    D = diameter / 1000  # m
    i = slope / 1000  # -
    
    result = hydraulic_calculator.manning_flow(
        diameter=D,
        slope=i,
        roughness=roughness
    )
    
    # Tính tỷ lệ đầy
    filling_ratio = flow_rate / 1000 / result["flow_rate"] if result["flow_rate"] > 0 else 1.0
    
    # Validate
    validation = pipe_rules.validate_velocity(result["velocity"], "wastewater")
    
    return {
        "input": {
            "flow_rate": flow_rate,
            "diameter": diameter,
            "slope": slope,
            "material": material.value,
            "roughness": roughness
        },
        "results": {
            "velocity": round(result["velocity"], 3),
            "flow_capacity": round(result["flow_rate"] * 1000, 1),  # L/s
            "filling_ratio": round(min(filling_ratio, 1.0), 2),
            "hydraulic_radius": round(result["hydraulic_radius"], 4)
        },
        "validation": validation
    }


@router.get("/materials")
async def list_pipe_materials():
    """Liệt kê các loại vật liệu ống và hệ số nhám"""
    return {
        "materials": [
            {
                "code": mat.value,
                "name": _get_material_name(mat.value),
                "manning_n": pipe_rules.get_manning_n(mat.value),
                "max_velocity": getattr(pipe_rules, "max_velocity", {}).get(mat.value, 4.0)
            }
            for mat in MaterialType
        ]
    }


@router.get("/standard-diameters")
async def list_standard_diameters():
    """Liệt kê đường kính tiêu chuẩn"""
    return {
        "gravity_pipes": pipe_rules.STANDARD_DIAMETERS,
        "pressure_pipes": [50, 63, 75, 90, 110, 125, 160, 200, 250, 315, 400, 500, 630],
        "unit": "mm"
    }


@router.get("/min-slopes")
async def get_minimum_slopes():
    """Lấy độ dốc tối thiểu theo đường kính"""
    return {
        "min_slopes": pipe_rules.MIN_SLOPE_BY_DIAMETER,
        "unit": "‰"
    }


def _get_material_name(code: str) -> str:
    """Lấy tên vật liệu từ code"""
    names = {
        "concrete": "Bê tông cốt thép",
        "hdpe": "HDPE đặc",
        "pvc": "PVC-U",
        "composite": "Composite (GRP)",
        "ductile_iron": "Gang dẻo",
        "steel": "Thép"
    }
    return names.get(code, code)
