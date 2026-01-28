"""
Database Models - Mô hình dữ liệu HydroDraft
SQLite compatible với versioning support
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship, DeclarativeBase
from datetime import datetime
import enum


class Base(DeclarativeBase):
    """Base class cho models"""
    pass


class JobStatus(str, enum.Enum):
    """Trạng thái công việc"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TankType(str, enum.Enum):
    """Loại bể"""
    SEDIMENTATION = "sedimentation"
    FILTRATION = "filtration"
    STORAGE = "storage"
    BUFFER = "buffer"
    AERATION = "aeration"
    DISINFECTION = "disinfection"


class MaterialType(str, enum.Enum):
    """Loại vật liệu"""
    CONCRETE = "concrete"
    STEEL = "steel"
    HDPE = "hdpe"
    PVC = "pvc"
    STAINLESS = "stainless"
    COMPOSITE = "composite"


# ============== CORE MODELS ==============

class Project(Base):
    """Mô hình Dự án"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    location = Column(String(500))
    client = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    jobs = relationship("DesignJob", back_populates="project", cascade="all, delete-orphan")
    tanks = relationship("Tank", back_populates="project", cascade="all, delete-orphan")
    pipelines = relationship("Pipeline", back_populates="project", cascade="all, delete-orphan")
    wells = relationship("Well", back_populates="project", cascade="all, delete-orphan")
    versions = relationship("DesignVersion", back_populates="project", cascade="all, delete-orphan")


class DesignJob(Base):
    """Mô hình Công việc thiết kế"""
    __tablename__ = "design_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), unique=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"))
    job_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    input_params = Column(JSON)
    calculation_results = Column(JSON)
    output_files = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    project = relationship("Project", back_populates="jobs")


class Tank(Base):
    """Mô hình Bể"""
    __tablename__ = "tanks"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String(255), nullable=False)
    tank_type = Column(String(50), nullable=False)
    
    # Kích thước
    length = Column(Float)
    width = Column(Float)
    depth = Column(Float)
    wall_thickness = Column(Float, default=0.3)
    
    # Thông số kỹ thuật
    design_flow = Column(Float)
    inlet_diameter = Column(Float)
    outlet_diameter = Column(Float)
    foundation_level = Column(Float)
    
    # Vật liệu
    material = Column(String(50), default="concrete")
    
    # Kết quả tính toán
    volume = Column(Float)
    retention_time = Column(Float)
    surface_loading = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="tanks")


class Pipeline(Base):
    """Mô hình Đường ống"""
    __tablename__ = "pipelines"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String(255), nullable=False)
    
    # Điểm đầu và cuối
    start_x = Column(Float)
    start_y = Column(Float)
    start_z = Column(Float)
    end_x = Column(Float)
    end_y = Column(Float)
    end_z = Column(Float)
    
    # Thông số kỹ thuật
    diameter = Column(Float, nullable=False)
    slope = Column(Float)
    material = Column(String(50), default="hdpe")
    roughness = Column(Float, default=0.013)
    cover_depth = Column(Float, default=0.8)
    
    # Kết quả tính toán
    length = Column(Float)
    velocity = Column(Float)
    flow_capacity = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="pipelines")


class Well(Base):
    """Mô hình Giếng"""
    __tablename__ = "wells"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String(255), nullable=False)
    well_type = Column(String(50))
    
    # Vị trí
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    ground_level = Column(Float)
    
    # Thông số kỹ thuật
    depth = Column(Float, nullable=False)
    casing_diameter = Column(Float)
    screen_length = Column(Float)
    pump_type = Column(String(100))
    pump_capacity = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="wells")


# ============== VERSIONING MODELS ==============

class DesignVersion(Base):
    """Mô hình Phiên bản thiết kế - Engineering Version Control"""
    __tablename__ = "design_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(String(50), unique=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"))
    
    # Thông tin version
    version_number = Column(Integer, nullable=False)
    version_tag = Column(String(50))  # e.g., "v1.0", "draft", "final"
    description = Column(Text)
    
    # Snapshot data
    input_snapshot = Column(JSON, nullable=False)  # Tất cả input parameters
    ruleset_snapshot = Column(JSON)  # Rules được áp dụng
    calculation_log = Column(JSON)  # Chi tiết tính toán
    output_metadata = Column(JSON)  # Thông tin output files
    
    # Audit trail
    created_by = Column(String(100), default="system")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Trạng thái
    is_current = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    
    # Override tracking
    has_overrides = Column(Boolean, default=False)
    override_reasons = Column(JSON)  # Danh sách các override và lý do
    
    project = relationship("Project", back_populates="versions")


# ============== TEMPLATE & RULES MODELS ==============

class Template(Base):
    """Mô hình Template thiết kế"""
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    version = Column(String(20), default="1.0")
    description = Column(Text)
    data = Column(JSON, nullable=False)  # Full template data
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Rule(Base):
    """Mô hình Quy tắc thiết kế"""
    __tablename__ = "rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    version = Column(String(20), default="1.0.0")
    description = Column(Text)
    data = Column(JSON, nullable=False)  # Full rule data
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============== SYSTEM MODELS ==============

class SystemConfig(Base):
    """Cấu hình hệ thống"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
