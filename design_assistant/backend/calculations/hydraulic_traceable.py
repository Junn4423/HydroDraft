"""
Traceable Hydraulic Engine - Động cơ tính toán thủy lực có truy xuất

SPRINT 2: TRANSPARENT ENGINEERING
Mọi tính toán đều có:
- Công thức LaTeX
- Giá trị đầu vào
- Tham chiếu tiêu chuẩn
- Điều kiện áp dụng
- Kết quả chi tiết

Tiêu chuẩn áp dụng:
- TCVN 7957:2008 - Thoát nước - Mạng lưới và công trình bên ngoài
- TCVN 33:2006 - Cấp nước - Mạng lưới đường ống và công trình
- TCVN 4474:1987 - Thoát nước bên trong
"""

import math
import uuid
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, asdict
from datetime import datetime

from calculations.calculation_log import (
    CalculationLog, CalculationStep, Violation,
    CalculationStatus, ViolationSeverity,
    CalculationLogger, EngineeringConstants
)


@dataclass
class TraceableFlowResult:
    """Kết quả dòng chảy có truy xuất"""
    
    # Kết quả tính toán
    velocity: float                  # Vận tốc (m/s)
    flow_rate: float                 # Lưu lượng (m³/s)
    area: float                      # Diện tích mặt cắt (m²)
    wetted_perimeter: float          # Chu vi ướt (m)
    hydraulic_radius: float          # Bán kính thủy lực (m)
    reynolds_number: float           # Số Reynolds
    flow_regime: str                 # Chế độ chảy
    froude_number: float             # Số Froude
    flow_state: str                  # Trạng thái dòng chảy
    
    # Log tính toán
    calculation_log: CalculationLog = None
    
    def to_dict(self) -> Dict:
        return {
            "velocity": self.velocity,
            "flow_rate": self.flow_rate,
            "area": self.area,
            "wetted_perimeter": self.wetted_perimeter,
            "hydraulic_radius": self.hydraulic_radius,
            "reynolds_number": self.reynolds_number,
            "flow_regime": self.flow_regime,
            "froude_number": self.froude_number,
            "flow_state": self.flow_state,
            "calculation_log": self.calculation_log.to_dict() if self.calculation_log else None
        }


@dataclass
class TraceableHeadLossResult:
    """Kết quả tổn thất cột nước có truy xuất"""
    
    friction_loss: float             # Tổn thất ma sát (m)
    minor_loss: float                # Tổn thất cục bộ (m)
    total_loss: float                # Tổng tổn thất (m)
    velocity_head: float             # Cột nước vận tốc (m)
    friction_factor: float           # Hệ số ma sát Darcy
    
    # Log tính toán
    calculation_log: CalculationLog = None
    
    def to_dict(self) -> Dict:
        return {
            "friction_loss": self.friction_loss,
            "minor_loss": self.minor_loss,
            "total_loss": self.total_loss,
            "velocity_head": self.velocity_head,
            "friction_factor": self.friction_factor,
            "calculation_log": self.calculation_log.to_dict() if self.calculation_log else None
        }


