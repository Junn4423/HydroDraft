"""
API Router - Export Endpoints

Các endpoint xuất file:
- POST /export/dxf - Xuất file DXF
- POST /export/step - Xuất file STEP 3D
- POST /export/ifc - Xuất file IFC/BIM
- POST /export/report - Xuất báo cáo
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum
import os

from generators.dxf_generator import DXFGenerator
from generators.cad_3d_generator import CAD3DGenerator
from generators.ifc_generator import IFCGenerator

router = APIRouter(prefix="/export", tags=["Export"])


class ExportFormat(str, Enum):
    """Định dạng xuất"""
    DXF = "dxf"
    DWG = "dwg"  # Cần thêm converter
    STEP = "step"
    IGES = "iges"
    IFC = "ifc"
    PDF = "pdf"
    EXCEL = "excel"


class ExportDXFRequest(BaseModel):
    """Request xuất DXF"""
    job_id: str = Field(..., description="ID công việc thiết kế")
    elements: List[str] = Field(
        default=["all"],
        description="Danh sách phần tử cần xuất: plan, section, profile, ..."
    )
    scale: str = Field("1:100", description="Tỷ lệ bản vẽ")
    include_dimensions: bool = Field(True, description="Bao gồm kích thước")
    include_annotations: bool = Field(True, description="Bao gồm ghi chú")


class ExportSTEPRequest(BaseModel):
    """Request xuất STEP 3D"""
    job_id: str = Field(..., description="ID công việc thiết kế")
    elements: List[str] = Field(default=["all"], description="Phần tử cần xuất")
    version: str = Field("AP214", description="Phiên bản STEP")


class ExportIFCRequest(BaseModel):
    """Request xuất IFC"""
    job_id: str = Field(..., description="ID công việc thiết kế")
    project_name: str = Field(..., description="Tên dự án")
    site_name: str = Field("Site", description="Tên công trường")
    include_properties: bool = Field(True, description="Bao gồm thuộc tính")
    ifc_schema: str = Field("IFC4", description="Schema IFC")


class ReportType(str, Enum):
    """Loại báo cáo"""
    CALCULATION = "calculation"  # Báo cáo tính toán
    BOQ = "boq"  # Bảng khối lượng
    SPECIFICATION = "specification"  # Chỉ dẫn kỹ thuật
    SUMMARY = "summary"  # Tổng hợp


class ExportReportRequest(BaseModel):
    """Request xuất báo cáo"""
    job_id: str = Field(..., description="ID công việc thiết kế")
    report_type: ReportType = Field(..., description="Loại báo cáo")
    format: str = Field("pdf", description="Định dạng: pdf, docx, xlsx")
    language: str = Field("vi", description="Ngôn ngữ: vi, en")


class ExportResponse(BaseModel):
    """Response cho export"""
    success: bool
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    message: str


@router.post("/dxf", response_model=ExportResponse)
async def export_dxf(request: ExportDXFRequest):
    """
    Xuất file DXF 2D
    
    Hỗ trợ:
    - Mặt bằng (plan)
    - Mặt cắt (section)
    - Trắc dọc (profile)
    - Chi tiết (detail)
    """
    try:
        output_dir = f"./outputs/{request.job_id}"
        
        # Kiểm tra thư mục tồn tại
        if not os.path.exists(output_dir):
            raise HTTPException(
                status_code=404,
                detail=f"Không tìm thấy dữ liệu cho job {request.job_id}"
            )
        
        # Tìm file DXF đã tạo
        dxf_files = [f for f in os.listdir(output_dir) if f.endswith('.dxf')]
        
        if not dxf_files:
            raise HTTPException(
                status_code=404,
                detail="Chưa có file DXF được tạo"
            )
        
        file_path = os.path.join(output_dir, dxf_files[0])
        file_size = os.path.getsize(file_path)
        
        return ExportResponse(
            success=True,
            file_path=file_path,
            file_size=file_size,
            message="Xuất DXF thành công"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xuất DXF: {str(e)}")


@router.post("/step", response_model=ExportResponse)
async def export_step(request: ExportSTEPRequest):
    """
    Xuất file STEP 3D
    
    Yêu cầu pythonOCC
    """
    try:
        output_dir = f"./outputs/{request.job_id}"
        
        if not os.path.exists(output_dir):
            raise HTTPException(
                status_code=404,
                detail=f"Không tìm thấy dữ liệu cho job {request.job_id}"
            )
        
        # Tạo 3D generator
        gen_3d = CAD3DGenerator(output_dir=output_dir)
        
        # TODO: Load design data từ job và tạo 3D model
        # Tạm thời trả về thông báo
        
        return ExportResponse(
            success=False,
            message="Chức năng xuất STEP đang được phát triển"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xuất STEP: {str(e)}")


@router.post("/ifc", response_model=ExportResponse)
async def export_ifc(request: ExportIFCRequest):
    """
    Xuất file IFC/BIM
    
    Yêu cầu ifcopenshell
    """
    try:
        output_dir = f"./outputs/{request.job_id}"
        
        if not os.path.exists(output_dir):
            raise HTTPException(
                status_code=404,
                detail=f"Không tìm thấy dữ liệu cho job {request.job_id}"
            )
        
        # Tạo IFC generator
        ifc_gen = IFCGenerator(output_dir=output_dir)
        ifc_gen.create_new_model(
            project_name=request.project_name,
            site_name=request.site_name
        )
        
        # TODO: Load design data từ job và thêm elements
        
        file_path = ifc_gen.save(f"export_{request.job_id}")
        
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            return ExportResponse(
                success=True,
                file_path=file_path,
                file_size=file_size,
                message="Xuất IFC thành công"
            )
        else:
            return ExportResponse(
                success=False,
                message="Không thể tạo file IFC. Kiểm tra ifcopenshell đã cài đặt."
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xuất IFC: {str(e)}")


@router.post("/report", response_model=ExportResponse)
async def export_report(
    request: ExportReportRequest,
    background_tasks: BackgroundTasks
):
    """
    Xuất báo cáo
    
    Các loại:
    - Báo cáo tính toán (calculation)
    - Bảng khối lượng (boq)
    - Chỉ dẫn kỹ thuật (specification)
    """
    try:
        output_dir = f"./outputs/{request.job_id}"
        
        if not os.path.exists(output_dir):
            raise HTTPException(
                status_code=404,
                detail=f"Không tìm thấy dữ liệu cho job {request.job_id}"
            )
        
        # TODO: Implement report generation
        # Cần thêm ReportGenerator class
        
        return ExportResponse(
            success=False,
            message="Chức năng xuất báo cáo đang được phát triển"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xuất báo cáo: {str(e)}")


@router.get("/files/{job_id}")
async def list_job_files(job_id: str):
    """
    Liệt kê tất cả file đã xuất cho một job
    
    Returns:
        Danh sách file với tên, kích thước, loại
    """
    output_dir = f"./outputs/{job_id}"
    
    if not os.path.exists(output_dir):
        raise HTTPException(status_code=404, detail=f"Không tìm thấy dữ liệu cho job {job_id}")
    
    files = []
    for filename in os.listdir(output_dir):
        file_path = os.path.join(output_dir, filename)
        if os.path.isfile(file_path):
            ext = os.path.splitext(filename)[1].lower()
            file_type = {
                ".dxf": "CAD Drawing",
                ".pdf": "PDF Report",
                ".ifc": "BIM Model",
                ".step": "3D Model",
                ".stp": "3D Model",
            }.get(ext, "File")
            
            files.append({
                "filename": filename,
                "size": os.path.getsize(file_path),
                "type": file_type,
                "extension": ext,
                "download_url": f"/api/v1/export/download/{job_id}/{filename}"
            })
    
    return {
        "job_id": job_id,
        "files": files,
        "total": len(files)
    }


@router.get("/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    """
    Download file đã xuất
    """
    file_path = f"./outputs/{job_id}/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File không tồn tại")
    
    # Xác định media type
    media_types = {
        ".dxf": "application/dxf",
        ".step": "application/step",
        ".stp": "application/step",
        ".ifc": "application/x-step",
        ".pdf": "application/pdf",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }
    
    ext = os.path.splitext(filename)[1].lower()
    media_type = media_types.get(ext, "application/octet-stream")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )


@router.get("/download/{job_id}")
async def download_all_files(job_id: str):
    """
    Download file chính (DXF) cho một job
    Tự động tìm file DXF đầu tiên
    """
    output_dir = f"./outputs/{job_id}"
    
    if not os.path.exists(output_dir):
        raise HTTPException(status_code=404, detail=f"Không tìm thấy dữ liệu cho job {job_id}")
    
    # Ưu tiên file DXF
    for filename in os.listdir(output_dir):
        if filename.endswith('.dxf'):
            file_path = os.path.join(output_dir, filename)
            return FileResponse(
                path=file_path,
                filename=filename,
                media_type="application/dxf"
            )
    
    # Không có DXF, thử PDF
    for filename in os.listdir(output_dir):
        if filename.endswith('.pdf'):
            file_path = os.path.join(output_dir, filename)
            return FileResponse(
                path=file_path,
                filename=filename,
                media_type="application/pdf"
            )
    
    # Không có file nào phù hợp
    raise HTTPException(status_code=404, detail="Không tìm thấy file bản vẽ")


@router.get("/formats")
async def list_export_formats():
    """Liệt kê các định dạng xuất hỗ trợ"""
    return {
        "2D_CAD": [
            {"format": "DXF", "description": "AutoCAD DXF (R2018)", "available": True},
            {"format": "DWG", "description": "AutoCAD DWG", "available": False, "note": "Cần ODA converter"}
        ],
        "3D_CAD": [
            {"format": "STEP", "description": "STEP AP214/AP242", "available": True, "note": "Yêu cầu pythonOCC"},
            {"format": "IGES", "description": "IGES 5.3", "available": False}
        ],
        "BIM": [
            {"format": "IFC", "description": "IFC4", "available": True, "note": "Yêu cầu ifcopenshell"}
        ],
        "Documents": [
            {"format": "PDF", "description": "Báo cáo PDF", "available": False},
            {"format": "XLSX", "description": "Excel spreadsheet", "available": False},
            {"format": "DOCX", "description": "Word document", "available": False}
        ]
    }
