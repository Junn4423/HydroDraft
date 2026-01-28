"""
Pydantic Schemas - Định nghĩa schema cho dữ liệu đầu vào/đầu ra
"""

from pydantic import BaseModel, Field, validator, model_validator
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from datetime import datetime

# ==================== ENUMS ====================

class TankType(str, Enum):
    """Loại bể xử lý"""
    SEDIMENTATION = "sedimentation"      # Bể lắng
    FILTRATION = "filtration"            # Bể lọc
    STORAGE = "storage"                  # Bể chứa
    BUFFER = "buffer"                    # Bể điều hòa
    AERATION = "aeration"                # Bể sục khí
    DISINFECTION = "disinfection"        # Bể khử trùng
    EQUALIZATION = "equalization"        # Bể điều hòa lưu lượng

class MaterialType(str, Enum):
    """Loại vật liệu"""
    CONCRETE = "concrete"        # Bê tông cốt thép
    STEEL = "steel"              # Thép
    HDPE = "hdpe"                # HDPE
    PVC = "pvc"                  # PVC
    UPVC = "upvc"                # uPVC
    STAINLESS = "stainless"      # Inox
    COMPOSITE = "composite"      # Composite
    DUCTILE_IRON = "ductile_iron"  # Gang dẻo

class PumpType(str, Enum):
    """Loại máy bơm"""
    SUBMERSIBLE = "submersible"      # Bơm chìm
    CENTRIFUGAL = "centrifugal"      # Bơm ly tâm
    AXIAL = "axial"                  # Bơm hướng trục
    SCREW = "screw"                  # Bơm trục vít
    DIAPHRAGM = "diaphragm"          # Bơm màng

class WellType(str, Enum):
    """Loại giếng"""
    MONITORING = "monitoring"        # Giếng quan trắc
    PUMPING = "pumping"              # Giếng khai thác
    INJECTION = "injection"          # Giếng bổ cập
    OBSERVATION = "observation"      # Giếng quan sát

# ==================== TANK SCHEMAS ====================

class TankInput(BaseModel):
    """Schema đầu vào cho thiết kế bể"""
    
    # Thông tin cơ bản
    name: str = Field(..., description="Tên bể", example="Bể lắng sơ cấp")
    tank_type: TankType = Field(..., description="Loại bể")
    
    # Thông số thiết kế
    design_flow: float = Field(..., gt=0, description="Lưu lượng thiết kế (m³/ngày)", example=1000)
    
    # Kích thước (tùy chọn - hệ thống có thể tự tính)
    length: Optional[float] = Field(None, gt=0, description="Chiều dài (m)")
    width: Optional[float] = Field(None, gt=0, description="Chiều rộng (m)")
    depth: Optional[float] = Field(None, gt=0, description="Chiều sâu nước (m)")
    
    # Vật liệu
    material: MaterialType = Field(default=MaterialType.CONCRETE, description="Vật liệu xây dựng")
    wall_thickness: float = Field(default=0.3, ge=0.15, le=1.0, description="Chiều dày thành (m)")
    
    # Đường ống
    inlet_diameter: Optional[float] = Field(None, gt=0, description="Đường kính ống vào (mm)")
    outlet_diameter: Optional[float] = Field(None, gt=0, description="Đường kính ống ra (mm)")
    
    # Cao độ
    foundation_level: float = Field(default=0.0, description="Cao độ đáy bể (m)")
    freeboard: float = Field(default=0.3, ge=0.2, le=0.5, description="Chiều cao an toàn (m)")
    
    # Thông số bổ sung cho bể lắng
    settling_velocity: Optional[float] = Field(None, gt=0, description="Vận tốc lắng (m/h)")
    sludge_zone_depth: Optional[float] = Field(None, gt=0, description="Chiều sâu vùng bùn (m)")
    
    @validator('design_flow')
    def validate_design_flow(cls, v):
        if v <= 0:
            raise ValueError("Lưu lượng thiết kế phải lớn hơn 0")
        if v > 1000000:
            raise ValueError("Lưu lượng thiết kế quá lớn (>1,000,000 m³/ngày)")
        return v
    
    @model_validator(mode='after')
    def validate_dimensions(self):
        """Kiểm tra tính hợp lý của kích thước"""
        if self.length and self.width:
            ratio = self.length / self.width
            if ratio < 0.5 or ratio > 10:
                # Chỉ cảnh báo, không raise error
                pass
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Bể lắng sơ cấp",
                "tank_type": "sedimentation",
                "design_flow": 1000,
                "material": "concrete",
                "wall_thickness": 0.3,
                "foundation_level": -3.0,
                "settling_velocity": 1.5
            }
        }

