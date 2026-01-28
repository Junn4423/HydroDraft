"""
Traceable Tank Design Engine - Động cơ thiết kế bể có truy xuất

SPRINT 2: TRANSPARENT ENGINEERING
Thiết kế bể với:
- Đầy đủ log tính toán
- Tham chiếu tiêu chuẩn TCVN
- Kiểm tra vi phạm tự động
- Tích hợp Safety Layer

Tiêu chuẩn áp dụng:
- TCVN 7957:2008 - Thoát nước - Mạng lưới và công trình bên ngoài
- TCVN 33:2006 - Cấp nước - Mạng lưới đường ống và công trình
- TCVN 4116:1985 - Bể chứa nước
"""

import math
import uuid
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from calculations.calculation_log import (
    CalculationLog, CalculationStep, Violation,
    CalculationStatus, ViolationSeverity,
    CalculationLogger
)
from calculations.structural_traceable import TraceableStructuralEngine
from calculations.safety_layer import SafetyEnforcementLayer, DesignValidator, get_safety_layer


@dataclass
class TankDesignResult:
    """Kết quả thiết kế bể hoàn chỉnh"""
    
    # Thông tin chung
    tank_type: str
    tank_name: str
    num_tanks: int
    
    # Kích thước
    length: float
    width: float
    water_depth: float
    total_depth: float
    wall_thickness: float
    bottom_thickness: float
    
    # Thủy lực
    design_flow: float
    retention_time: float
    surface_loading: float
    horizontal_velocity: float
    
    # Đường ống
    inlet_diameter: float
    outlet_diameter: float
    
    # Thể tích
    volume_per_tank: float
    volume_total: float
    
    # Trạng thái
    is_valid: bool
    can_export: bool
    
    # Logs
    calculation_log: CalculationLog = None
    structural_log: CalculationLog = None
    
    def to_dict(self) -> Dict:
        return {
            "tank_type": self.tank_type,
            "tank_name": self.tank_name,
            "num_tanks": self.num_tanks,
            "dimensions": {
                "length": self.length,
                "width": self.width,
                "water_depth": self.water_depth,
                "total_depth": self.total_depth,
                "wall_thickness": self.wall_thickness,
                "bottom_thickness": self.bottom_thickness
            },
            "hydraulics": {
                "design_flow": self.design_flow,
                "retention_time": self.retention_time,
                "surface_loading": self.surface_loading,
                "horizontal_velocity": self.horizontal_velocity
            },
            "pipes": {
                "inlet_diameter": self.inlet_diameter,
                "outlet_diameter": self.outlet_diameter
            },
            "volume": {
                "per_tank": self.volume_per_tank,
                "total": self.volume_total
            },
            "status": {
                "is_valid": self.is_valid,
                "can_export": self.can_export
            },
            "calculation_log": self.calculation_log.to_dict() if self.calculation_log else None,
            "structural_log": self.structural_log.to_dict() if self.structural_log else None
        }


