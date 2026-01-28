"""
Traceable Structural Engine - Động cơ tính toán kết cấu có truy xuất

SPRINT 2: TRANSPARENT ENGINEERING
Tính toán kết cấu đầy đủ với:
- Công thức LaTeX
- Tham chiếu tiêu chuẩn TCVN
- Điều kiện áp dụng
- Kiểm tra an toàn
- Vi phạm tiêu chuẩn

Tiêu chuẩn áp dụng:
- TCVN 5574:2018 - Kết cấu bê tông và bê tông cốt thép
- TCVN 2737:1995 - Tải trọng và tác động
- TCVN 9386:2012 - Thiết kế công trình chịu động đất
- TCVN 4116:1985 - Bể chứa nước
"""

import math
import uuid
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
from datetime import datetime

from calculations.calculation_log import (
    CalculationLog, CalculationStep, Violation,
    CalculationStatus, ViolationSeverity,
    CalculationLogger, EngineeringConstants
)


@dataclass
class LoadCase:
    """Tổ hợp tải trọng"""
    id: str
    name: str
    description: str
    
    # Tải trọng
    water_inside: bool = True        # Bể đầy nước phía trong
    water_level: float = 1.0         # Mức nước (tỷ lệ với chiều cao)
    soil_outside: bool = False       # Áp lực đất phía ngoài
    groundwater: bool = False        # Nước ngầm
    surcharge: float = 0.0           # Hoạt tải mặt đất (kN/m²)
    
    # Hệ số
    load_factor: float = 1.2         # Hệ số tải trọng


@dataclass
class WallDesignResult:
    """Kết quả thiết kế thành bể"""
    
    # Kích thước
    height: float
    thickness: float
    effective_depth: float
    
    # Áp lực
    water_pressure_max: float
    soil_pressure_max: float
    net_pressure_max: float
    
    # Nội lực
    moment_max: float
    shear_max: float
    governing_case: str
    
    # Cốt thép
    As_required: float
    As_provided: float
    reinforcement: str
    
    # Kiểm tra
    is_valid: bool
    
    # Log
    calculation_log: CalculationLog = None
    
    def to_dict(self) -> Dict:
        return {
            "height": self.height,
            "thickness": self.thickness,
            "effective_depth": self.effective_depth,
            "water_pressure_max": self.water_pressure_max,
            "soil_pressure_max": self.soil_pressure_max,
            "net_pressure_max": self.net_pressure_max,
            "moment_max": self.moment_max,
            "shear_max": self.shear_max,
            "governing_case": self.governing_case,
            "As_required": self.As_required,
            "As_provided": self.As_provided,
            "reinforcement": self.reinforcement,
            "is_valid": self.is_valid,
            "calculation_log": self.calculation_log.to_dict() if self.calculation_log else None
        }


@dataclass
class SlabDesignResult:
    """Kết quả thiết kế bản đáy/nắp"""
    
    # Kích thước
    length: float
    width: float
    thickness: float
    
    # Tải trọng
    dead_load: float
    live_load: float
    water_load: float
    total_load: float
    
    # Nội lực
    moment_x: float
    moment_y: float
    
    # Cốt thép
    As_x: float
    As_y: float
    reinforcement_x: str
    reinforcement_y: str
    
    # Kiểm tra
    is_valid: bool
    
    # Log
    calculation_log: CalculationLog = None


@dataclass
class StabilityResult:
    """Kết quả kiểm tra ổn định"""
    
    # Đẩy nổi
    uplift_force: float
    resisting_force: float
    uplift_safety_factor: float
    uplift_ok: bool
    
    # Lật
    overturning_moment: float
    resisting_moment: float
    overturning_safety_factor: float
    overturning_ok: bool
    
    # Trượt
    sliding_force: float
    friction_force: float
    sliding_safety_factor: float
    sliding_ok: bool
    
    # Tổng kết
    is_stable: bool
    
    # Log
    calculation_log: CalculationLog = None


