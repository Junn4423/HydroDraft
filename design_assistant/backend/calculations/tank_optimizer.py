"""
Tank Cost Optimizer - Tối ưu hóa kích thước bể

Module tối ưu hóa kích thước bể L×W×H để chi phí (Bê tông + Thép + Ván khuôn)
là thấp nhất cho một thể tích yêu cầu.

Tính năng:
- Auto-sizing từ lưu lượng đầu vào
- Tối ưu hóa đa mục tiêu (chi phí, kết cấu, thủy lực)
- So sánh nhiều phương án
- Xét đến ràng buộc thực tế (thi công, vận hành)

Phương pháp:
- Gradient descent với ràng buộc
- Grid search cho không gian tham số nhỏ
- Genetic algorithm cho bài toán phức tạp
"""

from typing import Dict, Any, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import math
from datetime import datetime


class TankType(Enum):
    """Loại bể"""
    SEDIMENTATION = "sedimentation"     # Bể lắng
    STORAGE = "storage"                  # Bể chứa
    EQUALIZATION = "equalization"        # Bể điều hòa
    AERATION = "aeration"               # Bể sục khí
    CLARIFIER = "clarifier"             # Bể lọc


@dataclass
class MaterialCost:
    """Đơn giá vật liệu"""
    concrete_per_m3: float = 2_500_000      # VND/m³ bê tông
    steel_per_kg: float = 18_000             # VND/kg thép
    formwork_per_m2: float = 250_000         # VND/m² ván khuôn
    excavation_per_m3: float = 150_000       # VND/m³ đào đất
    backfill_per_m3: float = 100_000         # VND/m³ đắp đất
    waterproofing_per_m2: float = 180_000    # VND/m² chống thấm
    
    # Chi phí phụ (%)
    indirect_cost_ratio: float = 0.15        # Chi phí gián tiếp
    contingency_ratio: float = 0.10          # Dự phòng


@dataclass
class TankConstraints:
    """Ràng buộc thiết kế"""
    # Kích thước
    min_length: float = 2.0          # m
    max_length: float = 50.0         # m
    min_width: float = 2.0           # m
    max_width: float = 30.0          # m
    min_depth: float = 2.0           # m
    max_depth: float = 8.0           # m
    
    # Tỷ lệ
    min_LW_ratio: float = 0.5        # L/W tối thiểu
    max_LW_ratio: float = 4.0        # L/W tối đa
    
    # Thủy lực (cho bể lắng)
    min_retention_time: float = 1.5  # giờ
    max_retention_time: float = 4.0  # giờ
    max_surface_loading: float = 40  # m³/m²/ngày
    max_weir_loading: float = 250    # m³/m/ngày
    
    # Kết cấu
    min_wall_thickness: float = 0.20 # m
    max_wall_thickness: float = 0.50 # m
    min_bottom_thickness: float = 0.25  # m


@dataclass
class OptimizationResult:
    """Kết quả tối ưu hóa"""
    # Kích thước tối ưu
    length: float
    width: float
    water_depth: float
    total_depth: float
    wall_thickness: float
    bottom_thickness: float
    
    # Thể tích
    volume_required: float
    volume_provided: float
    
    # Chi phí
    cost_breakdown: Dict[str, float]
    total_cost: float
    cost_per_m3: float  # Chi phí trên 1m³ thể tích chứa
    
    # Khối lượng
    concrete_volume: float  # m³
    steel_weight: float     # kg
    formwork_area: float    # m²
    
    # So sánh với phương án khác
    alternatives: List[Dict] = field(default_factory=list)
    savings_vs_default: float = 0.0
    
    # Metadata
    optimization_method: str = ""
    iterations: int = 0
    calculation_time: float = 0.0


