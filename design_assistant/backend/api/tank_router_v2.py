"""
API Router - Tank Design V2 (Traceable)

SPRINT 2: TRANSPARENT ENGINEERING
API endpoints với calculation logs đầy đủ

Endpoints:
- POST /design/tank/v2 - Thiết kế bể với log chi tiết
- POST /design/tank/v2/override - Override vi phạm
- GET /design/tank/v2/report/{job_id} - Lấy báo cáo tính toán
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from models.schemas import TankType
from calculations import (
    TraceableTankDesignEngine,
    SafetyEnforcementLayer,
    get_safety_layer,
    CalculationLog
)
from generators.dxf_generator import DXFGenerator

router = APIRouter(prefix="/design/tank/v2", tags=["Tank Design V2 - Traceable"])

# Services
tank_engine = TraceableTankDesignEngine()
safety_layer = get_safety_layer()

# Storage cho calculation logs (production: dùng database)
_calculation_logs: Dict[str, CalculationLog] = {}


class TankDesignRequestV2(BaseModel):
    """Request model cho thiết kế bể V2"""
    
    # Thông tin cơ bản
    project_name: str = Field(..., description="Tên dự án")
    tank_name: str = Field(..., description="Tên/ký hiệu bể")
    tank_type: TankType = Field(..., description="Loại bể")
    
    # Thông số thiết kế
    design_flow: float = Field(..., gt=0, description="Lưu lượng (m³/ngày)")
    num_tanks: int = Field(default=1, ge=1, le=10, description="Số bể")
    
    # Thông số tùy chọn
    retention_time: Optional[float] = Field(None, description="Thời gian lưu (h)")
    surface_loading_rate: Optional[float] = Field(None, description="Tải trọng bề mặt")
    settling_velocity: Optional[float] = Field(None, description="Vận tốc lắng (m/h)")
    
    # Kích thước (nếu đã biết)
    length: Optional[float] = Field(None, gt=0, description="Chiều dài (m)")
    width: Optional[float] = Field(None, gt=0, description="Chiều rộng (m)")  
    depth: Optional[float] = Field(None, gt=0, description="Chiều sâu (m)")
    
    # Vật liệu
    concrete_grade: str = Field(default="B25", description="Mác bê tông")
    steel_grade: str = Field(default="CB300-V", description="Mác thép")
    
    # Options
    generate_drawing: bool = Field(default=True)
    include_structural: bool = Field(default=True)


class OverrideRequestV2(BaseModel):
    """Request override vi phạm"""
    
    job_id: str = Field(..., description="Job ID")
    violation_id: str = Field(..., description="ID vi phạm cần override")
    reason: str = Field(..., min_length=50, description="Lý do override (≥50 ký tự)")
    engineer_id: str = Field(..., description="ID kỹ sư")
    engineer_name: str = Field(..., description="Tên kỹ sư")
    reference_doc: Optional[str] = Field(None, description="Tài liệu tham chiếu")


class TankDesignResponseV2(BaseModel):
    """Response model V2 với calculation log"""
    
    job_id: str
    status: str
    can_export: bool
    
    # Kết quả thiết kế
    dimensions: dict
    hydraulics: dict
    structural: Optional[dict] = None
    pipes: dict
    volume: dict
    
    # Calculation log tóm tắt
    calculation_summary: dict
    
    # Vi phạm
    violations: List[dict] = []
    warnings: List[str] = []
    
    # Files
    drawing_file: Optional[str] = None
    
    # Full log (optional)
    full_calculation_log: Optional[dict] = None


@router.post("/", response_model=TankDesignResponseV2)
async def design_tank_v2(
    request: TankDesignRequestV2,
    include_full_log: bool = False
):
    """
    Thiết kế bể với calculation log đầy đủ
    
    Returns kết quả thiết kế kèm:
    - Từng bước tính toán
    - Công thức và tham chiếu
    - Vi phạm tiêu chuẩn
    - Khả năng export
    """
    job_id = str(uuid.uuid4())[:8]
    
    try:
        # 1. Thiết kế theo loại bể
        if request.tank_type == TankType.SEDIMENTATION:
            result = tank_engine.design_sedimentation_tank(
                tank_name=request.tank_name,
                design_flow=request.design_flow,
                num_tanks=request.num_tanks,
                settling_velocity=request.settling_velocity,
                retention_time=request.retention_time,
                surface_loading_rate=request.surface_loading_rate,
                length=request.length,
                width=request.width,
                depth=request.depth,
                concrete_grade=request.concrete_grade,
                steel_grade=request.steel_grade
            )
        elif request.tank_type == TankType.STORAGE:
            # Tính thể tích từ lưu lượng và thời gian lưu
            storage_volume = (request.design_flow * (request.retention_time or 6)) / 24
            result = tank_engine.design_storage_tank(
                tank_name=request.tank_name,
                storage_volume=storage_volume,
                design_flow=request.design_flow,
                num_tanks=request.num_tanks,
                length=request.length,
                width=request.width,
                depth=request.depth,
                concrete_grade=request.concrete_grade,
                steel_grade=request.steel_grade
            )
        else:
            # Mặc định: bể lắng
            result = tank_engine.design_sedimentation_tank(
                tank_name=request.tank_name,
                design_flow=request.design_flow,
                num_tanks=request.num_tanks,
                retention_time=request.retention_time,
                concrete_grade=request.concrete_grade,
                steel_grade=request.steel_grade
            )
        
        # 2. Lưu calculation log
        if result.calculation_log:
            _calculation_logs[job_id] = result.calculation_log
        
        # 3. Tạo bản vẽ nếu có thể export
        drawing_file = None
        if request.generate_drawing and result.can_export:
            dxf_gen = DXFGenerator(output_dir=f"./outputs/{job_id}")
            
            dxf_gen.draw_tank_plan(
                length=result.length,
                width=result.width,
                wall_thickness=result.wall_thickness,
                inlet_diameter=result.inlet_diameter,
                outlet_diameter=result.outlet_diameter,
                origin=(0, 0)
            )
            
            dxf_gen.draw_tank_section(
                length=result.length,
                total_depth=result.total_depth,
                water_depth=result.water_depth,
                wall_thickness=result.wall_thickness,
                bottom_thickness=result.bottom_thickness,
                freeboard=result.total_depth - result.water_depth - 0.5,
                origin=(0, -result.total_depth - 5)
            )
            
            dxf_gen.add_title_block(
                project_name=request.project_name,
                drawing_title=f"BỂ {request.tank_name}",
                scale="1:100"
            )
            
            drawing_file = dxf_gen.save(f"tank_{request.tank_name}")
        
        # 4. Chuẩn bị response
        calc_log = result.calculation_log
        
        # Tóm tắt calculation
        calculation_summary = {
            "log_id": calc_log.log_id if calc_log else None,
            "calculation_type": calc_log.calculation_type if calc_log else None,
            "total_steps": len(calc_log.steps) if calc_log else 0,
            "total_violations": len(calc_log.violations) if calc_log else 0,
            "critical_violations": len([v for v in calc_log.violations if v.severity.value == "critical" and not v.is_overridden]) if calc_log else 0,
            "standards_applied": calc_log.standards_applied if calc_log else [],
            "calculation_time_ms": calc_log.calculation_time_ms if calc_log else 0
        }
        
        # Danh sách vi phạm
        violations = []
        if calc_log:
            for v in calc_log.violations:
                violations.append({
                    "violation_id": v.violation_id,
                    "parameter": v.parameter,
                    "severity": v.severity.value,
                    "message": v.message,
                    "suggestion": v.suggestion,
                    "standard": v.standard,
                    "clause": v.clause,
                    "is_overridden": v.is_overridden
                })
        
        # Warnings từ steps
        warnings = []
        if calc_log:
            for step in calc_log.steps:
                warnings.extend(step.warnings)
        
        response = TankDesignResponseV2(
            job_id=job_id,
            status="completed" if result.is_valid else "warning",
            can_export=result.can_export,
            dimensions={
                "length": result.length,
                "width": result.width,
                "water_depth": result.water_depth,
                "total_depth": result.total_depth,
                "wall_thickness": result.wall_thickness,
                "bottom_thickness": result.bottom_thickness,
                "num_tanks": result.num_tanks
            },
            hydraulics={
                "design_flow": result.design_flow,
                "retention_time": result.retention_time,
                "surface_loading": result.surface_loading,
                "horizontal_velocity": result.horizontal_velocity
            },
            structural={
                "concrete_grade": request.concrete_grade,
                "steel_grade": request.steel_grade,
                "is_valid": result.is_valid
            } if request.include_structural else None,
            pipes={
                "inlet_diameter": result.inlet_diameter,
                "outlet_diameter": result.outlet_diameter
            },
            volume={
                "per_tank": result.volume_per_tank,
                "total": result.volume_total
            },
            calculation_summary=calculation_summary,
            violations=violations,
            warnings=warnings,
            drawing_file=drawing_file,
            full_calculation_log=calc_log.to_dict() if include_full_log and calc_log else None
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi thiết kế: {str(e)}")


@router.post("/override")
async def override_violation(request: OverrideRequestV2):
    """
    Override vi phạm tiêu chuẩn
    
    Yêu cầu:
    - Lý do chi tiết (≥50 ký tự)
    - Thông tin kỹ sư
    - Sẽ được ghi nhận vào log
    """
    # Lấy calculation log
    calc_log = _calculation_logs.get(request.job_id)
    if not calc_log:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy job: {request.job_id}")
    
    # Thực hiện override
    success, message = safety_layer.request_override(
        calc_log=calc_log,
        violation_id=request.violation_id,
        reason=request.reason,
        engineer_id=request.engineer_id,
        engineer_name=request.engineer_name,
        reference_doc=request.reference_doc
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # Kiểm tra lại trạng thái
    safety_result = safety_layer.check_calculation_log(calc_log)
    
    return {
        "success": True,
        "message": message,
        "can_export_now": safety_result.can_export,
        "remaining_violations": safety_result.pending_override
    }


@router.get("/report/{job_id}")
async def get_calculation_report(job_id: str, format: str = "text"):
    """
    Lấy báo cáo tính toán chi tiết
    
    Args:
        job_id: ID của job
        format: "text" hoặc "json"
    """
    calc_log = _calculation_logs.get(job_id)
    if not calc_log:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy job: {job_id}")
    
    if format == "json":
        return calc_log.to_dict()
    else:
        # Text format cho in ấn
        return {
            "report": calc_log.to_report_format(),
            "override_report": safety_layer.generate_override_report(calc_log)
        }


@router.get("/steps/{job_id}")
async def get_calculation_steps(job_id: str):
    """
    Lấy danh sách các bước tính toán
    
    Dùng để hiển thị progress hoặc review từng bước
    """
    calc_log = _calculation_logs.get(job_id)
    if not calc_log:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy job: {job_id}")
    
    steps = []
    for step in calc_log.steps:
        steps.append({
            "step_id": step.step_id,
            "name": step.name,
            "description": step.description,
            "formula_latex": step.formula_latex,
            "formula_text": step.formula_text,
            "reference": step.reference,
            "inputs": step.inputs,
            "result": step.result,
            "result_formatted": step.result_formatted,
            "status": step.status.value,
            "warnings": step.warnings
        })
    
    return {
        "job_id": job_id,
        "total_steps": len(steps),
        "steps": steps
    }


@router.get("/violations/{job_id}")
async def get_violations(job_id: str):
    """
    Lấy danh sách vi phạm
    """
    calc_log = _calculation_logs.get(job_id)
    if not calc_log:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy job: {job_id}")
    
    safety_result = safety_layer.check_calculation_log(calc_log)
    
    return {
        "job_id": job_id,
        "can_export": safety_result.can_export,
        "total_violations": safety_result.total_violations,
        "critical_count": safety_result.critical_violations,
        "major_count": safety_result.major_violations,
        "minor_count": safety_result.minor_violations,
        "overridden_count": safety_result.overridden_count,
        "pending_override": safety_result.pending_override,
        "violations": [v.to_dict() for v in safety_result.violations],
        "block_reasons": safety_result.block_reasons
    }
