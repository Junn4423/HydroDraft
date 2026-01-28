"""
Calculation Log System - Hệ thống ghi nhận tính toán kỹ thuật

SPRINT 2: TRANSPARENT ENGINEERING
Biến mọi tính toán từ Black Box → White Box

Mọi kết quả phải:
- Có công thức LaTeX
- Có giá trị đầu vào
- Có tham chiếu tiêu chuẩn
- Có mô tả rõ ràng
- Có điều kiện áp dụng
- Có kết quả cuối cùng
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from datetime import datetime
import math


class CalculationStatus(str, Enum):
    """Trạng thái tính toán"""
    SUCCESS = "success"              # Tính toán thành công
    WARNING = "warning"              # Cảnh báo (vượt khuyến nghị)
    VIOLATION = "violation"          # Vi phạm tiêu chuẩn
    ERROR = "error"                  # Lỗi tính toán
    OVERRIDDEN = "overridden"        # Đã được override bởi kỹ sư


class ViolationSeverity(str, Enum):
    """Mức độ nghiêm trọng của vi phạm"""
    INFO = "info"                    # Thông tin
    MINOR = "minor"                  # Vi phạm nhỏ
    MAJOR = "major"                  # Vi phạm lớn
    CRITICAL = "critical"            # Vi phạm nghiêm trọng - chặn xuất


@dataclass
class CalculationStep:
    """
    Một bước tính toán đơn lẻ
    
    Theo yêu cầu Sprint 2:
    - formula_latex: Công thức LaTeX
    - inputs: Giá trị đầu vào
    - reference: Tham chiếu tiêu chuẩn
    - description: Mô tả bằng ngôn ngữ tự nhiên
    - conditions: Điều kiện áp dụng, cảnh báo
    - result: Kết quả tính toán
    """
    
    # Thông tin cơ bản
    step_id: str                     # ID bước tính toán
    name: str                        # Tên bước
    description: str                 # Mô tả chi tiết
    
    # Công thức và tham chiếu
    formula_latex: str               # Công thức LaTeX
    formula_text: str                # Công thức dạng text (backup)
    reference: str                   # Tham chiếu tiêu chuẩn (TCVN, ISO, etc.)
    
    # Dữ liệu đầu vào
    inputs: Dict[str, Any]           # {tên_biến: giá_trị}
    input_descriptions: Dict[str, str] = field(default_factory=dict)  # Mô tả các biến
    
    # Điều kiện và giới hạn
    conditions: List[str] = field(default_factory=list)  # Điều kiện áp dụng
    assumptions: List[str] = field(default_factory=list)  # Giả định
    limits: Dict[str, Any] = field(default_factory=dict)  # Giới hạn {min, max, unit}
    
    # Kết quả
    result: Any = None               # Giá trị kết quả
    result_unit: str = ""            # Đơn vị
    result_formatted: str = ""       # Kết quả đã format
    
    # Trạng thái
    status: CalculationStatus = CalculationStatus.SUCCESS
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Chuyển đổi thành dict"""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "description": self.description,
            "formula_latex": self.formula_latex,
            "formula_text": self.formula_text,
            "reference": self.reference,
            "inputs": self.inputs,
            "input_descriptions": self.input_descriptions,
            "conditions": self.conditions,
            "assumptions": self.assumptions,
            "limits": self.limits,
            "result": self.result,
            "result_unit": self.result_unit,
            "result_formatted": self.result_formatted,
            "status": self.status.value,
            "warnings": self.warnings,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Violation:
    """Vi phạm tiêu chuẩn"""
    
    violation_id: str                # ID vi phạm
    parameter: str                   # Thông số vi phạm
    actual_value: Any                # Giá trị thực tế
    limit_value: Any                 # Giá trị giới hạn
    limit_type: str                  # "min", "max", "range", "exact"
    severity: ViolationSeverity      # Mức độ nghiêm trọng
    
    standard: str                    # Tiêu chuẩn viện dẫn
    clause: str                      # Điều khoản
    message: str                     # Thông báo
    suggestion: str                  # Đề xuất khắc phục
    
    # Override
    is_overridden: bool = False
    override_reason: str = ""
    override_by: str = ""
    override_timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "violation_id": self.violation_id,
            "parameter": self.parameter,
            "actual_value": self.actual_value,
            "limit_value": self.limit_value,
            "limit_type": self.limit_type,
            "severity": self.severity.value,
            "standard": self.standard,
            "clause": self.clause,
            "message": self.message,
            "suggestion": self.suggestion,
            "is_overridden": self.is_overridden,
            "override_reason": self.override_reason,
            "override_by": self.override_by,
            "override_timestamp": self.override_timestamp.isoformat() if self.override_timestamp else None
        }


