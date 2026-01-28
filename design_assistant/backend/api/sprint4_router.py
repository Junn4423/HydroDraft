"""
Sprint 4 API Router - BIM & Enterprise Integration

Endpoints:
- /api/v1/bim/* - BIM Bridge endpoints
- /api/v1/versions/* - Version management
- /api/v1/reports/* - PDF report generation
- /api/v1/viewer/* - 3D viewer config
"""

from fastapi import APIRouter, HTTPException, Query, Body, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import json

# Import Sprint 4 modules
from generators.bim_bridge import BIMBridge, BIMCategory
from generators.version_manager import (
    VersionManager, get_version_manager, 
    VersionStatus, VersionDiff
)
from generators.pdf_report import (
    PDFReportGenerator, ReportConfig, ReportLanguage
)
from generators.viewer_config import (
    ViewerConfig, generate_viewer_html, generate_react_viewer_component
)

router = APIRouter(prefix="/api/v1", tags=["Sprint 4 - BIM & Enterprise"])


# ============== SCHEMAS ==============

class TankBIMRequest(BaseModel):
    """Request cho BIM tank export"""
    name: str = Field(..., description="Tên bể")
    length: float = Field(..., gt=0, description="Chiều dài trong (m)")
    width: float = Field(..., gt=0, description="Chiều rộng trong (m)")
    depth: float = Field(..., gt=0, description="Chiều sâu (m)")
    wall_thickness: float = Field(0.3, gt=0, description="Chiều dày tường (m)")
    foundation_thickness: float = Field(0.4, gt=0, description="Chiều dày đáy (m)")
    tank_type: str = Field("sedimentation", description="Loại bể")
    origin: List[float] = Field([0, 0, 0], description="Tọa độ gốc [x, y, z]")
    design_params: Optional[Dict[str, Any]] = Field(None, description="Thông số thiết kế bổ sung")


class PipeBIMRequest(BaseModel):
    """Request cho BIM pipe export"""
    name: str
    start_point: List[float] = Field(..., description="Điểm đầu [x, y, z]")
    end_point: List[float] = Field(..., description="Điểm cuối [x, y, z]")
    diameter: float = Field(..., gt=0, description="Đường kính (mm)")
    material: str = Field("HDPE", description="Vật liệu")
    pipe_type: str = Field("gravity", description="Loại ống")


class ProjectBIMRequest(BaseModel):
    """Request cho full project BIM export"""
    project_name: str
    project_number: str = ""
    client: str = ""
    location: str = ""
    tanks: List[TankBIMRequest] = []
    pipes: List[PipeBIMRequest] = []


class VersionCreateRequest(BaseModel):
    """Request tạo version mới"""
    project_id: str
    input_params: Dict[str, Any]
    calculation_log: Dict[str, Any]
    output_files: Optional[List[Dict[str, str]]] = None
    applied_rules: Optional[Dict[str, Any]] = None
    override_log: Optional[List[Dict[str, Any]]] = None
    description: str = ""
    tag: Optional[str] = None


class VersionCompareRequest(BaseModel):
    """Request so sánh versions"""
    version_from: str
    version_to: str


class ReportRequest(BaseModel):
    """Request tạo báo cáo PDF"""
    project_name: str
    project_code: str = ""
    client: str = ""
    location: str = ""
    prepared_by: str = "HydroDraft"
    checked_by: str = ""
    approved_by: str = ""
    language: str = Field("vi", description="vi hoặc en")
    project_data: Dict[str, Any] = {}
    calculation_results: Dict[str, Any] = {}
    output_files: Optional[List[Dict[str, str]]] = None


# ============== BIM ENDPOINTS ==============

@router.post("/bim/export/tank")
async def export_tank_bim(request: TankBIMRequest):
    """
    Xuất BIM data cho một bể
    
    Trả về:
    - BIM_Data.json
    - Dynamo script
    - pyRevit script
    """
    try:
        bridge = BIMBridge(output_dir="./outputs/bim")
        bridge.set_project_info(
            name=f"Tank_{request.name}",
            number="",
            client="",
            location=""
        )
        
        # Add tank
        element = bridge.add_tank(
            name=request.name,
            length=request.length,
            width=request.width,
            depth=request.depth,
            wall_thickness=request.wall_thickness,
            foundation_thickness=request.foundation_thickness,
            origin=tuple(request.origin),
            tank_type=request.tank_type,
            design_params=request.design_params
        )
        
        # Export files
        json_path = bridge.export_bim_data(f"tank_{request.name}_BIM_Data.json")
        dynamo_path = bridge.generate_dynamo_script(f"tank_{request.name}_Dynamo.dyn")
        pyrevit_path = bridge.generate_pyrevit_script(f"tank_{request.name}_pyRevit.py")
        
        return {
            "success": True,
            "element_id": element.element_id,
            "files": {
                "bim_data": json_path,
                "dynamo_script": dynamo_path,
                "pyrevit_script": pyrevit_path
            },
            "message": "BIM data exported successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bim/export/project")
