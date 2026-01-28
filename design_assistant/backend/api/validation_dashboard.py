"""
Validation Dashboard API - Bảng kiểm tra thiết kế

Module hiển thị bảng so sánh kết quả tính toán với giá trị tiêu chuẩn.
Giúp kỹ sư nhanh chóng xác định các vấn đề cần giải quyết.

Tính năng:
- So sánh giá trị tính toán vs tiêu chuẩn
- Highlight các mục FAIL/WARNING
- Tổng hợp kết quả kiểm tra
- Đề xuất giải pháp
- Export dashboard ra PDF/Excel
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json


class CheckStatus(Enum):
    """Trạng thái kiểm tra"""
    PASS = ("PASS", "✓", "#4CAF50")         # Green
    WARNING = ("WARNING", "⚠", "#FF9800")    # Orange
    FAIL = ("FAIL", "✗", "#F44336")          # Red
    NOT_CHECKED = ("N/A", "-", "#9E9E9E")    # Gray
    
    def __init__(self, label: str, icon: str, color: str):
        self.label = label
        self.icon = icon
        self.color = color


@dataclass
class ValidationItem:
    """Một mục kiểm tra"""
    category: str           # Phân loại (Thủy lực, Kết cấu, ...)
    check_name: str         # Tên kiểm tra
    parameter: str          # Tên thông số
    calculated_value: float # Giá trị tính toán
    unit: str              # Đơn vị
    limit_min: Optional[float] = None   # Giới hạn dưới
    limit_max: Optional[float] = None   # Giới hạn trên
    standard_ref: str = ""  # Tham chiếu tiêu chuẩn
    status: CheckStatus = CheckStatus.NOT_CHECKED
    message: str = ""
    suggestion: str = ""
    
    def evaluate(self) -> 'ValidationItem':
        """Đánh giá trạng thái dựa trên giá trị và giới hạn"""
        val = self.calculated_value
        
        if self.limit_min is not None and self.limit_max is not None:
            if self.limit_min <= val <= self.limit_max:
                self.status = CheckStatus.PASS
                self.message = f"{val} nằm trong khoảng [{self.limit_min}, {self.limit_max}]"
            elif val < self.limit_min:
                self.status = CheckStatus.FAIL
                self.message = f"{val} < {self.limit_min} (giới hạn dưới)"
                self.suggestion = f"Cần tăng giá trị lên ≥ {self.limit_min}"
            else:
                self.status = CheckStatus.FAIL
                self.message = f"{val} > {self.limit_max} (giới hạn trên)"
                self.suggestion = f"Cần giảm giá trị xuống ≤ {self.limit_max}"
        elif self.limit_min is not None:
            if val >= self.limit_min:
                self.status = CheckStatus.PASS
                self.message = f"{val} ≥ {self.limit_min}"
            else:
                self.status = CheckStatus.FAIL
                self.message = f"{val} < {self.limit_min}"
                self.suggestion = f"Cần tăng giá trị lên ≥ {self.limit_min}"
        elif self.limit_max is not None:
            if val <= self.limit_max:
                self.status = CheckStatus.PASS
                self.message = f"{val} ≤ {self.limit_max}"
            else:
                self.status = CheckStatus.FAIL
                self.message = f"{val} > {self.limit_max}"
                self.suggestion = f"Cần giảm giá trị xuống ≤ {self.limit_max}"
        
        return self
    
    def to_dict(self) -> Dict:
        return {
            "category": self.category,
            "check_name": self.check_name,
            "parameter": self.parameter,
            "value": self.calculated_value,
            "unit": self.unit,
            "limit_min": self.limit_min,
            "limit_max": self.limit_max,
            "status": self.status.label,
            "status_icon": self.status.icon,
            "status_color": self.status.color,
            "message": self.message,
            "suggestion": self.suggestion,
            "standard": self.standard_ref
        }


@dataclass
class ValidationDashboard:
    """Dashboard tổng hợp kết quả kiểm tra"""
    project_name: str = ""
    element_name: str = ""
    items: List[ValidationItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def total_checks(self) -> int:
        return len(self.items)
    
    @property
    def passed_checks(self) -> int:
        return sum(1 for item in self.items if item.status == CheckStatus.PASS)
    
    @property
    def failed_checks(self) -> int:
        return sum(1 for item in self.items if item.status == CheckStatus.FAIL)
    
    @property
    def warning_checks(self) -> int:
        return sum(1 for item in self.items if item.status == CheckStatus.WARNING)
    
    @property
    def pass_rate(self) -> float:
        if self.total_checks == 0:
            return 100.0
        return self.passed_checks / self.total_checks * 100
    
    @property
    def overall_status(self) -> CheckStatus:
        if self.failed_checks > 0:
            return CheckStatus.FAIL
        elif self.warning_checks > 0:
            return CheckStatus.WARNING
        return CheckStatus.PASS
    
    def add_item(self, item: ValidationItem) -> None:
        item.evaluate()
        self.items.append(item)
    
    def get_items_by_category(self) -> Dict[str, List[ValidationItem]]:
        result = {}
        for item in self.items:
            if item.category not in result:
                result[item.category] = []
            result[item.category].append(item)
        return result
    
    def get_failed_items(self) -> List[ValidationItem]:
        return [item for item in self.items if item.status == CheckStatus.FAIL]
    
    def to_dict(self) -> Dict:
        return {
            "project_name": self.project_name,
            "element_name": self.element_name,
            "summary": {
                "total_checks": self.total_checks,
                "passed": self.passed_checks,
                "failed": self.failed_checks,
                "warnings": self.warning_checks,
                "pass_rate": round(self.pass_rate, 1),
                "overall_status": self.overall_status.label,
                "overall_color": self.overall_status.color
            },
            "items_by_category": {
                cat: [item.to_dict() for item in items]
                for cat, items in self.get_items_by_category().items()
            },
            "failed_items": [item.to_dict() for item in self.get_failed_items()],
            "created_at": self.created_at.isoformat()
        }
    
    def to_html_table(self) -> str:
        """Xuất dashboard ra HTML table"""
        html = f"""
        <div class="validation-dashboard">
            <h3>Kết quả kiểm tra: {self.element_name}</h3>
            <div class="summary">
                <span class="total">Tổng: {self.total_checks}</span>
                <span class="pass">Đạt: {self.passed_checks}</span>
                <span class="fail">Không đạt: {self.failed_checks}</span>
                <span class="warning">Cảnh báo: {self.warning_checks}</span>
                <span class="rate">Tỷ lệ: {self.pass_rate:.1f}%</span>
            </div>
            <table class="validation-table">
                <thead>
                    <tr>
                        <th>Phân loại</th>
                        <th>Kiểm tra</th>
                        <th>Thông số</th>
                        <th>Giá trị</th>
                        <th>Giới hạn</th>
                        <th>Trạng thái</th>
                        <th>Ghi chú</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in self.items:
            limit_str = ""
            if item.limit_min is not None and item.limit_max is not None:
                limit_str = f"[{item.limit_min}, {item.limit_max}]"
            elif item.limit_min is not None:
                limit_str = f"≥ {item.limit_min}"
            elif item.limit_max is not None:
                limit_str = f"≤ {item.limit_max}"
            
            html += f"""
                <tr class="status-{item.status.label.lower()}">
                    <td>{item.category}</td>
                    <td>{item.check_name}</td>
                    <td>{item.parameter}</td>
                    <td>{item.calculated_value} {item.unit}</td>
                    <td>{limit_str} {item.unit}</td>
                    <td style="background-color: {item.status.color}; color: white;">
                        {item.status.icon} {item.status.label}
                    </td>
                    <td>{item.message}</td>
                </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
        return html


class TankValidationBuilder:
    """
    Xây dựng dashboard kiểm tra cho thiết kế bể
    """
    
    # Giới hạn thủy lực theo TCVN
    HYDRAULIC_LIMITS = {
        "sedimentation": {
            "retention_time": (1.5, 4.0, "giờ", "TCVN 7957:2008"),
            "surface_loading": (None, 40, "m³/m²/ngày", "TCVN 7957:2008"),
            "weir_loading": (None, 250, "m³/m/ngày", "TCVN 7957:2008"),
            "horizontal_velocity": (None, 0.005, "m/s", "TCVN 7957:2008"),
            "length_width_ratio": (2, 5, "", "Khuyến nghị"),
            "length_depth_ratio": (8, 20, "", "Khuyến nghị"),
        },
        "storage": {
            "retention_time": (2, 24, "giờ", "TCVN 7957:2008"),
            "freeboard": (0.3, 0.5, "m", "TCVN 7957:2008"),
        },
        "aeration": {
            "retention_time": (4, 12, "giờ", "TCVN 7957:2008"),
            "organic_loading": (None, 0.5, "kg BOD/m³/ngày", "TCVN 7957:2008"),
        }
    }
    
    # Giới hạn kết cấu theo TCVN 5574
    STRUCTURAL_LIMITS = {
        "wall_thickness_ratio": (0.05, 0.15, "", "h/H"),
        "safety_factor_flotation": (1.2, None, "", "TCVN 5574:2018"),
        "safety_factor_bearing": (2.0, None, "", "TCVN 5574:2018"),
        "crack_width": (None, 0.2, "mm", "TCVN 5574:2018"),
        "deflection_ratio": (None, 0.004, "", "L/250"),
        "steel_ratio_min": (0.1, None, "%", "TCVN 5574:2018"),
        "steel_ratio_max": (None, 4.0, "%", "TCVN 5574:2018"),
    }
    
    @classmethod
    def create_tank_dashboard(
        cls,
        tank_type: str,
        design_params: Dict[str, Any],
        hydraulic_results: Dict[str, Any] = None,
        structural_results: Dict[str, Any] = None,
        crack_results: Dict[str, Any] = None
    ) -> ValidationDashboard:
        """
        Tạo dashboard kiểm tra cho thiết kế bể
        
        Args:
            tank_type: Loại bể
            design_params: Thông số thiết kế
            hydraulic_results: Kết quả tính thủy lực
            structural_results: Kết quả tính kết cấu
            crack_results: Kết quả kiểm toán nứt
            
        Returns:
            ValidationDashboard: Dashboard hoàn chỉnh
        """
        dashboard = ValidationDashboard(
            element_name=f"Bể {tank_type}",
            project_name=design_params.get("project_name", "")
        )
        
        # 1. Kiểm tra thủy lực
        if hydraulic_results:
            limits = cls.HYDRAULIC_LIMITS.get(tank_type, {})
            
            # Thời gian lưu
            if "retention_time" in hydraulic_results and "retention_time" in limits:
                lim = limits["retention_time"]
                dashboard.add_item(ValidationItem(
                    category="Thủy lực",
                    check_name="Thời gian lưu nước",
                    parameter="HRT",
                    calculated_value=hydraulic_results["retention_time"],
                    unit=lim[2],
                    limit_min=lim[0],
                    limit_max=lim[1],
                    standard_ref=lim[3]
                ))
            
            # Tải trọng bề mặt
            if "surface_loading" in hydraulic_results and "surface_loading" in limits:
                lim = limits["surface_loading"]
                dashboard.add_item(ValidationItem(
                    category="Thủy lực",
                    check_name="Tải trọng bề mặt",
                    parameter="SLR",
                    calculated_value=hydraulic_results["surface_loading"],
                    unit=lim[2],
                    limit_min=lim[0],
                    limit_max=lim[1],
                    standard_ref=lim[3]
                ))
            
            # Tải trọng máng tràn
            if "weir_loading" in hydraulic_results and "weir_loading" in limits:
                lim = limits["weir_loading"]
                dashboard.add_item(ValidationItem(
                    category="Thủy lực",
                    check_name="Tải trọng máng tràn",
                    parameter="WLR",
                    calculated_value=hydraulic_results["weir_loading"],
                    unit=lim[2],
                    limit_min=lim[0],
                    limit_max=lim[1],
                    standard_ref=lim[3]
                ))
            
            # Vận tốc ngang
            if "horizontal_velocity" in hydraulic_results and "horizontal_velocity" in limits:
                lim = limits["horizontal_velocity"]
                dashboard.add_item(ValidationItem(
                    category="Thủy lực",
                    check_name="Vận tốc ngang",
                    parameter="v_h",
                    calculated_value=hydraulic_results["horizontal_velocity"],
                    unit=lim[2],
                    limit_min=lim[0],
                    limit_max=lim[1],
                    standard_ref=lim[3]
                ))
        
        # 2. Kiểm tra hình học
        dims = design_params.get("dimensions", {})
        if dims:
            L = dims.get("length", 0)
            W = dims.get("width", 0)
            H = dims.get("water_depth", 0) or dims.get("depth", 0)
            t = dims.get("wall_thickness", 0)
            
            if L and W:
                dashboard.add_item(ValidationItem(
                    category="Hình học",
                    check_name="Tỷ lệ L/W",
                    parameter="L/W",
                    calculated_value=round(L/W, 2) if W > 0 else 0,
                    unit="",
                    limit_min=0.5,
                    limit_max=4.0,
                    standard_ref="Khuyến nghị"
                ))
            
            if L and H:
                dashboard.add_item(ValidationItem(
                    category="Hình học",
                    check_name="Tỷ lệ L/H",
                    parameter="L/H",
                    calculated_value=round(L/H, 2) if H > 0 else 0,
                    unit="",
                    limit_min=2,
                    limit_max=20,
                    standard_ref="Khuyến nghị"
                ))
            
            if t and H:
                dashboard.add_item(ValidationItem(
                    category="Kết cấu",
                    check_name="Chiều dày thành/Chiều cao",
                    parameter="t/H",
                    calculated_value=round(t/H, 3) if H > 0 else 0,
                    unit="",
                    limit_min=0.05,
                    limit_max=0.15,
                    standard_ref="TCVN 5574:2018"
                ))
        
        # 3. Kiểm tra kết cấu
        if structural_results:
            # Hệ số an toàn đẩy nổi
            if "flotation_sf" in structural_results:
                dashboard.add_item(ValidationItem(
                    category="Kết cấu",
                    check_name="Hệ số an toàn đẩy nổi",
                    parameter="SF_float",
                    calculated_value=structural_results["flotation_sf"],
                    unit="",
                    limit_min=1.2,
                    standard_ref="TCVN 5574:2018"
                ))
            
            # Hệ số an toàn chịu tải đất nền
            if "bearing_sf" in structural_results:
                dashboard.add_item(ValidationItem(
                    category="Kết cấu",
                    check_name="Hệ số an toàn nền",
                    parameter="SF_bearing",
                    calculated_value=structural_results["bearing_sf"],
                    unit="",
                    limit_min=2.0,
                    standard_ref="TCVN 5574:2018"
                ))
            
            # Hàm lượng cốt thép
            if "steel_ratio" in structural_results:
                dashboard.add_item(ValidationItem(
                    category="Kết cấu",
                    check_name="Hàm lượng cốt thép",
                    parameter="μ",
                    calculated_value=structural_results["steel_ratio"],
                    unit="%",
                    limit_min=0.1,
                    limit_max=4.0,
                    standard_ref="TCVN 5574:2018"
                ))
        
        # 4. Kiểm tra nứt
        if crack_results:
            acr = crack_results.get("acr_calculated", 0)
            acr_limit = crack_results.get("acr_limit", 0.2)
            
            dashboard.add_item(ValidationItem(
                category="Kết cấu",
                check_name="Bề rộng vết nứt",
                parameter="acr",
                calculated_value=acr,
                unit="mm",
                limit_max=acr_limit,
                standard_ref="TCVN 5574:2018"
            ))
            
            sigma_s = crack_results.get("sigma_s", 0)
            sigma_limit = crack_results.get("sigma_s_limit", 320)
            
            if sigma_s:
                dashboard.add_item(ValidationItem(
                    category="Kết cấu",
                    check_name="Ứng suất cốt thép",
                    parameter="σs",
                    calculated_value=sigma_s,
                    unit="MPa",
                    limit_max=sigma_limit,
                    standard_ref="TCVN 5574:2018"
                ))
        
        return dashboard
    
    @classmethod
    def create_quick_check(
        cls,
        length: float,
        width: float,
        depth: float,
        wall_thickness: float,
        flow_rate: float = None,
        tank_type: str = "sedimentation"
    ) -> ValidationDashboard:
        """
        Kiểm tra nhanh chỉ từ thông số cơ bản
        """
        design_params = {
            "dimensions": {
                "length": length,
                "width": width,
                "water_depth": depth,
                "wall_thickness": wall_thickness
            }
        }
        
        hydraulic_results = None
        if flow_rate:
            volume = length * width * depth
            hydraulic_results = {
                "retention_time": volume / (flow_rate / 24),  # giờ
                "surface_loading": flow_rate / (length * width),
                "weir_loading": flow_rate / (2 * width),  # Giả định 2 máng
                "horizontal_velocity": (flow_rate / 86400) / (width * depth)
            }
        
        return cls.create_tank_dashboard(
            tank_type=tank_type,
            design_params=design_params,
            hydraulic_results=hydraulic_results
        )


class VersionComparer:
    """
    So sánh hai phương án thiết kế
    """
    
    @classmethod
    def compare_designs(
        cls,
        design_a: Dict[str, Any],
        design_b: Dict[str, Any],
        name_a: str = "Phương án A",
        name_b: str = "Phương án B"
    ) -> Dict[str, Any]:
        """
        So sánh hai phương án thiết kế
        
        Args:
            design_a, design_b: Kết quả thiết kế từ optimizer
            name_a, name_b: Tên phương án
            
        Returns:
            Dict: Bảng so sánh chi tiết
        """
        comparison = {
            "designs": {
                "A": {"name": name_a, **design_a},
                "B": {"name": name_b, **design_b}
            },
            "comparison_items": [],
            "winner": None,
            "recommendation": ""
        }
        
        # So sánh các thông số
        items = []
        
        # Kích thước
        dims_a = design_a.get("dimensions", {})
        dims_b = design_b.get("dimensions", {})
        
        for key, label in [
            ("length", "Chiều dài (m)"),
            ("width", "Chiều rộng (m)"),
            ("water_depth", "Chiều sâu (m)"),
            ("wall_thickness", "Dày thành (m)")
        ]:
            va = dims_a.get(key, 0)
            vb = dims_b.get(key, 0)
            diff = vb - va
            pct = (diff / va * 100) if va else 0
            
            items.append({
                "parameter": label,
                "value_a": va,
                "value_b": vb,
                "difference": round(diff, 2),
                "percent_change": round(pct, 1),
                "better": "A" if va < vb and key != "wall_thickness" else "B" if vb < va else "="
            })
        
        # Chi phí
        cost_a = design_a.get("cost", {}).get("total_cost_per_tank", 0)
        cost_b = design_b.get("cost", {}).get("total_cost_per_tank", 0)
        cost_diff = cost_b - cost_a
        cost_pct = (cost_diff / cost_a * 100) if cost_a else 0
        
        items.append({
            "parameter": "Chi phí (VND)",
            "value_a": cost_a,
            "value_b": cost_b,
            "difference": round(cost_diff, 0),
            "percent_change": round(cost_pct, 1),
            "better": "A" if cost_a < cost_b else "B" if cost_b < cost_a else "="
        })
        
        # Khối lượng vật tư
        qty_a = design_a.get("quantities", {})
        qty_b = design_b.get("quantities", {})
        
        for key, label in [
            ("concrete_per_tank", "Bê tông (m³)"),
            ("steel_per_tank", "Cốt thép (kg)"),
            ("formwork_per_tank", "Ván khuôn (m²)")
        ]:
            va = qty_a.get(key, 0)
            vb = qty_b.get(key, 0)
            diff = vb - va
            pct = (diff / va * 100) if va else 0
            
            items.append({
                "parameter": label,
                "value_a": va,
                "value_b": vb,
                "difference": round(diff, 2),
                "percent_change": round(pct, 1),
                "better": "A" if va < vb else "B" if vb < va else "="
            })
        
        comparison["comparison_items"] = items
        
        # Xác định phương án tốt hơn (dựa trên chi phí)
        if cost_a < cost_b:
            comparison["winner"] = "A"
            saving = cost_b - cost_a
            comparison["recommendation"] = f"{name_a} tiết kiệm {saving:,.0f} VND ({abs(cost_pct):.1f}%) so với {name_b}"
        elif cost_b < cost_a:
            comparison["winner"] = "B"
            saving = cost_a - cost_b
            comparison["recommendation"] = f"{name_b} tiết kiệm {saving:,.0f} VND ({abs(cost_pct):.1f}%) so với {name_a}"
        else:
            comparison["winner"] = "="
            comparison["recommendation"] = "Hai phương án có chi phí tương đương"
        
        return comparison
    
    @classmethod
    def format_comparison_table(cls, comparison: Dict) -> str:
        """Format bảng so sánh ra text"""
        lines = []
        lines.append("=" * 70)
        lines.append("SO SÁNH PHƯƠNG ÁN THIẾT KẾ")
        lines.append("=" * 70)
        lines.append("")
        
        # Header
        name_a = comparison["designs"]["A"]["name"]
        name_b = comparison["designs"]["B"]["name"]
        lines.append(f"{'Thông số':<25} {name_a:>15} {name_b:>15} {'Chênh lệch':>12}")
        lines.append("-" * 70)
        
        for item in comparison["comparison_items"]:
            better = "◀" if item["better"] == "A" else "▶" if item["better"] == "B" else ""
            lines.append(
                f"{item['parameter']:<25} {item['value_a']:>15,.1f} {item['value_b']:>15,.1f} "
                f"{item['percent_change']:>+10.1f}% {better}"
            )
        
        lines.append("-" * 70)
        lines.append("")
        lines.append(f"📌 KẾT LUẬN: {comparison['recommendation']}")
        lines.append("=" * 70)
        
        return "\n".join(lines)
