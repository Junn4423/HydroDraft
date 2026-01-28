"""
Safety Enforcement Layer - Lớp kiểm soát an toàn

SPRINT 2: TRANSPARENT ENGINEERING
Chặn xuất bản vẽ/báo cáo khi có vi phạm nghiêm trọng
Yêu cầu ghi nhận lý do khi override

Chức năng:
1. Phát hiện vi phạm tự động
2. Chặn export khi có vi phạm CRITICAL
3. Yêu cầu justification khi override
4. Ghi nhận tất cả override vào log
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum

from calculations.calculation_log import (
    CalculationLog, Violation, ViolationSeverity,
    CalculationStatus
)


class ExportBlockReason(str, Enum):
    """Lý do chặn xuất"""
    CRITICAL_VIOLATION = "critical_violation"
    MISSING_DATA = "missing_data"
    CALCULATION_ERROR = "calculation_error"
    UNRESOLVED_WARNINGS = "unresolved_warnings"
    OVERRIDE_REQUIRED = "override_required"


@dataclass
class OverrideRecord:
    """Bản ghi override vi phạm"""
    
    override_id: str
    violation_id: str
    parameter: str
    
    # Giá trị
    actual_value: Any
    limit_value: Any
    
    # Thông tin override
    reason: str                     # Lý do override (bắt buộc)
    engineer_id: str                # ID kỹ sư override
    engineer_name: str              # Tên kỹ sư
    
    # Tham chiếu
    reference_doc: Optional[str]    # Tài liệu tham chiếu (nếu có)
    approval_level: str             # Cấp phê duyệt
    
    # Thời gian
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "override_id": self.override_id,
            "violation_id": self.violation_id,
            "parameter": self.parameter,
            "actual_value": self.actual_value,
            "limit_value": self.limit_value,
            "reason": self.reason,
            "engineer_id": self.engineer_id,
            "engineer_name": self.engineer_name,
            "reference_doc": self.reference_doc,
            "approval_level": self.approval_level,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SafetyCheckResult:
    """Kết quả kiểm tra an toàn"""
    
    can_export: bool
    block_reasons: List[str]
    
    total_violations: int
    critical_violations: int
    major_violations: int
    minor_violations: int
    
    overridden_count: int
    pending_override: int
    
    violations: List[Violation]
    override_records: List[OverrideRecord]
    
    def to_dict(self) -> Dict:
        return {
            "can_export": self.can_export,
            "block_reasons": self.block_reasons,
            "total_violations": self.total_violations,
            "critical_violations": self.critical_violations,
            "major_violations": self.major_violations,
            "minor_violations": self.minor_violations,
            "overridden_count": self.overridden_count,
            "pending_override": self.pending_override,
            "violations": [v.to_dict() for v in self.violations],
            "override_records": [o.to_dict() for o in self.override_records]
        }


class SafetyEnforcementLayer:
    """
    Lớp kiểm soát an toàn
    
    Chức năng:
    - Kiểm tra vi phạm từ CalculationLog
    - Chặn export khi có CRITICAL violation
    - Quản lý override với justification
    - Lưu trữ và truy xuất override history
    """
    
    # Các vi phạm yêu cầu override bắt buộc
    REQUIRED_OVERRIDE_VIOLATIONS = {
        "velocity_min",
        "velocity_max",
        "uplift_safety",
        "wall_thickness_min",
        "retention_time_min",
        "surface_loading_max",
        "crack_width_max",
        "safety_factor_min"
    }
    
    # Cấp phê duyệt theo mức độ vi phạm
    APPROVAL_LEVELS = {
        ViolationSeverity.INFO: "engineer",
        ViolationSeverity.MINOR: "engineer",
        ViolationSeverity.MAJOR: "senior_engineer",
        ViolationSeverity.CRITICAL: "chief_engineer"
    }
    
    def __init__(self):
        self._override_history: Dict[str, List[OverrideRecord]] = {}
        self._pending_overrides: Dict[str, Violation] = {}
    
    def check_calculation_log(
        self,
        calc_log: CalculationLog
    ) -> SafetyCheckResult:
        """
        Kiểm tra CalculationLog và xác định có thể export không
        
        Args:
            calc_log: CalculationLog cần kiểm tra
            
        Returns:
            SafetyCheckResult
        """
        violations = calc_log.violations
        
        # Đếm vi phạm theo mức độ
        critical = [v for v in violations if v.severity == ViolationSeverity.CRITICAL and not v.is_overridden]
        major = [v for v in violations if v.severity == ViolationSeverity.MAJOR and not v.is_overridden]
        minor = [v for v in violations if v.severity == ViolationSeverity.MINOR and not v.is_overridden]
        info = [v for v in violations if v.severity == ViolationSeverity.INFO]
        
        overridden = [v for v in violations if v.is_overridden]
        pending = [v for v in violations if not v.is_overridden and v.severity in [ViolationSeverity.CRITICAL, ViolationSeverity.MAJOR]]
        
        # Xác định có thể export
        can_export = len(critical) == 0
        
        block_reasons = []
        if critical:
            block_reasons.append(f"Có {len(critical)} vi phạm nghiêm trọng chưa được override")
            for v in critical:
                block_reasons.append(f"  - {v.message}")
        
        # Lấy override records
        override_records = self._override_history.get(calc_log.log_id, [])
        
        return SafetyCheckResult(
            can_export=can_export,
            block_reasons=block_reasons,
            total_violations=len(violations),
            critical_violations=len(critical),
            major_violations=len(major),
            minor_violations=len(minor),
            overridden_count=len(overridden),
            pending_override=len(pending),
            violations=violations,
            override_records=override_records
        )
    
    def request_override(
        self,
        calc_log: CalculationLog,
        violation_id: str,
        reason: str,
        engineer_id: str,
        engineer_name: str,
        reference_doc: str = None
    ) -> Tuple[bool, str]:
        """
        Yêu cầu override vi phạm
        
        Args:
            calc_log: CalculationLog chứa vi phạm
            violation_id: ID của vi phạm cần override
            reason: Lý do override (bắt buộc, tối thiểu 50 ký tự)
            engineer_id: ID kỹ sư
            engineer_name: Tên kỹ sư
            reference_doc: Tài liệu tham chiếu (nếu có)
            
        Returns:
            (success, message)
        """
        # Tìm vi phạm
        violation = None
        for v in calc_log.violations:
            if v.violation_id == violation_id:
                violation = v
                break
        
        if violation is None:
            return False, f"Không tìm thấy vi phạm với ID: {violation_id}"
        
        # Kiểm tra lý do
        if len(reason.strip()) < 50:
            return False, "Lý do override phải có ít nhất 50 ký tự để đảm bảo giải trình đầy đủ"
        
        # Xác định cấp phê duyệt
        approval_level = self.APPROVAL_LEVELS.get(violation.severity, "engineer")
        
        # Tạo override record
        override_record = OverrideRecord(
            override_id=str(uuid.uuid4())[:8],
            violation_id=violation_id,
            parameter=violation.parameter,
            actual_value=violation.actual_value,
            limit_value=violation.limit_value,
            reason=reason,
            engineer_id=engineer_id,
            engineer_name=engineer_name,
            reference_doc=reference_doc,
            approval_level=approval_level
        )
        
        # Cập nhật violation
        violation.is_overridden = True
        violation.override_reason = reason
        violation.override_by = engineer_name
        violation.override_timestamp = override_record.timestamp
        
        # Lưu override record
        if calc_log.log_id not in self._override_history:
            self._override_history[calc_log.log_id] = []
        self._override_history[calc_log.log_id].append(override_record)
        
        # Cập nhật trạng thái log
        self._update_log_status(calc_log)
        
        return True, f"Đã override vi phạm {violation_id}. Cấp phê duyệt: {approval_level}"
    
    def _update_log_status(self, calc_log: CalculationLog):
        """Cập nhật trạng thái log sau khi override"""
        
        # Kiểm tra còn vi phạm critical nào chưa override không
        critical_pending = [
            v for v in calc_log.violations 
            if v.severity == ViolationSeverity.CRITICAL and not v.is_overridden
        ]
        
        calc_log.can_export = len(critical_pending) == 0
        
        if len(critical_pending) == 0:
            # Kiểm tra có warning không
            has_warnings = any(
                v.severity in [ViolationSeverity.MAJOR, ViolationSeverity.MINOR]
                and not v.is_overridden
                for v in calc_log.violations
            )
            
            if has_warnings:
                calc_log.overall_status = CalculationStatus.WARNING
            else:
                calc_log.overall_status = CalculationStatus.SUCCESS
    
    def get_override_history(self, log_id: str) -> List[OverrideRecord]:
        """Lấy lịch sử override của một log"""
        return self._override_history.get(log_id, [])
    
    def generate_override_report(self, calc_log: CalculationLog) -> str:
        """
        Tạo báo cáo override để đính kèm vào hồ sơ
        
        Args:
            calc_log: CalculationLog
            
        Returns:
            Báo cáo dạng text
        """
        overrides = self._override_history.get(calc_log.log_id, [])
        
        if not overrides:
            return "Không có vi phạm nào được override."
        
        lines = [
            "=" * 80,
            "BÁO CÁO OVERRIDE VI PHẠM TIÊU CHUẨN",
            f"Log ID: {calc_log.log_id}",
            f"Module: {calc_log.module_name}",
            f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            ""
        ]
        
        for i, override in enumerate(overrides, 1):
            lines.extend([
                f"{i}. Vi phạm: {override.violation_id}",
                f"   Thông số: {override.parameter}",
                f"   Giá trị thực tế: {override.actual_value}",
                f"   Giá trị giới hạn: {override.limit_value}",
                f"   ",
                f"   LÝ DO OVERRIDE:",
                f"   {override.reason}",
                f"   ",
                f"   Kỹ sư: {override.engineer_name} ({override.engineer_id})",
                f"   Cấp phê duyệt: {override.approval_level}",
                f"   Thời gian: {override.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                f"   Tài liệu tham chiếu: {override.reference_doc or 'Không có'}",
                "-" * 80
            ])
        
        lines.extend([
            "",
            f"Tổng số override: {len(overrides)}",
            "",
            "Chữ ký kỹ sư phụ trách: ___________________",
            "",
            "Chữ ký phê duyệt: ___________________",
            "=" * 80
        ])
        
        return "\n".join(lines)


# ==================== VALIDATORS ====================

class DesignValidator:
    """
    Validators cho các loại thiết kế
    """
    
    @staticmethod
    def validate_tank_design(
        design_result: Dict[str, Any],
        tank_type: str
    ) -> List[Violation]:
        """
        Validate thiết kế bể
        
        Returns:
            List các vi phạm phát hiện được
        """
        from calculations.calculation_log import CalculationLogger
        
        violations = []
        
        # Giới hạn theo loại bể
        limits = {
            "sedimentation": {
                "retention_time": {"min": 1.5, "max": 4.0, "unit": "h"},
                "surface_loading": {"min": 20, "max": 60, "unit": "m³/m².d"},
                "velocity": {"max": 0.025, "unit": "m/s"},
                "depth": {"min": 2.5, "max": 5.0, "unit": "m"}
            },
            "storage": {
                "retention_time": {"min": 4.0, "max": 24.0, "unit": "h"},
                "depth": {"min": 2.0, "max": 6.0, "unit": "m"}
            },
            "aeration": {
                "retention_time": {"min": 4.0, "max": 12.0, "unit": "h"},
                "depth": {"min": 3.0, "max": 6.0, "unit": "m"}
            }
        }
        
        tank_limits = limits.get(tank_type, limits["storage"])
        
        # Kiểm tra thời gian lưu
        if "retention_time" in design_result and "retention_time" in tank_limits:
            rt = design_result["retention_time"]
            rt_limits = tank_limits["retention_time"]
            
            if rt < rt_limits["min"]:
                violations.append(CalculationLogger.create_violation(
                    violation_id="retention_time_min",
                    parameter="retention_time",
                    actual_value=rt,
                    limit_value=rt_limits["min"],
                    limit_type="min",
                    severity=ViolationSeverity.MAJOR,
                    standard="TCVN 7957:2008",
                    clause="Bảng 7.2",
                    message=f"Thời gian lưu {rt:.1f}h < tối thiểu {rt_limits['min']}h",
                    suggestion=f"Tăng thể tích bể hoặc giảm lưu lượng để đạt thời gian lưu ≥ {rt_limits['min']}h"
                ))
            
            if rt > rt_limits["max"]:
                violations.append(CalculationLogger.create_violation(
                    violation_id="retention_time_max",
                    parameter="retention_time",
                    actual_value=rt,
                    limit_value=rt_limits["max"],
                    limit_type="max",
                    severity=ViolationSeverity.MINOR,
                    standard="TCVN 7957:2008",
                    clause="Bảng 7.2",
                    message=f"Thời gian lưu {rt:.1f}h > khuyến nghị {rt_limits['max']}h",
                    suggestion=f"Xem xét giảm thể tích bể để tiết kiệm chi phí"
                ))
        
        # Kiểm tra tải trọng bề mặt
        if "surface_loading" in design_result and "surface_loading" in tank_limits:
            sl = design_result["surface_loading"]
            sl_limits = tank_limits["surface_loading"]
            
            if sl > sl_limits["max"]:
                violations.append(CalculationLogger.create_violation(
                    violation_id="surface_loading_max",
                    parameter="surface_loading",
                    actual_value=sl,
                    limit_value=sl_limits["max"],
                    limit_type="max",
                    severity=ViolationSeverity.CRITICAL,
                    standard="TCVN 7957:2008",
                    clause="Bảng 7.2",
                    message=f"Tải trọng bề mặt {sl:.1f} m³/m².d > tối đa {sl_limits['max']} m³/m².d",
                    suggestion="Tăng diện tích bể hoặc thêm số lượng bể"
                ))
        
        # Kiểm tra vận tốc ngang
        if "horizontal_velocity" in design_result and "velocity" in tank_limits:
            v = design_result["horizontal_velocity"]
            v_limit = tank_limits["velocity"]["max"]
            
            if v > v_limit:
                violations.append(CalculationLogger.create_violation(
                    violation_id="velocity_max",
                    parameter="horizontal_velocity",
                    actual_value=v,
                    limit_value=v_limit,
                    limit_type="max",
                    severity=ViolationSeverity.MAJOR,
                    standard="TCVN 7957:2008",
                    clause="Điều 7.3.5",
                    message=f"Vận tốc ngang {v:.4f} m/s > tối đa {v_limit} m/s",
                    suggestion="Tăng chiều rộng bể hoặc giảm lưu lượng mỗi bể"
                ))
        
        return violations
    
    @staticmethod
    def validate_pipe_design(
        design_result: Dict[str, Any],
        pipe_type: str = "gravity"
    ) -> List[Violation]:
        """
        Validate thiết kế đường ống
        """
        from calculations.calculation_log import CalculationLogger
        
        violations = []
        
        # Giới hạn theo TCVN 7957:2008
        if pipe_type == "gravity":
            v_min = 0.7
            v_max = 4.0
            fill_max = 0.8
        else:
            v_min = 0.5
            v_max = 2.5
            fill_max = 1.0
        
        # Kiểm tra vận tốc
        if "velocity" in design_result:
            v = design_result["velocity"]
            
            if v < v_min:
                violations.append(CalculationLogger.create_violation(
                    violation_id="pipe_velocity_min",
                    parameter="velocity",
                    actual_value=v,
                    limit_value=v_min,
                    limit_type="min",
                    severity=ViolationSeverity.MAJOR,
                    standard="TCVN 7957:2008",
                    clause="Điều 5.3.4",
                    message=f"Vận tốc {v:.2f} m/s < tự làm sạch {v_min} m/s",
                    suggestion="Tăng độ dốc hoặc giảm đường kính ống"
                ))
            
            if v > v_max:
                violations.append(CalculationLogger.create_violation(
                    violation_id="pipe_velocity_max",
                    parameter="velocity",
                    actual_value=v,
                    limit_value=v_max,
                    limit_type="max",
                    severity=ViolationSeverity.MAJOR,
                    standard="TCVN 7957:2008",
                    clause="Điều 5.3.5",
                    message=f"Vận tốc {v:.2f} m/s > tối đa {v_max} m/s (mài mòn)",
                    suggestion="Giảm độ dốc hoặc tăng đường kính ống"
                ))
        
        # Kiểm tra độ đầy
        if "fill_ratio" in design_result:
            fill = design_result["fill_ratio"]
            
            if fill > fill_max:
                violations.append(CalculationLogger.create_violation(
                    violation_id="fill_ratio_max",
                    parameter="fill_ratio",
                    actual_value=fill,
                    limit_value=fill_max,
                    limit_type="max",
                    severity=ViolationSeverity.CRITICAL,
                    standard="TCVN 7957:2008",
                    clause="Điều 5.3.2",
                    message=f"Độ đầy {fill:.2f} > tối đa {fill_max}",
                    suggestion="Tăng đường kính ống để giảm độ đầy"
                ))
        
        return violations


# Singleton instance
_safety_layer = None

def get_safety_layer() -> SafetyEnforcementLayer:
    """Lấy singleton instance của SafetyEnforcementLayer"""
    global _safety_layer
    if _safety_layer is None:
        _safety_layer = SafetyEnforcementLayer()
    return _safety_layer


# Import compatibility
from typing import Tuple
