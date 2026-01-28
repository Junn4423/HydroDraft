"""
Plate Moment Tables - Bảng tra nội lực bản mặt

Bảng hệ số moment cho bản mặt có các điều kiện biên khác nhau.
Tham khảo:
- PCA Tables - Portland Cement Association
- Bảng tra nội lực bản mặt theo TCVN 5574:2018
- Theory of Plates and Shells - Timoshenko

Áp dụng cho:
- Thành bể chữ nhật (ngàm 3 cạnh, tự do 1 cạnh)
- Đáy bể (kê 4 cạnh hoặc ngàm 4 cạnh)
- Bản mặt có tải phân bố tam giác (áp lực thủy tĩnh)
"""

from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import math


class BoundaryCondition(Enum):
    """Điều kiện biên của cạnh bản"""
    FREE = "free"           # Tự do
    PINNED = "pinned"       # Kê đơn / gối
    FIXED = "fixed"         # Ngàm / liên kết cứng


class LoadType(Enum):
    """Loại tải trọng"""
    UNIFORM = "uniform"                     # Phân bố đều
    TRIANGULAR = "triangular"               # Tam giác (áp lực thủy tĩnh)
    TRAPEZOIDAL = "trapezoidal"             # Hình thang
    HYDROSTATIC_WITH_SURCHARGE = "hydro_sur"  # Thủy tĩnh + tải mặt đất


@dataclass
class PlateGeometry:
    """Hình học bản mặt"""
    length: float           # Chiều dài a (m) - cạnh ngắn thường là chiều cao H
    width: float            # Chiều rộng b (m) - cạnh dài thường là chiều ngang L
    thickness: float        # Chiều dày (m)
    
    @property
    def aspect_ratio(self) -> float:
        """Tỷ lệ cạnh b/a"""
        return self.width / self.length if self.length > 0 else 1.0
    
    @property
    def short_side(self) -> float:
        """Cạnh ngắn"""
        return min(self.length, self.width)
    
    @property
    def long_side(self) -> float:
        """Cạnh dài"""
        return max(self.length, self.width)


@dataclass
class MomentResult:
    """Kết quả moment tại các vị trí"""
    # Moment dương (căng trong)
    Mx_positive: float      # kN.m/m - Phương ngang
    My_positive: float      # kN.m/m - Phương đứng
    
    # Moment âm tại gối
    Mx_negative: float      # kN.m/m
    My_negative: float      # kN.m/m
    
    # Vị trí moment max
    location_description: str
    
    # Hệ số sử dụng
    alpha_x: float
    alpha_y: float
    beta_x: float
    beta_y: float