async def export_project_bim(request: ProjectBIMRequest):
    """
    Xuất BIM data cho toàn bộ dự án
    """
    try:
        bridge = BIMBridge(output_dir="./outputs/bim")
        bridge.set_project_info(
            name=request.project_name,
            number=request.project_number,
            client=request.client,
            location=request.location
        )
        
        elements = []
        
        # Add tanks
        for tank in request.tanks:
            elem = bridge.add_tank(
                name=tank.name,
                length=tank.length,
                width=tank.width,
                depth=tank.depth,
                wall_thickness=tank.wall_thickness,
                foundation_thickness=tank.foundation_thickness,
                origin=tuple(tank.origin),
                tank_type=tank.tank_type,
                design_params=tank.design_params
            )
            elements.append({"type": "tank", "id": elem.element_id, "name": tank.name})
        
        # Add pipes
        for pipe in request.pipes:
            elem = bridge.add_pipe(
                name=pipe.name,
                start_point=tuple(pipe.start_point),
                end_point=tuple(pipe.end_point),
                diameter=pipe.diameter,
                material_key=pipe.material,
                pipe_type=pipe.pipe_type
            )
            elements.append({"type": "pipe", "id": elem.element_id, "name": pipe.name})
        
        # Export files
        safe_name = request.project_name.replace(" ", "_")
        json_path = bridge.export_bim_data(f"{safe_name}_BIM_Data.json")
        dynamo_path = bridge.generate_dynamo_script(f"{safe_name}_Dynamo.dyn")
        pyrevit_path = bridge.generate_pyrevit_script(f"{safe_name}_pyRevit.py")
        
        return {
            "success": True,
            "project": request.project_name,
            "elements": elements,
            "files": {
                "bim_data": json_path,
                "dynamo_script": dynamo_path,
                "pyrevit_script": pyrevit_path
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bim/download/{filename}")
async def download_bim_file(filename: str):
    """Download BIM file"""
    filepath = os.path.join("./outputs/bim", filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/octet-stream"
    )


# ============== VERSION ENDPOINTS ==============

@router.post("/versions/create")
async def create_version(request: VersionCreateRequest):
    """
    Tạo version mới cho thiết kế
    """
    try:
        manager = get_version_manager("./data/versions")
        
        version = manager.create_version(
            project_id=request.project_id,
            input_params=request.input_params,
            calculation_log=request.calculation_log,
            output_files=request.output_files,
            applied_rules=request.applied_rules,
            override_log=request.override_log,
            description=request.description,
            tag=request.tag
        )
        
        return {
            "success": True,
            "version_id": version.version_id,
            "version_number": version.version_number,
            "version_tag": version.version_tag,
            "content_hash": version.content_hash,
            "created_at": version.created_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/versions/{project_id}/list")
async def list_versions(project_id: str):
    """
    Liệt kê tất cả versions của project
    """
    try:
        manager = get_version_manager("./data/versions")
        history = manager.get_version_history(project_id)
        
        return {
            "project_id": project_id,
            "total_versions": len(history),
            "versions": history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/versions/{version_id}")
async def get_version(version_id: str):
    """
    Lấy chi tiết một version
    """
    try:
        manager = get_version_manager("./data/versions")
        version = manager.get_version(version_id)
        
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return version.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/versions/compare")
async def compare_versions(request: VersionCompareRequest):
    """
    So sánh 2 versions
    """
    try:
        manager = get_version_manager("./data/versions")
        
        report = manager.generate_diff_report(
            request.version_from,
            request.version_to
        )
        
        return report
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/versions/{version_id}/approve")
async def approve_version(
    version_id: str,
    approved_by: str = Query(..., description="Người phê duyệt")
):
    """
    Phê duyệt version
    """
    try:
        manager = get_version_manager("./data/versions")
        success = manager.approve_version(version_id, approved_by)
        
        if not success:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return {
            "success": True,
            "version_id": version_id,
            "status": "approved",
            "approved_by": approved_by
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/versions/{project_id}/rollback/{version_id}")
async def rollback_version(project_id: str, version_id: str):
    """
    Rollback về version cũ
    """
    try:
        manager = get_version_manager("./data/versions")
        
        new_version = manager.rollback_to_version(
            project_id=project_id,
            version_id=version_id
        )
        
        return {
            "success": True,
            "rollback_from": version_id,
            "new_version_id": new_version.version_id,
            "new_version_tag": new_version.version_tag
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== REPORT ENDPOINTS ==============

@router.post("/reports/technical")
async def generate_technical_report(request: ReportRequest):
    """
    Tạo báo cáo kỹ thuật PDF
    """
    try:
        generator = PDFReportGenerator(output_dir="./outputs/reports")
        
        config = ReportConfig(
            title="BÁO CÁO KỸ THUẬT",
            subtitle="Thiết kế hệ thống xử lý nước",
            project_name=request.project_name,
            project_code=request.project_code,
            client=request.client,
            location=request.location,
            prepared_by=request.prepared_by,
            checked_by=request.checked_by,
            approved_by=request.approved_by,
            language=ReportLanguage.VIETNAMESE if request.language == "vi" else ReportLanguage.ENGLISH
        )
        
        generator.set_config(config)
        
        filepath = generator.generate_technical_report(
            project_data=request.project_data,
            calculation_results=request.calculation_results,
            output_files=request.output_files
        )
        
        return {
            "success": True,
            "file_path": filepath,
            "file_name": os.path.basename(filepath)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/calculation")
async def generate_calculation_report(
    project_name: str = Query(...),
    calculation_log: Dict[str, Any] = Body(...)
):
    """
    Tạo phụ lục tính toán PDF
    """
    try:
        generator = PDFReportGenerator(output_dir="./outputs/reports")
        
        config = ReportConfig(
            title="PHỤ LỤC TÍNH TOÁN",
            project_name=project_name
        )
        generator.set_config(config)
        
        filepath = generator.generate_calculation_appendix(calculation_log)
        
        return {
            "success": True,
            "file_path": filepath,
            "file_name": os.path.basename(filepath)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/download/{filename}")
async def download_report(filename: str):
    """Download PDF report"""
    filepath = os.path.join("./outputs/reports", filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    media_type = "application/pdf" if filename.endswith(".pdf") else "text/plain"
    
    return FileResponse(
        filepath,
        filename=filename,
        media_type=media_type
    )


# ============== VIEWER ENDPOINTS ==============

@router.get("/viewer/config")
async def get_viewer_config():
    """
    Lấy cấu hình mặc định cho 3D viewer
    """
    config = ViewerConfig()
    config.add_section("xy", position=0, enabled=False)
    
    return {
        "config": json.loads(config.to_json()),
        "supported_formats": ["IFC", "IFC2x3", "IFC4"]
    }


@router.get("/viewer/html")
async def get_viewer_html(
    ifc_url: str = Query(..., description="URL to IFC file")
):
    """
    Lấy HTML snippet cho IFC viewer
    """
    html = generate_viewer_html(ifc_url)
    
    return JSONResponse(
        content={"html": html},
        media_type="application/json"
    )


@router.get("/viewer/react-component")
async def get_react_viewer_component():
    """
    Lấy React component cho IFC viewer
    """
    component = generate_react_viewer_component()
    
    return {
        "component": component,
        "dependencies": [
            "web-ifc-viewer",
            "three"
        ],
        "usage": "import IFCViewer from './IFCViewer'; <IFCViewer ifcUrl='/path/to/model.ifc' />"
    }


# ============== HEALTH CHECK ==============

@router.get("/sprint4/health")
async def sprint4_health():
    """
    Kiểm tra trạng thái Sprint 4 modules
    """
    # Check reportlab
    try:
        from reportlab.lib.pagesizes import A4
        pdf_available = True
    except:
        pdf_available = False
    
    return {
        "sprint": 4,
        "status": "healthy",
        "modules": {
            "bim_bridge": True,
            "version_manager": True,
            "pdf_reports": pdf_available,
            "viewer_config": True
        },
        "endpoints": {
            "bim": ["/api/v1/bim/export/tank", "/api/v1/bim/export/project"],
            "versions": ["/api/v1/versions/create", "/api/v1/versions/compare"],
            "reports": ["/api/v1/reports/technical", "/api/v1/reports/calculation"],
            "viewer": ["/api/v1/viewer/config", "/api/v1/viewer/html"]
        }
    }