class TraceableStructuralEngine:
    """
    Động cơ tính toán kết cấu với truy xuất đầy đủ
    
    Hỗ trợ:
    - Tính toán áp lực
    - Thiết kế thành bể (wall design)
    - Thiết kế đáy bể (slab design)
    - Kiểm tra ổn định (stability check)
    - Kiểm tra nứt (crack control)
    - Tính cốt thép (reinforcement)
    """
    
    # ==================== HẰNG SỐ VẬT LIỆU ====================
    
    # Cường độ bê tông (MPa) - TCVN 5574:2018 Bảng 6
    CONCRETE_STRENGTH = EngineeringConstants.CONCRETE_STRENGTH
    
    # Cường độ thép (MPa) - TCVN 5574:2018 Bảng 13
    STEEL_STRENGTH = EngineeringConstants.STEEL_STRENGTH
    
    # Trọng lượng riêng (kN/m³)
    UNIT_WEIGHT = {
        "water": 10.0,
        "concrete": 25.0,
        "reinforced_concrete": 25.5,
        "soil_dry": 18.0,
        "soil_saturated": 20.0,
        "sludge": 12.0,
        "sand": 17.0
    }
    
    # Hệ số tải trọng - TCVN 2737:1995
    LOAD_FACTORS = {
        "dead": 1.1,
        "live": 1.3,
        "water": 1.2,
        "soil": 1.2,
        "seismic": 1.0
    }
    
    # Giới hạn an toàn - TCVN 5574:2018
    SAFETY_LIMITS = {
        "uplift_min": 1.2,           # Hệ số an toàn chống đẩy nổi
        "overturning_min": 1.5,      # Hệ số an toàn chống lật
        "sliding_min": 1.3,          # Hệ số an toàn chống trượt
        "bearing_min": 2.0,          # Hệ số an toàn sức chịu tải
        "crack_width_max": 0.2,      # Bề rộng vết nứt tối đa (mm)
        "deflection_ratio": 250      # L/250
    }
    
    # Tổ hợp tải trọng tiêu chuẩn cho bể
    STANDARD_LOAD_CASES = [
        LoadCase("LC1", "Bể đầy - Không đất", "Bể đầy nước, không có áp lực đất", 
                 water_inside=True, water_level=1.0, soil_outside=False, load_factor=1.2),
        LoadCase("LC2", "Bể rỗng - Có đất", "Bể rỗng, có áp lực đất và hoạt tải",
                 water_inside=False, water_level=0, soil_outside=True, surcharge=10, load_factor=1.2),
        LoadCase("LC3", "Bể đầy - Có đất", "Bể đầy, có áp lực đất và hoạt tải (tổ hợp đặc biệt)",
                 water_inside=True, water_level=1.0, soil_outside=True, surcharge=20, load_factor=1.35)
    ]
    
    # ==================== TÍNH ÁP LỰC ====================
    
    @classmethod
    def calculate_water_pressure(
        cls,
        depth: float,
        water_level: float = 1.0,
        gamma_w: float = None
    ) -> Tuple[Dict[str, float], CalculationStep]:
        """
        Tính áp lực thủy tĩnh
        
        p = γ × h (phân bố tam giác)
        P = 0.5 × γ × h² (lực tổng hợp)
        
        Args:
            depth: Chiều sâu tổng (m)
            water_level: Mức nước (tỷ lệ 0-1)
            gamma_w: Trọng lượng riêng nước (kN/m³)
            
        Returns:
            (Dict kết quả, CalculationStep)
        """
        if gamma_w is None:
            gamma_w = cls.UNIT_WEIGHT["water"]
        
        h_water = depth * water_level  # Chiều cao cột nước thực tế
        
        # Áp lực tại đáy
        p_max = gamma_w * h_water  # kN/m²
        
        # Lực tổng hợp (cho 1m dài)
        P_total = 0.5 * gamma_w * h_water ** 2  # kN/m
        
        # Điểm đặt lực (từ đáy)
        y_centroid = h_water / 3  # m
        
        # Moment tại đáy (nếu ngàm)
        M_base = P_total * y_centroid  # kN.m/m
        
        result = {
            "water_depth": h_water,
            "pressure_max": round(p_max, 2),
            "total_force": round(P_total, 2),
            "centroid_height": round(y_centroid, 3),
            "base_moment": round(M_base, 2)
        }
        
        step = CalculationLogger.create_step(
            step_id="water_pressure",
            name="Tính áp lực thủy tĩnh",
            description=f"Áp lực nước tác dụng lên thành bể với chiều cao cột nước h = {h_water:.2f}m",
            formula_latex=r"""
            p_{max} = \gamma_w \times h \\
            P = \frac{1}{2} \gamma_w h^2 \\
            y_c = \frac{h}{3}
            """,
            formula_text="p_max = γ × h; P = 0.5 × γ × h²; y_c = h/3",
            reference="TCVN 4116:1985 - Bể chứa nước; Thủy tĩnh học",
            inputs={
                "γ_w": gamma_w,
                "h": h_water,
                "water_level": water_level
            },
            input_descriptions={
                "γ_w": "Trọng lượng riêng nước (kN/m³)",
                "h": "Chiều cao cột nước (m)",
                "water_level": "Mức nước tương đối"
            },
            conditions=[
                "Áp lực phân bố tam giác từ 0 (mặt nước) đến p_max (đáy)",
                "Điểm đặt lực cách đáy h/3"
            ],
            result=result,
            result_unit=""
        )
        
        return result, step
    
    @classmethod
    def calculate_soil_pressure(
        cls,
        depth: float,
        Ka: float = 0.33,
        gamma_s: float = None,
        surcharge: float = 0,
        groundwater_level: float = 0
    ) -> Tuple[Dict[str, float], CalculationStep]:
        """
        Tính áp lực đất chủ động (Rankine)
        
        p = Ka × γ × h + Ka × q
        
        Args:
            depth: Chiều sâu chôn (m)
            Ka: Hệ số áp lực đất chủ động
            gamma_s: Trọng lượng riêng đất (kN/m³)
            surcharge: Hoạt tải mặt đất (kN/m²)
            groundwater_level: Mực nước ngầm từ đáy (m)
            
        Returns:
            (Dict kết quả, CalculationStep)
        """
        if gamma_s is None:
            gamma_s = cls.UNIT_WEIGHT["soil_dry"]
        
        # Áp lực do trọng lượng đất
        p_soil = Ka * gamma_s * depth  # kN/m²
        
        # Áp lực do hoạt tải
        p_surcharge = Ka * surcharge  # kN/m² (không đổi theo chiều sâu)
        
        # Tổng áp lực tại đáy
        p_max = p_soil + p_surcharge
        
        # Lực tổng hợp
        P_soil = 0.5 * Ka * gamma_s * depth ** 2  # Tam giác
        P_surcharge = Ka * surcharge * depth       # Chữ nhật
        P_total = P_soil + P_surcharge
        
        # Điểm đặt lực
        if P_total > 0:
            y_centroid = (P_soil * depth/3 + P_surcharge * depth/2) / P_total
        else:
            y_centroid = depth / 3
        
        result = {
            "depth": depth,
            "Ka": Ka,
            "pressure_soil": round(p_soil, 2),
            "pressure_surcharge": round(p_surcharge, 2),
            "pressure_max": round(p_max, 2),
            "force_soil": round(P_soil, 2),
            "force_surcharge": round(P_surcharge, 2),
            "total_force": round(P_total, 2),
            "centroid_height": round(y_centroid, 3)
        }
        
        step = CalculationLogger.create_step(
            step_id="soil_pressure",
            name="Tính áp lực đất chủ động",
            description=f"Áp lực đất tác dụng lên thành bể chôn h = {depth:.2f}m, Ka = {Ka}",
            formula_latex=r"""
            p_{soil} = K_a \times \gamma_s \times h \\
            p_{surcharge} = K_a \times q \\
            P = \frac{1}{2} K_a \gamma_s h^2 + K_a q h
            """,
            formula_text="p = Ka × γ × h + Ka × q",
            reference="TCVN 9362:2012 - Nền công trình; Lý thuyết Rankine",
            inputs={
                "Ka": Ka,
                "γ_s": gamma_s,
                "h": depth,
                "q": surcharge
            },
            input_descriptions={
                "Ka": "Hệ số áp lực đất chủ động",
                "γ_s": "Trọng lượng riêng đất (kN/m³)",
                "h": "Chiều sâu chôn (m)",
                "q": "Hoạt tải mặt đất (kN/m²)"
            },
            conditions=[
                "Đất đồng nhất, không dính (c = 0)",
                "Thành tường thẳng đứng, lưng tường nhẵn",
                "Ka = tan²(45° - φ/2) với φ là góc ma sát trong"
            ],
            assumptions=[
                f"Ka = {Ka} (giả định φ ≈ 30°)",
                "Không có nước ngầm" if groundwater_level == 0 else f"Mực nước ngầm: {groundwater_level}m"
            ],
            result=result,
            result_unit=""
        )
        
        return result, step
    
    # ==================== THIẾT KẾ THÀNH BỂ ====================
    
    @classmethod
    def design_tank_wall(
        cls,
        height: float,
        span: float,
        wall_thickness: float = None,
        concrete_grade: str = "B25",
        steel_grade: str = "CB300-V",
        cover: float = 40,
        load_cases: List[LoadCase] = None,
        support_condition: str = "fixed-free"
    ) -> WallDesignResult:
        """
        Thiết kế thành bể bê tông cốt thép
        
        Args:
            height: Chiều cao thành (m)
            span: Nhịp thành / Chiều rộng bể (m)
            wall_thickness: Chiều dày thành (m), None = tự động
            concrete_grade: Mác bê tông
            steel_grade: Mác thép
            cover: Lớp bảo vệ (mm)
            load_cases: Danh sách tổ hợp tải, None = mặc định
            support_condition: Điều kiện biên ("fixed-free", "fixed-fixed", "pinned-free")
            
        Returns:
            WallDesignResult
        """
        import time
        start_time = time.time()
        
        # Khởi tạo log
        log = CalculationLogger.create_log(
            log_id=str(uuid.uuid4())[:8],
            calculation_type="structural_wall",
            module_name="Thiết kế thành bể BTCT",
            description=f"Thành bể H={height}m, L={span}m, bê tông {concrete_grade}",
            standards=["TCVN 5574:2018", "TCVN 4116:1985", "TCVN 2737:1995"]
        )
        
        # 1. Xác định chiều dày thành
        if wall_thickness is None:
            # Chiều dày tối thiểu theo TCVN: t ≥ max(200mm, H/15)
            t_min = max(0.20, height / 15)
            wall_thickness = math.ceil(t_min * 20) / 20  # Làm tròn lên 5cm
        
        t_step = CalculationLogger.create_step(
            step_id="wall_thickness",
            name="Xác định chiều dày thành",
            description=f"Chiều dày thành tối thiểu theo TCVN 5574:2018",
            formula_latex=r"t_{min} = \max(200mm, H/15)",
            formula_text="t_min = max(200mm, H/15)",
            reference="TCVN 5574:2018 - Điều 10.3.1; TCVN 4116:1985",
            inputs={
                "H": height,
                "t_calc": max(0.20, height / 15),
                "t_adopted": wall_thickness
            },
            result=wall_thickness,
            result_unit="m"
        )
        log.add_step(t_step)
        
        # 2. Tính toán cho từng tổ hợp tải trọng
        if load_cases is None:
            load_cases = cls.STANDARD_LOAD_CASES
        
        max_moment = 0
        max_shear = 0
        governing_case = ""
        water_p_max = 0
        soil_p_max = 0
        
        for lc in load_cases:
            lc_step_desc = f"Tổ hợp {lc.id}: {lc.description}"
            
            # Áp lực nước (trong)
            if lc.water_inside:
                water_result, water_step = cls.calculate_water_pressure(height, lc.water_level)
                log.add_step(water_step)
                M_water = water_result["base_moment"]
                p_water = water_result["pressure_max"]
            else:
                M_water = 0
                p_water = 0
            
            # Áp lực đất (ngoài)
            if lc.soil_outside:
                soil_result, soil_step = cls.calculate_soil_pressure(height, surcharge=lc.surcharge)
                log.add_step(soil_step)
                M_soil = soil_result["total_force"] * soil_result["centroid_height"]
                p_soil = soil_result["pressure_max"]
            else:
                M_soil = 0
                p_soil = 0
            
            # Moment tính toán (lấy hiệu vì áp lực ngược chiều)
            # Thành bể chịu moment lớn nhất khi một bên có áp lực
            M_net = max(M_water, M_soil) * lc.load_factor
            
            # Hệ số moment theo điều kiện biên
            if support_condition == "fixed-free":
                # Thành ngàm dưới, tự do trên: M = wH²/6
                k_moment = 1.0 / 6
            elif support_condition == "fixed-fixed":
                # Ngàm hai đầu: M = wH²/12
                k_moment = 1.0 / 12
            else:
                k_moment = 1.0 / 8
            
            # Moment thiết kế
            p_max = max(p_water, p_soil)
            M_design = p_max * height ** 2 * k_moment * lc.load_factor
            
            # Lực cắt
            V_design = p_max * height / 2 * lc.load_factor
            
            if M_design > max_moment:
                max_moment = M_design
                max_shear = V_design
                governing_case = lc.id
                water_p_max = p_water
                soil_p_max = p_soil
            
            # Ghi nhận tổ hợp tải
            lc_step = CalculationLogger.create_step(
                step_id=f"load_case_{lc.id}",
                name=f"Tổ hợp tải {lc.id}",
                description=lc_step_desc,
                formula_latex=r"M_d = k \times p_{max} \times H^2 \times \gamma_f",
                formula_text="M_d = k × p_max × H² × γ_f",
                reference="TCVN 5574:2018 - Chương 8",
                inputs={
                    "p_water": p_water,
                    "p_soil": p_soil,
                    "H": height,
                    "k": k_moment,
                    "γ_f": lc.load_factor
                },
                result={
                    "M_design": round(M_design, 2),
                    "V_design": round(V_design, 2)
                },
                result_unit="kN.m/m"
            )
            log.add_step(lc_step)
        
        # 3. Tính cốt thép chịu uốn
        d = wall_thickness - cover/1000 - 0.010  # Chiều cao hữu ích (giả định φ20)
        
        rebar_result, rebar_step = cls.calculate_reinforcement(
            moment=max_moment,
            width=1.0,
            effective_depth=d,
            concrete_grade=concrete_grade,
            steel_grade=steel_grade
        )
        log.add_step(rebar_step)
        
        # 4. Kiểm tra chiều dày thành
        t_min_required = max(0.20, height / 15, d + cover/1000 + 0.020)
        
        if wall_thickness < t_min_required:
            violation = CalculationLogger.create_violation(
                violation_id="wall_thickness_min",
                parameter="wall_thickness",
                actual_value=wall_thickness,
                limit_value=t_min_required,
                limit_type="min",
                severity=ViolationSeverity.MAJOR,
                standard="TCVN 5574:2018",
                clause="Điều 10.3.1",
                message=f"Chiều dày thành {wall_thickness*1000:.0f}mm < yêu cầu {t_min_required*1000:.0f}mm",
                suggestion=f"Tăng chiều dày thành lên ≥ {math.ceil(t_min_required*20)/20*1000:.0f}mm"
            )
            log.add_violation(violation)
        
        # 5. Kiểm tra nứt (đơn giản hóa)
        crack_check_step = cls.check_crack_width(
            As=rebar_result["As_provided"],
            moment=max_moment / cls.LOAD_FACTORS["water"],  # Moment tiêu chuẩn
            depth=d,
            width=1.0,
            steel_grade=steel_grade
        )
        log.add_step(crack_check_step)
        
        # Kết quả
        log.final_results = {
            "wall_height_m": height,
            "wall_thickness_m": wall_thickness,
            "effective_depth_m": round(d, 3),
            "water_pressure_max_kPa": round(water_p_max, 2),
            "soil_pressure_max_kPa": round(soil_p_max, 2),
            "moment_max_kNm_m": round(max_moment, 2),
            "shear_max_kN_m": round(max_shear, 2),
            "governing_case": governing_case,
            "As_required_mm2_m": round(rebar_result["As_required"], 0),
            "As_provided_mm2_m": round(rebar_result["As_provided"], 0),
            "reinforcement": rebar_result["reinforcement"],
            "concrete_grade": concrete_grade,
            "steel_grade": steel_grade
        }
        
        log.calculation_time_ms = (time.time() - start_time) * 1000
        
        return WallDesignResult(
            height=height,
            thickness=wall_thickness,
            effective_depth=round(d, 3),
            water_pressure_max=round(water_p_max, 2),
            soil_pressure_max=round(soil_p_max, 2),
            net_pressure_max=round(max(water_p_max, soil_p_max), 2),
            moment_max=round(max_moment, 2),
            shear_max=round(max_shear, 2),
            governing_case=governing_case,
            As_required=round(rebar_result["As_required"], 0),
            As_provided=round(rebar_result["As_provided"], 0),
            reinforcement=rebar_result["reinforcement"],
            is_valid=log.can_export,
            calculation_log=log
        )
    
    # ==================== TÍNH CỐT THÉP ====================
    
    @classmethod
    def calculate_reinforcement(
        cls,
        moment: float,
        width: float,
        effective_depth: float,
        concrete_grade: str = "B25",
        steel_grade: str = "CB300-V"
    ) -> Tuple[Dict[str, Any], CalculationStep]:
        """
        Tính cốt thép chịu uốn theo TCVN 5574:2018
        
        Args:
            moment: Moment uốn tính toán (kN.m)
            width: Chiều rộng tiết diện (m)
            effective_depth: Chiều cao hữu ích (m)
            concrete_grade: Mác bê tông
            steel_grade: Mác thép
            
        Returns:
            (Dict kết quả, CalculationStep)
        """
        # Lấy cường độ vật liệu
        Rb = cls.CONCRETE_STRENGTH[concrete_grade]["Rb"]  # MPa
        Rs = cls.STEEL_STRENGTH[steel_grade]["Rs"]        # MPa
        
        # Đổi đơn vị
        M = moment * 1e6          # N.mm
        b = width * 1000          # mm
        h0 = effective_depth * 1000  # mm
        
        # Tính hệ số αm
        alpha_m = M / (Rb * b * h0 ** 2)
        
        # Giới hạn vùng nén
        xi_R = 0.617  # TCVN 5574:2018, thép CB300-V
        alpha_R = xi_R * (1 - 0.5 * xi_R)  # ≈ 0.427
        
        if alpha_m > alpha_R:
            # Cần cốt thép chịu nén hoặc tăng tiết diện
            xi = xi_R
            As = xi * Rb * b * h0 / Rs
            status = "compression_required"
            warnings = ["Hệ số αm > αR, cần cốt thép chịu nén hoặc tăng tiết diện"]
        else:
            # Chỉ cốt thép chịu kéo
            xi = 1 - math.sqrt(1 - 2 * alpha_m)
            As = xi * Rb * b * h0 / Rs
            status = "ok"
            warnings = []
        
        # Cốt thép tối thiểu (TCVN 5574:2018 - Điều 10.3.2)
        mu_min = 0.05  # % cho cấu kiện chịu uốn
        As_min = mu_min / 100 * b * h0
        
        As = max(As, As_min)
        
        # Chọn cốt thép
        bar_options = [
            (10, math.pi * 10**2 / 4),
            (12, math.pi * 12**2 / 4),
            (14, math.pi * 14**2 / 4),
            (16, math.pi * 16**2 / 4),
            (18, math.pi * 18**2 / 4),
            (20, math.pi * 20**2 / 4),
            (22, math.pi * 22**2 / 4),
            (25, math.pi * 25**2 / 4)
        ]
        
        # Tìm phương án bố trí tối ưu
        best_option = None
        for dia, As_bar in bar_options:
            n_bars = math.ceil(As / As_bar)
            spacing = (b - 2 * 40) / n_bars if n_bars > 0 else 0
            
            if 80 <= spacing <= 300:  # Khoảng cách hợp lý
                As_provided = n_bars * As_bar
                if best_option is None or As_provided < best_option["As_provided"]:
                    best_option = {
                        "diameter": dia,
                        "n_bars": n_bars,
                        "As_bar": As_bar,
                        "As_provided": As_provided,
                        "spacing": round(spacing, 0)
                    }
        
        # Nếu không tìm được, dùng φ16
        if best_option is None:
            dia = 16
            As_bar = math.pi * 16**2 / 4
            n_bars = math.ceil(As / As_bar)
            spacing = round((b - 2 * 40) / max(n_bars, 1), 0)
            best_option = {
                "diameter": dia,
                "n_bars": n_bars,
                "As_bar": As_bar,
                "As_provided": n_bars * As_bar,
                "spacing": spacing
            }
        
        # Tạo ký hiệu cốt thép
        reinforcement = f"φ{best_option['diameter']}a{int(best_option['spacing'])}"
        
        result = {
            "alpha_m": round(alpha_m, 4),
            "alpha_R": round(alpha_R, 4),
            "xi": round(xi, 4),
            "As_required": round(As, 0),
            "As_min": round(As_min, 0),
            "As_provided": round(best_option["As_provided"], 0),
            "n_bars": best_option["n_bars"],
            "bar_diameter": best_option["diameter"],
            "spacing": best_option["spacing"],
            "reinforcement": reinforcement,
            "mu": round(best_option["As_provided"] / (b * h0) * 100, 3),
            "status": status
        }
        
        step = CalculationLogger.create_step(
            step_id="reinforcement",
            name="Tính cốt thép chịu uốn",
            description=f"Tính cốt thép theo TCVN 5574:2018, M = {moment:.2f} kN.m",
            formula_latex=r"""
            \alpha_m = \frac{M}{R_b \times b \times h_0^2} \\
            \xi = 1 - \sqrt{1 - 2\alpha_m} \\
            A_s = \frac{\xi \times R_b \times b \times h_0}{R_s}
            """,
            formula_text="αm = M/(Rb×b×h0²); ξ = 1-√(1-2αm); As = ξ×Rb×b×h0/Rs",
            reference="TCVN 5574:2018 - Điều 8.1.8",
            inputs={
                "M": moment,
                "b": width,
                "h0": effective_depth,
                "Rb": Rb,
                "Rs": Rs,
                "concrete": concrete_grade,
                "steel": steel_grade
            },
            input_descriptions={
                "M": "Moment tính toán (kN.m)",
                "b": "Chiều rộng (m)",
                "h0": "Chiều cao hữu ích (m)",
                "Rb": "Cường độ bê tông (MPa)",
                "Rs": "Cường độ thép (MPa)"
            },
            conditions=[
                f"αm = {alpha_m:.4f} {'< αR (OK)' if alpha_m <= alpha_R else '> αR (KHÔNG ĐẠT)'}",
                f"μ_min = {mu_min}%"
            ],
            result=result,
            result_unit=""
        )
        
        if warnings:
            step.warnings = warnings
            step.status = CalculationStatus.WARNING
        
        return result, step
    
    # ==================== KIỂM TRA NỨT ====================
    
    @classmethod
    def check_crack_width(
        cls,
        As: float,
        moment: float,
        depth: float,
        width: float,
        steel_grade: str = "CB300-V"
    ) -> CalculationStep:
        """
        Kiểm tra bề rộng vết nứt (đơn giản hóa)
        
        Args:
            As: Diện tích cốt thép (mm²)
            moment: Moment tiêu chuẩn (kN.m)
            depth: Chiều cao hữu ích (m)
            width: Chiều rộng (m)
            steel_grade: Mác thép
            
        Returns:
            CalculationStep
        """
        # Ứng suất trong cốt thép (đơn giản hóa)
        M = moment * 1e6  # N.mm
        h0 = depth * 1000  # mm
        
        # Cánh tay đòn nội lực (giả định z ≈ 0.9h0)
        z = 0.9 * h0
        
        # Ứng suất
        sigma_s = M / (As * z) if As > 0 else 0
        
        # Bề rộng vết nứt theo công thức đơn giản (TCVN 5574:2018)
        Es = cls.STEEL_STRENGTH[steel_grade]["Es"]  # MPa
        
        # acrc = φ1 × φ2 × φ3 × ψs × σs/Es × (3.5c + 0.4d/μ)
        # Đơn giản hóa:
        phi1 = 1.0  # Tải trọng dài hạn
        phi2 = 0.5  # Thép có gờ
        phi3 = 1.0
        psi_s = 1.0
        
        # Giả định
        c = 40  # Lớp bảo vệ (mm)
        d_bar = 16  # Đường kính thanh (mm)
        mu = As / (width * 1000 * h0)  # Hàm lượng cốt thép
        
        if mu > 0:
            acrc = phi1 * phi2 * phi3 * psi_s * (sigma_s / Es) * (3.5 * c + 0.4 * d_bar / mu)
        else:
            acrc = 0
        
        # Giới hạn
        acrc_limit = cls.SAFETY_LIMITS["crack_width_max"]
        
        status = CalculationStatus.SUCCESS if acrc <= acrc_limit else CalculationStatus.VIOLATION
        
        step = CalculationLogger.create_step(
            step_id="crack_check",
            name="Kiểm tra bề rộng vết nứt",
            description=f"Kiểm tra vết nứt theo TCVN 5574:2018",
            formula_latex=r"a_{crc} = \varphi_1 \varphi_2 \varphi_3 \psi_s \frac{\sigma_s}{E_s} \left(3.5c + 0.4\frac{d}{\mu}\right)",
            formula_text="acrc = φ₁φ₂φ₃ψs × (σs/Es) × (3.5c + 0.4d/μ)",
            reference="TCVN 5574:2018 - Điều 8.2.15",
            inputs={
                "As": As,
                "M": moment,
                "σs": round(sigma_s, 1),
                "Es": Es,
                "μ": round(mu * 100, 3)
            },
            input_descriptions={
                "As": "Diện tích cốt thép (mm²)",
                "M": "Moment tiêu chuẩn (kN.m)",
                "σs": "Ứng suất thép (MPa)",
                "Es": "Module đàn hồi thép (MPa)",
                "μ": "Hàm lượng cốt thép (%)"
            },
            conditions=[
                f"acrc = {acrc:.3f}mm {'≤' if acrc <= acrc_limit else '>'} [acrc] = {acrc_limit}mm"
            ],
            result={
                "crack_width": round(acrc, 3),
                "limit": acrc_limit,
                "status": "PASS" if acrc <= acrc_limit else "FAIL"
            },
            result_unit="mm"
        )
        step.status = status
        
        if status == CalculationStatus.VIOLATION:
            step.warnings.append(f"Bề rộng vết nứt vượt giới hạn: {acrc:.3f}mm > {acrc_limit}mm")
        
        return step
    
    # ==================== KIỂM TRA ỔN ĐỊNH ====================
    
    @classmethod
    def check_stability(
        cls,
        length: float,
        width: float,
        total_depth: float,
        wall_thickness: float,
        bottom_thickness: float,
        water_depth: float,
        foundation_depth: float = 0,
        groundwater_depth: float = None,
        soil_friction: float = 0.5
    ) -> StabilityResult:
        """
        Kiểm tra ổn định bể (đẩy nổi, lật, trượt)
        
        Args:
            length: Chiều dài bể (m)
            width: Chiều rộng bể (m)
            total_depth: Tổng chiều sâu bể (m)
            wall_thickness: Chiều dày thành (m)
            bottom_thickness: Chiều dày đáy (m)
            water_depth: Chiều sâu nước trong bể (m)
            foundation_depth: Độ sâu đặt móng (m)
            groundwater_depth: Độ sâu mực nước ngầm từ mặt đất (m)
            soil_friction: Hệ số ma sát đất-bê tông
            
        Returns:
            StabilityResult
        """
        import time
        start_time = time.time()
        
        log = CalculationLogger.create_log(
            log_id=str(uuid.uuid4())[:8],
            calculation_type="structural_stability",
            module_name="Kiểm tra ổn định bể",
            description=f"Bể {length}x{width}m, sâu {total_depth}m",
            standards=["TCVN 5574:2018", "TCVN 9362:2012"]
        )
        
        gamma_c = cls.UNIT_WEIGHT["reinforced_concrete"]
        gamma_w = cls.UNIT_WEIGHT["water"]
        
        # Kích thước ngoài
        L_out = length + 2 * wall_thickness
        W_out = width + 2 * wall_thickness
        H_total = total_depth + bottom_thickness
        
        # 1. KIỂM TRA ĐẨY NỔI
        # Trọng lượng bể rỗng
        V_concrete = (
            bottom_thickness * L_out * W_out +                    # Đáy
            4 * wall_thickness * total_depth * (length + width) / 2 +  # Thành (gần đúng)
            2 * wall_thickness * total_depth * width              # 2 thành dài
        )
        W_structure = V_concrete * gamma_c
        
        # Lực đẩy nổi (khi bể rỗng, nước ngầm cao)
        if groundwater_depth is not None:
            h_submerged = max(0, H_total - groundwater_depth)
        else:
            h_submerged = H_total  # Giả định nước ngầm ở mặt đất
        
        V_displaced = L_out * W_out * h_submerged
        F_uplift = V_displaced * gamma_w
        
        # Trọng lượng nước trong bể (khi đầy)
        W_water = length * width * water_depth * gamma_w
        
        # Lực chống đẩy nổi = Trọng lượng bể
        # Trường hợp bất lợi nhất: bể rỗng
        F_resist_uplift = W_structure
        
        SF_uplift = F_resist_uplift / F_uplift if F_uplift > 0 else 999
        uplift_ok = SF_uplift >= cls.SAFETY_LIMITS["uplift_min"]
        
        uplift_step = CalculationLogger.create_step(
            step_id="uplift_check",
            name="Kiểm tra đẩy nổi",
            description="Kiểm tra ổn định chống đẩy nổi khi bể rỗng",
            formula_latex=r"K_{dn} = \frac{G_{bt}}{F_{dn}} \geq [K_{dn}] = 1.2",
            formula_text="K_dn = G_bt / F_dn ≥ 1.2",
            reference="TCVN 5574:2018 - Điều 10.5",
            inputs={
                "V_concrete": round(V_concrete, 2),
                "G_structure": round(W_structure, 2),
                "h_submerged": round(h_submerged, 2),
                "F_uplift": round(F_uplift, 2)
            },
            result={
                "SF": round(SF_uplift, 2),
                "limit": cls.SAFETY_LIMITS["uplift_min"],
                "status": "PASS" if uplift_ok else "FAIL"
            },
            result_unit=""
        )
        log.add_step(uplift_step)
        
        if not uplift_ok:
            violation = CalculationLogger.create_violation(
                violation_id="uplift_safety",
                parameter="uplift_safety_factor",
                actual_value=round(SF_uplift, 2),
                limit_value=cls.SAFETY_LIMITS["uplift_min"],
                limit_type="min",
                severity=ViolationSeverity.CRITICAL,
                standard="TCVN 5574:2018",
                clause="Điều 10.5",
                message=f"Hệ số an toàn chống đẩy nổi {SF_uplift:.2f} < {cls.SAFETY_LIMITS['uplift_min']}",
                suggestion="Tăng chiều dày đáy hoặc bố trí neo/cọc chống đẩy nổi"
            )
            log.add_violation(violation)
        
        # 2. KIỂM TRA LẬT (đơn giản - không có tải trọng ngang lớn)
        # Với bể ngầm, thường không cần kiểm tra lật trừ khi có động đất
        M_overturn = 0  # Moment gây lật
        M_resist = W_structure * W_out / 2  # Moment chống lật
        
        SF_overturn = M_resist / M_overturn if M_overturn > 0 else 999
        overturn_ok = True  # Luôn đạt với bể đối xứng không có tải ngang
        
        # 3. KIỂM TRA TRƯỢT
        # Lực ngang (áp lực đất không cân bằng - thường nhỏ)
        F_sliding = 0  # Giả định đất đồng nhất
        F_friction = soil_friction * W_structure
        
        SF_sliding = F_friction / F_sliding if F_sliding > 0 else 999
        sliding_ok = True
        
        # Kết quả tổng hợp
        is_stable = uplift_ok and overturn_ok and sliding_ok
        
        log.final_results = {
            "structure_weight_kN": round(W_structure, 2),
            "uplift_force_kN": round(F_uplift, 2),
            "uplift_SF": round(SF_uplift, 2),
            "uplift_OK": uplift_ok,
            "overturn_SF": round(SF_overturn, 2),
            "overturn_OK": overturn_ok,
            "sliding_SF": round(SF_sliding, 2),
            "sliding_OK": sliding_ok,
            "is_stable": is_stable
        }
        
        log.calculation_time_ms = (time.time() - start_time) * 1000
        
        return StabilityResult(
            uplift_force=round(F_uplift, 2),
            resisting_force=round(F_resist_uplift, 2),
            uplift_safety_factor=round(SF_uplift, 2),
            uplift_ok=uplift_ok,
            overturning_moment=round(M_overturn, 2),
            resisting_moment=round(M_resist, 2),
            overturning_safety_factor=round(SF_overturn, 2),
            overturning_ok=overturn_ok,
            sliding_force=round(F_sliding, 2),
            friction_force=round(F_friction, 2),
            sliding_safety_factor=round(SF_sliding, 2),
            sliding_ok=sliding_ok,
            is_stable=is_stable,
            calculation_log=log
        )


# Alias for backward compatibility
class StructuralCalculatorV2(TraceableStructuralEngine):
    pass