class TankCalculationResult(BaseModel):
    """Kết quả tính toán bể"""
    
    # Kích thước tính toán
    length: float = Field(..., description="Chiều dài (m)")
    width: float = Field(..., description="Chiều rộng (m)")  
    depth: float = Field(..., description="Chiều sâu nước (m)")
    total_depth: float = Field(..., description="Chiều sâu tổng (m)")
    
    # Thể tích
    volume: float = Field(..., description="Thể tích hữu ích (m³)")
    total_volume: float = Field(..., description="Thể tích tổng (m³)")
    
    # Thông số thủy lực
    retention_time: float = Field(..., description="Thời gian lưu nước (giờ)")
    surface_loading: float = Field(..., description="Tải trọng bề mặt (m³/m²/ngày)")
    weir_loading: Optional[float] = Field(None, description="Tải trọng máng tràn (m³/m/ngày)")
    velocity: Optional[float] = Field(None, description="Vận tốc ngang (m/s)")
    
    # Kết cấu
    wall_height: float = Field(..., description="Chiều cao thành (m)")
    bottom_slope: Optional[float] = Field(None, description="Độ dốc đáy (%)")
    
    # Đường ống
    inlet_diameter: float = Field(..., description="Đường kính ống vào (mm)")
    outlet_diameter: float = Field(..., description="Đường kính ống ra (mm)")
    
    # Bùn (cho bể lắng)
    sludge_volume: Optional[float] = Field(None, description="Thể tích bùn (m³)")
    sludge_pumping_rate: Optional[float] = Field(None, description="Lưu lượng bơm bùn (m³/h)")

class TankOutput(BaseModel):
    """Schema đầu ra cho thiết kế bể"""
    
    id: int
    name: str
    tank_type: TankType
    calculation: TankCalculationResult
    validation_results: List['ValidationResult']
    warnings: List[str] = []
    created_at: datetime

class TankDesignResult(BaseModel):
    """Kết quả thiết kế bể hoàn chỉnh"""
    
    job_id: str
    status: str
    tank: TankOutput
    files: Dict[str, str] = {}  # {format: file_path}
    report_url: Optional[str] = None

# ==================== PIPELINE SCHEMAS ====================

class PipePoint(BaseModel):
    """Điểm trên tuyến ống"""
    x: float = Field(..., description="Tọa độ X")
    y: float = Field(..., description="Tọa độ Y")
    z: Optional[float] = Field(None, description="Cao độ (m)")
    station: Optional[float] = Field(None, description="Lý trình (m)")

