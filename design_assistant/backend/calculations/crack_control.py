"""
Crack Width Control - Kiểm toán bề rộng vết nứt

Module kiểm tra bề rộng vết nứt theo TCVN 5574:2018
Đây là yêu cầu quan trọng cho bể chứa nước vì:
- Nứt ảnh hưởng độ bền và tuổi thọ công trình
- Nứt gây thấm, rò rỉ
- Với bể chứa nước, kiểm toán nứt thường quyết định lượng thép

Tham chiếu:
- TCVN 5574:2018 - Mục 8.2: Tính toán theo điều kiện hình thành vết nứt
- TCVN 5574:2018 - Mục 8.3: Tính toán theo điều kiện mở rộng vết nứt
- EN 1992-1-1: Eurocode 2 (tham khảo)
"""

from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import math


class ExposureClass(Enum):
    """Cấp độ môi trường theo TCVN 5574:2018"""
    XC1 = ("XC1", "Khô hoặc ẩm liên tục", 0.4)
    XC2 = ("XC2", "Ẩm, hiếm khi khô", 0.3)
    XC3 = ("XC3", "Ẩm vừa phải", 0.3)
    XC4 = ("XC4", "Chu kỳ ướt và khô", 0.2)
    XD1 = ("XD1", "Ẩm vừa phải có chloride", 0.3)
    XD2 = ("XD2", "Ướt, hiếm khi khô, có chloride", 0.2)
    XD3 = ("XD3", "Chu kỳ ướt khô có chloride", 0.2)
    XS1 = ("XS1", "Muối biển trong không khí", 0.3)
    XS2 = ("XS2", "Ngập nước biển", 0.2)
    XS3 = ("XS3", "Vùng thủy triều", 0.2)
    
    # Đặc biệt cho bể chứa nước
    WATER_RETAINING = ("WR", "Bể chứa nước - Chống thấm", 0.2)
    WATER_RETAINING_STRICT = ("WRS", "Bể chứa nước - Nghiêm ngặt", 0.1)
    
    def __init__(self, code: str, description: str, max_crack_width: float):
        self.code = code
        self.description = description
        self.acr_max = max_crack_width  # mm


@dataclass 
class CrackCheckResult:
    """Kết quả kiểm tra nứt"""
    # Thông số đầu vào
    moment: float           # kN.m
    As_provided: float      # mm²
    bar_diameter: float     # mm
    spacing: float          # mm
    cover: float            # mm
    
    # Kết quả tính toán
    acr_calculated: float   # Bề rộng vết nứt tính toán (mm)
    acr_limit: float        # Bề rộng vết nứt giới hạn (mm)
    
    # Ứng suất
    sigma_s: float          # Ứng suất trong thép (MPa)
    sigma_s_limit: float    # Ứng suất giới hạn thép (MPa)
    
    # Kết luận
    is_satisfied: bool
    status: str             # "PASS", "FAIL", "WARNING"
    message: str
    
    # Khuyến nghị nếu không đạt
    suggestions: List[str]


