"""
Tank Design Calculator - Tính toán thiết kế bể

Bao gồm:
- Bể lắng (sedimentation)
- Bể lọc (filtration)
- Bể chứa (storage)
- Bể điều hòa (buffer)
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from rules.tank_rules import TankRules
from rules.engine import RuleResult

@dataclass
class TankDimensions:
    """Kích thước bể"""
    length: float           # Chiều dài (m)
    width: float            # Chiều rộng (m)
    water_depth: float      # Chiều sâu nước (m)
    freeboard: float        # Chiều cao an toàn (m)
    sludge_depth: float     # Chiều sâu vùng bùn (m)
    total_depth: float      # Tổng chiều sâu (m)
    wall_thickness: float   # Chiều dày thành (m)
    bottom_thickness: float # Chiều dày đáy (m)
    
    @property
    def surface_area(self) -> float:
        """Diện tích bề mặt (m²)"""
        return self.length * self.width
    
    @property
    def water_volume(self) -> float:
        """Thể tích nước (m³)"""
        return self.length * self.width * self.water_depth
    
    @property
    def total_volume(self) -> float:
        """Thể tích tổng (m³)"""
        return self.length * self.width * (self.water_depth + self.sludge_depth)
    
    @property
    def outer_length(self) -> float:
        """Chiều dài ngoài (m)"""
        return self.length + 2 * self.wall_thickness
    
    @property
    def outer_width(self) -> float:
        """Chiều rộng ngoài (m)"""
        return self.width + 2 * self.wall_thickness

@dataclass
class TankHydraulics:
    """Thông số thủy lực bể"""
    design_flow: float          # Lưu lượng thiết kế (m³/ngày)
    retention_time: float       # Thời gian lưu (giờ)
    surface_loading: float      # Tải trọng bề mặt (m³/m²/ngày)
    weir_loading: float         # Tải trọng máng tràn (m³/m/ngày)
    horizontal_velocity: float  # Vận tốc ngang (m/s)
    inlet_velocity: float       # Vận tốc ống vào (m/s)
    outlet_velocity: float      # Vận tốc ống ra (m/s)

@dataclass
class TankStructure:
    """Thông số kết cấu bể"""
    inlet_diameter: float       # Đường kính ống vào (mm)
    outlet_diameter: float      # Đường kính ống ra (mm)
    inlet_invert: float         # Cao độ đáy ống vào (m)
    outlet_invert: float        # Cao độ đáy ống ra (m)
    bottom_slope: float         # Độ dốc đáy (%)
    sludge_pipe_diameter: float # Đường kính ống bùn (mm)
    concrete_volume: float      # Khối lượng bê tông (m³)
    steel_weight: float         # Khối lượng thép (kg)


class TankDesignCalculator:
    """
    Tính toán thiết kế bể xử lý nước
    
    Hỗ trợ:
    - Bể lắng ngang (horizontal sedimentation)
    - Bể lắng đứng (vertical sedimentation)
    - Bể lọc nhanh (rapid filter)
    - Bể chứa nước sạch (storage)
    - Bể điều hòa (equalization)
    """
    
    # Vận tốc trong ống khuyến nghị
    PIPE_VELOCITY = {
        "inlet": {"min": 0.6, "max": 1.2, "design": 0.9},
        "outlet": {"min": 0.5, "max": 1.0, "design": 0.8},
        "sludge": {"min": 1.0, "max": 2.0, "design": 1.5}
    }
    
    def __init__(self):
        self.rules = TankRules()
    
    @classmethod
    def design_sedimentation_tank(
        cls,
        design_flow: float = None,         # Lưu lượng thiết kế (m³/ngày)
        settling_velocity: float = None,   # Vận tốc lắng (m/h)
        num_tanks: int = 1,         # Số bể
        number_of_tanks: int = None, # Alias cho num_tanks
        length: float = None,       # Chiều dài (m) - tùy chọn
        width: float = None,        # Chiều rộng (m) - tùy chọn
        depth: float = None,        # Chiều sâu nước (m) - tùy chọn
        foundation_level: float = 0.0,  # Cao độ đáy (m)
        # Thông số thay thế từ API
        flow_rate: float = None,    # Alias cho design_flow
        detention_time: float = None,      # Thời gian lưu (giờ)
        surface_loading_rate: float = None # Tải trọng bề mặt (m³/m²/ngày)
    ) -> Dict[str, Any]:
        """
        Thiết kế bể lắng
        
        Công thức chính:
        - Diện tích bề mặt: A = Q / v₀ (m²)
        - Thời gian lưu: t = V / Q (giờ)
        - Tải trọng bề mặt: SLR = Q / A (m³/m²/ngày)
        
        Args:
            design_flow/flow_rate: Lưu lượng thiết kế (m³/ngày)
            settling_velocity: Vận tốc lắng của hạt (m/h)
            num_tanks/number_of_tanks: Số bể lắng
            detention_time: Thời gian lưu (giờ)
            surface_loading_rate: Tải trọng bề mặt (m³/m²/ngày)
            length, width, depth: Kích thước (nếu muốn chỉ định)
            foundation_level: Cao độ đáy bể (m)
            
        Returns:
            Dict: Kết quả thiết kế đầy đủ
        """
        # Xử lý alias parameters
        if flow_rate is not None and design_flow is None:
            design_flow = flow_rate
        if number_of_tanks is not None:
            num_tanks = number_of_tanks
        
        # Tính settling_velocity từ surface_loading_rate nếu cần
        if settling_velocity is None:
            if surface_loading_rate is not None:
                # v₀ = SLR / 24 (m/h) - tải trọng bề mặt chuyển đổi
                settling_velocity = surface_loading_rate / 24
            else:
                # Giá trị mặc định cho bể lắng nước thải
                settling_velocity = 1.5  # m/h
        
        # Lưu lượng mỗi bể
        Q_per_tank = design_flow / num_tanks  # m³/ngày
        Q_hourly = Q_per_tank / 24  # m³/h
        Q_sec = Q_per_tank / 86400  # m³/s
        
        # 1. Tính diện tích bề mặt từ vận tốc lắng hoặc thời gian lưu
        if detention_time is not None and depth is not None:
            # Tính từ thời gian lưu: V = Q * t, A = V / H
            volume_required = Q_hourly * detention_time
            surface_area_required = volume_required / depth
        else:
            # v₀ = Q / A => A = Q / v₀
            surface_area_required = Q_hourly / settling_velocity  # m²
        
        # 2. Xác định kích thước
        limits = TankRules.get_limits("sedimentation")
        
        if depth is None:
            depth = (limits.min_depth + limits.max_depth) / 2  # 3.75m
        
        if length is None and width is None:
            # Tính từ diện tích và tỷ lệ L/W = 3
            L_W_ratio = 3.0
            width = math.sqrt(surface_area_required / L_W_ratio)
            length = width * L_W_ratio
        elif length is None:
            length = surface_area_required / width
        elif width is None:
            width = surface_area_required / length
        
        # Làm tròn kích thước (bội số 0.5m)
        length = math.ceil(length * 2) / 2
        width = math.ceil(width * 2) / 2
        depth = round(depth * 2) / 2
        
        # 3. Tính các thông số thủy lực
        surface_area = length * width
        volume = surface_area * depth
        
        # Thời gian lưu (giờ)
        retention_time = volume / Q_hourly
        
        # Tải trọng bề mặt (m³/m²/ngày)
        surface_loading = Q_per_tank / surface_area
        
        # Vận tốc ngang (m/s)
        cross_section = width * depth
        horizontal_velocity = Q_sec / cross_section
        
        # 4. Tính kích thước ống
        # Ống vào: v = 0.9 m/s
        inlet_area = Q_sec / cls.PIPE_VELOCITY["inlet"]["design"]
        inlet_diameter = math.sqrt(4 * inlet_area / math.pi) * 1000  # mm
        inlet_diameter = cls._round_pipe_diameter(inlet_diameter)
        
        # Ống ra: v = 0.8 m/s
        outlet_area = Q_sec / cls.PIPE_VELOCITY["outlet"]["design"]
        outlet_diameter = math.sqrt(4 * outlet_area / math.pi) * 1000
        outlet_diameter = cls._round_pipe_diameter(outlet_diameter)
        
        # 5. Tính máng tràn
        # Chu vi máng = 2 × width (2 bên)
        weir_length = 2 * width
        weir_loading = Q_per_tank / weir_length  # m³/m/ngày
        
        # 6. Tính vùng bùn
        # Giả định nồng độ bùn 5000 mg/L, lượng bùn 200 mg/L từ nước thô
        sludge_production = 0.0002 * Q_per_tank  # m³/ngày (ước tính)
        sludge_storage_days = 7  # Lưu bùn 7 ngày
        sludge_volume = sludge_production * sludge_storage_days
        sludge_depth = sludge_volume / surface_area
        sludge_depth = max(0.5, round(sludge_depth * 2) / 2)  # Tối thiểu 0.5m
        
        # 7. Tính chiều dày thành
        total_depth = depth + sludge_depth + 0.3  # +0.3m freeboard
        wall_thickness = TankRules.get_recommended_wall_thickness(total_depth)
        
        # 8. Tạo kết quả
        dimensions = TankDimensions(
            length=length,
            width=width,
            water_depth=depth,
            freeboard=0.3,
            sludge_depth=sludge_depth,
            total_depth=total_depth,
            wall_thickness=wall_thickness,
            bottom_thickness=0.3
        )
        
        hydraulics = TankHydraulics(
            design_flow=Q_per_tank,
            retention_time=round(retention_time, 2),
            surface_loading=round(surface_loading, 2),
            weir_loading=round(weir_loading, 2),
            horizontal_velocity=round(horizontal_velocity, 6),
            inlet_velocity=cls.PIPE_VELOCITY["inlet"]["design"],
            outlet_velocity=cls.PIPE_VELOCITY["outlet"]["design"]
        )
        
        structure = TankStructure(
            inlet_diameter=inlet_diameter,
            outlet_diameter=outlet_diameter,
            inlet_invert=foundation_level + depth - 0.3,
            outlet_invert=foundation_level + depth - 0.1,
            bottom_slope=2.0,  # 2% về hố bùn
            sludge_pipe_diameter=150,
            concrete_volume=cls._estimate_concrete_volume(dimensions),
            steel_weight=cls._estimate_steel_weight(dimensions)
        )

        # 8b. Thể tích nước
        volume_per_tank = round(dimensions.water_volume, 2)
        volume_total = round(volume_per_tank * num_tanks, 2)
        
        # 9. Kiểm tra quy tắc
        validation_params = {
            "retention_time": retention_time,
            "surface_loading": surface_loading,
            "velocity": horizontal_velocity,
            "weir_loading": weir_loading,
            "length": length,
            "width": width,
            "depth": depth
        }
        validation_results = TankRules.validate_tank_design("sedimentation", validation_params)
        
        # 10. Tạo cảnh báo
        warnings = []
        for result in validation_results:
            if result.status.value in ["warning", "fail"]:
                warnings.append(result.message)
        
        return {
            "tank_type": "sedimentation",
            "num_tanks": num_tanks,
            "dimensions": asdict(dimensions),
            "hydraulics": asdict(hydraulics),
            "structure": asdict(structure),
            "volume": {
                "per_tank": volume_per_tank,
                "total": volume_total
            },
            "validation": [r.to_dict() for r in validation_results],
            "warnings": warnings,
            "summary": {
                "Số bể": num_tanks,
                "Kích thước (DxRxS)": f"{length} x {width} x {total_depth} m",
                "Thể tích hữu ích": f"{round(volume, 1)} m³",
                "Thời gian lưu": f"{round(retention_time, 1)} giờ",
                "Tải trọng bề mặt": f"{round(surface_loading, 1)} m³/m²/ngày",
                "Ống vào": f"DN{int(inlet_diameter)}",
                "Ống ra": f"DN{int(outlet_diameter)}"
            },
            "calculated_at": datetime.now().isoformat()
        }
    
    @classmethod
    def design_storage_tank(
        cls,
        storage_volume: float,      # Thể tích yêu cầu (m³)
        design_flow: float = None,  # Lưu lượng (m³/ngày) - để tính ống
        num_tanks: int = 1,
        length: float = None,
        width: float = None,
        depth: float = None,
        foundation_level: float = 0.0
    ) -> Dict[str, Any]:
        """
        Thiết kế bể chứa
        
        Args:
            storage_volume: Thể tích chứa yêu cầu (m³)
            design_flow: Lưu lượng qua bể (m³/ngày)
            num_tanks: Số bể
            
        Returns:
            Dict: Kết quả thiết kế
        """
        # Thể tích mỗi bể
        V_per_tank = storage_volume / num_tanks
        
        # Xác định kích thước
        if depth is None:
            depth = 4.0  # Mặc định 4m
        
        surface_area_required = V_per_tank / depth
        
        if length is None and width is None:
            # Bể vuông hoặc gần vuông
            side = math.sqrt(surface_area_required)
            length = math.ceil(side * 2) / 2
            width = math.ceil(side * 2) / 2
        elif length is None:
            length = math.ceil(surface_area_required / width * 2) / 2
        elif width is None:
            width = math.ceil(surface_area_required / length * 2) / 2
        
        # Tính lại thể tích thực
        actual_volume = length * width * depth
        
        # Tính ống nếu có lưu lượng
        if design_flow:
            Q_sec = design_flow / 86400
            inlet_area = Q_sec / 1.0  # v = 1.0 m/s
            inlet_diameter = math.sqrt(4 * inlet_area / math.pi) * 1000
            inlet_diameter = cls._round_pipe_diameter(inlet_diameter)
        else:
            inlet_diameter = 200  # Mặc định
        
        # Thời gian lưu
        retention_time = actual_volume / (design_flow / 24) if design_flow else 0
        
        # Kích thước bể
        total_depth = depth + 0.3  # +freeboard
        wall_thickness = TankRules.get_recommended_wall_thickness(total_depth)
        
        dimensions = TankDimensions(
            length=length,
            width=width,
            water_depth=depth,
            freeboard=0.3,
            sludge_depth=0,
            total_depth=total_depth,
            wall_thickness=wall_thickness,
            bottom_thickness=0.3
        )
        
        return {
            "tank_type": "storage",
            "num_tanks": num_tanks,
            "dimensions": asdict(dimensions),
            "hydraulics": {
                "storage_volume_required": storage_volume,
                "storage_volume_actual": round(actual_volume * num_tanks, 1),
                "retention_time": round(retention_time, 1) if retention_time else None,
                "inlet_diameter": inlet_diameter,
                "outlet_diameter": inlet_diameter
            },
            "summary": {
                "Số bể": num_tanks,
                "Kích thước (DxRxS)": f"{length} x {width} x {total_depth} m",
                "Thể tích hữu ích": f"{round(actual_volume, 1)} m³/bể",
                "Tổng thể tích": f"{round(actual_volume * num_tanks, 1)} m³"
            }
        }
    
    @classmethod
    def design_buffer_tank(
        cls,
        peak_flow: float,           # Lưu lượng đỉnh (m³/h)
        average_flow: float,        # Lưu lượng trung bình (m³/h)
        buffer_time: float = 4.0,   # Thời gian điều hòa (giờ)
        foundation_level: float = 0.0
    ) -> Dict[str, Any]:
        """
        Thiết kế bể điều hòa
        
        Công thức:
        V = (Q_peak - Q_avg) × t
        
        Args:
            peak_flow: Lưu lượng đỉnh (m³/h)
            average_flow: Lưu lượng trung bình (m³/h)
            buffer_time: Thời gian điều hòa (giờ)
            
        Returns:
            Dict: Kết quả thiết kế
        """
        # Thể tích điều hòa
        buffer_volume = (peak_flow - average_flow) * buffer_time
        
        # Thêm hệ số an toàn 20%
        design_volume = buffer_volume * 1.2
        
        # Thiết kế với chiều sâu 3.5m
        depth = 3.5
        surface_area = design_volume / depth
        
        # Tỷ lệ L/W = 2
        width = math.sqrt(surface_area / 2)
        length = width * 2
        
        # Làm tròn
        length = math.ceil(length * 2) / 2
        width = math.ceil(width * 2) / 2
        
        actual_volume = length * width * depth
        
        # Tính ống
        Q_sec = peak_flow / 3600
        inlet_diameter = cls._round_pipe_diameter(
            math.sqrt(4 * Q_sec / 1.0 / math.pi) * 1000
        )
        
        total_depth = depth + 0.5  # Freeboard lớn hơn cho điều hòa
        wall_thickness = TankRules.get_recommended_wall_thickness(total_depth)
        
        dimensions = TankDimensions(
            length=length,
            width=width,
            water_depth=depth,
            freeboard=0.5,
            sludge_depth=0,
            total_depth=total_depth,
            wall_thickness=wall_thickness,
            bottom_thickness=0.3
        )
        
        # Tính công suất khuấy trộn (nếu cần)
        mixing_power = 0.01 * actual_volume  # 10W/m³
        
        return {
            "tank_type": "buffer",
            "dimensions": asdict(dimensions),
            "hydraulics": {
                "peak_flow": peak_flow,
                "average_flow": average_flow,
                "buffer_volume_required": round(buffer_volume, 1),
                "buffer_volume_actual": round(actual_volume, 1),
                "buffer_time": buffer_time,
                "inlet_diameter": inlet_diameter,
                "outlet_diameter": inlet_diameter
            },
            "equipment": {
                "mixing_power": round(mixing_power, 2),
                "air_blower": "Khuyến nghị lắp đặt máy thổi khí khuấy trộn"
            },
            "summary": {
                "Kích thước (DxRxS)": f"{length} x {width} x {total_depth} m",
                "Thể tích điều hòa": f"{round(actual_volume, 1)} m³",
                "Thời gian điều hòa": f"{buffer_time} giờ",
                "Công suất khuấy": f"{round(mixing_power, 2)} kW"
            }
        }
    
    @staticmethod
    def _round_pipe_diameter(diameter: float) -> float:
        """Làm tròn lên đường kính tiêu chuẩn"""
        standard_diameters = [
            50, 75, 100, 125, 150, 200, 250, 300, 350, 400,
            450, 500, 600, 700, 800, 900, 1000, 1200, 1500
        ]
        for d in standard_diameters:
            if d >= diameter:
                return d
        return standard_diameters[-1]
    
    @staticmethod
    def _estimate_concrete_volume(dims: TankDimensions) -> float:
        """Ước tính khối lượng bê tông"""
        # Thể tích thành
        wall_volume = 2 * (dims.length + dims.width) * dims.total_depth * dims.wall_thickness
        # Thể tích đáy
        bottom_volume = dims.outer_length * dims.outer_width * dims.bottom_thickness
        
        return round(wall_volume + bottom_volume, 2)
    
    @staticmethod
    def _estimate_steel_weight(dims: TankDimensions) -> float:
        """Ước tính khối lượng thép (kg)"""
        concrete_volume = TankDesignCalculator._estimate_concrete_volume(dims)
        # Giả định hàm lượng thép 100 kg/m³ bê tông
        return round(concrete_volume * 100, 0)
