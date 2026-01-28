"""
Hydraulic Calculator - Tính toán thủy lực

Bao gồm:
- Phương trình liên tục
- Công thức Manning
- Số Reynolds
- Tổn thất cột nước
"""

import math
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class FlowResult:
    """Kết quả tính toán dòng chảy"""
    velocity: float         # Vận tốc (m/s)
    flow_rate: float        # Lưu lượng (m³/s)
    area: float             # Diện tích mặt cắt (m²)
    wetted_perimeter: float # Chu vi ướt (m)
    hydraulic_radius: float # Bán kính thủy lực (m)
    reynolds_number: float  # Số Reynolds
    flow_regime: str        # Chế độ chảy
    froude_number: float    # Số Froude

@dataclass
class HeadLossResult:
    """Kết quả tính tổn thất cột nước"""
    friction_loss: float    # Tổn thất ma sát (m)
    minor_loss: float       # Tổn thất cục bộ (m)
    total_loss: float       # Tổng tổn thất (m)
    velocity_head: float    # Cột nước vận tốc (m)
    energy_grade: float     # Đường năng lượng (m)


class HydraulicCalculator:
    """
    Tính toán thủy lực cho đường ống và kênh mương
    
    Công thức sử dụng:
    - Manning: V = (1/n) * R^(2/3) * S^(1/2)
    - Liên tục: Q = V * A
    - Reynolds: Re = V * D / ν
    - Darcy-Weisbach: hf = f * (L/D) * (V²/2g)
    - Hazen-Williams: V = k * C * R^0.63 * S^0.54
    """
    
    # Hằng số vật lý
    GRAVITY = 9.81  # m/s²
    WATER_KINEMATIC_VISCOSITY = 1.004e-6  # m²/s ở 20°C
    
    @classmethod
    def continuity_equation(
        cls,
        flow_rate: float = None,   # m³/s
        velocity: float = None,     # m/s
        area: float = None          # m²
    ) -> Dict[str, float]:
        """
        Phương trình liên tục: Q = V × A
        
        Cho 2 trong 3 thông số, tính thông số còn lại
        """
        if flow_rate is not None and velocity is not None:
            area = flow_rate / velocity
        elif flow_rate is not None and area is not None:
            velocity = flow_rate / area
        elif velocity is not None and area is not None:
            flow_rate = velocity * area
        else:
            raise ValueError("Cần cung cấp ít nhất 2 thông số")
        
        return {
            "flow_rate": flow_rate,  # m³/s
            "velocity": velocity,     # m/s
            "area": area             # m²
        }
    
    @classmethod
    def manning_equation(
        cls,
        hydraulic_radius: float,  # Bán kính thủy lực (m)
        slope: float,             # Độ dốc (m/m hoặc %)
        manning_n: float = 0.013  # Hệ số nhám Manning
    ) -> float:
        """
        Công thức Manning: V = (1/n) × R^(2/3) × S^(1/2)
        
        Args:
            hydraulic_radius: Bán kính thủy lực R = A/P (m)
            slope: Độ dốc đáy (m/m). Nếu nhập % thì chia 100
            manning_n: Hệ số nhám Manning
            
        Returns:
            velocity: Vận tốc dòng chảy (m/s)
        """
        # Chuyển đổi slope nếu nhập %
        if slope > 1:
            slope = slope / 100
        
        velocity = (1 / manning_n) * (hydraulic_radius ** (2/3)) * (slope ** 0.5)
        return velocity
    
    @classmethod
    def reynolds_number(
        cls,
        velocity: float,      # Vận tốc (m/s)
        diameter: float,      # Đường kính hoặc chiều sâu đặc trưng (m)
        kinematic_viscosity: float = None  # Độ nhớt động học (m²/s)
    ) -> Tuple[float, str]:
        """
        Tính số Reynolds và xác định chế độ chảy
        
        Re = V × D / ν
        
        Returns:
            (reynolds_number, flow_regime)
        """
        if kinematic_viscosity is None:
            kinematic_viscosity = cls.WATER_KINEMATIC_VISCOSITY
        
        Re = velocity * diameter / kinematic_viscosity
        
        if Re < 2300:
            regime = "laminar"      # Chảy tầng
        elif Re < 4000:
            regime = "transitional" # Chuyển tiếp
        else:
            regime = "turbulent"    # Chảy rối
        
        return Re, regime
    
    @classmethod
    def froude_number(
        cls,
        velocity: float,  # m/s
        depth: float      # Chiều sâu nước (m)
    ) -> Tuple[float, str]:
        """
        Tính số Froude và xác định trạng thái dòng chảy
        
        Fr = V / √(g × D)
        
        Returns:
            (froude_number, flow_state)
        """
        Fr = velocity / math.sqrt(cls.GRAVITY * depth)
        
        if Fr < 1:
            state = "subcritical"   # Chảy êm (dưới tới hạn)
        elif Fr == 1:
            state = "critical"      # Chảy tới hạn
        else:
            state = "supercritical" # Chảy xiết (trên tới hạn)
        
        return Fr, state
    
    @classmethod
    def circular_pipe_flow(
        cls,
        diameter: float,      # Đường kính trong (mm)
        slope: float,         # Độ dốc (%)
        fill_ratio: float,    # Tỷ lệ đầy (0-1)
        manning_n: float = 0.013
    ) -> FlowResult:
        """
        Tính toán dòng chảy trong ống tròn (tự chảy)
        
        Args:
            diameter: Đường kính trong (mm)
            slope: Độ dốc (%)
            fill_ratio: Tỷ lệ đầy y/D (0-1)
            manning_n: Hệ số nhám Manning
            
        Returns:
            FlowResult: Kết quả tính toán
        """
        # Chuyển đổi đơn vị
        D = diameter / 1000  # mm -> m
        S = slope / 100      # % -> m/m
        h = fill_ratio * D   # Chiều cao nước (m)
        
        # Góc tâm (radians)
        # θ = 2 × arccos(1 - 2h/D)
        theta = 2 * math.acos(1 - 2 * fill_ratio)
        
        # Diện tích mặt cắt ướt
        # A = (D²/8) × (θ - sin(θ))
        A = (D ** 2 / 8) * (theta - math.sin(theta))
        
        # Chu vi ướt
        # P = D × θ / 2
        P = D * theta / 2
        
        # Bán kính thủy lực
        R = A / P if P > 0 else 0
        
        # Vận tốc (Manning)
        V = cls.manning_equation(R, S, manning_n)
        
        # Lưu lượng
        Q = V * A
        
        # Số Reynolds
        D_h = 4 * R  # Đường kính thủy lực
        Re, regime = cls.reynolds_number(V, D_h)
        
        # Số Froude
        Fr, _ = cls.froude_number(V, h)
        
        return FlowResult(
            velocity=round(V, 4),
            flow_rate=round(Q, 6),
            area=round(A, 6),
            wetted_perimeter=round(P, 4),
            hydraulic_radius=round(R, 4),
            reynolds_number=round(Re, 0),
            flow_regime=regime,
            froude_number=round(Fr, 3)
        )
    
    @classmethod
    def full_pipe_flow(
        cls,
        diameter: float,      # mm
        slope: float,         # %
        manning_n: float = 0.013
    ) -> Dict[str, float]:
        """
        Tính khả năng tải của ống khi chảy đầy
        
        Args:
            diameter: Đường kính trong (mm)
            slope: Độ dốc (%)
            manning_n: Hệ số nhám
            
        Returns:
            Dict với Q_full, V_full
        """
        D = diameter / 1000  # m
        S = slope / 100      # m/m
        
        # Ống đầy: A = πD²/4, R = D/4
        A = math.pi * D ** 2 / 4
        R = D / 4
        
        V = cls.manning_equation(R, S, manning_n)
        Q = V * A
        
        return {
            "Q_full": round(Q, 6),       # m³/s
            "V_full": round(V, 4),       # m/s
            "A_full": round(A, 6),       # m²
            "R_full": round(R, 4)        # m
        }
    
    @classmethod
    def calculate_required_slope(
        cls,
        diameter: float,      # mm
        design_flow: float,   # m³/s
        fill_ratio: float = 0.7,
        manning_n: float = 0.013
    ) -> float:
        """
        Tính độ dốc cần thiết để đạt lưu lượng thiết kế
        
        Args:
            diameter: Đường kính (mm)
            design_flow: Lưu lượng thiết kế (m³/s)
            fill_ratio: Tỷ lệ đầy thiết kế
            manning_n: Hệ số nhám
            
        Returns:
            slope: Độ dốc yêu cầu (%)
        """
        D = diameter / 1000  # m
        h = fill_ratio * D
        
        # Tính hình học
        theta = 2 * math.acos(1 - 2 * fill_ratio)
        A = (D ** 2 / 8) * (theta - math.sin(theta))
        P = D * theta / 2
        R = A / P
        
        # Từ Manning: V = Q/A = (1/n) × R^(2/3) × S^(1/2)
        # => S = [(Q × n) / (A × R^(2/3))]²
        
        V_required = design_flow / A
        S = ((V_required * manning_n) / (R ** (2/3))) ** 2
        
        return round(S * 100, 4)  # Trả về %
    
    @classmethod
    def darcy_weisbach_friction_loss(
        cls,
        length: float,        # Chiều dài (m)
        diameter: float,      # Đường kính (mm)
        velocity: float,      # Vận tốc (m/s)
        friction_factor: float = None,  # Hệ số ma sát
        roughness: float = 0.0001  # Độ nhám tương đối (m)
    ) -> float:
        """
        Tổn thất ma sát theo Darcy-Weisbach
        
        hf = f × (L/D) × (V²/2g)
        
        Args:
            length: Chiều dài ống (m)
            diameter: Đường kính trong (mm)
            velocity: Vận tốc (m/s)
            friction_factor: Hệ số ma sát f (nếu không có sẽ tính)
            roughness: Độ nhám tuyệt đối (m)
            
        Returns:
            friction_loss: Tổn thất ma sát (m)
        """
        D = diameter / 1000  # m
        
        if friction_factor is None:
            # Tính hệ số ma sát bằng công thức Swamee-Jain
            Re, _ = cls.reynolds_number(velocity, D)
            
            if Re < 2300:
                friction_factor = 64 / Re
            else:
                # Swamee-Jain equation
                friction_factor = 0.25 / (
                    math.log10(roughness / (3.7 * D) + 5.74 / (Re ** 0.9))
                ) ** 2
        
        hf = friction_factor * (length / D) * (velocity ** 2 / (2 * cls.GRAVITY))
        
        return round(hf, 4)
    
    @classmethod
    def minor_loss(
        cls,
        velocity: float,      # m/s
        K_total: float        # Tổng hệ số tổn thất cục bộ
    ) -> float:
        """
        Tổn thất cục bộ
        
        hm = K × (V²/2g)
        
        Args:
            velocity: Vận tốc (m/s)
            K_total: Tổng hệ số tổn thất cục bộ
            
        Returns:
            minor_loss: Tổn thất cục bộ (m)
        """
        hm = K_total * (velocity ** 2 / (2 * cls.GRAVITY))
        return round(hm, 4)
    
    @classmethod
    def hazen_williams(
        cls,
        diameter: float,      # mm
        slope: float,         # m/m
        C: float = 130        # Hệ số Hazen-Williams
    ) -> Dict[str, float]:
        """
        Công thức Hazen-Williams (cho ống áp lực)
        
        V = 0.849 × C × R^0.63 × S^0.54
        
        Args:
            diameter: Đường kính (mm)
            slope: Gradient thủy lực (m/m)
            C: Hệ số Hazen-Williams
            
        Returns:
            Dict với velocity, flow_rate
        """
        D = diameter / 1000  # m
        R = D / 4  # Bán kính thủy lực cho ống đầy
        A = math.pi * D ** 2 / 4
        
        V = 0.849 * C * (R ** 0.63) * (slope ** 0.54)
        Q = V * A
        
        return {
            "velocity": round(V, 4),
            "flow_rate": round(Q, 6)
        }
    
    @classmethod
    def calculate_head_loss(
        cls,
        length: float,        # m
        diameter: float,      # mm
        flow_rate: float,     # m³/s
        roughness: float = 0.0001,  # m
        minor_loss_K: float = 0     # Hệ số tổn thất cục bộ
    ) -> HeadLossResult:
        """
        Tính toán tổng tổn thất cột nước
        
        Args:
            length: Chiều dài tuyến ống (m)
            diameter: Đường kính trong (mm)
            flow_rate: Lưu lượng (m³/s)
            roughness: Độ nhám tuyệt đối (m)
            minor_loss_K: Tổng hệ số tổn thất cục bộ
            
        Returns:
            HeadLossResult: Kết quả tổn thất
        """
        D = diameter / 1000  # m
        A = math.pi * D ** 2 / 4
        V = flow_rate / A
        
        # Tổn thất ma sát
        hf = cls.darcy_weisbach_friction_loss(length, diameter, V, roughness=roughness)
        
        # Tổn thất cục bộ
        hm = cls.minor_loss(V, minor_loss_K)
        
        # Cột nước vận tốc
        hv = V ** 2 / (2 * cls.GRAVITY)
        
        # Tổng tổn thất
        h_total = hf + hm
        
        return HeadLossResult(
            friction_loss=round(hf, 4),
            minor_loss=round(hm, 4),
            total_loss=round(h_total, 4),
            velocity_head=round(hv, 4),
            energy_grade=round(h_total + hv, 4)
        )
    
    @classmethod
    def open_channel_flow(
        cls,
        bottom_width: float,  # Chiều rộng đáy (m)
        side_slope: float,    # Độ dốc mái (H:V, ví dụ 1:1)
        depth: float,         # Chiều sâu nước (m)
        bed_slope: float,     # Độ dốc đáy (%)
        manning_n: float = 0.025
    ) -> Dict[str, float]:
        """
        Tính toán dòng chảy trong kênh hình thang
        
        Args:
            bottom_width: Chiều rộng đáy b (m)
            side_slope: Độ dốc mái m (H:V)
            depth: Chiều sâu nước h (m)
            bed_slope: Độ dốc đáy S (%)
            manning_n: Hệ số nhám Manning
            
        Returns:
            Dict với các thông số thủy lực
        """
        b = bottom_width
        m = side_slope
        h = depth
        S = bed_slope / 100
        
        # Diện tích mặt cắt: A = (b + m×h) × h
        A = (b + m * h) * h
        
        # Chu vi ướt: P = b + 2×h×√(1 + m²)
        P = b + 2 * h * math.sqrt(1 + m ** 2)
        
        # Bán kính thủy lực
        R = A / P
        
        # Chiều rộng mặt nước: T = b + 2×m×h
        T = b + 2 * m * h
        
        # Chiều sâu thủy lực: D_h = A/T
        D_h = A / T
        
        # Vận tốc Manning
        V = cls.manning_equation(R, S, manning_n)
        
        # Lưu lượng
        Q = V * A
        
        # Số Froude
        Fr, state = cls.froude_number(V, D_h)
        
        return {
            "area": round(A, 4),
            "wetted_perimeter": round(P, 4),
            "hydraulic_radius": round(R, 4),
            "top_width": round(T, 4),
            "hydraulic_depth": round(D_h, 4),
            "velocity": round(V, 4),
            "flow_rate": round(Q, 4),
            "froude_number": round(Fr, 3),
            "flow_state": state
        }
