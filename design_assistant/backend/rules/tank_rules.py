"""
Tank Rules - Quy tắc thiết kế bể

Bao gồm:
- Bể lắng (sedimentation)
- Bể lọc (filtration)
- Bể chứa (storage)
- Bể điều hòa (buffer/equalization)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from .engine import RuleResult, RuleStatus

@dataclass
class TankDesignLimits:
    """Giới hạn thiết kế bể"""
    min_retention_time: float       # Thời gian lưu tối thiểu (giờ)
    max_retention_time: float       # Thời gian lưu tối đa (giờ)
    min_surface_loading: float      # Tải trọng bề mặt tối thiểu (m³/m²/ngày)
    max_surface_loading: float      # Tải trọng bề mặt tối đa (m³/m²/ngày)
    min_depth: float                # Chiều sâu tối thiểu (m)
    max_depth: float                # Chiều sâu tối đa (m)
    min_length_width_ratio: float   # Tỷ lệ L/W tối thiểu
    max_length_width_ratio: float   # Tỷ lệ L/W tối đa
    min_velocity: float             # Vận tốc ngang tối thiểu (m/s)
    max_velocity: float             # Vận tốc ngang tối đa (m/s)
    min_weir_loading: float         # Tải trọng máng tràn tối thiểu (m³/m/ngày)
    max_weir_loading: float         # Tải trọng máng tràn tối đa (m³/m/ngày)


class TankRules:
    """
    Quy tắc thiết kế bể xử lý nước/nước thải
    
    Tham chiếu tiêu chuẩn:
    - TCVN 7957:2008 - Thoát nước
    - TCVN 33:2006 - Cấp nước
    - EPA Design Manual
    """
    
    # Giới hạn thiết kế theo loại bể
    DESIGN_LIMITS = {
        "sedimentation": TankDesignLimits(
            min_retention_time=1.5,
            max_retention_time=4.0,
            min_surface_loading=20,
            max_surface_loading=60,
            min_depth=2.5,
            max_depth=5.0,
            min_length_width_ratio=2.0,
            max_length_width_ratio=5.0,
            min_velocity=0.001,
            max_velocity=0.025,
            min_weir_loading=100,
            max_weir_loading=300
        ),
        "filtration": TankDesignLimits(
            min_retention_time=0.5,
            max_retention_time=2.0,
            min_surface_loading=100,
            max_surface_loading=200,
            min_depth=2.0,
            max_depth=4.0,
            min_length_width_ratio=1.0,
            max_length_width_ratio=3.0,
            min_velocity=0.005,
            max_velocity=0.01,
            min_weir_loading=150,
            max_weir_loading=400
        ),
        "storage": TankDesignLimits(
            min_retention_time=4.0,
            max_retention_time=24.0,
            min_surface_loading=10,
            max_surface_loading=100,
            min_depth=2.0,
            max_depth=6.0,
            min_length_width_ratio=0.5,
            max_length_width_ratio=3.0,
            min_velocity=0.001,
            max_velocity=0.05,
            min_weir_loading=50,
            max_weir_loading=200
        ),
        "buffer": TankDesignLimits(
            min_retention_time=2.0,
            max_retention_time=8.0,
            min_surface_loading=30,
            max_surface_loading=80,
            min_depth=2.5,
            max_depth=5.0,
            min_length_width_ratio=1.0,
            max_length_width_ratio=4.0,
            min_velocity=0.001,
            max_velocity=0.03,
            min_weir_loading=80,
            max_weir_loading=250
        ),
        "aeration": TankDesignLimits(
            min_retention_time=4.0,
            max_retention_time=12.0,
            min_surface_loading=20,
            max_surface_loading=50,
            min_depth=3.0,
            max_depth=6.0,
            min_length_width_ratio=1.5,
            max_length_width_ratio=4.0,
            min_velocity=0.01,
            max_velocity=0.05,
            min_weir_loading=100,
            max_weir_loading=250
        )
    }
    
    # Hệ số an toàn
    SAFETY_FACTORS = {
        "volume": 1.2,          # Hệ số an toàn thể tích
        "flow": 1.5,            # Hệ số lưu lượng đỉnh
        "structural": 1.5,      # Hệ số an toàn kết cấu
        "freeboard": 0.3        # Chiều cao an toàn (m)
    }
    
    # Chiều dày thành bể theo chiều sâu
    WALL_THICKNESS = {
        3.0: 0.25,  # Chiều sâu <= 3m: thành dày 0.25m
        4.0: 0.30,  # Chiều sâu <= 4m: thành dày 0.30m
        5.0: 0.35,  # Chiều sâu <= 5m: thành dày 0.35m
        6.0: 0.40,  # Chiều sâu <= 6m: thành dày 0.40m
    }
    
    @classmethod
    def get_limits(cls, tank_type: str) -> TankDesignLimits:
        """Lấy giới hạn thiết kế theo loại bể"""
        return cls.DESIGN_LIMITS.get(tank_type, cls.DESIGN_LIMITS["storage"])
    
    @classmethod
    def validate_retention_time(
        cls,
        tank_type: str,
        retention_time: float
    ) -> RuleResult:
        """Kiểm tra thời gian lưu nước"""
        if retention_time is None:
            return RuleResult(
                rule_id="retention_time",
                rule_name="Thời gian lưu nước",
                parameter="retention_time",
                value=None,
                status=RuleStatus.WARNING,
                message="Chưa có dữ liệu thời gian lưu nước",
                standard="TCVN 7957:2008"
            )
        limits = cls.get_limits(tank_type)
        
        if retention_time < limits.min_retention_time:
            return RuleResult(
                rule_id="retention_time",
                rule_name="Thời gian lưu nước",
                parameter="retention_time",
                value=retention_time,
                status=RuleStatus.FAIL,
                message=f"Thời gian lưu {retention_time:.2f}h nhỏ hơn tối thiểu {limits.min_retention_time}h",
                suggestion=f"Tăng thể tích bể hoặc giảm lưu lượng để đạt ≥ {limits.min_retention_time}h",
                standard="TCVN 7957:2008"
            )
        elif retention_time > limits.max_retention_time:
            return RuleResult(
                rule_id="retention_time",
                rule_name="Thời gian lưu nước",
                parameter="retention_time",
                value=retention_time,
                status=RuleStatus.WARNING,
                message=f"Thời gian lưu {retention_time:.2f}h lớn hơn khuyến nghị {limits.max_retention_time}h",
                suggestion="Có thể giảm kích thước bể để tối ưu chi phí",
                standard="TCVN 7957:2008"
            )
        
        return RuleResult(
            rule_id="retention_time",
            rule_name="Thời gian lưu nước",
            parameter="retention_time",
            value=retention_time,
            status=RuleStatus.PASS,
            message=f"Thời gian lưu {retention_time:.2f}h đạt yêu cầu",
            standard="TCVN 7957:2008"
        )
    
    @classmethod
    def validate_surface_loading(
        cls,
        tank_type: str,
        surface_loading: float
    ) -> RuleResult:
        """Kiểm tra tải trọng bề mặt"""
        if surface_loading is None:
            return RuleResult(
                rule_id="surface_loading",
                rule_name="Tải trọng bề mặt",
                parameter="surface_loading",
                value=None,
                status=RuleStatus.WARNING,
                message="Chưa có dữ liệu tải trọng bề mặt",
                standard="TCVN 7957:2008"
            )
        limits = cls.get_limits(tank_type)
        
        if surface_loading > limits.max_surface_loading:
            return RuleResult(
                rule_id="surface_loading",
                rule_name="Tải trọng bề mặt",
                parameter="surface_loading",
                value=surface_loading,
                status=RuleStatus.FAIL,
                message=f"Tải trọng bề mặt {surface_loading:.1f} m³/m²/ngày vượt tối đa {limits.max_surface_loading}",
                suggestion=f"Tăng diện tích bề mặt bể để giảm tải trọng xuống ≤ {limits.max_surface_loading}",
                standard="TCVN 7957:2008"
            )
        elif surface_loading < limits.min_surface_loading:
            return RuleResult(
                rule_id="surface_loading",
                rule_name="Tải trọng bề mặt",
                parameter="surface_loading",
                value=surface_loading,
                status=RuleStatus.WARNING,
                message=f"Tải trọng bề mặt {surface_loading:.1f} m³/m²/ngày thấp hơn khuyến nghị",
                suggestion="Có thể giảm diện tích bể để tối ưu chi phí",
                standard="TCVN 7957:2008"
            )
        
        return RuleResult(
            rule_id="surface_loading",
            rule_name="Tải trọng bề mặt",
            parameter="surface_loading",
            value=surface_loading,
            status=RuleStatus.PASS,
            message=f"Tải trọng bề mặt {surface_loading:.1f} m³/m²/ngày đạt yêu cầu",
            standard="TCVN 7957:2008"
        )
    
    @classmethod
    def validate_velocity(
        cls,
        tank_type: str,
        velocity: float
    ) -> RuleResult:
        """Kiểm tra vận tốc ngang trong bể"""
        if velocity is None:
            return RuleResult(
                rule_id="horizontal_velocity",
                rule_name="Vận tốc ngang",
                parameter="velocity",
                value=None,
                status=RuleStatus.PASS,
                message="Chưa có dữ liệu vận tốc ngang",
                standard="TCVN 7957:2008"
            )
        limits = cls.get_limits(tank_type)
        
        if velocity > limits.max_velocity:
            return RuleResult(
                rule_id="horizontal_velocity",
                rule_name="Vận tốc ngang",
                parameter="velocity",
                value=velocity,
                status=RuleStatus.FAIL,
                message=f"Vận tốc ngang {velocity:.4f} m/s vượt tối đa {limits.max_velocity} m/s",
                suggestion="Tăng tiết diện ngang hoặc giảm lưu lượng",
                standard="TCVN 7957:2008"
            )
        
        return RuleResult(
            rule_id="horizontal_velocity",
            rule_name="Vận tốc ngang",
            parameter="velocity",
            value=velocity,
            status=RuleStatus.PASS,
            message=f"Vận tốc ngang {velocity:.4f} m/s đạt yêu cầu",
            standard="TCVN 7957:2008"
        )
    
    @classmethod
    def validate_dimensions(
        cls,
        tank_type: str,
        length: float,
        width: float,
        depth: float
    ) -> List[RuleResult]:
        """Kiểm tra kích thước bể"""
        limits = cls.get_limits(tank_type)
        results = []
        
        # Kiểm tra None values
        if length is None or width is None or depth is None:
            results.append(RuleResult(
                rule_id="dimensions",
                rule_name="Kích thước bể",
                parameter="dimensions",
                value=None,
                status=RuleStatus.WARNING,
                message="Chưa có đủ dữ liệu kích thước bể (length/width/depth)",
                standard="TCVN 7957:2008"
            ))
            return results
        
        # Kiểm tra chiều sâu
        if depth < limits.min_depth:
            results.append(RuleResult(
                rule_id="depth",
                rule_name="Chiều sâu nước",
                parameter="depth",
                value=depth,
                status=RuleStatus.FAIL,
                message=f"Chiều sâu {depth:.2f}m nhỏ hơn tối thiểu {limits.min_depth}m",
                suggestion=f"Tăng chiều sâu lên ≥ {limits.min_depth}m",
                standard="TCVN 7957:2008"
            ))
        elif depth > limits.max_depth:
            results.append(RuleResult(
                rule_id="depth",
                rule_name="Chiều sâu nước",
                parameter="depth",
                value=depth,
                status=RuleStatus.WARNING,
                message=f"Chiều sâu {depth:.2f}m lớn hơn khuyến nghị {limits.max_depth}m",
                suggestion="Xem xét giảm chiều sâu và tăng diện tích mặt bằng",
                standard="TCVN 7957:2008"
            ))
        else:
            results.append(RuleResult(
                rule_id="depth",
                rule_name="Chiều sâu nước",
                parameter="depth",
                value=depth,
                status=RuleStatus.PASS,
                message=f"Chiều sâu {depth:.2f}m đạt yêu cầu"
            ))
        
        # Kiểm tra tỷ lệ L/W
        ratio = length / width if width > 0 else 0
        if ratio < limits.min_length_width_ratio:
            results.append(RuleResult(
                rule_id="length_width_ratio",
                rule_name="Tỷ lệ dài/rộng",
                parameter="L/W",
                value=ratio,
                status=RuleStatus.WARNING,
                message=f"Tỷ lệ L/W = {ratio:.2f} nhỏ hơn khuyến nghị {limits.min_length_width_ratio}",
                suggestion=f"Tăng chiều dài hoặc giảm chiều rộng để L/W ≥ {limits.min_length_width_ratio}",
                standard="TCVN 7957:2008"
            ))
        elif ratio > limits.max_length_width_ratio:
            results.append(RuleResult(
                rule_id="length_width_ratio",
                rule_name="Tỷ lệ dài/rộng",
                parameter="L/W",
                value=ratio,
                status=RuleStatus.WARNING,
                message=f"Tỷ lệ L/W = {ratio:.2f} lớn hơn khuyến nghị {limits.max_length_width_ratio}",
                suggestion="Xem xét chia thành nhiều bể song song",
                standard="TCVN 7957:2008"
            ))
        else:
            results.append(RuleResult(
                rule_id="length_width_ratio",
                rule_name="Tỷ lệ dài/rộng",
                parameter="L/W",
                value=ratio,
                status=RuleStatus.PASS,
                message=f"Tỷ lệ L/W = {ratio:.2f} đạt yêu cầu"
            ))
        
        return results
    
    @classmethod
    def validate_weir_loading(
        cls,
        tank_type: str,
        weir_loading: float
    ) -> RuleResult:
        """Kiểm tra tải trọng máng tràn"""
        if weir_loading is None:
            return RuleResult(
                rule_id="weir_loading",
                rule_name="Tải trọng máng tràn",
                parameter="weir_loading",
                value=None,
                status=RuleStatus.PASS,
                message="Chưa có dữ liệu tải trọng máng tràn",
                standard="TCVN 7957:2008"
            )
        limits = cls.get_limits(tank_type)
        
        if weir_loading > limits.max_weir_loading:
            return RuleResult(
                rule_id="weir_loading",
                rule_name="Tải trọng máng tràn",
                parameter="weir_loading",
                value=weir_loading,
                status=RuleStatus.FAIL,
                message=f"Tải trọng máng tràn {weir_loading:.1f} m³/m/ngày vượt tối đa {limits.max_weir_loading}",
                suggestion="Tăng chiều dài máng tràn hoặc thêm máng tràn phụ",
                standard="TCVN 7957:2008"
            )
        
        return RuleResult(
            rule_id="weir_loading",
            rule_name="Tải trọng máng tràn",
            parameter="weir_loading",
            value=weir_loading,
            status=RuleStatus.PASS,
            message=f"Tải trọng máng tràn {weir_loading:.1f} m³/m/ngày đạt yêu cầu",
            standard="TCVN 7957:2008"
        )
    
    @classmethod
    def get_recommended_wall_thickness(cls, depth: float) -> float:
        """Lấy chiều dày thành bể khuyến nghị theo chiều sâu"""
        for max_depth, thickness in sorted(cls.WALL_THICKNESS.items()):
            if depth <= max_depth:
                return thickness
        return 0.45  # Mặc định cho chiều sâu > 6m
    
    @classmethod
    def validate_tank_design(
        cls,
        tank_type: str,
        params: Dict[str, Any]
    ) -> List[RuleResult]:
        """
        Kiểm tra toàn bộ thiết kế bể
        
        Args:
            tank_type: Loại bể
            params: Dict chứa các thông số thiết kế
            
        Returns:
            List[RuleResult]: Danh sách kết quả kiểm tra
        """
        results = []
        
        # Kiểm tra thời gian lưu
        if "retention_time" in params:
            results.append(cls.validate_retention_time(tank_type, params["retention_time"]))
        
        # Kiểm tra tải trọng bề mặt
        if "surface_loading" in params:
            results.append(cls.validate_surface_loading(tank_type, params["surface_loading"]))
        
        # Kiểm tra vận tốc
        if "velocity" in params:
            results.append(cls.validate_velocity(tank_type, params["velocity"]))
        
        # Kiểm tra kích thước
        if all(k in params for k in ["length", "width", "depth"]):
            results.extend(cls.validate_dimensions(
                tank_type,
                params["length"],
                params["width"],
                params["depth"]
            ))
        
        # Kiểm tra tải trọng máng tràn
        if "weir_loading" in params:
            results.append(cls.validate_weir_loading(tank_type, params["weir_loading"]))
        
        return results
    
    @classmethod
    def calculate_recommended_dimensions(
        cls,
        tank_type: str,
        design_flow: float,  # m³/ngày
        settling_velocity: float = None  # m/h (cho bể lắng)
    ) -> Dict[str, float]:
        """
        Tính toán kích thước khuyến nghị
        
        Args:
            tank_type: Loại bể
            design_flow: Lưu lượng thiết kế (m³/ngày)
            settling_velocity: Vận tốc lắng (m/h) - cho bể lắng
            
        Returns:
            Dict: Kích thước khuyến nghị
        """
        limits = cls.get_limits(tank_type)
        
        # Tính diện tích bề mặt từ tải trọng bề mặt trung bình
        avg_surface_loading = (limits.min_surface_loading + limits.max_surface_loading) / 2
        surface_area = design_flow / avg_surface_loading
        
        # Tính chiều sâu
        avg_depth = (limits.min_depth + limits.max_depth) / 2
        
        # Tính thể tích
        volume = surface_area * avg_depth
        
        # Tính thời gian lưu
        retention_time = volume / (design_flow / 24)  # giờ
        
        # Điều chỉnh nếu thời gian lưu không đạt
        if retention_time < limits.min_retention_time:
            volume = design_flow / 24 * limits.min_retention_time
            surface_area = volume / avg_depth
        
        # Tính L và W với tỷ lệ khuyến nghị
        avg_ratio = (limits.min_length_width_ratio + limits.max_length_width_ratio) / 2
        width = (surface_area / avg_ratio) ** 0.5
        length = width * avg_ratio
        
        # Làm tròn
        length = round(length * 2) / 2  # Làm tròn 0.5m
        width = round(width * 2) / 2
        depth = round(avg_depth * 2) / 2
        
        return {
            "length": length,
            "width": width,
            "depth": depth,
            "surface_area": length * width,
            "volume": length * width * depth,
            "wall_thickness": cls.get_recommended_wall_thickness(depth)
        }
