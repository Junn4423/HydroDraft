"""
Structural Rules - Quy tắc thiết kế kết cấu

Bao gồm:
- Kiểm tra kết cấu bể
- Kiểm tra áp lực thành
- Kiểm tra ổn định
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from .engine import RuleResult, RuleStatus
import math

@dataclass
class StructuralLimits:
    """Giới hạn kết cấu"""
    min_safety_factor: float        # Hệ số an toàn tối thiểu
    max_stress_ratio: float         # Tỷ lệ ứng suất tối đa
    min_wall_thickness: float       # Chiều dày thành tối thiểu (m)
    max_deflection_ratio: float     # Tỷ lệ biến dạng tối đa (L/xxx)
    min_cover: float                # Lớp bê tông bảo vệ tối thiểu (mm)


class StructuralRules:
    """
    Quy tắc thiết kế kết cấu
    
    Tham chiếu tiêu chuẩn:
    - TCVN 5574:2018 - Kết cấu bê tông và bê tông cốt thép
    - TCVN 2737:1995 - Tải trọng và tác động
    - TCVN 9386:2012 - Thiết kế công trình chịu động đất
    """
    
    # Giới hạn kết cấu theo loại công trình
    STRUCTURAL_LIMITS = {
        "tank": StructuralLimits(
            min_safety_factor=1.5,
            max_stress_ratio=0.85,
            min_wall_thickness=0.20,
            max_deflection_ratio=250,  # L/250
            min_cover=40
        ),
        "foundation": StructuralLimits(
            min_safety_factor=2.0,
            max_stress_ratio=0.80,
            min_wall_thickness=0.30,
            max_deflection_ratio=500,  # L/500
            min_cover=50
        ),
        "pipe_support": StructuralLimits(
            min_safety_factor=1.5,
            max_stress_ratio=0.85,
            min_wall_thickness=0.15,
            max_deflection_ratio=300,
            min_cover=35
        )
    }
    
    # Cường độ vật liệu (MPa)
    MATERIAL_STRENGTH = {
        "concrete": {
            "B15": {"fc": 8.5, "fct": 0.75},    # Bê tông B15
            "B20": {"fc": 11.5, "fct": 0.90},   # Bê tông B20
            "B25": {"fc": 14.5, "fct": 1.05},   # Bê tông B25
            "B30": {"fc": 17.0, "fct": 1.15},   # Bê tông B30
            "B35": {"fc": 19.5, "fct": 1.25}    # Bê tông B35
        },
        "steel": {
            "CB240-T": {"fy": 240, "fu": 380},  # Thép CB240-T
            "CB300-V": {"fy": 300, "fu": 450},  # Thép CB300-V
            "CB400-V": {"fy": 400, "fu": 570}   # Thép CB400-V
        }
    }
    
    # Trọng lượng riêng vật liệu (kN/m³)
    UNIT_WEIGHT = {
        "water": 10.0,
        "concrete": 25.0,
        "soil": 18.0,
        "saturated_soil": 20.0,
        "sludge": 12.0
    }
    
    # Hệ số tải trọng
    LOAD_FACTORS = {
        "dead_load": 1.1,       # Tĩnh tải
        "live_load": 1.3,       # Hoạt tải
        "water_load": 1.2,      # Tải trọng nước
        "soil_load": 1.2,       # Áp lực đất
        "seismic": 1.0          # Tải trọng động đất
    }
    
    @classmethod
    def get_limits(cls, structure_type: str) -> StructuralLimits:
        """Lấy giới hạn kết cấu theo loại công trình"""
        return cls.STRUCTURAL_LIMITS.get(structure_type, cls.STRUCTURAL_LIMITS["tank"])
    
    @classmethod
    def calculate_wall_pressure(
        cls,
        depth: float,           # Chiều sâu nước (m)
        include_surcharge: bool = False,
        surcharge: float = 10.0  # Hoạt tải mặt đất (kN/m²)
    ) -> Dict[str, float]:
        """
        Tính áp lực tác dụng lên thành bể
        
        Args:
            depth: Chiều sâu nước (m)
            include_surcharge: Có tính hoạt tải mặt đất không
            surcharge: Hoạt tải mặt đất (kN/m²)
            
        Returns:
            Dict: Các giá trị áp lực
        """
        gamma_w = cls.UNIT_WEIGHT["water"]
        
        # Áp lực nước (tam giác)
        water_pressure_max = gamma_w * depth  # kN/m² tại đáy
        water_force = 0.5 * water_pressure_max * depth  # kN/m chiều dài
        water_moment_arm = depth / 3  # Từ đáy
        
        result = {
            "water_pressure_max": water_pressure_max,
            "water_force": water_force,
            "water_moment_arm": water_moment_arm,
            "water_moment": water_force * water_moment_arm
        }
        
        # Áp lực đất (khi bể chôn)
        if include_surcharge:
            Ka = 0.33  # Hệ số áp lực đất chủ động (giả định)
            gamma_s = cls.UNIT_WEIGHT["soil"]
            
            soil_pressure_max = Ka * gamma_s * depth + Ka * surcharge
            soil_force = 0.5 * Ka * gamma_s * depth ** 2 + Ka * surcharge * depth
            
            result.update({
                "soil_pressure_max": soil_pressure_max,
                "soil_force": soil_force,
                "surcharge_effect": Ka * surcharge * depth
            })
        
        return result
    
    @classmethod
    def validate_wall_thickness(
        cls,
        structure_type: str,
        wall_thickness: float,
        depth: float
    ) -> RuleResult:
        """Kiểm tra chiều dày thành"""
        limits = cls.get_limits(structure_type)
        
        # Chiều dày tối thiểu theo chiều sâu
        min_thickness = max(limits.min_wall_thickness, depth / 15)
        
        if wall_thickness < min_thickness:
            return RuleResult(
                rule_id="wall_thickness",
                rule_name="Chiều dày thành",
                parameter="wall_thickness",
                value=wall_thickness,
                status=RuleStatus.FAIL,
                message=f"Chiều dày {wall_thickness:.2f}m nhỏ hơn tối thiểu {min_thickness:.2f}m",
                suggestion=f"Tăng chiều dày thành lên ≥ {min_thickness:.2f}m",
                standard="TCVN 5574:2018"
            )
        
        return RuleResult(
            rule_id="wall_thickness",
            rule_name="Chiều dày thành",
            parameter="wall_thickness",
            value=wall_thickness,
            status=RuleStatus.PASS,
            message=f"Chiều dày thành {wall_thickness:.2f}m đạt yêu cầu",
            standard="TCVN 5574:2018"
        )
    
    @classmethod
    def validate_safety_factor(
        cls,
        structure_type: str,
        safety_factor: float
    ) -> RuleResult:
        """Kiểm tra hệ số an toàn"""
        limits = cls.get_limits(structure_type)
        
        if safety_factor < limits.min_safety_factor:
            return RuleResult(
                rule_id="safety_factor",
                rule_name="Hệ số an toàn",
                parameter="safety_factor",
                value=safety_factor,
                status=RuleStatus.FAIL,
                message=f"Hệ số an toàn {safety_factor:.2f} nhỏ hơn tối thiểu {limits.min_safety_factor}",
                suggestion="Tăng cường kết cấu hoặc giảm tải trọng",
                standard="TCVN 5574:2018"
            )
        elif safety_factor < limits.min_safety_factor * 1.1:
            return RuleResult(
                rule_id="safety_factor",
                rule_name="Hệ số an toàn",
                parameter="safety_factor",
                value=safety_factor,
                status=RuleStatus.WARNING,
                message=f"Hệ số an toàn {safety_factor:.2f} gần với giới hạn tối thiểu",
                suggestion="Xem xét tăng cường để có dự phòng tốt hơn",
                standard="TCVN 5574:2018"
            )
        
        return RuleResult(
            rule_id="safety_factor",
            rule_name="Hệ số an toàn",
            parameter="safety_factor",
            value=safety_factor,
            status=RuleStatus.PASS,
            message=f"Hệ số an toàn {safety_factor:.2f} đạt yêu cầu",
            standard="TCVN 5574:2018"
        )
    
    @classmethod
    def validate_deflection(
        cls,
        structure_type: str,
        deflection: float,
        span: float
    ) -> RuleResult:
        """Kiểm tra độ võng"""
        limits = cls.get_limits(structure_type)
        
        max_deflection = span / limits.max_deflection_ratio * 1000  # mm
        
        if deflection > max_deflection:
            return RuleResult(
                rule_id="deflection",
                rule_name="Độ võng",
                parameter="deflection",
                value=deflection,
                status=RuleStatus.FAIL,
                message=f"Độ võng {deflection:.1f}mm vượt giới hạn L/{limits.max_deflection_ratio} = {max_deflection:.1f}mm",
                suggestion="Tăng chiều cao tiết diện hoặc cường độ vật liệu",
                standard="TCVN 5574:2018"
            )
        
        return RuleResult(
            rule_id="deflection",
            rule_name="Độ võng",
            parameter="deflection",
            value=deflection,
            status=RuleStatus.PASS,
            message=f"Độ võng {deflection:.1f}mm đạt yêu cầu (giới hạn {max_deflection:.1f}mm)",
            standard="TCVN 5574:2018"
        )
    
    @classmethod
    def calculate_required_reinforcement(
        cls,
        moment: float,          # kN.m
        width: float,           # m
        effective_depth: float, # m
        concrete_grade: str = "B25",
        steel_grade: str = "CB300-V"
    ) -> Dict[str, Any]:
        """
        Tính cốt thép yêu cầu cho tiết diện chịu uốn
        
        Args:
            moment: Moment uốn (kN.m)
            width: Chiều rộng tiết diện (m)
            effective_depth: Chiều cao hữu ích (m)
            concrete_grade: Mác bê tông
            steel_grade: Mác thép
            
        Returns:
            Dict: Diện tích cốt thép yêu cầu
        """
        # Lấy cường độ vật liệu
        fc = cls.MATERIAL_STRENGTH["concrete"][concrete_grade]["fc"]  # MPa
        fy = cls.MATERIAL_STRENGTH["steel"][steel_grade]["fy"]  # MPa
        
        # Đổi đơn vị
        M = moment * 1e6  # N.mm
        b = width * 1000  # mm
        d = effective_depth * 1000  # mm
        
        # Tính hệ số αm
        alpha_m = M / (fc * b * d ** 2)
        
        # Kiểm tra điều kiện
        alpha_R = 0.427  # Giới hạn vùng nén tối đa
        
        if alpha_m > alpha_R:
            # Cần cốt thép chịu nén
            result = {
                "status": "compression_steel_required",
                "message": "Tiết diện cần cốt thép chịu nén",
                "alpha_m": alpha_m
            }
        else:
            # Chỉ cần cốt thép chịu kéo
            xi = 1 - math.sqrt(1 - 2 * alpha_m)
            As = xi * fc * b * d / fy  # mm²
            
            # Cốt thép tối thiểu
            As_min = 0.001 * b * d  # 0.1%
            As = max(As, As_min)
            
            # Tính đường kính và số thanh
            # Giả định thanh φ12
            As_bar = math.pi * 12 ** 2 / 4  # mm²
            n_bars = math.ceil(As / As_bar)
            spacing = (b - 2 * 40) / (n_bars - 1) if n_bars > 1 else 0  # mm
            
            result = {
                "status": "ok",
                "alpha_m": round(alpha_m, 4),
                "xi": round(xi, 4),
                "As_required": round(As, 0),  # mm²
                "As_min": round(As_min, 0),
                "As_provided": round(n_bars * As_bar, 0),
                "reinforcement": f"{n_bars}φ12",
                "spacing": round(spacing, 0),
                "ratio": round(As / (b * d) * 100, 3)  # %
            }
        
        return result
    
    @classmethod
    def validate_structural_design(
        cls,
        structure_type: str,
        params: Dict[str, Any]
    ) -> List[RuleResult]:
        """
        Kiểm tra toàn bộ thiết kế kết cấu
        
        Args:
            structure_type: Loại kết cấu
            params: Dict chứa các thông số thiết kế
            
        Returns:
            List[RuleResult]: Danh sách kết quả kiểm tra
        """
        results = []
        
        # Kiểm tra chiều dày thành
        if "wall_thickness" in params and "depth" in params:
            results.append(cls.validate_wall_thickness(
                structure_type, params["wall_thickness"], params["depth"]
            ))
        
        # Kiểm tra hệ số an toàn
        if "safety_factor" in params:
            results.append(cls.validate_safety_factor(
                structure_type, params["safety_factor"]
            ))
        
        # Kiểm tra độ võng
        if "deflection" in params and "span" in params:
            results.append(cls.validate_deflection(
                structure_type, params["deflection"], params["span"]
            ))
        
        return results