@dataclass
class CalculationLog:
    """
    Log tính toán hoàn chỉnh cho một module
    
    Chứa tất cả các bước tính toán, vi phạm, và metadata
    để có thể truy xuất và kiểm toán
    """
    
    # Thông tin chung
    log_id: str                      # ID duy nhất
    calculation_type: str            # Loại tính toán (hydraulic, structural, tank, etc.)
    module_name: str                 # Tên module
    description: str                 # Mô tả tổng quan
    
    # Các bước tính toán
    steps: List[CalculationStep] = field(default_factory=list)
    
    # Vi phạm
    violations: List[Violation] = field(default_factory=list)
    
    # Kết quả tổng hợp
    final_results: Dict[str, Any] = field(default_factory=dict)
    
    # Trạng thái tổng thể
    overall_status: CalculationStatus = CalculationStatus.SUCCESS
    can_export: bool = True          # Có thể xuất bản vẽ/báo cáo
    
    # Tiêu chuẩn áp dụng
    standards_applied: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    calculation_time_ms: float = 0   # Thời gian tính toán (ms)
    user_id: Optional[str] = None
    
    def add_step(self, step: CalculationStep):
        """Thêm bước tính toán"""
        self.steps.append(step)
        
        # Cập nhật trạng thái tổng thể
        if step.status == CalculationStatus.VIOLATION:
            self.overall_status = CalculationStatus.VIOLATION
        elif step.status == CalculationStatus.WARNING and self.overall_status == CalculationStatus.SUCCESS:
            self.overall_status = CalculationStatus.WARNING
        elif step.status == CalculationStatus.ERROR:
            self.overall_status = CalculationStatus.ERROR
    
    def add_violation(self, violation: Violation):
        """Thêm vi phạm"""
        self.violations.append(violation)
        
        # Chặn xuất nếu vi phạm nghiêm trọng và chưa được override
        if violation.severity == ViolationSeverity.CRITICAL and not violation.is_overridden:
            self.can_export = False
            self.overall_status = CalculationStatus.VIOLATION
    
    def get_summary(self) -> Dict:
        """Tóm tắt log"""
        return {
            "log_id": self.log_id,
            "calculation_type": self.calculation_type,
            "module_name": self.module_name,
            "total_steps": len(self.steps),
            "total_violations": len(self.violations),
            "critical_violations": len([v for v in self.violations if v.severity == ViolationSeverity.CRITICAL and not v.is_overridden]),
            "overall_status": self.overall_status.value,
            "can_export": self.can_export,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_dict(self) -> Dict:
        """Chuyển đổi thành dict đầy đủ"""
        return {
            "log_id": self.log_id,
            "calculation_type": self.calculation_type,
            "module_name": self.module_name,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
            "violations": [v.to_dict() for v in self.violations],
            "final_results": self.final_results,
            "overall_status": self.overall_status.value,
            "can_export": self.can_export,
            "standards_applied": self.standards_applied,
            "timestamp": self.timestamp.isoformat(),
            "calculation_time_ms": self.calculation_time_ms,
            "user_id": self.user_id
        }
    
    def to_report_format(self) -> str:
        """
        Xuất định dạng báo cáo kỹ thuật
        Có thể in ra PDF hoặc nhúng vào báo cáo
        """
        lines = []
        lines.append(f"=" * 80)
        lines.append(f"BÁO CÁO TÍNH TOÁN KỸ THUẬT")
        lines.append(f"Module: {self.module_name}")
        lines.append(f"Mô tả: {self.description}")
        lines.append(f"Thời gian: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"=" * 80)
        lines.append("")
        
        # Tiêu chuẩn áp dụng
        if self.standards_applied:
            lines.append("TIÊU CHUẨN ÁP DỤNG:")
            for std in self.standards_applied:
                lines.append(f"  • {std}")
            lines.append("")
        
        # Các bước tính toán
        lines.append("CÁC BƯỚC TÍNH TOÁN:")
        lines.append("-" * 80)
        
        for i, step in enumerate(self.steps, 1):
            lines.append(f"\n{i}. {step.name}")
            lines.append(f"   Mô tả: {step.description}")
            lines.append(f"   Công thức: {step.formula_text}")
            lines.append(f"   Tham chiếu: {step.reference}")
            lines.append(f"   Đầu vào:")
            for key, value in step.inputs.items():
                desc = step.input_descriptions.get(key, "")
                lines.append(f"      {key} = {value} {desc}")
            lines.append(f"   Kết quả: {step.result_formatted}")
            
            if step.conditions:
                lines.append(f"   Điều kiện:")
                for cond in step.conditions:
                    lines.append(f"      • {cond}")
            
            if step.warnings:
                lines.append(f"   ⚠ Cảnh báo:")
                for warn in step.warnings:
                    lines.append(f"      • {warn}")
        
        # Vi phạm
        if self.violations:
            lines.append("")
            lines.append("=" * 80)
            lines.append("DANH SÁCH VI PHẠM:")
            lines.append("-" * 80)
            
            for v in self.violations:
                status = "✓ Đã override" if v.is_overridden else "✗ Chưa xử lý"
                lines.append(f"\n[{v.severity.value.upper()}] {v.message}")
                lines.append(f"   Thông số: {v.parameter} = {v.actual_value}")
                lines.append(f"   Giới hạn: {v.limit_type} {v.limit_value}")
                lines.append(f"   Tiêu chuẩn: {v.standard} - {v.clause}")
                lines.append(f"   Đề xuất: {v.suggestion}")
                lines.append(f"   Trạng thái: {status}")
                if v.is_overridden:
                    lines.append(f"   Lý do override: {v.override_reason}")
        
        # Kết quả cuối cùng
        lines.append("")
        lines.append("=" * 80)
        lines.append("KẾT QUẢ TỔNG HỢP:")
        lines.append("-" * 80)
        for key, value in self.final_results.items():
            lines.append(f"   {key}: {value}")
        
        lines.append("")
        lines.append(f"Trạng thái: {self.overall_status.value.upper()}")
        lines.append(f"Có thể xuất bản vẽ: {'CÓ' if self.can_export else 'KHÔNG'}")
        lines.append("=" * 80)
        
        return "\n".join(lines)


class CalculationLogger:
    """
    Factory class để tạo và quản lý CalculationLog
    """
    
    _instance = None
    _current_log: Optional[CalculationLog] = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def create_log(
        cls,
        log_id: str,
        calculation_type: str,
        module_name: str,
        description: str,
        standards: List[str] = None
    ) -> CalculationLog:
        """Tạo log mới"""
        log = CalculationLog(
            log_id=log_id,
            calculation_type=calculation_type,
            module_name=module_name,
            description=description,
            standards_applied=standards or []
        )
        return log
    
    @classmethod
    def create_step(
        cls,
        step_id: str,
        name: str,
        description: str,
        formula_latex: str,
        formula_text: str,
        reference: str,
        inputs: Dict[str, Any],
        result: Any,
        result_unit: str = "",
        input_descriptions: Dict[str, str] = None,
        conditions: List[str] = None,
        assumptions: List[str] = None,
        limits: Dict[str, Any] = None
    ) -> CalculationStep:
        """Tạo bước tính toán"""
        
        # Format kết quả
        if isinstance(result, float):
            result_formatted = f"{result:.4f} {result_unit}".strip()
        else:
            result_formatted = f"{result} {result_unit}".strip()
        
        step = CalculationStep(
            step_id=step_id,
            name=name,
            description=description,
            formula_latex=formula_latex,
            formula_text=formula_text,
            reference=reference,
            inputs=inputs,
            input_descriptions=input_descriptions or {},
            conditions=conditions or [],
            assumptions=assumptions or [],
            limits=limits or {},
            result=result,
            result_unit=result_unit,
            result_formatted=result_formatted
        )
        
        return step
    
    @classmethod
    def create_violation(
        cls,
        violation_id: str,
        parameter: str,
        actual_value: Any,
        limit_value: Any,
        limit_type: str,
        severity: ViolationSeverity,
        standard: str,
        clause: str,
        message: str,
        suggestion: str
    ) -> Violation:
        """Tạo vi phạm"""
        return Violation(
            violation_id=violation_id,
            parameter=parameter,
            actual_value=actual_value,
            limit_value=limit_value,
            limit_type=limit_type,
            severity=severity,
            standard=standard,
            clause=clause,
            message=message,
            suggestion=suggestion
        )


# ==================== ENGINEERING CONSTANTS ====================

class EngineeringConstants:
    """
    Hằng số kỹ thuật với tham chiếu
    """
    
    # Vật lý cơ bản
    GRAVITY = 9.80665  # m/s² - Gia tốc trọng trường tiêu chuẩn
    
    # Nước ở 20°C
    WATER_DENSITY = 998.2  # kg/m³
    WATER_KINEMATIC_VISCOSITY_20C = 1.004e-6  # m²/s
    WATER_DYNAMIC_VISCOSITY_20C = 1.002e-3  # Pa.s
    
    # Bảng độ nhớt động học theo nhiệt độ (m²/s)
    WATER_VISCOSITY_TABLE = {
        0: 1.787e-6,
        5: 1.519e-6,
        10: 1.307e-6,
        15: 1.139e-6,
        20: 1.004e-6,
        25: 0.893e-6,
        30: 0.801e-6,
        35: 0.727e-6,
        40: 0.658e-6
    }
    
    # Hệ số nhám Manning tiêu biểu
    MANNING_N = {
        "concrete_smooth": 0.012,
        "concrete_rough": 0.015,
        "steel": 0.011,
        "cast_iron": 0.013,
        "pvc": 0.009,
        "hdpe": 0.009,
        "ductile_iron": 0.012,
        "brick": 0.015,
        "earth_clean": 0.022,
        "earth_weedy": 0.030
    }
    
    # Hệ số Hazen-Williams
    HAZEN_WILLIAMS_C = {
        "pvc": 150,
        "hdpe": 150,
        "steel_new": 140,
        "steel_old": 100,
        "cast_iron_new": 130,
        "cast_iron_old": 80,
        "concrete": 120,
        "ductile_iron": 140
    }
    
    # Cường độ bê tông (MPa) - TCVN 5574:2018
    CONCRETE_STRENGTH = {
        "B15": {"Rb": 8.5, "Rbt": 0.75, "Eb": 23000},
        "B20": {"Rb": 11.5, "Rbt": 0.90, "Eb": 27500},
        "B25": {"Rb": 14.5, "Rbt": 1.05, "Eb": 30000},
        "B30": {"Rb": 17.0, "Rbt": 1.15, "Eb": 32500},
        "B35": {"Rb": 19.5, "Rbt": 1.25, "Eb": 34500},
        "B40": {"Rb": 22.0, "Rbt": 1.35, "Eb": 36000}
    }
    
    # Cường độ thép (MPa) - TCVN 5574:2018
    STEEL_STRENGTH = {
        "CB240-T": {"Rs": 210, "Rsc": 210, "Es": 200000},
        "CB300-V": {"Rs": 260, "Rsc": 260, "Es": 200000},
        "CB400-V": {"Rs": 350, "Rsc": 350, "Es": 200000},
        "CB500-V": {"Rs": 435, "Rsc": 400, "Es": 200000}
    }
    
    @classmethod
    def get_water_viscosity(cls, temperature: float) -> float:
        """
        Nội suy độ nhớt động học theo nhiệt độ
        
        Args:
            temperature: Nhiệt độ nước (°C)
            
        Returns:
            Độ nhớt động học (m²/s)
        """
        temps = sorted(cls.WATER_VISCOSITY_TABLE.keys())
        
        # Clamp temperature
        if temperature <= temps[0]:
            return cls.WATER_VISCOSITY_TABLE[temps[0]]
        if temperature >= temps[-1]:
            return cls.WATER_VISCOSITY_TABLE[temps[-1]]
        
        # Linear interpolation
        for i in range(len(temps) - 1):
            if temps[i] <= temperature <= temps[i + 1]:
                t1, t2 = temps[i], temps[i + 1]
                v1, v2 = cls.WATER_VISCOSITY_TABLE[t1], cls.WATER_VISCOSITY_TABLE[t2]
                return v1 + (v2 - v1) * (temperature - t1) / (t2 - t1)
        
        return cls.WATER_KINEMATIC_VISCOSITY_20C