class PlateMomentTables:
    """
    Bảng tra hệ số moment cho bản mặt
    
    CASE 1: Bản ngàm 3 cạnh, tự do 1 cạnh (thành bể)
            - Cạnh dưới ngàm (liên kết với đáy)
            - 2 cạnh bên ngàm (liên kết với thành kế bên)
            - Cạnh trên tự do (mặt nước)
            
    CASE 2: Bản ngàm 4 cạnh (đáy bể liên tục)
    
    CASE 3: Bản kê 4 cạnh (đáy bể đơn giản)
    """
    
    # ===========================================
    # CASE 1: Thành bể - Ngàm 3 cạnh, tự do 1 cạnh
    # Tải tam giác (áp lực thủy tĩnh) với đỉnh tại cạnh tự do
    # ===========================================
    
    # Hệ số moment cho thành bể với tải tam giác
    # Key: b/a (chiều rộng/chiều cao), Value: (alpha_x, alpha_y, beta_x, beta_y)
    # alpha: hệ số moment dương giữa bản
    # beta: hệ số moment âm tại gối
    # Mx_max = alpha_x * q_max * a²
    # My_max = alpha_y * q_max * a²
    
    WALL_TRIANGULAR_LOAD_3FIXED_1FREE = {
        # b/a  : (αx_pos, αy_pos, βx_neg, βy_neg)
        0.5:    (0.006, 0.024, 0.018, 0.068),
        0.75:   (0.012, 0.022, 0.025, 0.052),
        1.0:    (0.018, 0.020, 0.033, 0.042),
        1.25:   (0.023, 0.018, 0.038, 0.035),
        1.5:    (0.027, 0.016, 0.043, 0.031),
        1.75:   (0.030, 0.015, 0.047, 0.028),
        2.0:    (0.032, 0.014, 0.050, 0.026),
        2.5:    (0.035, 0.012, 0.054, 0.023),
        3.0:    (0.037, 0.011, 0.056, 0.021),
        4.0:    (0.038, 0.010, 0.058, 0.019),
        # Khi b/a >= 4, thành bể làm việc như console
    }
    
    # ===========================================
    # CASE 1B: Thành bể - Ngàm 2 cạnh (đáy + 1 bên), tự do 2 cạnh
    # Cho góc bể
    # ===========================================
    
    WALL_TRIANGULAR_LOAD_2FIXED_2FREE = {
        0.5:    (0.003, 0.008, 0.008, 0.032),
        0.75:   (0.006, 0.010, 0.014, 0.030),
        1.0:    (0.010, 0.012, 0.020, 0.028),
        1.25:   (0.014, 0.013, 0.025, 0.027),
        1.5:    (0.018, 0.014, 0.029, 0.026),
        2.0:    (0.023, 0.014, 0.035, 0.024),
    }
    
    # ===========================================
    # CASE 2: Đáy bể - Ngàm 4 cạnh
    # Tải phân bố đều
    # ===========================================
    
    SLAB_UNIFORM_LOAD_4FIXED = {
        # b/a  : (αx_pos, αy_pos, βx_neg, βy_neg)
        1.0:    (0.018, 0.018, 0.051, 0.051),
        1.1:    (0.021, 0.017, 0.055, 0.046),
        1.2:    (0.024, 0.016, 0.059, 0.042),
        1.3:    (0.027, 0.015, 0.062, 0.039),
        1.4:    (0.029, 0.014, 0.065, 0.036),
        1.5:    (0.031, 0.013, 0.067, 0.034),
        1.6:    (0.033, 0.012, 0.069, 0.032),
        1.7:    (0.034, 0.012, 0.071, 0.031),
        1.8:    (0.035, 0.011, 0.072, 0.029),
        1.9:    (0.036, 0.011, 0.073, 0.028),
        2.0:    (0.037, 0.010, 0.074, 0.027),
        2.5:    (0.039, 0.009, 0.077, 0.024),
        3.0:    (0.040, 0.008, 0.078, 0.022),
    }
    
    # ===========================================
    # CASE 3: Đáy bể - Kê 4 cạnh
    # Tải phân bố đều
    # ===========================================
    
    SLAB_UNIFORM_LOAD_4PINNED = {
        # b/a  : (αx, αy) - Chỉ có moment dương
        1.0:    (0.044, 0.044),
        1.1:    (0.050, 0.039),
        1.2:    (0.055, 0.035),
        1.3:    (0.060, 0.032),
        1.4:    (0.064, 0.029),
        1.5:    (0.068, 0.027),
        1.6:    (0.071, 0.025),
        1.7:    (0.074, 0.024),
        1.8:    (0.076, 0.022),
        1.9:    (0.078, 0.021),
        2.0:    (0.080, 0.020),
        2.5:    (0.085, 0.016),
        3.0:    (0.088, 0.014),
    }
    
    # ===========================================
    # CASE 4: Đáy bể - Kê 2 cạnh đối nhau, ngàm 2 cạnh kia
    # ===========================================
    
    SLAB_UNIFORM_LOAD_2FIXED_2PINNED = {
        # b/a (cạnh ngàm / cạnh kê)
        1.0:    (0.028, 0.028, 0.058, 0.000),
        1.2:    (0.035, 0.024, 0.068, 0.000),
        1.5:    (0.045, 0.018, 0.080, 0.000),
        2.0:    (0.055, 0.013, 0.090, 0.000),
    }
    
    @classmethod
    def interpolate_coefficients(
        cls,
        table: Dict[float, Tuple],
        ratio: float
    ) -> Tuple:
        """
        Nội suy tuyến tính các hệ số từ bảng
        
        Args:
            table: Bảng tra (dict)
            ratio: Tỷ lệ cạnh b/a
        """
        ratios = sorted(table.keys())
        
        # Kiểm tra biên
        if ratio <= ratios[0]:
            return table[ratios[0]]
        if ratio >= ratios[-1]:
            return table[ratios[-1]]
        
        # Tìm 2 giá trị bao quanh
        for i in range(len(ratios) - 1):
            r1, r2 = ratios[i], ratios[i + 1]
            if r1 <= ratio <= r2:
                # Nội suy
                t = (ratio - r1) / (r2 - r1)
                coef1 = table[r1]
                coef2 = table[r2]
                
                result = tuple(
                    c1 + t * (c2 - c1) 
                    for c1, c2 in zip(coef1, coef2)
                )
                return result
        
        return table[ratios[-1]]
    
    @classmethod
    def calculate_wall_moment(
        cls,
        height: float,              # Chiều cao thành (m) - cạnh a
        width: float,               # Chiều rộng bể (m) - cạnh b (nhịp)
        water_depth: float,         # Chiều sâu nước (m)
        gamma_water: float = 10.0,  # Trọng lượng riêng nước (kN/m³)
        surcharge: float = 0.0,     # Tải mặt đất (kN/m², nếu là bể chôn)
        Ka: float = 0.33,           # Hệ số áp lực đất chủ động
        load_factor: float = 1.2,   # Hệ số tải trọng
        boundary_type: str = "3fixed_1free"  # "3fixed_1free" hoặc "2fixed_2free"
    ) -> MomentResult:
        """
        Tính moment trong thành bể theo phương pháp tra bảng
        
        Điều kiện biên mặc định:
        - Cạnh dưới: Ngàm với đáy
        - 2 cạnh bên: Ngàm với thành kế bên
        - Cạnh trên: Tự do (mặt nước)
        
        Tải trọng: Tam giác (áp lực thủy tĩnh)
        - q = 0 tại mặt nước
        - q_max = gamma × H tại đáy
        
        Args:
            height: Chiều cao thành (m)
            width: Chiều rộng/nhịp thành (m)
            water_depth: Chiều sâu nước (m)
            gamma_water: Trọng lượng riêng nước (kN/m³)
            surcharge: Tải mặt đất nếu bể chôn (kN/m²)
            Ka: Hệ số áp lực đất chủ động
            load_factor: Hệ số tải trọng
            boundary_type: Loại điều kiện biên
        
        Returns:
            MomentResult: Kết quả moment
        """
        # Cạnh ngắn a = H (chiều cao)
        a = height
        # Cạnh dài b = W (chiều rộng bể)
        b = width
        
        # Tỷ lệ cạnh
        ratio = b / a if a > 0 else 1.0
        
        # Áp lực max tại đáy
        q_water = gamma_water * water_depth  # kN/m²
        
        # Nếu có áp lực đất (bể chôn)
        if surcharge > 0:
            q_soil = Ka * surcharge  # Phần đều từ hoạt tải
            # Phần tam giác từ đất sẽ được tính riêng
        else:
            q_soil = 0
        
        # Áp lực thiết kế (đã nhân hệ số)
        q_max = (q_water + q_soil) * load_factor
        
        # Tra bảng hệ số
        if boundary_type == "3fixed_1free":
            table = cls.WALL_TRIANGULAR_LOAD_3FIXED_1FREE
        else:
            table = cls.WALL_TRIANGULAR_LOAD_2FIXED_2FREE
        
        coeffs = cls.interpolate_coefficients(table, ratio)
        
        if len(coeffs) == 4:
            alpha_x, alpha_y, beta_x, beta_y = coeffs
        else:
            alpha_x, alpha_y = coeffs[:2]
            beta_x, beta_y = 0, 0
        
        # Tính moment
        # M = alpha × q_max × a²
        Mx_positive = alpha_x * q_max * a ** 2  # kN.m/m
        My_positive = alpha_y * q_max * a ** 2  # kN.m/m
        
        # Moment âm tại gối
        Mx_negative = beta_x * q_max * a ** 2   # kN.m/m
        My_negative = beta_y * q_max * a ** 2   # kN.m/m
        
        return MomentResult(
            Mx_positive=round(Mx_positive, 2),
            My_positive=round(My_positive, 2),
            Mx_negative=round(Mx_negative, 2),
            My_negative=round(My_negative, 2),
            location_description=f"Mx+ tại giữa nhịp, My+ tại 0.3H từ đáy, M- tại gối",
            alpha_x=round(alpha_x, 4),
            alpha_y=round(alpha_y, 4),
            beta_x=round(beta_x, 4),
            beta_y=round(beta_y, 4)
        )
    
    @classmethod
    def calculate_slab_moment(
        cls,
        length: float,              # Chiều dài đáy (m)
        width: float,               # Chiều rộng đáy (m)
        load: float,                # Tải phân bố (kN/m²)
        load_factor: float = 1.2,
        boundary_condition: str = "4fixed"  # "4fixed", "4pinned", "2fixed_2pinned"
    ) -> MomentResult:
        """
        Tính moment trong đáy bể theo phương pháp tra bảng
        
        Args:
            length: Chiều dài đáy (m)
            width: Chiều rộng đáy (m)
            load: Tải phân bố (kN/m²)
            load_factor: Hệ số tải trọng
            boundary_condition: Điều kiện biên
        
        Returns:
            MomentResult: Kết quả moment
        """
        # Xác định cạnh ngắn và cạnh dài
        a = min(length, width)  # Cạnh ngắn
        b = max(length, width)  # Cạnh dài
        
        ratio = b / a
        
        # Tải thiết kế
        q = load * load_factor
        
        # Tra bảng
        if boundary_condition == "4fixed":
            table = cls.SLAB_UNIFORM_LOAD_4FIXED
            coeffs = cls.interpolate_coefficients(table, ratio)
            alpha_x, alpha_y, beta_x, beta_y = coeffs
        elif boundary_condition == "4pinned":
            table = cls.SLAB_UNIFORM_LOAD_4PINNED
            coeffs = cls.interpolate_coefficients(table, ratio)
            alpha_x, alpha_y = coeffs
            beta_x = beta_y = 0
        else:  # 2fixed_2pinned
            table = cls.SLAB_UNIFORM_LOAD_2FIXED_2PINNED
            coeffs = cls.interpolate_coefficients(table, ratio)
            alpha_x, alpha_y, beta_x, beta_y = coeffs
        
        # Tính moment
        Mx_positive = alpha_x * q * a ** 2
        My_positive = alpha_y * q * a ** 2
        Mx_negative = beta_x * q * a ** 2
        My_negative = beta_y * q * a ** 2
        
        return MomentResult(
            Mx_positive=round(Mx_positive, 2),
            My_positive=round(My_positive, 2),
            Mx_negative=round(Mx_negative, 2),
            My_negative=round(My_negative, 2),
            location_description="M+ tại giữa bản, M- tại gối (cạnh ngàm)",
            alpha_x=round(alpha_x, 4),
            alpha_y=round(alpha_y, 4),
            beta_x=round(beta_x, 4),
            beta_y=round(beta_y, 4)
        )
    
    @classmethod
    def get_moment_envelope(
        cls,
        height: float,
        width: float,
        water_depth: float,
        load_cases: Optional[list] = None
    ) -> Dict[str, MomentResult]:
        """
        Tính envelope moment cho các tổ hợp tải trọng
        
        Returns:
            Dict với key là tên tổ hợp, value là MomentResult
        """
        if load_cases is None:
            load_cases = [
                {"name": "LC1_BeDayKhongDat", "water": True, "soil": False, "factor": 1.2},
                {"name": "LC2_BeRongCoDat", "water": False, "soil": True, "factor": 1.2},
                {"name": "LC3_BeDayCoDat", "water": True, "soil": True, "factor": 1.35},
            ]
        
        results = {}
        
        for lc in load_cases:
            surcharge = 10.0 if lc.get("soil", False) else 0.0
            effective_depth = water_depth if lc.get("water", True) else 0.0
            
            if effective_depth > 0 or surcharge > 0:
                result = cls.calculate_wall_moment(
                    height=height,
                    width=width,
                    water_depth=effective_depth,
                    surcharge=surcharge,
                    load_factor=lc.get("factor", 1.2)
                )
                results[lc["name"]] = result
        
        return results