class CrackWidthChecker:
    """
    Kiểm tra bề rộng vết nứt theo TCVN 5574:2018
    
    Công thức cơ bản:
    acr = φ × (σs/Es) × ψs × ls × (3.5 - 100×μ)
    
    Trong đó:
    - φ: Hệ số xét ảnh hưởng của tải trọng dài hạn
    - σs: Ứng suất trong cốt thép chịu kéo
    - Es: Mô đun đàn hồi của thép (2×10^5 MPa)
    - ψs: Hệ số xét sự phân bố không đều biến dạng
    - ls: Khoảng cách cơ sở giữa các vết nứt
    - μ: Hàm lượng cốt thép
    """
    
    # Mô đun đàn hồi thép (MPa)
    ES = 200000
    
    # Hệ số φ cho tải trọng
    PHI_SHORT_TERM = 1.0        # Tải ngắn hạn
    PHI_LONG_TERM = 1.4         # Tải dài hạn (50% hoặc nhiều hơn)
    PHI_REPEATED = 1.2          # Tải lặp
    
    # Giới hạn bề rộng vết nứt theo môi trường (mm) - TCVN 5574:2018
    CRACK_WIDTH_LIMITS = {
        "mild": 0.4,            # Môi trường nhẹ (trong nhà)
        "moderate": 0.3,        # Môi trường vừa (ngoài trời có mái che)
        "severe": 0.2,          # Môi trường nặng (ngoài trời, ẩm ướt)
        "water_retaining": 0.2, # Bể chứa nước tiêu chuẩn
        "water_tight": 0.1,     # Bể chứa nước kín tuyệt đối
    }
    
    # Cường độ vật liệu (MPa)
    CONCRETE_STRENGTH = {
        "B15": {"fctm": 1.1, "Ecm": 23000},
        "B20": {"fctm": 1.35, "Ecm": 27000},
        "B25": {"fctm": 1.55, "Ecm": 30000},
        "B30": {"fctm": 1.75, "Ecm": 32500},
        "B35": {"fctm": 1.95, "Ecm": 34500},
        "B40": {"fctm": 2.10, "Ecm": 36000},
    }
    
    STEEL_STRENGTH = {
        "CB240-T": {"fy": 240, "fyk": 240},
        "CB300-V": {"fy": 300, "fyk": 300},
        "CB400-V": {"fy": 400, "fyk": 400},
        "CB500-V": {"fy": 500, "fyk": 500},
    }
    
    @classmethod
    def check_crack_width(
        cls,
        moment: float,              # kN.m - Moment tác dụng
        width: float,               # mm - Chiều rộng tiết diện (1000 cho 1m dài)
        height: float,              # mm - Chiều cao tiết diện
        As: float,                  # mm² - Diện tích cốt thép chịu kéo
        cover: float,               # mm - Lớp bảo vệ
        bar_diameter: float,        # mm - Đường kính thanh thép
        spacing: Optional[float] = None,      # mm - Khoảng cách thép
        concrete_grade: str = "B25",
        steel_grade: str = "CB400-V",
        environment: str = "water_retaining",  # Môi trường
        load_type: str = "long_term"  # "short_term", "long_term", "repeated"
    ) -> CrackCheckResult:
        """
        Kiểm tra bề rộng vết nứt theo TCVN 5574:2018
        
        Args:
            moment: Moment uốn (kN.m) cho 1m chiều dài
            width: Chiều rộng tiết diện (mm), thường = 1000mm
            height: Chiều cao tiết diện (mm)
            As: Diện tích cốt thép chịu kéo (mm²)
            cover: Lớp bê tông bảo vệ (mm)
            bar_diameter: Đường kính thanh thép (mm)
            spacing: Khoảng cách thanh thép (mm)
            concrete_grade: Mác bê tông
            steel_grade: Mác thép
            environment: Điều kiện môi trường
            load_type: Loại tải trọng
            
        Returns:
            CrackCheckResult: Kết quả kiểm tra
        """
        # Lấy thông số vật liệu
        concrete = cls.CONCRETE_STRENGTH.get(concrete_grade, cls.CONCRETE_STRENGTH["B25"])
        steel = cls.STEEL_STRENGTH.get(steel_grade, cls.STEEL_STRENGTH["CB400-V"])
        
        fctm = concrete["fctm"]  # Cường độ chịu kéo trung bình của bê tông
        Ecm = concrete["Ecm"]    # Mô đun đàn hồi bê tông
        fy = steel["fy"]         # Giới hạn chảy của thép
        
        # Chiều cao hữu ích
        d = height - cover - bar_diameter / 2  # mm
        
        # Tính ứng suất trong cốt thép
        # Đổi đơn vị moment: kN.m -> N.mm
        M = moment * 1e6  # N.mm
        
        # Tính cánh tay đòn (giả định z = 0.9d)
        z = 0.9 * d
        
        # Ứng suất trong thép
        sigma_s = M / (As * z) if As > 0 else 0  # MPa
        
        # Giới hạn ứng suất thép (0.8fy cho trạng thái sử dụng)
        sigma_s_limit = 0.8 * fy
        
        # Hệ số tải trọng φ
        if load_type == "short_term":
            phi = cls.PHI_SHORT_TERM
        elif load_type == "repeated":
            phi = cls.PHI_REPEATED
        else:
            phi = cls.PHI_LONG_TERM
        
        # Hàm lượng cốt thép μ
        Ac_eff = cls._calculate_effective_concrete_area(width, height, d, As, cover)
        mu = As / Ac_eff if Ac_eff > 0 else 0.01
        mu = max(mu, 0.005)  # Tối thiểu 0.5%
        
        # Khoảng cách giữa các thanh thép
        if spacing is None:
            # Tính từ diện tích và đường kính
            As_bar = math.pi * bar_diameter**2 / 4
            n_bars = max(1, As / As_bar)
            spacing = (width - 2 * cover) / n_bars if n_bars > 1 else width
        
        # Khoảng cách cơ sở giữa các vết nứt ls (TCVN 5574)
        ls = cls._calculate_crack_spacing(bar_diameter, cover, spacing, mu)
        
        # Hệ số ψs (phân bố không đều biến dạng)
        psi_s = cls._calculate_psi_s(sigma_s, fctm, mu)
        
        # Bề rộng vết nứt tính toán (mm)
        # acr = φ × (σs/Es) × ψs × ls × δ
        delta = 1.0  # Hệ số hiệu chỉnh (có thể điều chỉnh)
        
        acr = phi * (sigma_s / cls.ES) * psi_s * ls * delta
        
        # Phương pháp thay thế theo EN 1992 (so sánh)
        acr_eurocode = cls._calculate_crack_width_eurocode(
            sigma_s, bar_diameter, cover, spacing, mu, fctm, Ecm
        )
        
        # Lấy giá trị lớn hơn để an toàn
        acr = max(acr, acr_eurocode)
        
        # Giới hạn bề rộng vết nứt
        acr_limit = cls.CRACK_WIDTH_LIMITS.get(environment, 0.3)
        
        # Đánh giá kết quả
        is_satisfied = acr <= acr_limit
        
        if acr <= acr_limit * 0.8:
            status = "PASS"
            message = f"Đạt yêu cầu: acr = {acr:.3f}mm ≤ [{acr_limit}]mm"
        elif acr <= acr_limit:
            status = "WARNING"
            message = f"Đạt nhưng gần giới hạn: acr = {acr:.3f}mm ≈ [{acr_limit}]mm"
        else:
            status = "FAIL"
            message = f"KHÔNG ĐẠT: acr = {acr:.3f}mm > [{acr_limit}]mm"
        
        # Tạo khuyến nghị nếu không đạt
        suggestions = []
        if not is_satisfied or status == "WARNING":
            suggestions = cls._generate_suggestions(
                acr, acr_limit, As, bar_diameter, spacing, sigma_s, sigma_s_limit
            )
        
        return CrackCheckResult(
            moment=moment,
            As_provided=As,
            bar_diameter=bar_diameter,
            spacing=spacing,
            cover=cover,
            acr_calculated=round(acr, 3),
            acr_limit=acr_limit,
            sigma_s=round(sigma_s, 1),
            sigma_s_limit=round(sigma_s_limit, 1),
            is_satisfied=is_satisfied,
            status=status,
            message=message,
            suggestions=suggestions
        )
    
    @classmethod
    def _calculate_effective_concrete_area(
        cls, 
        width: float, 
        height: float, 
        d: float, 
        As: float, 
        cover: float
    ) -> float:
        """
        Tính diện tích bê tông hữu hiệu quanh cốt thép chịu kéo
        
        Ac,eff = b × hc,ef
        hc,ef = min(2.5(h-d), (h-x)/3, h/2)
        """
        h = height
        x = 0.4 * d  # Giả định chiều cao vùng nén
        
        hc_ef = min(
            2.5 * cover,
            (h - x) / 3,
            h / 2
        )
        
        return width * hc_ef
    
    @classmethod
    def _calculate_crack_spacing(
        cls,
        bar_diameter: float,
        cover: float,
        spacing: float,
        mu: float
    ) -> float:
        """
        Tính khoảng cách cơ sở giữa các vết nứt ls (TCVN 5574)
        
        ls = 0.5 × (d + 40/μ)
        hoặc theo EN 1992: Sr,max = 3.4c + 0.425 × k1 × k2 × φ/ρp,eff
        """
        # Theo TCVN 5574:2018
        ls_tcvn = 0.5 * (bar_diameter + 40 / (mu * 100))
        
        # Giới hạn ls
        ls_min = 1.5 * bar_diameter
        ls_max = min(300, 1.5 * spacing)
        
        return max(ls_min, min(ls_tcvn, ls_max))
    
    @classmethod
    def _calculate_psi_s(cls, sigma_s: float, fctm: float, mu: float) -> float:
        """
        Tính hệ số ψs (phân bố không đều biến dạng)
        
        ψs = 1 - 0.8 × (fctm / σs) × (1 / μ^0.5)
        """
        if sigma_s <= 0:
            return 1.0
        
        psi_s = 1 - 0.8 * (fctm / sigma_s) * (1 / math.sqrt(mu * 100))
        
        # Giới hạn
        return max(0.2, min(psi_s, 1.0))
    
    @classmethod
    def _calculate_crack_width_eurocode(
        cls,
        sigma_s: float,
        bar_diameter: float,
        cover: float,
        spacing: float,
        mu: float,
        fctm: float,
        Ecm: float
    ) -> float:
        """
        Tính bề rộng vết nứt theo EN 1992-1-1
        
        wk = Sr,max × (εsm - εcm)
        """
        # Khoảng cách vết nứt max
        k1 = 0.8  # Thanh vằn
        k2 = 0.5  # Uốn
        rho_p_eff = mu
        
        if rho_p_eff < 0.01:
            rho_p_eff = 0.01
        
        Sr_max = 3.4 * cover + 0.425 * k1 * k2 * bar_diameter / rho_p_eff
        
        # Biến dạng
        kt = 0.4  # Tải dài hạn
        alpha_e = cls.ES / Ecm
        
        eps_sm_minus_eps_cm = (sigma_s - kt * fctm * (1 + alpha_e * rho_p_eff) / rho_p_eff) / cls.ES
        eps_sm_minus_eps_cm = max(eps_sm_minus_eps_cm, 0.6 * sigma_s / cls.ES)
        
        return Sr_max * eps_sm_minus_eps_cm / 1000  # mm
    
    @classmethod
    def _generate_suggestions(
        cls,
        acr: float,
        acr_limit: float,
        As: float,
        bar_diameter: float,
        spacing: float,
        sigma_s: float,
        sigma_s_limit: float
    ) -> List[str]:
        """Tạo danh sách khuyến nghị cải thiện"""
        suggestions = []
        
        ratio = acr / acr_limit
        
        if ratio > 1.5:
            suggestions.append("⚠️ Vượt giới hạn nhiều - Cần tăng đáng kể lượng thép")
        
        # Tăng thép
        As_required = As * ratio * 1.1  # Thêm 10% dự phòng
        As_increase = As_required - As
        suggestions.append(f"📌 Tăng thêm khoảng {As_increase:.0f} mm² cốt thép (tổng As ≥ {As_required:.0f} mm²)")
        
        # Giảm đường kính, tăng số lượng
        if bar_diameter >= 14:
            new_dia = bar_diameter - 2
            new_spacing = spacing * (new_dia / bar_diameter) ** 2
            suggestions.append(f"📌 Thay φ{bar_diameter:.0f} bằng φ{new_dia:.0f}a{new_spacing:.0f} (thanh nhỏ hơn, mau hơn)")
        
        # Giảm khoảng cách
        if spacing > 100:
            new_spacing = max(75, spacing * 0.7)
            suggestions.append(f"📌 Giảm khoảng cách thép từ {spacing:.0f}mm xuống {new_spacing:.0f}mm")
        
        # Ứng suất cao
        if sigma_s > sigma_s_limit:
            suggestions.append(f"📌 Ứng suất thép σs = {sigma_s:.0f} MPa vượt giới hạn {sigma_s_limit:.0f} MPa")
        
        return suggestions
    
    @classmethod
    def design_for_crack_control(
        cls,
        moment: float,
        width: float,
        height: float,
        cover: float,
        concrete_grade: str = "B25",
        steel_grade: str = "CB400-V",
        environment: str = "water_retaining",
        max_bar_diameter: int = 16
    ) -> Dict[str, Any]:
        """
        Thiết kế cốt thép dựa trên kiểm soát vết nứt
        
        Phương pháp: Lặp để tìm lượng thép thỏa mãn điều kiện nứt
        
        Args:
            moment: Moment uốn (kN.m)
            width: Chiều rộng tiết diện (mm)
            height: Chiều cao tiết diện (mm)
            cover: Lớp bảo vệ (mm)
            concrete_grade: Mác bê tông
            steel_grade: Mác thép
            environment: Môi trường
            max_bar_diameter: Đường kính thép tối đa (mm)
            
        Returns:
            Dict: Thông số cốt thép được thiết kế
        """
        acr_limit = cls.CRACK_WIDTH_LIMITS.get(environment, 0.3)
        
        # Các phương án đường kính
        diameters = [10, 12, 14, 16, 18, 20]
        diameters = [d for d in diameters if d <= max_bar_diameter]
        
        best_solution = None
        min_As = float('inf')
        
        for dia in diameters:
            # Khoảng cách thử nghiệm
            for spacing in [75, 100, 125, 150, 175, 200]:
                # Tính diện tích thép
                As_bar = math.pi * dia**2 / 4
                n_bars = (width - 2 * cover) / spacing + 1
                As = n_bars * As_bar
                
                # Kiểm tra nứt
                result = cls.check_crack_width(
                    moment=moment,
                    width=width,
                    height=height,
                    As=As,
                    cover=cover,
                    bar_diameter=dia,
                    spacing=spacing,
                    concrete_grade=concrete_grade,
                    steel_grade=steel_grade,
                    environment=environment
                )
                
                # Nếu đạt và As nhỏ hơn giải pháp hiện tại
                if result.is_satisfied and As < min_As:
                    min_As = As
                    best_solution = {
                        "bar_diameter": dia,
                        "spacing": spacing,
                        "As_provided": round(As, 0),
                        "notation": f"φ{dia}a{spacing}",
                        "crack_check": {
                            "acr": result.acr_calculated,
                            "acr_limit": result.acr_limit,
                            "sigma_s": result.sigma_s
                        }
                    }
        
        if best_solution is None:
            # Không tìm được giải pháp, đề xuất tăng chiều dày
            return {
                "status": "FAIL",
                "message": "Không tìm được giải pháp thỏa mãn kiểm toán nứt",
                "suggestion": "Cần tăng chiều dày tiết diện hoặc sử dụng thép cường độ cao hơn"
            }
        
        return {
            "status": "OK",
            **best_solution
        }