class PipelineInput(BaseModel):
    """Schema đầu vào cho thiết kế đường ống"""
    
    name: str = Field(..., description="Tên tuyến ống")
    
    # Điểm đầu và cuối
    start_point: PipePoint = Field(..., description="Điểm đầu")
    end_point: PipePoint = Field(..., description="Điểm cuối")
    
    # Các điểm trung gian (tùy chọn)
    intermediate_points: List[PipePoint] = Field(default=[], description="Các điểm trung gian")
    
    # Thông số thiết kế
    design_flow: float = Field(..., gt=0, description="Lưu lượng thiết kế (m³/s)")
    diameter: Optional[float] = Field(None, gt=0, description="Đường kính (mm)")
    slope: Optional[float] = Field(None, description="Độ dốc (%)")
    
    # Vật liệu
    material: MaterialType = Field(default=MaterialType.HDPE, description="Vật liệu ống")
    roughness: float = Field(default=0.013, gt=0, description="Hệ số nhám Manning")
    
    # Lắp đặt
    cover_depth: float = Field(default=0.8, ge=0.5, le=5.0, description="Độ sâu chôn ống (m)")
    min_velocity: float = Field(default=0.6, description="Vận tốc tối thiểu (m/s)")
    max_velocity: float = Field(default=3.0, description="Vận tốc tối đa (m/s)")
    
    # Loại đường ống
    pipe_type: str = Field(default="gravity", description="Loại: gravity/pressure")
    
    @validator('slope')
    def validate_slope(cls, v):
        if v is not None and (v < 0.001 or v > 20):
            raise ValueError("Độ dốc phải nằm trong khoảng 0.001% - 20%")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Tuyến cống D300",
                "start_point": {"x": 0, "y": 0, "z": 10.5},
                "end_point": {"x": 100, "y": 50, "z": 9.5},
                "design_flow": 0.05,
                "material": "hdpe",
                "cover_depth": 1.0
            }
        }

class PipelineCalculationResult(BaseModel):
    """Kết quả tính toán đường ống"""
    
    # Kích thước
    length: float = Field(..., description="Chiều dài tuyến (m)")
    diameter: float = Field(..., description="Đường kính (mm)")
    slope: float = Field(..., description="Độ dốc (%)")
    
    # Thủy lực
    velocity: float = Field(..., description="Vận tốc (m/s)")
    flow_capacity: float = Field(..., description="Khả năng tải (m³/s)")
    fill_ratio: float = Field(..., description="Tỷ lệ đầy (%)")
    hydraulic_radius: float = Field(..., description="Bán kính thủy lực (m)")
    reynolds_number: float = Field(..., description="Số Reynolds")
    flow_regime: str = Field(..., description="Chế độ chảy")
    
    # Head loss
    friction_loss: float = Field(..., description="Tổn thất ma sát (m)")
    minor_loss: float = Field(..., description="Tổn thất cục bộ (m)")
    total_head_loss: float = Field(..., description="Tổng tổn thất (m)")
    
    # Cao độ
    invert_levels: List[Tuple[float, float]] = Field(..., description="Cao độ đáy ống [(station, level)]")

class PipelineOutput(BaseModel):
    """Schema đầu ra cho thiết kế đường ống"""
    
    id: int
    name: str
    calculation: PipelineCalculationResult
    validation_results: List['ValidationResult']
    warnings: List[str] = []
    created_at: datetime

class PipelineDesignResult(BaseModel):
    """Kết quả thiết kế đường ống hoàn chỉnh"""
    
    job_id: str
    status: str
    pipeline: PipelineOutput
    files: Dict[str, str] = {}
    report_url: Optional[str] = None

# ==================== WELL SCHEMAS ====================

class WellInput(BaseModel):
    """Schema đầu vào cho thiết kế giếng"""
    
    name: str = Field(..., description="Tên giếng")
    well_type: WellType = Field(default=WellType.MONITORING, description="Loại giếng")
    
    # Vị trí
    x: float = Field(..., description="Tọa độ X")
    y: float = Field(..., description="Tọa độ Y")
    ground_level: float = Field(default=0.0, description="Cao độ mặt đất (m)")
    
    # Thông số kỹ thuật
    depth: float = Field(..., gt=0, le=500, description="Chiều sâu (m)")
    casing_diameter: float = Field(default=150, gt=50, description="Đường kính ống chống (mm)")
    screen_length: Optional[float] = Field(None, gt=0, description="Chiều dài lọc (m)")
    screen_slot_size: Optional[float] = Field(None, description="Kích thước khe lọc (mm)")
    
    # Máy bơm (cho giếng khai thác)
    pump_type: Optional[PumpType] = Field(None, description="Loại máy bơm")
    pump_capacity: Optional[float] = Field(None, gt=0, description="Công suất bơm (m³/h)")
    pump_depth: Optional[float] = Field(None, description="Độ sâu đặt bơm (m)")
    
    # Thông số địa chất
    aquifer_top: Optional[float] = Field(None, description="Cao độ đỉnh tầng chứa nước (m)")
    aquifer_bottom: Optional[float] = Field(None, description="Cao độ đáy tầng chứa nước (m)")
    static_water_level: Optional[float] = Field(None, description="Mực nước tĩnh (m)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "GQ-01",
                "well_type": "monitoring",
                "x": 106.123,
                "y": 10.456,
                "ground_level": 5.0,
                "depth": 30,
                "casing_diameter": 110,
                "screen_length": 6
            }
        }

