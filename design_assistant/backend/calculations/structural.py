"""
Structural Calculator - Tính toán kết cấu

Bao gồm:
- Áp lực thành bể
- Tính cốt thép
- Kiểm tra ổn định
"""

import math
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from rules.structural_rules import StructuralRules

@dataclass
class LoadCase:
    """Tổ hợp tải trọng"""
    name: str
    description: str
    water_full: bool        # Bể đầy nước
    soil_pressure: bool     # Có áp lực đất
    surcharge: float        # Hoạt tải mặt đất (kN/m²)
    factor: float           # Hệ số tổ hợp


class StructuralCalculator:
    """
    Tính toán kết cấu bể và công trình
    
    Hỗ trợ:
    - Tính áp lực nước, đất
    - Thiết kế thành bể
    - Thiết kế đáy bể
    - Kiểm tra ổn định đẩy nổi
    """
    
    # Tổ hợp tải trọng tiêu chuẩn
    LOAD_CASES = [
        LoadCase("LC1", "Bể đầy, không có áp lực đất", True, False, 0, 1.2),
        LoadCase("LC2", "Bể rỗng, có áp lực đất", False, True, 10, 1.2),
        LoadCase("LC3", "Bể đầy, có áp lực đất và hoạt tải", True, True, 20, 1.35)
    ]
    
    @classmethod
    def calculate_wall_design(
        cls,
        height: float,              # Chiều cao thành (m)
        width: float,               # Chiều rộng bể (m) - nhịp thành
        wall_thickness: float,      # Chiều dày thành giả định (m)
        concrete_grade: str = "B25",
        steel_grade: str = "CB300-V",
        cover: float = 40           # Lớp bê tông bảo vệ (mm)
    ) -> Dict[str, Any]:
        """
        Tính toán thiết kế thành bể
        
        Args:
            height: Chiều cao thành (m)
            width: Chiều rộng bể (m)
            wall_thickness: Chiều dày thành (m)
            concrete_grade: Mác bê tông
            steel_grade: Mác thép
            cover: Lớp bê tông bảo vệ (mm)
            
        Returns:
            Dict: Kết quả tính toán kết cấu
        """
        results = {
            "input": {
                "height": height,
                "width": width,
                "wall_thickness": wall_thickness,
                "concrete_grade": concrete_grade,
                "steel_grade": steel_grade
            },
            "load_cases": [],
            "design_results": {},
            "reinforcement": {}
        }
        
        # Tính cho từng tổ hợp tải trọng
        max_moment = 0
        governing_case = None
        
        for lc in cls.LOAD_CASES:
            # Tính áp lực
            pressure_result = StructuralRules.calculate_wall_pressure(
                depth=height,
                include_surcharge=lc.soil_pressure,
                surcharge=lc.surcharge
            )
            
            # Tính moment
            if lc.water_full:
                # Áp lực nước từ trong ra
                q_water = pressure_result["water_pressure_max"]  # kN/m² tại đáy
                M_water = q_water * height**2 / 30  # Moment gần đúng cho tường ngàm-tự do
            else:
                q_water = 0
                M_water = 0
            
            if lc.soil_pressure:
                # Áp lực đất từ ngoài vào
                q_soil = pressure_result.get("soil_pressure_max", 0)
                M_soil = q_soil * height**2 / 30
            else:
                q_soil = 0
                M_soil = 0
            
            # Moment tính toán (lấy max giữa trong và ngoài)
            M_design = max(M_water, M_soil) * lc.factor  # kN.m/m
            
            lc_result = {
                "case": lc.name,
                "description": lc.description,
                "water_pressure": round(q_water, 2),
                "soil_pressure": round(q_soil, 2),
                "moment_water": round(M_water, 2),
                "moment_soil": round(M_soil, 2),
                "design_moment": round(M_design, 2)
            }
            results["load_cases"].append(lc_result)
            
            if M_design > max_moment:
                max_moment = M_design
                governing_case = lc.name
        
        # Tính cốt thép cho moment lớn nhất
        effective_depth = wall_thickness - cover/1000 - 0.01  # m (giả định φ20)
        
        reinforcement = StructuralRules.calculate_required_reinforcement(
            moment=max_moment,
            width=1.0,  # Tính cho 1m chiều dài
            effective_depth=effective_depth,
            concrete_grade=concrete_grade,
            steel_grade=steel_grade
        )
        
        results["design_results"] = {
            "governing_case": governing_case,
            "max_moment": round(max_moment, 2),
            "effective_depth": round(effective_depth * 1000, 0),  # mm
        }
        
        results["reinforcement"] = {
            "vertical_main": reinforcement,
            "horizontal_distribution": {
                "description": "Cốt thép phân bố ngang",
                "As_required": round(reinforcement.get("As_required", 0) * 0.2, 0),  # 20% cốt chịu lực
                "recommendation": "φ10a200 (As = 393 mm²/m)"
            }
        }
        
        # Kiểm tra chiều dày thành
        wall_check = StructuralRules.validate_wall_thickness("tank", wall_thickness, height)
        results["validation"] = [wall_check.to_dict()]
        
        # Tính khối lượng vật liệu (cho 1m dài thành)
        concrete_per_m = wall_thickness * height * 1.0  # m³/m
        steel_per_m = (reinforcement.get("As_provided", 0) + 393) / 1e6 * height * 7850  # kg/m
        
        results["quantities"] = {
            "concrete_per_m": round(concrete_per_m, 3),
            "steel_per_m": round(steel_per_m, 2),
            "note": "Khối lượng cho 1m chiều dài thành"
        }
        
        return results
    
    @classmethod
    def calculate_bottom_slab(
        cls,
        length: float,          # Chiều dài đáy (m)
        width: float,           # Chiều rộng đáy (m)
        water_depth: float,     # Chiều sâu nước (m)
        slab_thickness: float = 0.3,  # Chiều dày đáy (m)
        soil_bearing: float = 150,    # Sức chịu tải đất nền (kN/m²)
        concrete_grade: str = "B25",
        steel_grade: str = "CB300-V"
    ) -> Dict[str, Any]:
        """
        Tính toán đáy bể
        
        Args:
            length: Chiều dài đáy (m)
            width: Chiều rộng đáy (m)
            water_depth: Chiều sâu nước (m)
            slab_thickness: Chiều dày đáy (m)
            soil_bearing: Sức chịu tải đất nền (kN/m²)
            
        Returns:
            Dict: Kết quả tính toán
        """
        # Tải trọng tác dụng
        gamma_water = 10  # kN/m³
        gamma_concrete = 25  # kN/m³
        
        # Trọng lượng nước
        water_load = gamma_water * water_depth  # kN/m²
        
        # Trọng lượng bản thân đáy
        self_weight = gamma_concrete * slab_thickness  # kN/m²
        
        # Tổng tải trọng
        total_load = water_load + self_weight  # kN/m²
        
        # Kiểm tra sức chịu tải đất nền
        safety_factor = soil_bearing / total_load
        bearing_ok = safety_factor >= 2.0
        
        # Tính moment cho bản kê 4 cạnh
        # Sử dụng bảng hệ số cho bản kê 4 cạnh
        ratio = length / width if length > width else width / length
        
        # Hệ số moment (đơn giản hóa)
        if ratio <= 1.5:
            alpha_x = 0.045
            alpha_y = 0.045
        else:
            alpha_x = 0.070
            alpha_y = 0.030
        
        q_design = total_load * 1.2  # Hệ số tải trọng
        L_short = min(length, width)
        
        Mx = alpha_x * q_design * L_short**2  # kN.m/m
        My = alpha_y * q_design * L_short**2
        
        # Tính cốt thép
        effective_depth = slab_thickness - 0.05  # m
        
        reinf_x = StructuralRules.calculate_required_reinforcement(
            moment=Mx,
            width=1.0,
            effective_depth=effective_depth,
            concrete_grade=concrete_grade,
            steel_grade=steel_grade
        )
        
        reinf_y = StructuralRules.calculate_required_reinforcement(
            moment=My,
            width=1.0,
            effective_depth=effective_depth - 0.012,  # Trừ lớp thép X
            concrete_grade=concrete_grade,
            steel_grade=steel_grade
        )
        
        return {
            "input": {
                "length": length,
                "width": width,
                "water_depth": water_depth,
                "slab_thickness": slab_thickness
            },
            "loads": {
                "water_load": round(water_load, 2),
                "self_weight": round(self_weight, 2),
                "total_load": round(total_load, 2),
                "design_load": round(q_design, 2)
            },
            "bearing_check": {
                "soil_bearing_capacity": soil_bearing,
                "applied_pressure": round(total_load, 2),
                "safety_factor": round(safety_factor, 2),
                "status": "ĐẠT" if bearing_ok else "KHÔNG ĐẠT"
            },
            "moments": {
                "Mx": round(Mx, 2),
                "My": round(My, 2)
            },
            "reinforcement": {
                "direction_x": reinf_x,
                "direction_y": reinf_y
            },
            "recommendation": {
                "bottom_main": f"Thép đáy: {reinf_x.get('reinforcement', 'φ12a150')} cả 2 phương",
                "top_negative": "Thép mũ tại gối: φ12a150"
            }
        }
    
    @classmethod
    def check_flotation(
        cls,
        length: float,          # m
        width: float,           # m
        total_depth: float,     # m
        wall_thickness: float,  # m
        bottom_thickness: float,# m
        groundwater_level: float,  # Cao độ mực nước ngầm (m)
        foundation_level: float    # Cao độ đáy bể (m)
    ) -> Dict[str, Any]:
        """
        Kiểm tra ổn định đẩy nổi khi bể rỗng
        
        Args:
            length, width, total_depth: Kích thước bể (m)
            wall_thickness, bottom_thickness: Chiều dày kết cấu (m)
            groundwater_level: Cao độ mực nước ngầm (m)
            foundation_level: Cao độ đáy bể (m)
            
        Returns:
            Dict: Kết quả kiểm tra
        """
        gamma_water = 10  # kN/m³
        gamma_concrete = 25  # kN/m³
        
        # Chiều cao nước ngầm tác dụng
        hw = groundwater_level - foundation_level
        if hw <= 0:
            return {
                "status": "OK",
                "message": "Mực nước ngầm dưới đáy bể, không cần kiểm tra đẩy nổi"
            }
        
        # Diện tích đáy ngoài
        outer_length = length + 2 * wall_thickness
        outer_width = width + 2 * wall_thickness
        base_area = outer_length * outer_width
        
        # Lực đẩy nổi
        buoyancy = gamma_water * hw * base_area  # kN
        
        # Trọng lượng bể rỗng
        # Thể tích bê tông
        V_walls = 2 * (length + width) * total_depth * wall_thickness
        V_bottom = outer_length * outer_width * bottom_thickness
        V_concrete = V_walls + V_bottom
        
        weight_structure = gamma_concrete * V_concrete  # kN
        
        # Hệ số an toàn chống đẩy nổi
        sf = weight_structure / buoyancy if buoyancy > 0 else float('inf')
        
        # Yêu cầu SF >= 1.2
        status = "ĐẠT" if sf >= 1.2 else "KHÔNG ĐẠT"
        
        result = {
            "input": {
                "groundwater_level": groundwater_level,
                "foundation_level": foundation_level,
                "hw": round(hw, 2)
            },
            "forces": {
                "buoyancy_force": round(buoyancy, 2),
                "structure_weight": round(weight_structure, 2)
            },
            "safety_factor": round(sf, 2),
            "required_sf": 1.2,
            "status": status
        }
        
        if sf < 1.2:
            # Tính trọng lượng cần thêm
            required_weight = 1.2 * buoyancy
            additional_weight = required_weight - weight_structure
            
            # Có thể thêm lớp đất đắp hoặc tăng chiều dày đáy
            additional_slab = additional_weight / (gamma_concrete * base_area)
            
            result["countermeasures"] = {
                "additional_weight_required": round(additional_weight, 2),
                "option_1": f"Tăng chiều dày đáy thêm {round(additional_slab * 1000, 0)} mm",
                "option_2": "Sử dụng neo chống đẩy nổi",
                "option_3": "Hạ mực nước ngầm trong quá trình thi công"
            }
        
        return result
    
    @classmethod
    def calculate_quantities(
        cls,
        length: float,
        width: float,
        total_depth: float,
        wall_thickness: float,
        bottom_thickness: float,
        concrete_grade: str = "B25"
    ) -> Dict[str, Any]:
        """
        Tính khối lượng vật liệu
        
        Returns:
            Dict: Khối lượng bê tông và thép
        """
        # Kích thước ngoài
        outer_length = length + 2 * wall_thickness
        outer_width = width + 2 * wall_thickness
        
        # Thể tích bê tông
        V_walls = 2 * (length + width + 2 * wall_thickness) * total_depth * wall_thickness
        V_bottom = outer_length * outer_width * bottom_thickness
        V_total = V_walls + V_bottom
        
        # Hao hụt 5%
        V_total *= 1.05
        
        # Khối lượng thép (ước tính 100 kg/m³)
        steel_weight = V_total * 100
        
        return {
            "concrete": {
                "walls": round(V_walls * 1.05, 2),
                "bottom": round(V_bottom * 1.05, 2),
                "total": round(V_total, 2),
                "grade": concrete_grade,
                "unit": "m³"
            },
            "reinforcement": {
                "estimated_weight": round(steel_weight, 0),
                "unit": "kg",
                "note": "Ước tính theo hàm lượng 100 kg/m³ bê tông"
            },
            "formwork": {
                "walls_inner": round(2 * (length + width) * total_depth, 2),
                "walls_outer": round(2 * (outer_length + outer_width) * total_depth, 2),
                "bottom": round(outer_length * outer_width, 2),
                "total": round(
                    2 * (length + width) * total_depth +
                    2 * (outer_length + outer_width) * total_depth +
                    outer_length * outer_width, 2
                ),
                "unit": "m²"
            }
        }