class CrackWidthCalculatorTCVN:
    """
    Tính toán chi tiết bề rộng vết nứt theo TCVN 5574:2018
    
    Trình bày đầy đủ các bước tính toán để sử dụng trong thuyết minh
    """
    
    @classmethod
    def detailed_calculation(
        cls,
        moment: float,              # kN.m
        section_width: float,       # mm
        section_height: float,      # mm
        As: float,                  # mm²
        As_compression: float,      # mm² (cốt thép nén, nếu có)
        cover: float,               # mm
        bar_diameter: float,        # mm
        bar_spacing: float,         # mm
        concrete_grade: str,
        steel_grade: str,
        load_duration: str = "long"  # "short", "long"
    ) -> Dict[str, Any]:
        """
        Tính toán chi tiết với trình bày công thức
        
        Returns:
            Dict: Các bước tính toán chi tiết
        """
        # Lấy thông số vật liệu
        concrete = CrackWidthChecker.CONCRETE_STRENGTH.get(
            concrete_grade, 
            CrackWidthChecker.CONCRETE_STRENGTH["B25"]
        )
        steel = CrackWidthChecker.STEEL_STRENGTH.get(
            steel_grade,
            CrackWidthChecker.STEEL_STRENGTH["CB400-V"]
        )
        
        fctm = concrete["fctm"]
        Ecm = concrete["Ecm"]
        Es = CrackWidthChecker.ES
        fy = steel["fy"]
        
        # Chiều cao hữu ích
        d = section_height - cover - bar_diameter / 2
        
        # Tỉ số mô đun
        alpha_e = Es / Ecm
        
        # Bước 1: Tính đặc trưng tiết diện đã nứt
        step1 = cls._step1_cracked_section(
            section_width, section_height, d, As, As_compression, cover, alpha_e
        )
        
        # Bước 2: Tính ứng suất trong cốt thép
        step2 = cls._step2_steel_stress(
            moment, As, step1["z"], step1["x"]
        )
        
        # Bước 3: Tính khoảng cách vết nứt
        step3 = cls._step3_crack_spacing(
            bar_diameter, bar_spacing, cover, step1["rho_eff"]
        )
        
        # Bước 4: Tính biến dạng
        step4 = cls._step4_strain_difference(
            step2["sigma_s"], fctm, step1["rho_eff"], alpha_e, load_duration
        )
        
        # Bước 5: Tính bề rộng vết nứt
        acr = step3["Sr_max"] * step4["eps_diff"] / 1000
        
        return {
            "input": {
                "moment": moment,
                "section": f"{section_width}×{section_height}",
                "As": As,
                "cover": cover,
                "bar": f"φ{bar_diameter}a{bar_spacing}",
                "concrete": concrete_grade,
                "steel": steel_grade
            },
            "step1_section": step1,
            "step2_stress": step2,
            "step3_spacing": step3,
            "step4_strain": step4,
            "result": {
                "acr": round(acr, 3),
                "unit": "mm",
                "formula": "acr = Sr,max × (εsm - εcm)"
            }
        }
    
    @staticmethod
    def _step1_cracked_section(
        b: float, h: float, d: float, As: float, As_comp: float, 
        cover: float, alpha_e: float
    ) -> Dict[str, Any]:
        """Bước 1: Tính đặc trưng tiết diện đã nứt"""
        # Chiều cao vùng nén (phương pháp đơn giản)
        # x = d × [-αe×ρ + sqrt((αe×ρ)² + 2×αe×ρ)]
        rho = As / (b * d)
        
        term = alpha_e * rho
        x = d * (-term + math.sqrt(term**2 + 2 * term))
        
        # Cánh tay đòn
        z = d - x / 3
        
        # Diện tích bê tông hữu hiệu
        hc_eff = min(2.5 * (h - d), (h - x) / 3, h / 2)
        Ac_eff = b * hc_eff
        
        # Hàm lượng thép hữu hiệu
        rho_eff = As / Ac_eff
        
        return {
            "x": round(x, 1),
            "z": round(z, 1),
            "hc_eff": round(hc_eff, 1),
            "Ac_eff": round(Ac_eff, 0),
            "rho_eff": round(rho_eff, 4),
            "formula": "x = d×[-αe×ρ + √((αe×ρ)² + 2×αe×ρ)]",
            "note": "Đặc trưng tiết diện đã nứt theo TCVN 5574:2018"
        }
    
    @staticmethod
    def _step2_steel_stress(
        moment: float, As: float, z: float, x: float
    ) -> Dict[str, Any]:
        """Bước 2: Tính ứng suất trong cốt thép"""
        M = moment * 1e6  # N.mm
        sigma_s = M / (As * z)
        
        return {
            "sigma_s": round(sigma_s, 1),
            "unit": "MPa",
            "formula": "σs = M / (As × z)",
            "calculation": f"σs = {moment}×10⁶ / ({As} × {z:.1f}) = {sigma_s:.1f} MPa"
        }
    
    @staticmethod
    def _step3_crack_spacing(
        dia: float, spacing: float, cover: float, rho_eff: float
    ) -> Dict[str, Any]:
        """Bước 3: Tính khoảng cách vết nứt"""
        k1 = 0.8   # Thanh vằn
        k2 = 0.5   # Uốn
        k3 = 3.4
        k4 = 0.425
        
        Sr_max = k3 * cover + k4 * k1 * k2 * dia / rho_eff
        Sr_max = min(Sr_max, 300)  # Giới hạn max
        
        return {
            "Sr_max": round(Sr_max, 1),
            "unit": "mm",
            "k1": k1,
            "k2": k2,
            "formula": "Sr,max = 3.4c + 0.425×k1×k2×φ/ρp,eff",
            "calculation": f"Sr,max = 3.4×{cover} + 0.425×{k1}×{k2}×{dia}/{rho_eff:.4f} = {Sr_max:.1f} mm"
        }
    
    @staticmethod
    def _step4_strain_difference(
        sigma_s: float, fctm: float, rho_eff: float, 
        alpha_e: float, load_duration: str
    ) -> Dict[str, Any]:
        """Bước 4: Tính hiệu biến dạng"""
        Es = CrackWidthChecker.ES
        kt = 0.4 if load_duration == "long" else 0.6
        
        # εsm - εcm
        term1 = sigma_s / Es
        term2 = kt * fctm * (1 + alpha_e * rho_eff) / (rho_eff * Es)
        
        eps_diff = term1 - term2
        eps_min = 0.6 * sigma_s / Es
        
        eps_diff = max(eps_diff, eps_min)
        
        return {
            "eps_sm_minus_eps_cm": round(eps_diff * 1000, 4),  # ×10⁻³
            "eps_min": round(eps_min * 1000, 4),
            "kt": kt,
            "formula": "εsm - εcm = σs/Es - kt×fctm×(1+αe×ρeff)/(ρeff×Es)",
            "note": f"Với tải {'dài hạn' if load_duration == 'long' else 'ngắn hạn'}, kt = {kt}"
        }