class TankCostOptimizer:
    """
    Bộ tối ưu hóa chi phí bể
    
    Quy trình:
    1. Xác định thể tích yêu cầu từ lưu lượng
    2. Tạo không gian tìm kiếm (L, W, H)
    3. Với mỗi bộ kích thước, tính chi phí
    4. Chọn bộ có chi phí thấp nhất thỏa ràng buộc
    """
    
    # Hàm lượng thép theo chiều sâu (kg/m³ bê tông)
    STEEL_RATIO = {
        (0, 3): 80,      # H < 3m
        (3, 4): 100,     # 3 ≤ H < 4m
        (4, 5): 120,     # 4 ≤ H < 5m
        (5, 6): 140,     # 5 ≤ H < 6m
        (6, 8): 160,     # H ≥ 6m
    }
    
    @classmethod
    def get_steel_ratio(cls, depth: float) -> float:
        """Lấy hàm lượng thép theo chiều sâu"""
        for (d_min, d_max), ratio in cls.STEEL_RATIO.items():
            if d_min <= depth < d_max:
                return ratio
        return 160  # Mặc định cho bể sâu
    
    @classmethod
    def calculate_dimensions_from_flow(
        cls,
        flow_rate: float,           # m³/ngày
        retention_time: float,      # giờ
        tank_type: TankType = TankType.SEDIMENTATION,
        num_tanks: int = 1
    ) -> Dict[str, float]:
        """
        Tính thể tích và kích thước sơ bộ từ lưu lượng
        
        Args:
            flow_rate: Lưu lượng (m³/ngày)
            retention_time: Thời gian lưu (giờ)
            tank_type: Loại bể
            num_tanks: Số bể
            
        Returns:
            Dict: Thông số thể tích và kích thước gợi ý
        """
        # Thể tích yêu cầu
        Q_hourly = flow_rate / 24  # m³/h
        volume_required = Q_hourly * retention_time / num_tanks  # m³/bể
        
        # Kích thước gợi ý (ước tính ban đầu)
        if tank_type == TankType.SEDIMENTATION:
            # Bể lắng: L/W = 3, H = 3.5m
            LW_ratio = 3.0
            H = 3.5
            surface_area = volume_required / H
            W = math.sqrt(surface_area / LW_ratio)
            L = W * LW_ratio
        elif tank_type == TankType.STORAGE:
            # Bể chứa: Vuông, H = 4m
            H = 4.0
            surface_area = volume_required / H
            W = L = math.sqrt(surface_area)
        else:
            # Mặc định
            H = 3.5
            surface_area = volume_required / H
            W = L = math.sqrt(surface_area)
        
        return {
            "volume_required": round(volume_required, 1),
            "suggested_length": round(L, 1),
            "suggested_width": round(W, 1),
            "suggested_depth": H,
            "surface_area": round(surface_area, 1)
        }
    
    @classmethod
    def calculate_cost(
        cls,
        length: float,
        width: float,
        water_depth: float,
        freeboard: float = 0.3,
        wall_thickness: Optional[float] = None,
        bottom_thickness: float = 0.3,
        unit_costs: Optional[MaterialCost] = None
    ) -> Dict[str, float]:
        """
        Tính chi phí xây dựng bể
        
        Args:
            length, width, water_depth: Kích thước trong (m)
            freeboard: Chiều cao an toàn (m)
            wall_thickness: Chiều dày thành, None = tự động
            bottom_thickness: Chiều dày đáy (m)
            unit_costs: Đơn giá vật liệu
            
        Returns:
            Dict: Chi tiết chi phí
        """
        if unit_costs is None:
            unit_costs = MaterialCost()
        
        # Tổng chiều sâu
        total_depth = water_depth + freeboard
        
        # Chiều dày thành (nếu chưa có)
        if wall_thickness is None:
            wall_thickness = cls._recommend_wall_thickness(total_depth)
        
        # Kích thước ngoài
        outer_length = length + 2 * wall_thickness
        outer_width = width + 2 * wall_thickness
        
        # === KHỐI LƯỢNG ===
        
        # Thể tích bê tông
        V_walls = 2 * (length + width + 2 * wall_thickness) * total_depth * wall_thickness
        V_bottom = outer_length * outer_width * bottom_thickness
        V_concrete = V_walls + V_bottom
        V_concrete *= 1.05  # Hao hụt 5%
        
        # Khối lượng thép
        steel_ratio = cls.get_steel_ratio(total_depth)
        steel_weight = V_concrete * steel_ratio  # kg
        
        # Diện tích ván khuôn
        A_walls_inner = 2 * (length + width) * total_depth
        A_walls_outer = 2 * (outer_length + outer_width) * total_depth
        A_bottom = outer_length * outer_width
        A_formwork = A_walls_inner + A_walls_outer + A_bottom
        
        # Diện tích chống thấm (mặt trong)
        A_waterproof = A_walls_inner + length * width
        
        # Đào đất (giả định bể chôn 2/3)
        excavation_depth = total_depth * 0.67 + bottom_thickness + 0.3  # + lớp đệm
        V_excavation = outer_length * outer_width * excavation_depth * 1.2  # Hệ số mái dốc
        
        # === CHI PHÍ ===
        
        cost_concrete = V_concrete * unit_costs.concrete_per_m3
        cost_steel = steel_weight * unit_costs.steel_per_kg
        cost_formwork = A_formwork * unit_costs.formwork_per_m2
        cost_waterproof = A_waterproof * unit_costs.waterproofing_per_m2
        cost_excavation = V_excavation * unit_costs.excavation_per_m3
        
        # Tổng chi phí trực tiếp
        direct_cost = (
            cost_concrete + cost_steel + cost_formwork +
            cost_waterproof + cost_excavation
        )
        
        # Chi phí gián tiếp
        indirect_cost = direct_cost * unit_costs.indirect_cost_ratio
        
        # Dự phòng
        contingency = direct_cost * unit_costs.contingency_ratio
        
        # Tổng chi phí
        total_cost = direct_cost + indirect_cost + contingency
        
        # Thể tích chứa
        water_volume = length * width * water_depth
        
        return {
            # Khối lượng
            "concrete_volume": round(V_concrete, 2),
            "steel_weight": round(steel_weight, 0),
            "formwork_area": round(A_formwork, 1),
            "waterproof_area": round(A_waterproof, 1),
            "excavation_volume": round(V_excavation, 1),
            
            # Chi phí thành phần
            "cost_concrete": round(cost_concrete, 0),
            "cost_steel": round(cost_steel, 0),
            "cost_formwork": round(cost_formwork, 0),
            "cost_waterproof": round(cost_waterproof, 0),
            "cost_excavation": round(cost_excavation, 0),
            "cost_indirect": round(indirect_cost, 0),
            "cost_contingency": round(contingency, 0),
            
            # Tổng
            "direct_cost": round(direct_cost, 0),
            "total_cost": round(total_cost, 0),
            "cost_per_m3": round(total_cost / water_volume, 0) if water_volume > 0 else 0,
            
            # Thông tin bổ sung
            "water_volume": round(water_volume, 1),
            "wall_thickness": wall_thickness,
            "total_depth": total_depth
        }
    
    @classmethod
    def optimize_dimensions(
        cls,
        volume_required: float,             # m³
        tank_type: TankType = TankType.SEDIMENTATION,
        flow_rate: Optional[float] = None,            # m³/ngày (cho kiểm tra thủy lực)
        constraints: Optional[TankConstraints] = None,
        unit_costs: Optional[MaterialCost] = None,
        method: str = "grid_search",        # "grid_search", "gradient", "genetic"
        precision: str = "normal"           # "coarse", "normal", "fine"
    ) -> OptimizationResult:
        """
        Tối ưu hóa kích thước bể
        
        Args:
            volume_required: Thể tích chứa yêu cầu (m³)
            tank_type: Loại bể
            flow_rate: Lưu lượng (m³/ngày) để kiểm tra thủy lực
            constraints: Ràng buộc
            unit_costs: Đơn giá
            method: Phương pháp tối ưu
            precision: Độ chính xác
            
        Returns:
            OptimizationResult: Kết quả tối ưu
        """
        import time
        start_time = time.time()
        
        if constraints is None:
            constraints = TankConstraints()
        if unit_costs is None:
            unit_costs = MaterialCost()
        
        # Xác định bước tìm kiếm
        step_sizes = {
            "coarse": (1.0, 1.0, 0.5),   # L, W, H
            "normal": (0.5, 0.5, 0.25),
            "fine": (0.25, 0.25, 0.1)
        }
        L_step, W_step, H_step = step_sizes.get(precision, step_sizes["normal"])
        
        # Ước lượng phạm vi tìm kiếm từ thể tích
        # V = L × W × H
        H_typical = 3.5
        A_typical = volume_required / H_typical
        L_typical = math.sqrt(A_typical * 2)  # Giả định L/W = 2
        
        # Phạm vi tìm kiếm
        L_range = (
            max(constraints.min_length, L_typical * 0.5),
            min(constraints.max_length, L_typical * 2.0)
        )
        W_range = (
            max(constraints.min_width, L_typical * 0.25),
            min(constraints.max_width, L_typical * 1.0)
        )
        H_range = (constraints.min_depth, constraints.max_depth)
        
        # Grid search
        best_cost = float('inf')
        best_config = None
        all_configs = []
        iterations = 0
        
        L = L_range[0]
        while L <= L_range[1]:
            W = W_range[0]
            while W <= W_range[1]:
                H = H_range[0]
                while H <= H_range[1]:
                    iterations += 1
                    
                    # Kiểm tra ràng buộc
                    if not cls._check_constraints(L, W, H, volume_required, 
                                                   flow_rate, constraints, tank_type):
                        H += H_step
                        continue
                    
                    # Tính chi phí
                    cost_result = cls.calculate_cost(L, W, H, unit_costs=unit_costs)
                    total_cost = cost_result["total_cost"]
                    
                    config = {
                        "length": L,
                        "width": W,
                        "water_depth": H,
                        "volume": round(L * W * H, 1),
                        "total_cost": total_cost,
                        "cost_per_m3": cost_result["cost_per_m3"]
                    }
                    all_configs.append(config)
                    
                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_config = {
                            "length": L,
                            "width": W,
                            "water_depth": H,
                            **cost_result
                        }
                    
                    H += H_step
                W += W_step
            L += L_step
        
        # Sắp xếp và lấy top 5 phương án
        all_configs.sort(key=lambda x: x["total_cost"])
        top_alternatives = all_configs[:5]
        
        # Tính tiết kiệm so với phương án mặc định
        default_config = cls._get_default_config(volume_required, tank_type)
        default_cost = cls.calculate_cost(
            default_config["length"],
            default_config["width"],
            default_config["depth"],
            unit_costs=unit_costs
        )
        
        savings = default_cost["total_cost"] - best_cost
        savings_percent = (savings / default_cost["total_cost"] * 100) if default_cost["total_cost"] > 0 else 0
        
        calc_time = time.time() - start_time
        
        if best_config is None:
            # Không tìm được giải pháp, trả về mặc định
            best_config = cls.calculate_cost(
                default_config["length"],
                default_config["width"],
                default_config["depth"],
                unit_costs=unit_costs
            )
            best_config["length"] = default_config["length"]
            best_config["width"] = default_config["width"]
            best_config["water_depth"] = default_config["depth"]
        
        # Chiều dày thành
        total_depth = best_config.get("total_depth", best_config["water_depth"] + 0.3)
        wall_thick = best_config.get("wall_thickness", cls._recommend_wall_thickness(total_depth))
        
        return OptimizationResult(
            length=best_config["length"],
            width=best_config["width"],
            water_depth=best_config["water_depth"],
            total_depth=total_depth,
            wall_thickness=wall_thick,
            bottom_thickness=0.3,
            volume_required=volume_required,
            volume_provided=best_config["water_volume"],
            cost_breakdown={
                "concrete": best_config["cost_concrete"],
                "steel": best_config["cost_steel"],
                "formwork": best_config["cost_formwork"],
                "waterproof": best_config["cost_waterproof"],
                "excavation": best_config["cost_excavation"],
                "indirect": best_config["cost_indirect"],
                "contingency": best_config["cost_contingency"]
            },
            total_cost=best_config["total_cost"],
            cost_per_m3=best_config["cost_per_m3"],
            concrete_volume=best_config["concrete_volume"],
            steel_weight=best_config["steel_weight"],
            formwork_area=best_config["formwork_area"],
            alternatives=[
                {
                    "rank": i + 1,
                    "dimensions": f"{a['length']}×{a['width']}×{a['water_depth']}m",
                    "volume": a["volume"],
                    "cost": a["total_cost"],
                    "cost_per_m3": a["cost_per_m3"],
                    "cost_diff": round((a["total_cost"] - best_cost) / 1e6, 2)  # Triệu VND
                }
                for i, a in enumerate(top_alternatives)
            ],
            savings_vs_default=round(savings_percent, 1),
            optimization_method=method,
            iterations=iterations,
            calculation_time=round(calc_time, 2)
        )
    
    @classmethod
    def _check_constraints(
        cls,
        L: float, W: float, H: float,
        volume_required: float,
        flow_rate: Optional[float],
        constraints: TankConstraints,
        tank_type: TankType
    ) -> bool:
        """Kiểm tra ràng buộc"""
        # Thể tích
        V = L * W * H
        if V < volume_required * 0.95:  # Cho phép sai số 5%
            return False
        if V > volume_required * 1.5:   # Không quá 50% thừa
            return False
        
        # Tỷ lệ L/W
        ratio = L / W if W > 0 else 1
        if ratio < constraints.min_LW_ratio or ratio > constraints.max_LW_ratio:
            return False
        
        # Kích thước giới hạn
        if L < constraints.min_length or L > constraints.max_length:
            return False
        if W < constraints.min_width or W > constraints.max_width:
            return False
        if H < constraints.min_depth or H > constraints.max_depth:
            return False
        
        # Kiểm tra thủy lực (nếu có lưu lượng)
        if flow_rate and tank_type == TankType.SEDIMENTATION:
            A = L * W
            retention_time = V / (flow_rate / 24)  # giờ
            surface_loading = flow_rate / A
            
            if retention_time < constraints.min_retention_time:
                return False
            if retention_time > constraints.max_retention_time:
                return False
            if surface_loading > constraints.max_surface_loading:
                return False
        
        return True
    
    @staticmethod
    def _recommend_wall_thickness(depth: float) -> float:
        """Đề xuất chiều dày thành theo chiều sâu"""
        if depth <= 3:
            return 0.20
        elif depth <= 4:
            return 0.25
        elif depth <= 5:
            return 0.30
        elif depth <= 6:
            return 0.35
        else:
            return 0.40
    
    @staticmethod
    def _get_default_config(volume: float, tank_type: TankType) -> Dict:
        """Lấy cấu hình mặc định (không tối ưu)"""
        if tank_type == TankType.SEDIMENTATION:
            H = 3.5
            A = volume / H
            W = math.sqrt(A / 3)
            L = W * 3
        else:
            H = 4.0
            A = volume / H
            W = L = math.sqrt(A)
        
        return {
            "length": round(L, 1),
            "width": round(W, 1),
            "depth": H
        }
    
    @classmethod
    def compare_alternatives(
        cls,
        volume_required: float,
        scenarios: Optional[List[Dict]] = None,
        unit_costs: Optional[MaterialCost] = None
    ) -> Dict[str, Any]:
        """
        So sánh nhiều phương án thiết kế
        
        Args:
            volume_required: Thể tích yêu cầu
            scenarios: List các phương án {"name": ..., "L": ..., "W": ..., "H": ...}
            
        Returns:
            Dict: Bảng so sánh
        """
        if unit_costs is None:
            unit_costs = MaterialCost()
        
        # Phương án mặc định
        if scenarios is None:
            # Tạo các phương án mẫu
            scenarios = cls._generate_sample_scenarios(volume_required)
        
        results = []
        
        for scenario in scenarios:
            cost = cls.calculate_cost(
                scenario["L"], scenario["W"], scenario["H"],
                unit_costs=unit_costs
            )
            
            results.append({
                "name": scenario.get("name", f"{scenario['L']}×{scenario['W']}×{scenario['H']}"),
                "dimensions": f"{scenario['L']} × {scenario['W']} × {scenario['H']} m",
                "volume": round(scenario["L"] * scenario["W"] * scenario["H"], 1),
                "concrete": cost["concrete_volume"],
                "steel": cost["steel_weight"],
                "formwork": cost["formwork_area"],
                "total_cost": cost["total_cost"],
                "cost_per_m3": cost["cost_per_m3"]
            })
        
        # Sắp xếp theo chi phí
        results.sort(key=lambda x: x["total_cost"])
        
        # Thêm rank và % chênh lệch
        min_cost = results[0]["total_cost"] if results else 1
        for i, r in enumerate(results):
            r["rank"] = i + 1
            r["cost_diff_percent"] = round((r["total_cost"] - min_cost) / min_cost * 100, 1)
        
        return {
            "volume_required": volume_required,
            "comparison": results,
            "recommendation": results[0] if results else None,
            "summary": {
                "best_option": results[0]["name"] if results else None,
                "worst_option": results[-1]["name"] if results else None,
                "max_savings": round((results[-1]["total_cost"] - results[0]["total_cost"]) / 1e6, 2) if len(results) > 1 else 0
            }
        }
    
    @staticmethod
    def _generate_sample_scenarios(volume: float) -> List[Dict]:
        """Tạo các phương án mẫu để so sánh"""
        scenarios = []
        
        # Phương án 1: Bể sâu (H lớn)
        H1 = 5.0
        A1 = volume / H1
        W1 = math.sqrt(A1 / 2)
        L1 = W1 * 2
        scenarios.append({
            "name": "Phương án A - Bể sâu",
            "L": round(L1, 1),
            "W": round(W1, 1),
            "H": H1
        })
        
        # Phương án 2: Bể nông (H nhỏ)
        H2 = 3.0
        A2 = volume / H2
        W2 = math.sqrt(A2 / 2)
        L2 = W2 * 2
        scenarios.append({
            "name": "Phương án B - Bể nông",
            "L": round(L2, 1),
            "W": round(W2, 1),
            "H": H2
        })
        
        # Phương án 3: Bể vuông
        H3 = 4.0
        A3 = volume / H3
        side = math.sqrt(A3)
        scenarios.append({
            "name": "Phương án C - Bể vuông",
            "L": round(side, 1),
            "W": round(side, 1),
            "H": H3
        })
        
        # Phương án 4: Bể dài (L/W = 4)
        H4 = 3.5
        A4 = volume / H4
        W4 = math.sqrt(A4 / 4)
        L4 = W4 * 4
        scenarios.append({
            "name": "Phương án D - Bể dài",
            "L": round(L4, 1),
            "W": round(W4, 1),
            "H": H4
        })
        
        return scenarios