class TraceableHydraulicEngine:
    """
    Động cơ tính toán thủy lực với truy xuất đầy đủ
    
    Tất cả các phương thức đều trả về:
    - Kết quả tính toán
    - CalculationLog với các bước chi tiết
    
    Tiêu chuẩn áp dụng:
    - TCVN 7957:2008 - Thoát nước
    - TCVN 33:2006 - Cấp nước
    - Colebrook-White, Darcy-Weisbach
    """
    
    # Hằng số
    GRAVITY = EngineeringConstants.GRAVITY
    
    # Giới hạn vận tốc theo TCVN 7957:2008
    VELOCITY_LIMITS = {
        "gravity_pipe": {
            "min": 0.7,   # m/s - Vận tốc tự làm sạch
            "max": 4.0,   # m/s - Tránh mài mòn
            "design": 1.0  # m/s - Vận tốc thiết kế
        },
        "pressure_pipe": {
            "min": 0.5,
            "max": 2.5,
            "design": 1.2
        },
        "open_channel": {
            "min": 0.4,
            "max": 3.0,
            "design": 0.8
        }
    }
    
    # Giới hạn số Froude
    FROUDE_LIMITS = {
        "subcritical_max": 0.9,      # Giới hạn chảy êm
        "supercritical_min": 1.1     # Giới hạn chảy xiết
    }
    
    @classmethod
    def calculate_reynolds_number(
        cls,
        velocity: float,
        characteristic_length: float,
        temperature: float = 20.0,
        kinematic_viscosity: float = None
    ) -> Tuple[float, str, CalculationStep]:
        """
        Tính số Reynolds và xác định chế độ chảy
        
        Re = V × D / ν
        
        Chế độ chảy:
        - Re < 2300: Chảy tầng (laminar)
        - 2300 ≤ Re < 4000: Chuyển tiếp (transitional)
        - Re ≥ 4000: Chảy rối (turbulent)
        
        Args:
            velocity: Vận tốc dòng chảy (m/s)
            characteristic_length: Chiều dài đặc trưng - đường kính hoặc chiều sâu (m)
            temperature: Nhiệt độ nước (°C)
            kinematic_viscosity: Độ nhớt động học (m²/s), nếu None sẽ nội suy theo T
            
        Returns:
            (Re, regime, CalculationStep)
        """
        # Lấy độ nhớt theo nhiệt độ
        if kinematic_viscosity is None:
            kinematic_viscosity = EngineeringConstants.get_water_viscosity(temperature)
        
        # Tính số Reynolds
        Re = velocity * characteristic_length / kinematic_viscosity
        
        # Xác định chế độ chảy
        if Re < 2300:
            regime = "laminar"
            regime_vi = "Chảy tầng"
        elif Re < 4000:
            regime = "transitional"
            regime_vi = "Chuyển tiếp"
        else:
            regime = "turbulent"
            regime_vi = "Chảy rối"
        
        # Tạo bước tính toán
        step = CalculationLogger.create_step(
            step_id="reynolds_number",
            name="Tính số Reynolds",
            description=f"Xác định chế độ chảy dựa trên số Reynolds. Re = {Re:.0f} → {regime_vi}",
            formula_latex=r"Re = \frac{V \times D}{\nu}",
            formula_text="Re = V × D / ν",
            reference="Fluid Mechanics - Frank M. White; TCVN 7957:2008 - Phụ lục A",
            inputs={
                "V": velocity,
                "D": characteristic_length,
                "ν": kinematic_viscosity,
                "T": temperature
            },
            input_descriptions={
                "V": "Vận tốc dòng chảy (m/s)",
                "D": "Chiều dài đặc trưng (m)",
                "ν": "Độ nhớt động học (m²/s)",
                "T": "Nhiệt độ nước (°C)"
            },
            conditions=[
                f"Re < 2300: Chảy tầng",
                f"2300 ≤ Re < 4000: Chuyển tiếp",
                f"Re ≥ 4000: Chảy rối"
            ],
            assumptions=[
                "Dòng chảy ổn định (steady flow)",
                "Chất lỏng Newton"
            ],
            result=Re,
            result_unit="-"
        )
        
        # Cảnh báo nếu chảy tầng (thường không mong muốn trong thoát nước)
        if regime == "laminar":
            step.status = CalculationStatus.WARNING
            step.warnings.append("Chế độ chảy tầng - vận tốc có thể quá thấp gây lắng đọng")
        
        return Re, regime, step
    
    @classmethod
    def calculate_froude_number(
        cls,
        velocity: float,
        hydraulic_depth: float
    ) -> Tuple[float, str, CalculationStep]:
        """
        Tính số Froude và xác định trạng thái dòng chảy
        
        Fr = V / √(g × h)
        
        Trạng thái:
        - Fr < 1: Chảy êm (subcritical)
        - Fr = 1: Chảy tới hạn (critical)
        - Fr > 1: Chảy xiết (supercritical)
        
        Args:
            velocity: Vận tốc dòng chảy (m/s)
            hydraulic_depth: Chiều sâu thủy lực (m) = A/T
            
        Returns:
            (Fr, state, CalculationStep)
        """
        Fr = velocity / math.sqrt(cls.GRAVITY * hydraulic_depth)
        
        if Fr < 1:
            state = "subcritical"
            state_vi = "Chảy êm (dưới tới hạn)"
        elif Fr == 1:
            state = "critical"
            state_vi = "Chảy tới hạn"
        else:
            state = "supercritical"
            state_vi = "Chảy xiết (trên tới hạn)"
        
        step = CalculationLogger.create_step(
            step_id="froude_number",
            name="Tính số Froude",
            description=f"Xác định trạng thái dòng chảy. Fr = {Fr:.3f} → {state_vi}",
            formula_latex=r"Fr = \frac{V}{\sqrt{g \times h}}",
            formula_text="Fr = V / √(g × h)",
            reference="Open Channel Hydraulics - Ven Te Chow; TCVN 7957:2008 - Điều 5.4",
            inputs={
                "V": velocity,
                "g": cls.GRAVITY,
                "h": hydraulic_depth
            },
            input_descriptions={
                "V": "Vận tốc dòng chảy (m/s)",
                "g": "Gia tốc trọng trường (m/s²)",
                "h": "Chiều sâu thủy lực (m)"
            },
            conditions=[
                "Fr < 1: Chảy êm - sóng có thể truyền ngược dòng",
                "Fr = 1: Chảy tới hạn - năng lượng riêng cực tiểu",
                "Fr > 1: Chảy xiết - sóng chỉ truyền xuôi dòng"
            ],
            assumptions=[
                "Phân bố vận tốc đều trên mặt cắt",
                "Đáy kênh nằm ngang hoặc dốc nhẹ"
            ],
            result=Fr,
            result_unit="-"
        )
        
        # Cảnh báo nếu gần tới hạn
        if 0.9 < Fr < 1.1:
            step.status = CalculationStatus.WARNING
            step.warnings.append("Dòng chảy gần tới hạn - có thể không ổn định, nên tránh thiết kế trong vùng này")
        
        return Fr, state, step
    
    @classmethod
    def calculate_manning_velocity(
        cls,
        hydraulic_radius: float,
        slope: float,
        manning_n: float,
        slope_unit: str = "decimal"
    ) -> Tuple[float, CalculationStep]:
        """
        Tính vận tốc theo công thức Manning
        
        V = (1/n) × R^(2/3) × S^(1/2)
        
        Args:
            hydraulic_radius: Bán kính thủy lực R = A/P (m)
            slope: Độ dốc đáy
            manning_n: Hệ số nhám Manning
            slope_unit: Đơn vị độ dốc ("decimal", "percent", "permille")
            
        Returns:
            (velocity, CalculationStep)
        """
        # Chuyển đổi đơn vị độ dốc
        S_original = slope
        if slope_unit == "percent" or slope > 1:
            slope = slope / 100
        elif slope_unit == "permille":
            slope = slope / 1000
        
        # Kiểm tra slope hợp lệ
        if slope <= 0:
            raise ValueError("Độ dốc phải lớn hơn 0")
        
        # Tính vận tốc
        velocity = (1 / manning_n) * (hydraulic_radius ** (2/3)) * (slope ** 0.5)
        
        step = CalculationLogger.create_step(
            step_id="manning_velocity",
            name="Tính vận tốc theo Manning",
            description=f"Công thức Manning cho dòng chảy đều trong kênh hở và ống tự chảy",
            formula_latex=r"V = \frac{1}{n} \times R^{2/3} \times S^{1/2}",
            formula_text="V = (1/n) × R^(2/3) × S^(1/2)",
            reference="TCVN 7957:2008 - Điều 5.3.2; Manning's equation (1889)",
            inputs={
                "n": manning_n,
                "R": hydraulic_radius,
                "S": slope,
                "S_original": S_original,
                "slope_unit": slope_unit
            },
            input_descriptions={
                "n": "Hệ số nhám Manning",
                "R": "Bán kính thủy lực (m)",
                "S": "Độ dốc đáy (m/m)",
                "S_original": f"Độ dốc đầu vào ({slope_unit})"
            },
            conditions=[
                "Dòng chảy đều (uniform flow)",
                "Kênh lăng trụ (prismatic channel)",
                "Mặt cắt không đổi theo chiều dòng chảy"
            ],
            assumptions=[
                "Chế độ chảy rối hoàn toàn",
                "Bề mặt nhám đồng nhất"
            ],
            limits={
                "n_range": {"min": 0.008, "max": 0.050},
                "S_range": {"min": 0.0001, "max": 0.10}
            },
            result=velocity,
            result_unit="m/s"
        )
        
        return velocity, step
    
    @classmethod
    def calculate_friction_factor_colebrook(
        cls,
        reynolds: float,
        relative_roughness: float,
        max_iterations: int = 50,
        tolerance: float = 1e-6
    ) -> Tuple[float, str, CalculationStep]:
        """
        Tính hệ số ma sát Darcy theo Colebrook-White (lặp)
        
        1/√f = -2 × log₁₀(ε/D/3.7 + 2.51/(Re×√f))
        
        Args:
            reynolds: Số Reynolds
            relative_roughness: Độ nhám tương đối ε/D
            max_iterations: Số lần lặp tối đa
            tolerance: Sai số cho phép
            
        Returns:
            (f, method, CalculationStep)
        """
        method = ""
        iterations_used = 0
        
        if reynolds < 2300:
            # Chảy tầng: f = 64/Re
            f = 64 / reynolds
            method = "laminar"
            formula_used = "f = 64 / Re (chảy tầng)"
        else:
            # Chảy rối: Colebrook-White iteration
            # Khởi tạo với Swamee-Jain
            f = 0.25 / (math.log10(relative_roughness / 3.7 + 5.74 / (reynolds ** 0.9))) ** 2
            
            for i in range(max_iterations):
                f_old = f
                # Colebrook-White: 1/√f = -2×log₁₀(ε/D/3.7 + 2.51/(Re×√f))
                rhs = -2 * math.log10(relative_roughness / 3.7 + 2.51 / (reynolds * math.sqrt(f)))
                f = 1 / (rhs ** 2)
                
                if abs(f - f_old) < tolerance:
                    iterations_used = i + 1
                    break
            
            method = "colebrook-white"
            formula_used = "Colebrook-White iteration"
        
        step = CalculationLogger.create_step(
            step_id="friction_factor",
            name="Tính hệ số ma sát Darcy",
            description=f"Phương pháp: {formula_used}. Số lần lặp: {iterations_used}",
            formula_latex=r"\frac{1}{\sqrt{f}} = -2 \log_{10}\left(\frac{\varepsilon/D}{3.7} + \frac{2.51}{Re \times \sqrt{f}}\right)",
            formula_text="1/√f = -2×log₁₀(ε/D/3.7 + 2.51/(Re×√f))",
            reference="Colebrook-White (1939); TCVN 7957:2008 - Phụ lục B",
            inputs={
                "Re": reynolds,
                "ε/D": relative_roughness,
                "iterations": iterations_used
            },
            input_descriptions={
                "Re": "Số Reynolds",
                "ε/D": "Độ nhám tương đối",
                "iterations": "Số lần lặp"
            },
            conditions=[
                f"Re < 2300: Chảy tầng, f = 64/Re",
                f"Re ≥ 2300: Chảy rối, dùng Colebrook-White"
            ],
            assumptions=[
                "Ống tròn, dòng chảy đầy",
                "Độ nhám đồng nhất"
            ],
            result=f,
            result_unit="-"
        )
        
        return f, method, step
    
    @classmethod
    def calculate_darcy_weisbach_loss(
        cls,
        length: float,
        diameter: float,
        velocity: float,
        friction_factor: float
    ) -> Tuple[float, CalculationStep]:
        """
        Tính tổn thất ma sát theo Darcy-Weisbach
        
        h_f = f × (L/D) × (V²/2g)
        
        Args:
            length: Chiều dài ống (m)
            diameter: Đường kính trong (m)
            velocity: Vận tốc (m/s)
            friction_factor: Hệ số ma sát Darcy
            
        Returns:
            (h_f, CalculationStep)
        """
        h_f = friction_factor * (length / diameter) * (velocity ** 2 / (2 * cls.GRAVITY))
        
        step = CalculationLogger.create_step(
            step_id="darcy_weisbach",
            name="Tính tổn thất ma sát Darcy-Weisbach",
            description=f"Tổn thất dọc đường do ma sát với thành ống",
            formula_latex=r"h_f = f \times \frac{L}{D} \times \frac{V^2}{2g}",
            formula_text="h_f = f × (L/D) × (V²/2g)",
            reference="Darcy-Weisbach equation; TCVN 7957:2008 - Điều 5.3.3",
            inputs={
                "f": friction_factor,
                "L": length,
                "D": diameter,
                "V": velocity,
                "g": cls.GRAVITY
            },
            input_descriptions={
                "f": "Hệ số ma sát Darcy",
                "L": "Chiều dài ống (m)",
                "D": "Đường kính trong (m)",
                "V": "Vận tốc (m/s)",
                "g": "Gia tốc trọng trường (m/s²)"
            },
            conditions=[
                "Áp dụng cho mọi chế độ chảy",
                "Đúng với mọi loại chất lỏng Newton"
            ],
            result=h_f,
            result_unit="m"
        )
        
        return h_f, step
    
    @classmethod
    def calculate_minor_losses(
        cls,
        velocity: float,
        k_coefficients: Dict[str, float]
    ) -> Tuple[float, CalculationStep]:
        """
        Tính tổn thất cục bộ
        
        h_m = Σ(K × V²/2g)
        
        Args:
            velocity: Vận tốc (m/s)
            k_coefficients: Dict của {tên phụ kiện: hệ số K}
            
        Returns:
            (h_m, CalculationStep)
        """
        K_total = sum(k_coefficients.values())
        h_m = K_total * (velocity ** 2 / (2 * cls.GRAVITY))
        
        # Tạo mô tả chi tiết
        details = [f"{name}: K = {k}" for name, k in k_coefficients.items()]
        
        step = CalculationLogger.create_step(
            step_id="minor_losses",
            name="Tính tổn thất cục bộ",
            description=f"Tổn thất qua các phụ kiện: {', '.join(details)}",
            formula_latex=r"h_m = \sum K \times \frac{V^2}{2g}",
            formula_text="h_m = ΣK × V²/2g",
            reference="TCVN 7957:2008 - Bảng 5; Idelchik - Handbook of Hydraulic Resistance",
            inputs={
                "V": velocity,
                "g": cls.GRAVITY,
                "K_coefficients": k_coefficients,
                "K_total": K_total
            },
            input_descriptions={
                "V": "Vận tốc (m/s)",
                "g": "Gia tốc trọng trường (m/s²)",
                "K_coefficients": "Hệ số tổn thất các phụ kiện",
                "K_total": "Tổng hệ số K"
            },
            conditions=[
                "Áp dụng cho dòng chảy rối",
                "Các phụ kiện cách xa nhau (>10D)"
            ],
            result=h_m,
            result_unit="m"
        )
        
        return h_m, step
    
    @classmethod
    def calculate_circular_pipe_geometry(
        cls,
        diameter: float,
        fill_ratio: float
    ) -> Tuple[Dict[str, float], CalculationStep]:
        """
        Tính các thông số hình học ống tròn tự chảy
        
        Args:
            diameter: Đường kính trong (m)
            fill_ratio: Tỷ lệ đầy h/D (0-1)
            
        Returns:
            (geometry_dict, CalculationStep)
        """
        D = diameter
        h = fill_ratio * D  # Chiều cao nước
        
        # Góc tâm (radians): θ = 2 × arccos(1 - 2h/D)
        theta = 2 * math.acos(1 - 2 * fill_ratio)
        
        # Diện tích mặt cắt ướt: A = (D²/8) × (θ - sin(θ))
        A = (D ** 2 / 8) * (theta - math.sin(theta))
        
        # Chu vi ướt: P = D × θ / 2
        P = D * theta / 2
        
        # Bán kính thủy lực: R = A / P
        R = A / P if P > 0 else 0
        
        # Chiều rộng mặt nước: T = D × sin(θ/2)
        T = D * math.sin(theta / 2)
        
        # Chiều sâu thủy lực: D_h = A / T
        D_h = A / T if T > 0 else h
        
        geometry = {
            "diameter": D,
            "fill_ratio": fill_ratio,
            "water_depth": h,
            "central_angle": theta,
            "central_angle_deg": math.degrees(theta),
            "area": A,
            "wetted_perimeter": P,
            "hydraulic_radius": R,
            "top_width": T,
            "hydraulic_depth": D_h
        }
        
        step = CalculationLogger.create_step(
            step_id="pipe_geometry",
            name="Tính hình học ống tròn tự chảy",
            description=f"Ống D = {D*1000:.0f}mm, tỷ lệ đầy h/D = {fill_ratio:.2f}",
            formula_latex=r"""
            \theta = 2 \arccos(1 - 2h/D) \\
            A = \frac{D^2}{8}(\theta - \sin\theta) \\
            P = \frac{D \times \theta}{2} \\
            R = \frac{A}{P}
            """,
            formula_text="θ = 2×arccos(1-2h/D); A = D²/8×(θ-sinθ); P = D×θ/2; R = A/P",
            reference="Hydraulics - Circular Conduits; TCVN 7957:2008 - Phụ lục A",
            inputs={
                "D": D,
                "h/D": fill_ratio,
                "h": h
            },
            input_descriptions={
                "D": "Đường kính trong (m)",
                "h/D": "Tỷ lệ đầy",
                "h": "Chiều cao nước (m)"
            },
            conditions=[
                f"0 < h/D < 1 (tự chảy không đầy)",
                f"h/D = 0.7 - 0.8 là tối ưu cho thoát nước"
            ],
            result=geometry,
            result_unit=""
        )
        
        return geometry, step
    
    @classmethod
    def calculate_pipe_flow_comprehensive(
        cls,
        diameter_mm: float,
        slope_percent: float,
        fill_ratio: float = 0.7,
        manning_n: float = 0.013,
        temperature: float = 20.0,
        roughness_mm: float = 0.1,
        pipe_length: float = 100.0,
        minor_loss_K: float = 0.0
    ) -> TraceableFlowResult:
        """
        Tính toán thủy lực ống tự chảy hoàn chỉnh
        
        Bao gồm:
        - Hình học mặt cắt
        - Vận tốc Manning
        - Số Reynolds & chế độ chảy
        - Số Froude & trạng thái dòng chảy
        - Tổn thất cột nước
        - Kiểm tra tiêu chuẩn
        
        Args:
            diameter_mm: Đường kính trong (mm)
            slope_percent: Độ dốc (%)
            fill_ratio: Tỷ lệ đầy (0-1)
            manning_n: Hệ số nhám Manning
            temperature: Nhiệt độ nước (°C)
            roughness_mm: Độ nhám tuyệt đối (mm)
            pipe_length: Chiều dài ống (m)
            minor_loss_K: Tổng hệ số tổn thất cục bộ
            
        Returns:
            TraceableFlowResult với đầy đủ log
        """
        import time
        start_time = time.time()
        
        # Khởi tạo log
        log = CalculationLogger.create_log(
            log_id=str(uuid.uuid4())[:8],
            calculation_type="hydraulic",
            module_name="Tính toán thủy lực ống tự chảy",
            description=f"Ống D{diameter_mm}mm, i={slope_percent}%, h/D={fill_ratio}",
            standards=["TCVN 7957:2008", "TCVN 33:2006"]
        )
        
        # Chuyển đổi đơn vị
        D = diameter_mm / 1000  # m
        S = slope_percent / 100  # m/m
        roughness = roughness_mm / 1000  # m
        
        violations = []
        
        # 1. Tính hình học mặt cắt
        geometry, geom_step = cls.calculate_circular_pipe_geometry(D, fill_ratio)
        log.add_step(geom_step)
        
        A = geometry["area"]
        P = geometry["wetted_perimeter"]
        R = geometry["hydraulic_radius"]
        D_h = geometry["hydraulic_depth"]
        h = geometry["water_depth"]
        
        # 2. Tính vận tốc Manning
        velocity, manning_step = cls.calculate_manning_velocity(R, S, manning_n, "decimal")
        log.add_step(manning_step)
        
        # 3. Tính lưu lượng
        Q = velocity * A
        flow_step = CalculationLogger.create_step(
            step_id="flow_rate",
            name="Tính lưu lượng",
            description="Áp dụng phương trình liên tục",
            formula_latex=r"Q = V \times A",
            formula_text="Q = V × A",
            reference="Phương trình liên tục",
            inputs={"V": velocity, "A": A},
            input_descriptions={"V": "Vận tốc (m/s)", "A": "Diện tích (m²)"},
            result=Q,
            result_unit="m³/s"
        )
        log.add_step(flow_step)
        
        # 4. Tính số Reynolds
        D_hydraulic = 4 * R  # Đường kính thủy lực
        Re, regime, re_step = cls.calculate_reynolds_number(velocity, D_hydraulic, temperature)
        log.add_step(re_step)
        
        # 5. Tính số Froude
        Fr, flow_state, fr_step = cls.calculate_froude_number(velocity, D_h)
        log.add_step(fr_step)
        
        # 6. Kiểm tra vận tốc theo tiêu chuẩn
        v_limits = cls.VELOCITY_LIMITS["gravity_pipe"]
        
        if velocity < v_limits["min"]:
            v_violation = CalculationLogger.create_violation(
                violation_id="velocity_min",
                parameter="velocity",
                actual_value=round(velocity, 3),
                limit_value=v_limits["min"],
                limit_type="min",
                severity=ViolationSeverity.MAJOR,
                standard="TCVN 7957:2008",
                clause="Điều 5.3.4 - Vận tốc tự làm sạch",
                message=f"Vận tốc {velocity:.3f} m/s < {v_limits['min']} m/s (tối thiểu)",
                suggestion=f"Tăng độ dốc hoặc giảm đường kính ống để đạt V ≥ {v_limits['min']} m/s"
            )
            log.add_violation(v_violation)
            violations.append(v_violation)
        
        if velocity > v_limits["max"]:
            v_violation = CalculationLogger.create_violation(
                violation_id="velocity_max",
                parameter="velocity",
                actual_value=round(velocity, 3),
                limit_value=v_limits["max"],
                limit_type="max",
                severity=ViolationSeverity.MAJOR,
                standard="TCVN 7957:2008",
                clause="Điều 5.3.5 - Vận tốc tối đa",
                message=f"Vận tốc {velocity:.3f} m/s > {v_limits['max']} m/s (tối đa)",
                suggestion=f"Giảm độ dốc hoặc tăng đường kính ống để đạt V ≤ {v_limits['max']} m/s"
            )
            log.add_violation(v_violation)
            violations.append(v_violation)
        
        # Bước kiểm tra vận tốc
        v_check_step = CalculationLogger.create_step(
            step_id="velocity_check",
            name="Kiểm tra vận tốc",
            description=f"Kiểm tra vận tốc V = {velocity:.3f} m/s với giới hạn TCVN",
            formula_latex=r"V_{min} \leq V \leq V_{max}",
            formula_text=f"{v_limits['min']} ≤ V ≤ {v_limits['max']} m/s",
            reference="TCVN 7957:2008 - Điều 5.3",
            inputs={
                "V": velocity,
                "V_min": v_limits["min"],
                "V_max": v_limits["max"]
            },
            result="PASS" if v_limits["min"] <= velocity <= v_limits["max"] else "FAIL",
            result_unit=""
        )
        if v_limits["min"] <= velocity <= v_limits["max"]:
            v_check_step.status = CalculationStatus.SUCCESS
        else:
            v_check_step.status = CalculationStatus.VIOLATION
        log.add_step(v_check_step)
        
        # 7. Tính tổn thất cột nước (nếu có chiều dài)
        if pipe_length > 0:
            relative_roughness = roughness / D
            f, f_method, f_step = cls.calculate_friction_factor_colebrook(Re, relative_roughness)
            log.add_step(f_step)
            
            h_f, hf_step = cls.calculate_darcy_weisbach_loss(pipe_length, D, velocity, f)
            log.add_step(hf_step)
            
            h_m = 0
            if minor_loss_K > 0:
                h_m, hm_step = cls.calculate_minor_losses(velocity, {"Tổng K": minor_loss_K})
                log.add_step(hm_step)
        else:
            f = 0
            h_f = 0
            h_m = 0
        
        # Kết quả cuối cùng
        log.final_results = {
            "diameter_mm": diameter_mm,
            "slope_percent": slope_percent,
            "fill_ratio": fill_ratio,
            "velocity_m_s": round(velocity, 4),
            "flow_rate_m3_s": round(Q, 6),
            "flow_rate_L_s": round(Q * 1000, 2),
            "reynolds_number": round(Re, 0),
            "flow_regime": regime,
            "froude_number": round(Fr, 3),
            "flow_state": flow_state,
            "hydraulic_radius_m": round(R, 4),
            "friction_loss_m": round(h_f, 4),
            "minor_loss_m": round(h_m, 4),
            "total_head_loss_m": round(h_f + h_m, 4)
        }
        
        # Thời gian tính toán
        log.calculation_time_ms = (time.time() - start_time) * 1000
        
        return TraceableFlowResult(
            velocity=round(velocity, 4),
            flow_rate=round(Q, 6),
            area=round(A, 6),
            wetted_perimeter=round(P, 4),
            hydraulic_radius=round(R, 4),
            reynolds_number=round(Re, 0),
            flow_regime=regime,
            froude_number=round(Fr, 3),
            flow_state=flow_state,
            calculation_log=log
        )
    
    @classmethod
    def calculate_head_loss_comprehensive(
        cls,
        diameter_mm: float,
        length_m: float,
        flow_rate_m3s: float,
        roughness_mm: float = 0.1,
        temperature: float = 20.0,
        fittings: Dict[str, float] = None
    ) -> TraceableHeadLossResult:
        """
        Tính tổng tổn thất cột nước cho đường ống áp lực
        
        Args:
            diameter_mm: Đường kính trong (mm)
            length_m: Chiều dài ống (m)
            flow_rate_m3s: Lưu lượng (m³/s)
            roughness_mm: Độ nhám tuyệt đối (mm)
            temperature: Nhiệt độ nước (°C)
            fittings: Dict của {tên phụ kiện: hệ số K}
            
        Returns:
            TraceableHeadLossResult
        """
        import time
        start_time = time.time()
        
        log = CalculationLogger.create_log(
            log_id=str(uuid.uuid4())[:8],
            calculation_type="hydraulic_head_loss",
            module_name="Tính tổn thất cột nước",
            description=f"Ống D{diameter_mm}mm, L={length_m}m, Q={flow_rate_m3s*1000:.2f} L/s",
            standards=["TCVN 7957:2008", "Darcy-Weisbach", "Colebrook-White"]
        )
        
        # Chuyển đổi đơn vị
        D = diameter_mm / 1000
        roughness = roughness_mm / 1000
        
        # Tính diện tích và vận tốc
        A = math.pi * D ** 2 / 4
        V = flow_rate_m3s / A
        
        # Bước 1: Tính vận tốc
        v_step = CalculationLogger.create_step(
            step_id="velocity",
            name="Tính vận tốc dòng chảy",
            description="Từ phương trình liên tục",
            formula_latex=r"V = \frac{Q}{A} = \frac{4Q}{\pi D^2}",
            formula_text="V = Q/A = 4Q/(πD²)",
            reference="Phương trình liên tục",
            inputs={"Q": flow_rate_m3s, "D": D, "A": A},
            result=V,
            result_unit="m/s"
        )
        log.add_step(v_step)
        
        # Bước 2: Tính số Reynolds
        kinematic_viscosity = EngineeringConstants.get_water_viscosity(temperature)
        Re, regime, re_step = cls.calculate_reynolds_number(V, D, temperature, kinematic_viscosity)
        log.add_step(re_step)
        
        # Bước 3: Tính hệ số ma sát
        relative_roughness = roughness / D
        f, f_method, f_step = cls.calculate_friction_factor_colebrook(Re, relative_roughness)
        log.add_step(f_step)
        
        # Bước 4: Tổn thất ma sát
        h_f, hf_step = cls.calculate_darcy_weisbach_loss(length_m, D, V, f)
        log.add_step(hf_step)
        
        # Bước 5: Tổn thất cục bộ
        h_m = 0
        if fittings:
            h_m, hm_step = cls.calculate_minor_losses(V, fittings)
            log.add_step(hm_step)
        
        # Cột nước vận tốc
        h_v = V ** 2 / (2 * cls.GRAVITY)
        
        # Tổng tổn thất
        h_total = h_f + h_m
        
        # Kết quả cuối cùng
        log.final_results = {
            "velocity_m_s": round(V, 4),
            "reynolds_number": round(Re, 0),
            "flow_regime": regime,
            "friction_factor": round(f, 6),
            "friction_loss_m": round(h_f, 4),
            "minor_loss_m": round(h_m, 4),
            "total_head_loss_m": round(h_total, 4),
            "velocity_head_m": round(h_v, 4),
            "head_loss_per_100m": round(h_f / length_m * 100, 4) if length_m > 0 else 0
        }
        
        log.calculation_time_ms = (time.time() - start_time) * 1000
        
        return TraceableHeadLossResult(
            friction_loss=round(h_f, 4),
            minor_loss=round(h_m, 4),
            total_loss=round(h_total, 4),
            velocity_head=round(h_v, 4),
            friction_factor=round(f, 6),
            calculation_log=log
        )


# Backward compatibility - giữ lại class cũ nhưng wrapper
class HydraulicCalculatorV2(TraceableHydraulicEngine):
    """
    Alias for backward compatibility
    """
    pass