class AdvancedWallDesign:
    """
    Thiết kế thành bể nâng cao với phương pháp tra bảng
    
    Sử dụng bảng PCA và TCVN cho các loại điều kiện biên khác nhau
    """
    
    @classmethod
    def design_tank_wall(
        cls,
        height: float,
        width: float,
        water_depth: float,
        wall_thickness: float = 0.25,
        concrete_grade: str = "B25",
        steel_grade: str = "CB400-V",
        cover: float = 40,  # mm
        environment: str = "moderate"  # "mild", "moderate", "severe"
    ) -> Dict[str, Any]:
        """
        Thiết kế hoàn chỉnh thành bể
        
        Args:
            height: Chiều cao thành (m)
            width: Chiều rộng bể (m) - nhịp thành
            water_depth: Chiều sâu nước (m)
            wall_thickness: Chiều dày thành (m)
            concrete_grade: Mác bê tông
            steel_grade: Mác thép
            cover: Lớp bảo vệ (mm)
            environment: Điều kiện môi trường
        
        Returns:
            Dict: Kết quả thiết kế đầy đủ
        """
        from calculations.crack_control import CrackWidthChecker
        from rules.structural_rules import StructuralRules
        
        result = {
            "input": {
                "height": height,
                "width": width,
                "water_depth": water_depth,
                "wall_thickness": wall_thickness,
                "concrete_grade": concrete_grade,
                "steel_grade": steel_grade,
                "cover": cover
            },
            "geometry": {},
            "internal_forces": {},
            "reinforcement": {},
            "crack_check": {},
            "validation": []
        }
        
        # 1. Tính nội lực bằng phương pháp tra bảng
        moment_results = PlateMomentTables.get_moment_envelope(
            height=height,
            width=width,
            water_depth=water_depth
        )
        
        # Tìm moment max
        max_Mx_pos = max(m.Mx_positive for m in moment_results.values())
        max_My_pos = max(m.My_positive for m in moment_results.values())
        max_Mx_neg = max(m.Mx_negative for m in moment_results.values())
        max_My_neg = max(m.My_negative for m in moment_results.values())
        
        result["internal_forces"] = {
            "load_cases": {
                name: {
                    "Mx_positive": m.Mx_positive,
                    "My_positive": m.My_positive,
                    "Mx_negative": m.Mx_negative,
                    "My_negative": m.My_negative,
                    "alpha_x": m.alpha_x,
                    "alpha_y": m.alpha_y,
                    "beta_x": m.beta_x,
                    "beta_y": m.beta_y
                }
                for name, m in moment_results.items()
            },
            "envelope": {
                "Mx_positive_max": max_Mx_pos,
                "My_positive_max": max_My_pos,
                "Mx_negative_max": max_Mx_neg,
                "My_negative_max": max_My_neg
            },
            "method": "PCA_TABLE_LOOKUP"
        }
        
        # 2. Tính cốt thép
        effective_depth = wall_thickness - cover / 1000 - 0.01  # m
        
        # Cốt thép dọc (chịu Mx)
        reinf_vertical = StructuralRules.calculate_required_reinforcement(
            moment=max(max_Mx_pos, max_Mx_neg),
            width=1.0,
            effective_depth=effective_depth,
            concrete_grade=concrete_grade,
            steel_grade=steel_grade
        )
        
        # Cốt thép ngang (chịu My)
        reinf_horizontal = StructuralRules.calculate_required_reinforcement(
            moment=max(max_My_pos, max_My_neg),
            width=1.0,
            effective_depth=effective_depth - 0.012,  # Lớp trong
            concrete_grade=concrete_grade,
            steel_grade=steel_grade
        )
        
        result["reinforcement"] = {
            "vertical_main": reinf_vertical,
            "horizontal_main": reinf_horizontal,
            "distribution": {
                "note": "Thép phân bố mặt ngoài",
                "vertical": "φ10a200 (As = 393 mm²/m)",
                "horizontal": "φ10a200 (As = 393 mm²/m)"
            }
        }
        
        # 3. Kiểm tra nứt (nếu module có sẵn)
        try:
            crack_result = CrackWidthChecker.check_crack_width(
                moment=max(max_Mx_pos, max_Mx_neg),
                width=1000,  # mm
                height=wall_thickness * 1000,  # mm
                As=reinf_vertical.get("As_provided", 800),
                cover=cover,
                bar_diameter=12,
                concrete_grade=concrete_grade,
                steel_grade=steel_grade,
                environment=environment
            )
            result["crack_check"] = crack_result
        except Exception:
            result["crack_check"] = {
                "note": "Module kiểm toán nứt chưa được triển khai"
            }
        
        # 4. Tổng hợp khuyến nghị
        result["recommendations"] = cls._generate_recommendations(
            height, width, wall_thickness, reinf_vertical, reinf_horizontal
        )
        
        return result
    
    @staticmethod
    def _generate_recommendations(
        height: float,
        width: float,
        thickness: float,
        reinf_v: dict,
        reinf_h: dict
    ) -> Dict[str, str]:
        """Tạo khuyến nghị thiết kế"""
        return {
            "wall_thickness": f"Chiều dày thành {thickness*1000:.0f}mm phù hợp cho chiều cao {height}m",
            "vertical_rebar": f"Thép đứng 2 lớp: {reinf_v.get('reinforcement', 'φ12a200')}",
            "horizontal_rebar": f"Thép ngang 2 lớp: {reinf_h.get('reinforcement', 'φ12a250')}",
            "construction_joint": f"Mạch thi công ngang tại cao độ +{height/2:.1f}m",
            "water_bar": "Băng cản nước PVC 320mm tại mạch thi công",
            "concrete_grade": "Sử dụng bê tông chống thấm mác W6"
        }
