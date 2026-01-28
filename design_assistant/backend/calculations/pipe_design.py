"""
Pipe Design Calculator - Tính toán thiết kế đường ống

Bao gồm:
- Đường ống tự chảy
- Đường ống áp lực
- Trắc dọc tuyến ống
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from rules.pipe_rules import PipeRules
from calculations.hydraulic import HydraulicCalculator

@dataclass
class PipeSegment:
    """Đoạn ống"""
    id: int
    start_station: float    # Lý trình đầu (m)
    end_station: float      # Lý trình cuối (m)
    length: float           # Chiều dài (m)
    diameter: float         # Đường kính (mm)
    slope: float            # Độ dốc (%)
    invert_start: float     # Cao độ đáy đầu (m)
    invert_end: float       # Cao độ đáy cuối (m)
    ground_start: float     # Cao độ mặt đất đầu (m)
    ground_end: float       # Cao độ mặt đất cuối (m)
    cover_start: float      # Độ sâu chôn đầu (m)
    cover_end: float        # Độ sâu chôn cuối (m)

@dataclass
class ManholeDef:
    """Giếng thăm"""
    id: str
    station: float          # Lý trình (m)
    ground_level: float     # Cao độ mặt đất (m)
    invert_level: float     # Cao độ đáy (m)
    depth: float            # Chiều sâu (m)
    diameter: float         # Đường kính (mm)
    manhole_type: str       # Loại giếng


class PipeDesignCalculator:
    """
    Tính toán thiết kế đường ống thoát nước
    
    Hỗ trợ:
    - Tính đường kính theo lưu lượng
    - Tính độ dốc yêu cầu
    - Thiết kế trắc dọc
    - Bố trí giếng thăm
    """
    
    # Khoảng cách giếng thăm tối đa (m)
    MAX_MANHOLE_SPACING = {
        "D150-D300": 40,
        "D300-D600": 50,
        "D600-D1000": 75,
        "D1000+": 100
    }
    
    def __init__(self):
        self.rules = PipeRules()
        self.hydraulic = HydraulicCalculator()
    
    def select_pipe_diameter(
        self,
        flow_rate: float,
        slope: float = 0.005,
        roughness: float = 0.013,
        pipe_type: str = "gravity",
        fill_ratio: float = 0.7
    ) -> float:
        """
        Chọn đường kính ống dựa trên lưu lượng
        
        Args:
            flow_rate: Lưu lượng thiết kế (L/s hoặc m³/s)
            slope: Độ dốc (%)
            roughness: Hệ số nhám Manning
            pipe_type: Loại ống (gravity/pressure)
            fill_ratio: Tỷ lệ đầy (cho ống tự chảy)
            
        Returns:
            float: Đường kính ống tiêu chuẩn (mm)
        """
        # Chuyển đổi lưu lượng nếu cần (L/s -> m³/s)
        Q = flow_rate / 1000 if flow_rate > 1 else flow_rate
        
        if pipe_type == "pressure":
            # Ống có áp: v = 1.0 m/s
            design_velocity = 1.0
            area = Q / design_velocity
            calc_diameter = math.sqrt(4 * area / math.pi) * 1000
        else:
            # Ống tự chảy: dùng công thức Manning
            # Q = (1/n) * A * R^(2/3) * S^(1/2)
            # Đơn giản hóa cho ống tròn đầy 70%
            n = roughness
            S = slope / 100 if slope > 0.1 else slope  # Chuyển % -> decimal
            
            # Ước tính đường kính từ công thức kinh nghiệm
            # D = (Q * n / (0.312 * S^0.5))^0.375 * 1000
            if S > 0:
                calc_diameter = ((Q * n) / (0.312 * math.sqrt(S))) ** 0.375 * 1000
            else:
                calc_diameter = ((Q * n) / (0.312 * math.sqrt(0.005))) ** 0.375 * 1000
        
        # Làm tròn lên đường kính tiêu chuẩn
        return PipeRules.get_nearest_standard_diameter(calc_diameter)
    
    def design_gravity_pipe_from_profile(
        self,
        flow_rate: float,
        profile_data: List[Dict],
        pipe_diameter: float,
        roughness: float = 0.013,
        min_cover: float = 0.8
    ) -> Dict[str, Any]:
        """
        Thiết kế ống tự chảy từ dữ liệu trắc dọc
        
        Args:
            flow_rate: Lưu lượng (L/s)
            profile_data: Danh sách điểm [{station, ground_level, name}]
            pipe_diameter: Đường kính ống (mm)
            roughness: Hệ số nhám Manning
            min_cover: Độ sâu chôn ống tối thiểu (m)
        """
        if len(profile_data) < 2:
            raise ValueError("Cần ít nhất 2 điểm để thiết kế")
        
        # Sắp xếp theo lý trình
        profile_data = sorted(profile_data, key=lambda p: p["station"])
        
        segments = []
        manholes = []
        
        # Tính cao độ đáy ống tại các điểm
        for i, point in enumerate(profile_data):
            invert = point["ground_level"] - min_cover - pipe_diameter / 1000
            manholes.append({
                "id": point.get("name", f"MH{i+1}"),
                "station": point["station"],
                "ground_level": point["ground_level"],
                "invert_level": round(invert, 3),
                "depth": round(min_cover + pipe_diameter / 1000, 2)
            })
        
        # Tạo các đoạn ống
        for i in range(len(manholes) - 1):
            mh_start = manholes[i]
            mh_end = manholes[i + 1]
            
            length = mh_end["station"] - mh_start["station"]
            drop = mh_start["invert_level"] - mh_end["invert_level"]
            slope = (drop / length) * 1000 if length > 0 else 0  # ‰
            
            # Tính vận tốc và khả năng tải
            flow_result = HydraulicCalculator.circular_pipe_flow(
                diameter=pipe_diameter,
                slope=slope / 10,  # Chuyển ‰ sang %
                fill_ratio=0.7,
                manning_n=roughness
            )
            
            segments.append({
                "segment_id": i + 1,
                "start_manhole": mh_start["id"],
                "end_manhole": mh_end["id"],
                "length": round(length, 2),
                "slope": round(slope, 2),
                "diameter": pipe_diameter,
                "velocity": round(flow_result.velocity, 2),
                "capacity": round(flow_result.flow_rate * 1000, 1),  # L/s
                "filling_ratio": 0.7
            })
        
        return {
            "segments": segments,
            "manholes": manholes,
            "total_length": round(profile_data[-1]["station"] - profile_data[0]["station"], 2)
        }
    
    def design_pressure_pipe_from_profile(
        self,
        flow_rate: float,
        profile_data: List[Dict],
        pipe_diameter: float,
        roughness: float = 0.009
    ) -> Dict[str, Any]:
        """
        Thiết kế ống có áp từ dữ liệu trắc dọc
        """
        if len(profile_data) < 2:
            raise ValueError("Cần ít nhất 2 điểm để thiết kế")
        
        profile_data = sorted(profile_data, key=lambda p: p["station"])
        
        segments = []
        manholes = []
        
        # Vận tốc trong ống có áp
        Q = flow_rate / 1000  # L/s -> m³/s
        area = math.pi * (pipe_diameter / 1000) ** 2 / 4
        velocity = Q / area if area > 0 else 0
        
        for i, point in enumerate(profile_data):
            manholes.append({
                "id": point.get("name", f"MH{i+1}"),
                "station": point["station"],
                "ground_level": point["ground_level"],
                "invert_level": round(point["ground_level"] - 1.0, 3),
                "depth": 1.0
            })
        
        for i in range(len(manholes) - 1):
            mh_start = manholes[i]
            mh_end = manholes[i + 1]
            length = mh_end["station"] - mh_start["station"]
            
            segments.append({
                "segment_id": i + 1,
                "start_manhole": mh_start["id"],
                "end_manhole": mh_end["id"],
                "length": round(length, 2),
                "slope": 0,
                "diameter": pipe_diameter,
                "velocity": round(velocity, 2),
                "capacity": round(flow_rate, 1),
                "filling_ratio": 1.0
            })
        
        return {
            "segments": segments,
            "manholes": manholes,
            "total_length": round(profile_data[-1]["station"] - profile_data[0]["station"], 2)
        }
    
    @classmethod
    def design_gravity_pipe(
        cls,
        design_flow: float,         # Lưu lượng thiết kế (m³/s)
        start_point: Tuple[float, float, float],  # (x, y, z) điểm đầu
        end_point: Tuple[float, float, float],    # (x, y, z) điểm cuối
        material: str = "hdpe",
        min_cover: float = 0.8,     # Độ sâu chôn tối thiểu (m)
        fill_ratio: float = 0.7,    # Tỷ lệ đầy thiết kế
        diameter: float = None,     # Đường kính (nếu đã biết)
        slope: float = None         # Độ dốc (nếu đã biết)
    ) -> Dict[str, Any]:
        """
        Thiết kế đường ống tự chảy
        
        Args:
            design_flow: Lưu lượng thiết kế (m³/s)
            start_point: Tọa độ điểm đầu (x, y, ground_level)
            end_point: Tọa độ điểm cuối (x, y, ground_level)
            material: Vật liệu ống
            min_cover: Độ sâu chôn ống tối thiểu (m)
            fill_ratio: Tỷ lệ đầy thiết kế (0-1)
            diameter: Đường kính chỉ định (mm)
            slope: Độ dốc chỉ định (%)
            
        Returns:
            Dict: Kết quả thiết kế đầy đủ
        """
        # 1. Tính chiều dài tuyến
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        horizontal_length = math.sqrt(dx**2 + dy**2)
        
        # 2. Tính độ dốc địa hình
        dz = start_point[2] - end_point[2]  # Cao độ đầu - cao độ cuối
        terrain_slope = (dz / horizontal_length) * 100 if horizontal_length > 0 else 0
        
        # 3. Lấy hệ số nhám Manning
        manning_n = PipeRules.get_manning_n(material)
        
        # 4. Xác định đường kính và độ dốc
        if diameter is None:
            # Tính đường kính từ lưu lượng
            if slope is None:
                # Sử dụng độ dốc địa hình nếu hợp lý
                slope = max(terrain_slope, 0.3)  # Tối thiểu 0.3%
            
            calc_result = PipeRules.calculate_recommended_diameter(
                design_flow=design_flow,
                slope=slope,
                material=material,
                fill_ratio=fill_ratio
            )
            diameter = calc_result["recommended_diameter"]
        
        if slope is None:
            # Tính độ dốc từ đường kính
            slope = HydraulicCalculator.calculate_required_slope(
                diameter=diameter,
                design_flow=design_flow,
                fill_ratio=fill_ratio,
                manning_n=manning_n
            )
        
        # 5. Kiểm tra độ dốc tối thiểu
        min_slope = PipeRules.get_min_slope(diameter)
        if slope < min_slope:
            slope = min_slope
        
        # 6. Tính toán thủy lực
        flow_result = HydraulicCalculator.circular_pipe_flow(
            diameter=diameter,
            slope=slope,
            fill_ratio=fill_ratio,
            manning_n=manning_n
        )
        
        # 7. Tính khả năng tải (ống đầy)
        full_capacity = HydraulicCalculator.full_pipe_flow(
            diameter=diameter,
            slope=slope,
            manning_n=manning_n
        )
        
        # 8. Tính cao độ đáy ống
        invert_start = start_point[2] - min_cover - diameter/1000
        invert_end = invert_start - (slope/100) * horizontal_length
        
        # Kiểm tra độ sâu chôn ống cuối
        cover_end = end_point[2] - invert_end - diameter/1000
        
        # 9. Tính tổn thất cột nước
        head_loss = HydraulicCalculator.calculate_head_loss(
            length=horizontal_length,
            diameter=diameter,
            flow_rate=design_flow,
            minor_loss_K=1.5  # Giả định tổn thất cục bộ
        )
        
        # 10. Kiểm tra quy tắc thiết kế
        validation_params = {
            "velocity": flow_result.velocity,
            "diameter": diameter,
            "slope": slope,
            "cover_depth": min_cover,
            "fill_ratio": fill_ratio * 100,
            "reynolds": flow_result.reynolds_number
        }
        validation_results = PipeRules.validate_pipe_design("gravity_sewer", validation_params)
        
        # 11. Tạo cảnh báo
        warnings = []
        for result in validation_results:
            if result.status.value in ["warning", "fail"]:
                warnings.append(result.message)
        
        if cover_end < min_cover:
            warnings.append(f"Độ sâu chôn ống cuối tuyến ({cover_end:.2f}m) nhỏ hơn yêu cầu ({min_cover}m)")
        
        return {
            "pipe_type": "gravity",
            "geometry": {
                "start_point": {"x": start_point[0], "y": start_point[1], "z": start_point[2]},
                "end_point": {"x": end_point[0], "y": end_point[1], "z": end_point[2]},
                "horizontal_length": round(horizontal_length, 2),
                "terrain_slope": round(terrain_slope, 3)
            },
            "design": {
                "diameter": diameter,
                "material": material,
                "slope": round(slope, 3),
                "manning_n": manning_n,
                "fill_ratio": fill_ratio
            },
            "hydraulics": {
                "design_flow": design_flow,
                "velocity": flow_result.velocity,
                "actual_flow": flow_result.flow_rate,
                "full_capacity": full_capacity["Q_full"],
                "capacity_ratio": round(design_flow / full_capacity["Q_full"] * 100, 1),
                "hydraulic_radius": flow_result.hydraulic_radius,
                "reynolds_number": flow_result.reynolds_number,
                "flow_regime": flow_result.flow_regime,
                "froude_number": flow_result.froude_number
            },
            "profile": {
                "invert_start": round(invert_start, 3),
                "invert_end": round(invert_end, 3),
                "cover_start": min_cover,
                "cover_end": round(cover_end, 3)
            },
            "head_loss": asdict(head_loss),
            "validation": [r.to_dict() for r in validation_results],
            "warnings": warnings,
            "summary": {
                "Đường kính": f"DN{int(diameter)} ({material.upper()})",
                "Chiều dài": f"{round(horizontal_length, 1)} m",
                "Độ dốc": f"{round(slope, 2)} %",
                "Vận tốc": f"{flow_result.velocity} m/s",
                "Lưu lượng thiết kế": f"{design_flow*1000:.1f} L/s",
                "Khả năng tải": f"{full_capacity['Q_full']*1000:.1f} L/s",
                "Chế độ chảy": flow_result.flow_regime
            },
            "calculated_at": datetime.now().isoformat()
        }
    
    @classmethod
    def design_pressure_pipe(
        cls,
        design_flow: float,         # m³/s
        start_point: Tuple[float, float, float],
        end_point: Tuple[float, float, float],
        material: str = "hdpe",
        pressure_class: float = 10, # Áp lực (bar)
        min_cover: float = 1.0,
        diameter: float = None
    ) -> Dict[str, Any]:
        """
        Thiết kế đường ống áp lực
        
        Args:
            design_flow: Lưu lượng thiết kế (m³/s)
            start_point: Tọa độ điểm đầu
            end_point: Tọa độ điểm cuối
            material: Vật liệu ống
            pressure_class: Cấp áp lực (bar)
            min_cover: Độ sâu chôn ống (m)
            diameter: Đường kính (nếu đã biết)
            
        Returns:
            Dict: Kết quả thiết kế
        """
        # Tính chiều dài
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        dz = end_point[2] - start_point[2]
        horizontal_length = math.sqrt(dx**2 + dy**2)
        total_length = math.sqrt(dx**2 + dy**2 + dz**2)
        
        # Xác định đường kính
        if diameter is None:
            # Vận tốc thiết kế 1.0 m/s cho ống áp lực
            design_velocity = 1.0
            area = design_flow / design_velocity
            calc_diameter = math.sqrt(4 * area / math.pi) * 1000
            diameter = PipeRules.get_nearest_standard_diameter(calc_diameter)
        
        # Tính vận tốc thực tế
        area = math.pi * (diameter/1000)**2 / 4
        velocity = design_flow / area
        
        # Tính số Reynolds
        Re, regime = HydraulicCalculator.reynolds_number(velocity, diameter/1000)
        
        # Tính tổn thất cột nước
        head_loss = HydraulicCalculator.calculate_head_loss(
            length=total_length,
            diameter=diameter,
            flow_rate=design_flow,
            minor_loss_K=5.0  # Nhiều phụ kiện hơn
        )
        
        # Tính cột nước yêu cầu
        # H = Δz + hf + hm + h_residual
        static_head = max(0, dz)  # Chênh cao
        residual_head = 10  # Áp dư yêu cầu (m)
        total_head = static_head + head_loss.total_loss + residual_head
        
        # Tính công suất bơm (nếu cần)
        pump_power = 0
        if total_head > 0:
            # P = ρ × g × Q × H / η
            efficiency = 0.7
            pump_power = 9.81 * design_flow * total_head / efficiency / 1000  # kW
        
        # Kiểm tra quy tắc
        validation_params = {
            "velocity": velocity,
            "diameter": diameter,
            "cover_depth": min_cover,
            "reynolds": Re
        }
        validation_results = PipeRules.validate_pipe_design("pressure", validation_params)
        
        warnings = []
        for result in validation_results:
            if result.status.value in ["warning", "fail"]:
                warnings.append(result.message)
        
        return {
            "pipe_type": "pressure",
            "geometry": {
                "start_point": {"x": start_point[0], "y": start_point[1], "z": start_point[2]},
                "end_point": {"x": end_point[0], "y": end_point[1], "z": end_point[2]},
                "horizontal_length": round(horizontal_length, 2),
                "total_length": round(total_length, 2),
                "elevation_difference": round(dz, 2)
            },
            "design": {
                "diameter": diameter,
                "material": material,
                "pressure_class": pressure_class,
                "wall_thickness": cls._get_pipe_wall_thickness(diameter, pressure_class, material)
            },
            "hydraulics": {
                "design_flow": design_flow,
                "velocity": round(velocity, 3),
                "reynolds_number": round(Re, 0),
                "flow_regime": regime
            },
            "head_analysis": {
                "static_head": round(static_head, 2),
                "friction_loss": head_loss.friction_loss,
                "minor_loss": head_loss.minor_loss,
                "total_head_required": round(total_head, 2),
                "pump_power_required": round(pump_power, 2)
            },
            "validation": [r.to_dict() for r in validation_results],
            "warnings": warnings,
            "summary": {
                "Đường kính": f"DN{int(diameter)} PN{int(pressure_class)} ({material.upper()})",
                "Chiều dài": f"{round(total_length, 1)} m",
                "Vận tốc": f"{round(velocity, 2)} m/s",
                "Tổn thất cột nước": f"{round(head_loss.total_loss, 2)} m",
                "Cột nước yêu cầu": f"{round(total_head, 1)} m",
                "Công suất bơm": f"{round(pump_power, 2)} kW"
            },
            "calculated_at": datetime.now().isoformat()
        }
    
    @classmethod
    def design_pipe_profile(
        cls,
        points: List[Dict[str, float]],  # [{station, ground_level, x, y}, ...]
        design_flow: float,
        material: str = "hdpe",
        min_cover: float = 0.8,
        diameter: float = None
    ) -> Dict[str, Any]:
        """
        Thiết kế trắc dọc tuyến ống
        
        Args:
            points: Danh sách điểm dọc tuyến
            design_flow: Lưu lượng thiết kế (m³/s)
            material: Vật liệu
            min_cover: Độ sâu chôn tối thiểu
            diameter: Đường kính (nếu đã biết)
            
        Returns:
            Dict: Trắc dọc và danh sách đoạn ống
        """
        if len(points) < 2:
            raise ValueError("Cần ít nhất 2 điểm để thiết kế trắc dọc")
        
        # Sắp xếp theo lý trình
        points = sorted(points, key=lambda p: p["station"])
        
        # Tính tổng chiều dài
        total_length = points[-1]["station"] - points[0]["station"]
        
        # Tính độ dốc trung bình
        total_drop = points[0]["ground_level"] - points[-1]["ground_level"]
        avg_slope = (total_drop / total_length) * 100 if total_length > 0 else 0.5
        
        # Xác định đường kính
        if diameter is None:
            calc_result = PipeRules.calculate_recommended_diameter(
                design_flow=design_flow,
                slope=max(avg_slope, 0.3),
                material=material
            )
            diameter = calc_result["recommended_diameter"]
        
        # Xác định vị trí giếng thăm
        max_spacing = cls._get_manhole_spacing(diameter)
        manholes = cls._generate_manholes(points, max_spacing, min_cover, diameter)
        
        # Tạo các đoạn ống
        segments = []
        for i in range(len(manholes) - 1):
            mh_start = manholes[i]
            mh_end = manholes[i + 1]
            
            seg_length = mh_end["station"] - mh_start["station"]
            seg_slope = ((mh_start["invert_level"] - mh_end["invert_level"]) / seg_length) * 100
            
            segment = PipeSegment(
                id=i + 1,
                start_station=mh_start["station"],
                end_station=mh_end["station"],
                length=round(seg_length, 2),
                diameter=diameter,
                slope=round(seg_slope, 3),
                invert_start=mh_start["invert_level"],
                invert_end=mh_end["invert_level"],
                ground_start=mh_start["ground_level"],
                ground_end=mh_end["ground_level"],
                cover_start=round(mh_start["ground_level"] - mh_start["invert_level"] - diameter/1000, 2),
                cover_end=round(mh_end["ground_level"] - mh_end["invert_level"] - diameter/1000, 2)
            )
            segments.append(asdict(segment))
        
        # Tính thủy lực cho từng đoạn
        hydraulics = []
        for seg in segments:
            flow_result = HydraulicCalculator.circular_pipe_flow(
                diameter=seg["diameter"],
                slope=seg["slope"],
                fill_ratio=0.7,
                manning_n=PipeRules.get_manning_n(material)
            )
            hydraulics.append({
                "segment_id": seg["id"],
                "velocity": flow_result.velocity,
                "capacity": flow_result.flow_rate,
                "reynolds": flow_result.reynolds_number
            })
        
        return {
            "profile": {
                "total_length": round(total_length, 2),
                "start_station": points[0]["station"],
                "end_station": points[-1]["station"],
                "total_drop": round(total_drop, 2),
                "average_slope": round(avg_slope, 3)
            },
            "design": {
                "diameter": diameter,
                "material": material,
                "manning_n": PipeRules.get_manning_n(material)
            },
            "manholes": manholes,
            "segments": segments,
            "hydraulics": hydraulics,
            "summary": {
                "Tổng chiều dài": f"{round(total_length, 1)} m",
                "Đường kính": f"DN{int(diameter)}",
                "Số giếng thăm": len(manholes),
                "Số đoạn ống": len(segments)
            }
        }
    
    @classmethod
    def _get_manhole_spacing(cls, diameter: float) -> float:
        """Lấy khoảng cách giếng thăm tối đa theo đường kính"""
        if diameter <= 300:
            return cls.MAX_MANHOLE_SPACING["D150-D300"]
        elif diameter <= 600:
            return cls.MAX_MANHOLE_SPACING["D300-D600"]
        elif diameter <= 1000:
            return cls.MAX_MANHOLE_SPACING["D600-D1000"]
        else:
            return cls.MAX_MANHOLE_SPACING["D1000+"]
    
    @classmethod
    def _generate_manholes(
        cls,
        points: List[Dict],
        max_spacing: float,
        min_cover: float,
        diameter: float
    ) -> List[Dict]:
        """Tạo danh sách giếng thăm"""
        manholes = []
        mh_id = 1
        
        # Giếng đầu tiên
        start_point = points[0]
        invert_start = start_point["ground_level"] - min_cover - diameter/1000
        manholes.append({
            "id": f"MH{mh_id:02d}",
            "station": start_point["station"],
            "ground_level": start_point["ground_level"],
            "invert_level": round(invert_start, 3),
            "depth": round(start_point["ground_level"] - invert_start, 2),
            "diameter": 1000,
            "type": "start"
        })
        
        # Các giếng trung gian
        current_station = start_point["station"]
        current_invert = invert_start
        
        for i in range(1, len(points)):
            point = points[i]
            distance = point["station"] - current_station
            
            # Thêm giếng nếu khoảng cách vượt quá max
            while distance > max_spacing:
                mh_id += 1
                new_station = current_station + max_spacing
                
                # Nội suy cao độ mặt đất
                ground_level = cls._interpolate_ground_level(points, new_station)
                
                # Tính cao độ đáy ống (giữ độ dốc hợp lý)
                slope = 0.5 / 100  # Độ dốc tạm 0.5%
                new_invert = current_invert - slope * max_spacing
                
                # Kiểm tra độ sâu chôn
                if ground_level - new_invert - diameter/1000 < min_cover:
                    new_invert = ground_level - min_cover - diameter/1000
                
                manholes.append({
                    "id": f"MH{mh_id:02d}",
                    "station": round(new_station, 2),
                    "ground_level": round(ground_level, 3),
                    "invert_level": round(new_invert, 3),
                    "depth": round(ground_level - new_invert, 2),
                    "diameter": 1000,
                    "type": "intermediate"
                })
                
                current_station = new_station
                current_invert = new_invert
                distance = point["station"] - current_station
        
        # Giếng cuối cùng
        mh_id += 1
        end_point = points[-1]
        slope = 0.5 / 100
        invert_end = current_invert - slope * (end_point["station"] - current_station)
        
        if end_point["ground_level"] - invert_end - diameter/1000 < min_cover:
            invert_end = end_point["ground_level"] - min_cover - diameter/1000
        
        manholes.append({
            "id": f"MH{mh_id:02d}",
            "station": end_point["station"],
            "ground_level": end_point["ground_level"],
            "invert_level": round(invert_end, 3),
            "depth": round(end_point["ground_level"] - invert_end, 2),
            "diameter": 1000,
            "type": "end"
        })
        
        return manholes
    
    @staticmethod
    def _interpolate_ground_level(points: List[Dict], station: float) -> float:
        """Nội suy cao độ mặt đất tại lý trình"""
        for i in range(len(points) - 1):
            if points[i]["station"] <= station <= points[i+1]["station"]:
                t = (station - points[i]["station"]) / (points[i+1]["station"] - points[i]["station"])
                return points[i]["ground_level"] + t * (points[i+1]["ground_level"] - points[i]["ground_level"])
        return points[-1]["ground_level"]
    
    @staticmethod
    def _get_pipe_wall_thickness(diameter: float, pressure: float, material: str) -> float:
        """Tính chiều dày thành ống áp lực"""
        # Công thức đơn giản cho HDPE
        if material.lower() == "hdpe":
            SDR = {6: 26, 10: 17, 16: 11}
            sdr = SDR.get(int(pressure), 17)
            return round(diameter / sdr, 1)
        elif material.lower() == "pvc":
            return round(diameter / 21, 1)
        else:
            return round(diameter / 15, 1)