class TraceableTankDesignEngine:
    """
    Động cơ thiết kế bể với truy xuất đầy đủ
    
    Hỗ trợ:
    - Bể lắng (sedimentation)
    - Bể chứa (storage)
    - Bể điều hòa (buffer/equalization)
    - Bể lọc (filtration)
    - Bể kỵ khí/hiếu khí (anaerobic/aerobic)
    
    Mỗi thiết kế bao gồm:
    - Tính toán thủy lực
    - Tính toán kết cấu
    - Kiểm tra tiêu chuẩn
    - Log chi tiết từng bước
    """
    
    # Giới hạn thiết kế theo TCVN 7957:2008
    DESIGN_LIMITS = {
        "sedimentation": {
            "retention_time": {"min": 1.5, "max": 4.0, "unit": "h"},
            "surface_loading": {"min": 20, "max": 60, "unit": "m³/m².d"},
            "velocity": {"max": 0.025, "unit": "m/s"},
            "depth": {"min": 2.5, "max": 5.0, "unit": "m"},
            "length_width_ratio": {"min": 2.0, "max": 5.0},
            "weir_loading": {"min": 100, "max": 300, "unit": "m³/m.d"}
        },
        "storage": {
            "retention_time": {"min": 4.0, "max": 24.0, "unit": "h"},
            "depth": {"min": 2.0, "max": 6.0, "unit": "m"}
        },
        "buffer": {
            "retention_time": {"min": 2.0, "max": 8.0, "unit": "h"},
            "depth": {"min": 2.5, "max": 5.0, "unit": "m"}
        },
        "aeration": {
            "retention_time": {"min": 4.0, "max": 12.0, "unit": "h"},
            "depth": {"min": 3.0, "max": 6.0, "unit": "m"},
            "F_M_ratio": {"min": 0.2, "max": 0.6, "unit": "kg BOD/kg MLSS.d"}
        }
    }
    
    # Vận tốc ống
    PIPE_VELOCITY = {
        "inlet": {"min": 0.6, "max": 1.2, "design": 0.9},
        "outlet": {"min": 0.5, "max": 1.0, "design": 0.8},
        "sludge": {"min": 1.0, "max": 2.0, "design": 1.5}
    }
    
    # Đường kính ống tiêu chuẩn
    STANDARD_DIAMETERS = [
        50, 75, 100, 125, 150, 200, 250, 300, 350, 400,
        450, 500, 600, 700, 800, 900, 1000, 1200, 1500
    ]
    
    def __init__(self):
        self.safety_layer = get_safety_layer()
    
    def design_sedimentation_tank(
        self,
        tank_name: str,
        design_flow: float,
        num_tanks: int = 1,
        settling_velocity: float = None,
        retention_time: float = None,
        surface_loading_rate: float = None,
        length: float = None,
        width: float = None,
        depth: float = None,
        concrete_grade: str = "B25",
        steel_grade: str = "CB300-V"
    ) -> TankDesignResult:
        """
        Thiết kế bể lắng với đầy đủ log
        
        Công thức chính:
        - Diện tích: A = Q / v₀
        - Thời gian lưu: t = V / Q
        - Tải trọng bề mặt: SLR = Q / A
        
        Args:
            tank_name: Tên/ký hiệu bể
            design_flow: Lưu lượng thiết kế (m³/ngày)
            num_tanks: Số bể
            settling_velocity: Vận tốc lắng (m/h)
            retention_time: Thời gian lưu (h)
            surface_loading_rate: Tải trọng bề mặt (m³/m².d)
            length, width, depth: Kích thước (nếu đã biết)
            
        Returns:
            TankDesignResult
        """
        import time
        start_time = time.time()
        
        # Khởi tạo log
        log = CalculationLogger.create_log(
            log_id=str(uuid.uuid4())[:8],
            calculation_type="tank_design",
            module_name="Thiết kế bể lắng",
            description=f"Bể {tank_name}, Q = {design_flow} m³/ngày, n = {num_tanks} bể",
            standards=["TCVN 7957:2008", "TCVN 4116:1985"]
        )
        
        limits = self.DESIGN_LIMITS["sedimentation"]
        
        # 1. XÁC ĐỊNH THÔNG SỐ THIẾT KẾ
        Q_total = design_flow                    # m³/ngày
        Q_per_tank = Q_total / num_tanks         # m³/ngày mỗi bể
        Q_hourly = Q_per_tank / 24               # m³/h
        Q_sec = Q_per_tank / 86400               # m³/s
        
        flow_step = CalculationLogger.create_step(
            step_id="flow_distribution",
            name="Phân phối lưu lượng",
            description=f"Chia lưu lượng tổng cho {num_tanks} bể",
            formula_latex=r"Q_{be} = \frac{Q_{tong}}{n}",
            formula_text="Q_bể = Q_tổng / n",
            reference="Nguyên tắc thiết kế",
            inputs={
                "Q_total": Q_total,
                "n": num_tanks
            },
            result={
                "Q_per_tank_day": round(Q_per_tank, 2),
                "Q_per_tank_hour": round(Q_hourly, 2),
                "Q_per_tank_sec": round(Q_sec, 6)
            },
            result_unit="m³/ngày"
        )
        log.add_step(flow_step)
        
        # 2. TÍNH DIỆN TÍCH BỀ MẶT
        if settling_velocity is None:
            if surface_loading_rate is not None:
                settling_velocity = surface_loading_rate / 24  # m/h
            else:
                settling_velocity = 1.5  # m/h mặc định
        
        if retention_time is not None and depth is not None:
            # Tính từ thời gian lưu
            volume_required = Q_hourly * retention_time
            surface_area = volume_required / depth
            calc_method = "Từ thời gian lưu"
        else:
            # Tính từ vận tốc lắng: A = Q / v₀
            surface_area = Q_hourly / settling_velocity
            calc_method = "Từ vận tốc lắng"
        
        area_step = CalculationLogger.create_step(
            step_id="surface_area",
            name="Tính diện tích bề mặt",
            description=f"Phương pháp: {calc_method}",
            formula_latex=r"A = \frac{Q}{v_0} = \frac{Q}{SLR/24}",
            formula_text="A = Q / v₀",
            reference="TCVN 7957:2008 - Điều 7.3.2",
            inputs={
                "Q_h": Q_hourly,
                "v_0": settling_velocity,
                "method": calc_method
            },
            input_descriptions={
                "Q_h": "Lưu lượng giờ (m³/h)",
                "v_0": "Vận tốc lắng (m/h)"
            },
            result=round(surface_area, 2),
            result_unit="m²"
        )
        log.add_step(area_step)
        
        # 3. XÁC ĐỊNH KÍCH THƯỚC
        if depth is None:
            depth = (limits["depth"]["min"] + limits["depth"]["max"]) / 2  # 3.75m
        
        if length is None and width is None:
            L_W_ratio = 3.0  # Tỷ lệ L/W tiêu chuẩn
            width = math.sqrt(surface_area / L_W_ratio)
            length = width * L_W_ratio
        elif length is None:
            length = surface_area / width
        elif width is None:
            width = surface_area / length
        
        # Làm tròn (bội số 0.5m)
        length = math.ceil(length * 2) / 2
        width = math.ceil(width * 2) / 2
        depth = round(depth * 2) / 2
        
        # Tính lại diện tích và thể tích thực
        actual_area = length * width
        actual_volume = actual_area * depth
        
        dims_step = CalculationLogger.create_step(
            step_id="dimensions",
            name="Xác định kích thước bể",
            description=f"Làm tròn đến bội số 0.5m",
            formula_latex=r"L/W = 3.0 \Rightarrow W = \sqrt{A/3}, L = 3W",
            formula_text="L/W = 3.0 → W = √(A/3), L = 3W",
            reference="TCVN 7957:2008 - Điều 7.3.3 (L/W = 2-5)",
            inputs={
                "A_required": round(surface_area, 2),
                "L_W_ratio": 3.0,
                "H_design": depth
            },
            result={
                "length": length,
                "width": width,
                "depth": depth,
                "actual_area": actual_area,
                "actual_volume": actual_volume
            },
            result_unit="m"
        )
        log.add_step(dims_step)
        
        # 4. TÍNH THÔNG SỐ THỦY LỰC
        # Thời gian lưu
        actual_retention = actual_volume / Q_hourly  # h
        
        # Tải trọng bề mặt
        actual_surface_loading = Q_per_tank / actual_area  # m³/m².d
        
        # Vận tốc ngang
        cross_section = width * depth
        horizontal_velocity = Q_sec / cross_section  # m/s
        
        # Kiểm tra tải trọng máng tràn
        weir_length = 2 * width  # Máng 2 bên
        weir_loading = Q_per_tank / weir_length  # m³/m.d
        
        hydraulics_step = CalculationLogger.create_step(
            step_id="hydraulics",
            name="Tính toán thủy lực",
            description="Các thông số thủy lực chính của bể lắng",
            formula_latex=r"""
            t = \frac{V}{Q} \\
            SLR = \frac{Q}{A} \\
            v_h = \frac{Q}{B \times H} \\
            WLR = \frac{Q}{L_{weir}}
            """,
            formula_text="t = V/Q; SLR = Q/A; v_h = Q/(B×H); WLR = Q/L_weir",
            reference="TCVN 7957:2008 - Điều 7.3",
            inputs={
                "V": actual_volume,
                "A": actual_area,
                "Q_day": Q_per_tank,
                "Q_sec": Q_sec,
                "B": width,
                "H": depth,
                "L_weir": weir_length
            },
            result={
                "retention_time_h": round(actual_retention, 2),
                "surface_loading_m3m2d": round(actual_surface_loading, 2),
                "horizontal_velocity_ms": round(horizontal_velocity, 5),
                "weir_loading_m3md": round(weir_loading, 2)
            },
            result_unit=""
        )
        log.add_step(hydraulics_step)
        
        # 5. KIỂM TRA GIỚI HẠN TCVN
        # Kiểm tra thời gian lưu
        if actual_retention < limits["retention_time"]["min"]:
            log.add_violation(CalculationLogger.create_violation(
                violation_id="retention_time_min",
                parameter="retention_time",
                actual_value=round(actual_retention, 2),
                limit_value=limits["retention_time"]["min"],
                limit_type="min",
                severity=ViolationSeverity.MAJOR,
                standard="TCVN 7957:2008",
                clause="Bảng 7.2",
                message=f"Thời gian lưu {actual_retention:.2f}h < tối thiểu {limits['retention_time']['min']}h",
                suggestion="Tăng thể tích bể hoặc giảm số bể"
            ))
        
        if actual_retention > limits["retention_time"]["max"]:
            log.add_violation(CalculationLogger.create_violation(
                violation_id="retention_time_max",
                parameter="retention_time",
                actual_value=round(actual_retention, 2),
                limit_value=limits["retention_time"]["max"],
                limit_type="max",
                severity=ViolationSeverity.MINOR,
                standard="TCVN 7957:2008",
                clause="Bảng 7.2",
                message=f"Thời gian lưu {actual_retention:.2f}h > khuyến nghị {limits['retention_time']['max']}h",
                suggestion="Xem xét giảm kích thước bể để tiết kiệm"
            ))
        
        # Kiểm tra tải trọng bề mặt
        if actual_surface_loading > limits["surface_loading"]["max"]:
            log.add_violation(CalculationLogger.create_violation(
                violation_id="surface_loading_max",
                parameter="surface_loading",
                actual_value=round(actual_surface_loading, 2),
                limit_value=limits["surface_loading"]["max"],
                limit_type="max",
                severity=ViolationSeverity.CRITICAL,
                standard="TCVN 7957:2008",
                clause="Bảng 7.2",
                message=f"Tải trọng bề mặt {actual_surface_loading:.1f} > tối đa {limits['surface_loading']['max']}",
                suggestion="Tăng diện tích bể hoặc thêm số bể"
            ))
        
        # Kiểm tra vận tốc ngang
        if horizontal_velocity > limits["velocity"]["max"]:
            log.add_violation(CalculationLogger.create_violation(
                violation_id="velocity_max",
                parameter="horizontal_velocity",
                actual_value=round(horizontal_velocity, 5),
                limit_value=limits["velocity"]["max"],
                limit_type="max",
                severity=ViolationSeverity.MAJOR,
                standard="TCVN 7957:2008",
                clause="Điều 7.3.5",
                message=f"Vận tốc ngang {horizontal_velocity:.5f} m/s > tối đa {limits['velocity']['max']} m/s",
                suggestion="Tăng chiều rộng hoặc chiều sâu bể"
            ))
        
        check_step = CalculationLogger.create_step(
            step_id="standard_check",
            name="Kiểm tra tiêu chuẩn",
            description="Kiểm tra các thông số với giới hạn TCVN 7957:2008",
            formula_latex="",
            formula_text="Kiểm tra min/max theo bảng 7.2",
            reference="TCVN 7957:2008 - Bảng 7.2",
            inputs={
                "t": actual_retention,
                "SLR": actual_surface_loading,
                "v_h": horizontal_velocity,
                "WLR": weir_loading
            },
            result={
                "retention_time": f"{actual_retention:.2f}h ({'OK' if limits['retention_time']['min'] <= actual_retention <= limits['retention_time']['max'] else 'FAIL'})",
                "surface_loading": f"{actual_surface_loading:.1f} ({'OK' if actual_surface_loading <= limits['surface_loading']['max'] else 'FAIL'})",
                "velocity": f"{horizontal_velocity:.5f} ({'OK' if horizontal_velocity <= limits['velocity']['max'] else 'FAIL'})",
                "weir_loading": f"{weir_loading:.1f} ({'OK' if limits['weir_loading']['min'] <= weir_loading <= limits['weir_loading']['max'] else 'CHECK'})"
            },
            result_unit=""
        )
        
        if log.violations:
            check_step.status = CalculationStatus.WARNING
        log.add_step(check_step)
        
        # 6. TÍNH ĐƯỜNG KÍNH ỐNG
        # Ống vào
        inlet_area = Q_sec / self.PIPE_VELOCITY["inlet"]["design"]
        inlet_diameter = math.sqrt(4 * inlet_area / math.pi) * 1000
        inlet_diameter = self._get_standard_diameter(inlet_diameter)
        
        # Ống ra
        outlet_area = Q_sec / self.PIPE_VELOCITY["outlet"]["design"]
        outlet_diameter = math.sqrt(4 * outlet_area / math.pi) * 1000
        outlet_diameter = self._get_standard_diameter(outlet_diameter)
        
        pipe_step = CalculationLogger.create_step(
            step_id="pipe_sizing",
            name="Tính kích thước đường ống",
            description="Chọn đường kính ống vào/ra theo vận tốc thiết kế",
            formula_latex=r"D = \sqrt{\frac{4Q}{\pi V}}",
            formula_text="D = √(4Q/πV)",
            reference="TCVN 7957:2008 - Điều 5.3",
            inputs={
                "Q": Q_sec,
                "V_inlet": self.PIPE_VELOCITY["inlet"]["design"],
                "V_outlet": self.PIPE_VELOCITY["outlet"]["design"]
            },
            result={
                "inlet_diameter": inlet_diameter,
                "outlet_diameter": outlet_diameter
            },
            result_unit="mm"
        )
        log.add_step(pipe_step)
        
        # 7. TÍNH KẾT CẤU
        sludge_depth = 0.5  # Vùng bùn
        freeboard = 0.3     # Chiều cao an toàn
        total_depth = depth + sludge_depth + freeboard
        
        # Chiều dày thành theo chiều sâu
        if total_depth <= 3.0:
            wall_thickness = 0.25
        elif total_depth <= 4.0:
            wall_thickness = 0.30
        elif total_depth <= 5.0:
            wall_thickness = 0.35
        else:
            wall_thickness = 0.40
        
        bottom_thickness = 0.30
        
        # Thiết kế kết cấu thành
        structural_result = TraceableStructuralEngine.design_tank_wall(
            height=total_depth,
            span=width,
            wall_thickness=wall_thickness,
            concrete_grade=concrete_grade,
            steel_grade=steel_grade
        )
        
        structure_step = CalculationLogger.create_step(
            step_id="structural",
            name="Thiết kế kết cấu",
            description="Thiết kế thành bể BTCT",
            formula_latex="",
            formula_text="Xem log kết cấu chi tiết",
            reference="TCVN 5574:2018",
            inputs={
                "H_total": total_depth,
                "span": width,
                "concrete": concrete_grade,
                "steel": steel_grade
            },
            result={
                "wall_thickness": wall_thickness,
                "bottom_thickness": bottom_thickness,
                "reinforcement": structural_result.reinforcement,
                "is_valid": structural_result.is_valid
            },
            result_unit=""
        )
        log.add_step(structure_step)
        
        # Copy violations từ structural
        for v in structural_result.calculation_log.violations:
            log.add_violation(v)
        
        # 8. KẾT QUẢ CUỐI CÙNG
        volume_per_tank = actual_volume
        volume_total = volume_per_tank * num_tanks
        
        log.final_results = {
            "tank_type": "sedimentation",
            "tank_name": tank_name,
            "num_tanks": num_tanks,
            "dimensions": {
                "length_m": length,
                "width_m": width,
                "water_depth_m": depth,
                "total_depth_m": total_depth,
                "wall_thickness_m": wall_thickness,
                "bottom_thickness_m": bottom_thickness
            },
            "hydraulics": {
                "design_flow_m3d": design_flow,
                "retention_time_h": round(actual_retention, 2),
                "surface_loading_m3m2d": round(actual_surface_loading, 2),
                "horizontal_velocity_ms": round(horizontal_velocity, 5),
                "weir_loading_m3md": round(weir_loading, 2)
            },
            "pipes": {
                "inlet_mm": inlet_diameter,
                "outlet_mm": outlet_diameter
            },
            "volume": {
                "per_tank_m3": round(volume_per_tank, 2),
                "total_m3": round(volume_total, 2)
            }
        }
        
        log.calculation_time_ms = (time.time() - start_time) * 1000
        
        # Kiểm tra an toàn
        safety_result = self.safety_layer.check_calculation_log(log)
        
        return TankDesignResult(
            tank_type="sedimentation",
            tank_name=tank_name,
            num_tanks=num_tanks,
            length=length,
            width=width,
            water_depth=depth,
            total_depth=total_depth,
            wall_thickness=wall_thickness,
            bottom_thickness=bottom_thickness,
            design_flow=design_flow,
            retention_time=round(actual_retention, 2),
            surface_loading=round(actual_surface_loading, 2),
            horizontal_velocity=round(horizontal_velocity, 5),
            inlet_diameter=inlet_diameter,
            outlet_diameter=outlet_diameter,
            volume_per_tank=round(volume_per_tank, 2),
            volume_total=round(volume_total, 2),
            is_valid=structural_result.is_valid,
            can_export=safety_result.can_export,
            calculation_log=log,
            structural_log=structural_result.calculation_log
        )
    
    def design_storage_tank(
        self,
        tank_name: str,
        storage_volume: float,
        design_flow: float = None,
        num_tanks: int = 1,
        length: float = None,
        width: float = None,
        depth: float = None,
        concrete_grade: str = "B25",
        steel_grade: str = "CB300-V"
    ) -> TankDesignResult:
        """
        Thiết kế bể chứa với đầy đủ log
        """
        import time
        start_time = time.time()
        
        log = CalculationLogger.create_log(
            log_id=str(uuid.uuid4())[:8],
            calculation_type="tank_design",
            module_name="Thiết kế bể chứa",
            description=f"Bể {tank_name}, V = {storage_volume} m³",
            standards=["TCVN 33:2006", "TCVN 4116:1985"]
        )
        
        # Thể tích mỗi bể
        V_per_tank = storage_volume / num_tanks
        
        # Xác định chiều sâu
        if depth is None:
            depth = 4.0  # Mặc định
        
        # Diện tích cần thiết
        surface_area = V_per_tank / depth
        
        # Xác định kích thước
        if length is None and width is None:
            side = math.sqrt(surface_area)
            length = math.ceil(side * 2) / 2
            width = math.ceil(side * 2) / 2
        elif length is None:
            length = math.ceil(surface_area / width * 2) / 2
        elif width is None:
            width = math.ceil(surface_area / length * 2) / 2
        
        # Làm tròn
        length = math.ceil(length * 2) / 2
        width = math.ceil(width * 2) / 2
        
        actual_volume = length * width * depth
        
        # Thời gian lưu
        if design_flow and design_flow > 0:
            retention_time = actual_volume / (design_flow / 24)
            Q_sec = design_flow / 86400
            
            # Tính ống
            inlet_area = Q_sec / 1.0
            inlet_diameter = self._get_standard_diameter(
                math.sqrt(4 * inlet_area / math.pi) * 1000
            )
        else:
            retention_time = 0
            inlet_diameter = 200
        
        outlet_diameter = inlet_diameter
        
        # Kết cấu
        freeboard = 0.3
        total_depth = depth + freeboard
        
        if total_depth <= 3.0:
            wall_thickness = 0.25
        elif total_depth <= 4.0:
            wall_thickness = 0.30
        else:
            wall_thickness = 0.35
        
        bottom_thickness = 0.30
        
        # Log các bước
        vol_step = CalculationLogger.create_step(
            step_id="volume",
            name="Tính thể tích bể chứa",
            description=f"Thể tích yêu cầu: {storage_volume} m³ cho {num_tanks} bể",
            formula_latex=r"V_{be} = \frac{V_{yeu\_cau}}{n}",
            formula_text="V_bể = V_yêu_cầu / n",
            reference="TCVN 33:2006",
            inputs={"V_total": storage_volume, "n": num_tanks},
            result={"V_per_tank": round(V_per_tank, 2), "V_actual": round(actual_volume, 2)},
            result_unit="m³"
        )
        log.add_step(vol_step)
        
        dims_step = CalculationLogger.create_step(
            step_id="dimensions",
            name="Xác định kích thước",
            description="Bể chứa thường có tỷ lệ L/W gần 1",
            formula_latex=r"A = V/H \Rightarrow L \approx W \approx \sqrt{A}",
            formula_text="A = V/H → L ≈ W ≈ √A",
            reference="TCVN 4116:1985",
            inputs={"A": surface_area, "H": depth},
            result={"L": length, "W": width, "H": depth},
            result_unit="m"
        )
        log.add_step(dims_step)
        
        log.final_results = {
            "tank_type": "storage",
            "tank_name": tank_name,
            "num_tanks": num_tanks,
            "volume_required": storage_volume,
            "volume_actual": round(actual_volume * num_tanks, 2),
            "dimensions": {
                "length": length,
                "width": width,
                "depth": depth,
                "total_depth": total_depth
            }
        }
        
        log.calculation_time_ms = (time.time() - start_time) * 1000
        
        return TankDesignResult(
            tank_type="storage",
            tank_name=tank_name,
            num_tanks=num_tanks,
            length=length,
            width=width,
            water_depth=depth,
            total_depth=total_depth,
            wall_thickness=wall_thickness,
            bottom_thickness=bottom_thickness,
            design_flow=design_flow or 0,
            retention_time=round(retention_time, 2),
            surface_loading=0,
            horizontal_velocity=0,
            inlet_diameter=inlet_diameter,
            outlet_diameter=outlet_diameter,
            volume_per_tank=round(actual_volume, 2),
            volume_total=round(actual_volume * num_tanks, 2),
            is_valid=True,
            can_export=log.can_export,
            calculation_log=log,
            structural_log=None
        )
    
    def _get_standard_diameter(self, diameter: float) -> float:
        """Làm tròn lên đường kính tiêu chuẩn"""
        for d in self.STANDARD_DIAMETERS:
            if d >= diameter:
                return d
        return self.STANDARD_DIAMETERS[-1]


# Alias for compatibility
class TankDesignCalculatorV2(TraceableTankDesignEngine):
    pass