class WellCalculationResult(BaseModel):
    """Kết quả tính toán giếng"""
    
    total_depth: float = Field(..., description="Chiều sâu tổng (m)")
    casing_length: float = Field(..., description="Chiều dài ống chống (m)")
    screen_length: float = Field(..., description="Chiều dài lọc (m)")
    gravel_pack_volume: float = Field(..., description="Thể tích sỏi lọc (m³)")
    cement_volume: float = Field(..., description="Thể tích xi măng (m³)")
    
    # Cho giếng khai thác
    safe_yield: Optional[float] = Field(None, description="Lưu lượng an toàn (m³/h)")
    drawdown: Optional[float] = Field(None, description="Độ hạ mực nước (m)")
    specific_capacity: Optional[float] = Field(None, description="Tỷ lưu lượng (m³/h/m)")

class WellOutput(BaseModel):
    """Schema đầu ra cho thiết kế giếng"""
    
    id: int
    name: str
    well_type: WellType
    calculation: WellCalculationResult
    validation_results: List['ValidationResult']
    warnings: List[str] = []
    created_at: datetime

class WellDesignResult(BaseModel):
    """Kết quả thiết kế giếng hoàn chỉnh"""
    
    job_id: str
    status: str
    well: WellOutput
    files: Dict[str, str] = {}
    report_url: Optional[str] = None

# ==================== COMMON SCHEMAS ====================

class ValidationResult(BaseModel):
    """Kết quả validation"""
    
    parameter: str = Field(..., description="Thông số kiểm tra")
    value: Any = Field(..., description="Giá trị")
    status: str = Field(..., description="Trạng thái: pass/warning/fail")
    message: str = Field(..., description="Thông báo")
    standard: Optional[str] = Field(None, description="Tiêu chuẩn tham chiếu")

class JobResponse(BaseModel):
    """Phản hồi công việc"""
    
    job_id: str = Field(..., description="ID công việc")
    status: str = Field(..., description="Trạng thái")
    message: str = Field(..., description="Thông báo")
    progress: Optional[int] = Field(None, ge=0, le=100, description="Tiến độ (%)")
    result_url: Optional[str] = Field(None, description="URL kết quả")
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "JOB-20260204-001",
                "status": "processing",
                "message": "Đang tính toán thiết kế...",
                "progress": 45,
                "created_at": "2026-02-04T10:30:00"
            }
        }

class CalculationReport(BaseModel):
    """Báo cáo tính toán"""
    
    job_id: str
    project_name: str
    design_type: str
    
    # Thông số đầu vào
    input_parameters: Dict[str, Any]
    
    # Kết quả tính toán
    calculations: List[Dict[str, Any]]
    
    # Kiểm tra tiêu chuẩn
    validation_results: List[ValidationResult]
    
    # Cảnh báo
    warnings: List[str]
    
    # File đính kèm
    attachments: List[str] = []
    
    # Thời gian
    generated_at: datetime = Field(default_factory=datetime.now)

# Update forward references
TankOutput.model_rebuild()
PipelineOutput.model_rebuild()
WellOutput.model_rebuild()
