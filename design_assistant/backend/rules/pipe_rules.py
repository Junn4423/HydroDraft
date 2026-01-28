"""
Pipe Rules - Quy tắc thiết kế đường ống

Bao gồm:
- Đường ống tự chảy (gravity)
- Đường ống áp lực (pressure)
- Thoát nước mưa/thải
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from .engine import RuleResult, RuleStatus
import math

@dataclass
class PipeDesignLimits:
    """Giới hạn thiết kế đường ống"""
    min_velocity: float         # Vận tốc tối thiểu (m/s)
    max_velocity: float         # Vận tốc tối đa (m/s)
    min_slope: float            # Độ dốc tối thiểu (%)
    max_slope: float            # Độ dốc tối đa (%)
    min_cover: float            # Độ sâu chôn ống tối thiểu (m)
    max_cover: float            # Độ sâu chôn ống tối đa (m)
    min_fill_ratio: float       # Tỷ lệ đầy tối thiểu (%)
    max_fill_ratio: float       # Tỷ lệ đầy tối đa (%)


class PipeRules:
    """
    Quy tắc thiết kế đường ống
    
    Tham chiếu tiêu chuẩn:
    - TCVN 7957:2008 - Thoát nước
    - TCVN 33:2006 - Cấp nước
    - TCVN 4513:1988 - Cấp nước bên trong
    """
    
    # Giới hạn theo loại đường ống
    DESIGN_LIMITS = {
        "gravity_sewer": PipeDesignLimits(
            min_velocity=0.6,
            max_velocity=4.0,
            min_slope=0.3,
            max_slope=15.0,
            min_cover=0.7,
            max_cover=8.0,
            min_fill_ratio=20,
            max_fill_ratio=80
        ),
        "gravity_drain": PipeDesignLimits(
            min_velocity=0.6,
            max_velocity=6.0,
            min_slope=0.2,
            max_slope=20.0,
            min_cover=0.5,
            max_cover=6.0,
            min_fill_ratio=10,
            max_fill_ratio=90
        ),
        "pressure": PipeDesignLimits(
            min_velocity=0.5,
            max_velocity=3.0,
            min_slope=0.0,
            max_slope=100.0,
            min_cover=0.8,
            max_cover=3.0,
            min_fill_ratio=100,
            max_fill_ratio=100
        ),
        "water_supply": PipeDesignLimits(
            min_velocity=0.5,
            max_velocity=2.5,
            min_slope=0.0,
            max_slope=100.0,
            min_cover=0.8,
            max_cover=2.5,
            min_fill_ratio=100,
            max_fill_ratio=100
        )
    }
    
    # Hệ số nhám Manning theo vật liệu
    MANNING_ROUGHNESS = {
        "concrete": 0.013,
        "hdpe": 0.009,
        "pvc": 0.009,
        "upvc": 0.009,
        "ductile_iron": 0.012,
        "steel": 0.011,
        "stainless": 0.010,
        "composite": 0.010
    }
    
    # Đường kính tiêu chuẩn (mm)
    STANDARD_DIAMETERS = [
        100, 150, 200, 250, 300, 350, 400, 450, 500,
        600, 700, 800, 900, 1000, 1200, 1400, 1500,
        1600, 1800, 2000, 2200, 2400, 2500, 3000
    ]
    
    # Độ dốc tối thiểu theo đường kính (cho tự chảy)
    MIN_SLOPE_BY_DIAMETER = {
        150: 0.8,   # D150: i_min = 0.8%
        200: 0.5,   # D200: i_min = 0.5%
        250: 0.4,
        300: 0.3,
        350: 0.25,
        400: 0.2,
        450: 0.18,
        500: 0.15,
        600: 0.12,
        700: 0.1,
        800: 0.08,
        900: 0.07,
        1000: 0.06,
        1200: 0.05,
        1500: 0.04,
        2000: 0.03
    }
    
    @classmethod
    def get_limits(cls, pipe_type: str) -> PipeDesignLimits:
        """Lấy giới hạn thiết kế theo loại ống"""
        return cls.DESIGN_LIMITS.get(pipe_type, cls.DESIGN_LIMITS["gravity_sewer"])
    
    @classmethod
    def get_manning_n(cls, material: str) -> float:
        """Lấy hệ số nhám Manning"""
        return cls.MANNING_ROUGHNESS.get(material, 0.013)
    
    @classmethod
    def get_min_slope(cls, diameter: float) -> float:
        """Lấy độ dốc tối thiểu theo đường kính"""
        for d, slope in sorted(cls.MIN_SLOPE_BY_DIAMETER.items()):
            if diameter <= d:
                return slope
        return 0.03  # Mặc định cho đường kính lớn
    
    @classmethod
    def get_nearest_standard_diameter(cls, diameter: float) -> float:
        """Lấy đường kính tiêu chuẩn gần nhất (lớn hơn)"""
        for std_d in cls.STANDARD_DIAMETERS:
            if std_d >= diameter:
                return std_d
        return cls.STANDARD_DIAMETERS[-1]
    
    @classmethod
    def validate_velocity(
        cls,
        pipe_type: str,
        velocity: float
    ) -> RuleResult:
        """Kiểm tra vận tốc dòng chảy"""
        if velocity is None:
            return RuleResult(
                rule_id="velocity",
                rule_name="Vận tốc dòng chảy",
                parameter="velocity",
                value=None,
                status=RuleStatus.WARNING,
                message="Chưa có dữ liệu vận tốc dòng chảy",
                standard="TCVN 7957:2008"
            )
        limits = cls.get_limits(pipe_type)
        
        if velocity < limits.min_velocity:
            return RuleResult(
                rule_id="velocity",
                rule_name="Vận tốc dòng chảy",
                parameter="velocity",
                value=velocity,
                status=RuleStatus.FAIL,
                message=f"Vận tốc {velocity:.2f} m/s nhỏ hơn tối thiểu {limits.min_velocity} m/s",
                suggestion="Tăng độ dốc hoặc giảm đường kính để tăng vận tốc tự rửa",
                standard="TCVN 7957:2008"
            )
        elif velocity > limits.max_velocity:
            return RuleResult(
                rule_id="velocity",
                rule_name="Vận tốc dòng chảy",
                parameter="velocity",
                value=velocity,
                status=RuleStatus.FAIL,
                message=f"Vận tốc {velocity:.2f} m/s vượt tối đa {limits.max_velocity} m/s",
                suggestion="Giảm độ dốc hoặc tăng đường kính để giảm xói mòn",
                standard="TCVN 7957:2008"
            )
        
        return RuleResult(
            rule_id="velocity",
            rule_name="Vận tốc dòng chảy",
            parameter="velocity",
            value=velocity,
            status=RuleStatus.PASS,
            message=f"Vận tốc {velocity:.2f} m/s đạt yêu cầu",
            standard="TCVN 7957:2008"
        )
    
    @classmethod
    def validate_slope(
        cls,
        pipe_type: str,
        diameter: float,
        slope: float
    ) -> RuleResult:
        """Kiểm tra độ dốc đường ống"""
        if slope is None or diameter is None:
            return RuleResult(
                rule_id="slope",
                rule_name="Độ dốc đường ống",
                parameter="slope",
                value=slope,
                status=RuleStatus.WARNING,
                message="Chưa có dữ liệu độ dốc hoặc đường kính",
                standard="TCVN 7957:2008"
            )
        limits = cls.get_limits(pipe_type)
        min_slope = cls.get_min_slope(diameter)
        
        if slope < min_slope:
            return RuleResult(
                rule_id="slope",
                rule_name="Độ dốc đường ống",
                parameter="slope",
                value=slope,
                status=RuleStatus.FAIL,
                message=f"Độ dốc {slope:.2f}% nhỏ hơn tối thiểu {min_slope}% cho D{diameter}",
                suggestion=f"Tăng độ dốc lên ≥ {min_slope}% hoặc sử dụng đường kính nhỏ hơn",
                standard="TCVN 7957:2008"
            )
        elif slope > limits.max_slope:
            return RuleResult(
                rule_id="slope",
                rule_name="Độ dốc đường ống",
                parameter="slope",
                value=slope,
                status=RuleStatus.WARNING,
                message=f"Độ dốc {slope:.2f}% lớn hơn khuyến nghị {limits.max_slope}%",
                suggestion="Xem xét sử dụng giếng thả bậc hoặc công trình giảm năng lượng",
                standard="TCVN 7957:2008"
            )
        
        return RuleResult(
            rule_id="slope",
            rule_name="Độ dốc đường ống",
            parameter="slope",
            value=slope,
            status=RuleStatus.PASS,
            message=f"Độ dốc {slope:.2f}% đạt yêu cầu",
            standard="TCVN 7957:2008"
        )
    
    @classmethod
    def validate_cover_depth(
        cls,
        pipe_type: str,
        cover_depth: float
    ) -> RuleResult:
        """Kiểm tra độ sâu chôn ống"""
        limits = cls.get_limits(pipe_type)
        
        if cover_depth < limits.min_cover:
            return RuleResult(
                rule_id="cover_depth",
                rule_name="Độ sâu chôn ống",
                parameter="cover_depth",
                value=cover_depth,
                status=RuleStatus.FAIL,
                message=f"Độ sâu chôn {cover_depth:.2f}m nhỏ hơn tối thiểu {limits.min_cover}m",
                suggestion=f"Hạ cao độ đáy ống để đảm bảo lớp phủ ≥ {limits.min_cover}m",
                standard="TCVN 7957:2008"
            )
        elif cover_depth > limits.max_cover:
            return RuleResult(
                rule_id="cover_depth",
                rule_name="Độ sâu chôn ống",
                parameter="cover_depth",
                value=cover_depth,
                status=RuleStatus.WARNING,
                message=f"Độ sâu chôn {cover_depth:.2f}m lớn hơn thông thường {limits.max_cover}m",
                suggestion="Xem xét sử dụng trạm bơm trung chuyển",
                standard="TCVN 7957:2008"
            )
        
        return RuleResult(
            rule_id="cover_depth",
            rule_name="Độ sâu chôn ống",
            parameter="cover_depth",
            value=cover_depth,
            status=RuleStatus.PASS,
            message=f"Độ sâu chôn {cover_depth:.2f}m đạt yêu cầu",
            standard="TCVN 7957:2008"
        )
    
    @classmethod
    def validate_fill_ratio(
        cls,
        pipe_type: str,
        fill_ratio: float
    ) -> RuleResult:
        """Kiểm tra tỷ lệ đầy ống"""
        limits = cls.get_limits(pipe_type)
        
        if fill_ratio > limits.max_fill_ratio:
            return RuleResult(
                rule_id="fill_ratio",
                rule_name="Tỷ lệ đầy ống",
                parameter="fill_ratio",
                value=fill_ratio,
                status=RuleStatus.FAIL,
                message=f"Tỷ lệ đầy {fill_ratio:.1f}% vượt tối đa {limits.max_fill_ratio}%",
                suggestion="Tăng đường kính ống hoặc độ dốc",
                standard="TCVN 7957:2008"
            )
        elif fill_ratio < limits.min_fill_ratio:
            return RuleResult(
                rule_id="fill_ratio",
                rule_name="Tỷ lệ đầy ống",
                parameter="fill_ratio",
                value=fill_ratio,
                status=RuleStatus.WARNING,
                message=f"Tỷ lệ đầy {fill_ratio:.1f}% thấp hơn khuyến nghị {limits.min_fill_ratio}%",
                suggestion="Xem xét sử dụng đường kính nhỏ hơn",
                standard="TCVN 7957:2008"
            )
        
        return RuleResult(
            rule_id="fill_ratio",
            rule_name="Tỷ lệ đầy ống",
            parameter="fill_ratio",
            value=fill_ratio,
            status=RuleStatus.PASS,
            message=f"Tỷ lệ đầy {fill_ratio:.1f}% đạt yêu cầu",
            standard="TCVN 7957:2008"
        )
    
    @classmethod
    def validate_reynolds_number(
        cls,
        reynolds: float
    ) -> RuleResult:
        """Kiểm tra số Reynolds và chế độ chảy"""
        if reynolds < 2300:
            regime = "chảy tầng (laminar)"
            status = RuleStatus.WARNING
            message = f"Re = {reynolds:.0f} - Chế độ chảy tầng, có thể gây lắng đọng"
        elif reynolds < 4000:
            regime = "chuyển tiếp (transitional)"
            status = RuleStatus.PASS
            message = f"Re = {reynolds:.0f} - Chế độ chuyển tiếp"
        else:
            regime = "chảy rối (turbulent)"
            status = RuleStatus.PASS
            message = f"Re = {reynolds:.0f} - Chế độ chảy rối, tốt cho vận chuyển"
        
        return RuleResult(
            rule_id="reynolds_number",
            rule_name="Số Reynolds",
            parameter="reynolds",
            value=reynolds,
            status=status,
            message=message,
            standard="Thủy lực học"
        )
    
    @classmethod
    def validate_pipe_design(
        cls,
        pipe_type: str,
        params: Dict[str, Any]
    ) -> List[RuleResult]:
        """
        Kiểm tra toàn bộ thiết kế đường ống
        
        Args:
            pipe_type: Loại đường ống
            params: Dict chứa các thông số thiết kế
            
        Returns:
            List[RuleResult]: Danh sách kết quả kiểm tra
        """
        results = []
        
        # Kiểm tra vận tốc
        if "velocity" in params:
            results.append(cls.validate_velocity(pipe_type, params["velocity"]))
        
        # Kiểm tra độ dốc
        if "slope" in params and "diameter" in params:
            results.append(cls.validate_slope(pipe_type, params["diameter"], params["slope"]))
        
        # Kiểm tra độ sâu chôn ống
        if "cover_depth" in params:
            results.append(cls.validate_cover_depth(pipe_type, params["cover_depth"]))
        
        # Kiểm tra tỷ lệ đầy
        if "fill_ratio" in params:
            results.append(cls.validate_fill_ratio(pipe_type, params["fill_ratio"]))
        
        # Kiểm tra số Reynolds
        if "reynolds" in params:
            results.append(cls.validate_reynolds_number(params["reynolds"]))
        
        return results
    
    @classmethod
    def calculate_recommended_diameter(
        cls,
        design_flow: float,      # m³/s
        slope: float,            # %
        material: str = "hdpe",
        fill_ratio: float = 0.7  # Tỷ lệ đầy thiết kế
    ) -> Dict[str, Any]:
        """
        Tính đường kính ống khuyến nghị
        
        Args:
            design_flow: Lưu lượng thiết kế (m³/s)
            slope: Độ dốc (%)
            material: Vật liệu ống
            fill_ratio: Tỷ lệ đầy thiết kế
            
        Returns:
            Dict: Đường kính và thông số tính toán
        """
        n = cls.get_manning_n(material)
        slope_decimal = slope / 100
        
        # Công thức Manning cho ống tròn đầy
        # Q = (1/n) * A * R^(2/3) * S^(1/2)
        # Với ống tròn đầy: A = π*D²/4, R = D/4
        
        # Tính đường kính cần thiết (ống đầy)
        # D = [(Q * n * 4^(5/3)) / (π * S^0.5)]^(3/8)
        
        D_full = ((design_flow * n * (4 ** (5/3))) / (math.pi * (slope_decimal ** 0.5))) ** (3/8)
        
        # Điều chỉnh cho fill_ratio
        D_required = D_full / (fill_ratio ** 0.5) * 1000  # mm
        
        # Lấy đường kính tiêu chuẩn
        D_standard = cls.get_nearest_standard_diameter(D_required)
        
        return {
            "calculated_diameter": round(D_required, 0),
            "recommended_diameter": D_standard,
            "material": material,
            "manning_n": n
        }