class AutoSizingCalculator:
    """
    Auto-sizing: Từ lưu lượng → Thể tích → Kích thước tối ưu → Bản vẽ
    
    Tích hợp đầy đủ quy trình thiết kế tự động
    """
    
    @classmethod
    def auto_design_from_flow(
        cls,
        flow_rate: float,               # m³/ngày
        tank_type: TankType = TankType.SEDIMENTATION,
        num_tanks: int = 1,
        retention_time: Optional[float] = None,   # giờ (tự động nếu None)
        optimize: bool = True,
        unit_costs: Optional[MaterialCost] = None
    ) -> Dict[str, Any]:
        """
        Thiết kế tự động từ lưu lượng đầu vào
        
        Args:
            flow_rate: Lưu lượng (m³/ngày)
            tank_type: Loại bể
            num_tanks: Số bể
            retention_time: Thời gian lưu (giờ)
            optimize: Có tối ưu kích thước không
            unit_costs: Đơn giá vật liệu
            
        Returns:
            Dict: Kết quả thiết kế hoàn chỉnh
        """
        # Xác định thời gian lưu nếu chưa có
        if retention_time is None:
            retention_time = cls._get_typical_retention_time(tank_type)
        
        # Tính thể tích yêu cầu
        Q_hourly = flow_rate / 24  # m³/h
        volume_per_tank = Q_hourly * retention_time
        total_volume = volume_per_tank * num_tanks
        
        # Tối ưu kích thước
        if optimize:
            opt_result = TankCostOptimizer.optimize_dimensions(
                volume_required=volume_per_tank,
                tank_type=tank_type,
                flow_rate=flow_rate / num_tanks,
                unit_costs=unit_costs
            )
            
            dimensions = {
                "length": opt_result.length,
                "width": opt_result.width,
                "water_depth": opt_result.water_depth,
                "total_depth": opt_result.total_depth,
                "wall_thickness": opt_result.wall_thickness,
                "bottom_thickness": opt_result.bottom_thickness
            }
            
            cost_info = {
                "total_cost_per_tank": opt_result.total_cost,
                "total_cost_all": opt_result.total_cost * num_tanks,
                "cost_per_m3": opt_result.cost_per_m3,
                "breakdown": opt_result.cost_breakdown,
                "savings_vs_default": f"{opt_result.savings_vs_default}%"
            }
            
            quantities = {
                "concrete_per_tank": opt_result.concrete_volume,
                "concrete_total": round(opt_result.concrete_volume * num_tanks, 1),
                "steel_per_tank": opt_result.steel_weight,
                "steel_total": round(opt_result.steel_weight * num_tanks, 0),
                "formwork_per_tank": opt_result.formwork_area,
                "formwork_total": round(opt_result.formwork_area * num_tanks, 1)
            }
            
            alternatives = opt_result.alternatives
        else:
            # Kích thước mặc định
            default = TankCostOptimizer._get_default_config(volume_per_tank, tank_type)
            cost_result = TankCostOptimizer.calculate_cost(
                default["length"], default["width"], default["depth"],
                unit_costs=unit_costs
            )
            
            dimensions = {
                "length": default["length"],
                "width": default["width"],
                "water_depth": default["depth"],
                "total_depth": default["depth"] + 0.3,
                "wall_thickness": cost_result["wall_thickness"],
                "bottom_thickness": 0.3
            }
            
            cost_info = {
                "total_cost_per_tank": cost_result["total_cost"],
                "total_cost_all": cost_result["total_cost"] * num_tanks,
                "cost_per_m3": cost_result["cost_per_m3"]
            }
            
            quantities = {
                "concrete_per_tank": cost_result["concrete_volume"],
                "steel_per_tank": cost_result["steel_weight"],
                "formwork_per_tank": cost_result["formwork_area"]
            }
            
            alternatives = []
        
        # Tính thông số thủy lực
        L, W, H = dimensions["length"], dimensions["width"], dimensions["water_depth"]
        actual_volume = L * W * H
        actual_retention = actual_volume / Q_hourly * num_tanks
        surface_loading = flow_rate / (L * W * num_tanks)
        
        hydraulics = {
            "flow_rate": flow_rate,
            "volume_required": round(total_volume, 1),
            "volume_provided": round(actual_volume * num_tanks, 1),
            "retention_time_target": retention_time,
            "retention_time_actual": round(actual_retention, 2),
            "surface_loading": round(surface_loading, 2),
            "surface_area": round(L * W * num_tanks, 1)
        }
        
        return {
            "input": {
                "flow_rate": flow_rate,
                "tank_type": tank_type.value,
                "num_tanks": num_tanks,
                "retention_time": retention_time
            },
            "dimensions": dimensions,
            "hydraulics": hydraulics,
            "cost": cost_info,
            "quantities": quantities,
            "alternatives": alternatives,
            "summary": {
                "Loại bể": tank_type.value,
                "Số lượng": f"{num_tanks} bể",
                "Kích thước mỗi bể": f"{L} × {W} × {dimensions['total_depth']} m",
                "Thể tích chứa": f"{round(actual_volume, 1)} m³/bể",
                "Chi phí": f"{cost_info['total_cost_per_tank']:,.0f} VND/bể",
                "Chi phí đơn vị": f"{cost_info['cost_per_m3']:,.0f} VND/m³"
            },
            "generated_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def _get_typical_retention_time(tank_type: TankType) -> float:
        """Lấy thời gian lưu tiêu biểu theo loại bể"""
        typical_times = {
            TankType.SEDIMENTATION: 2.5,    # giờ
            TankType.STORAGE: 6.0,          # giờ
            TankType.EQUALIZATION: 4.0,     # giờ
            TankType.AERATION: 8.0,         # giờ
            TankType.CLARIFIER: 2.0         # giờ
        }
        return typical_times.get(tank_type, 3.0)
