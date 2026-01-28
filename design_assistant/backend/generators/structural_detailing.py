"""
Structural Detailing for CAD - Chi tiết cốt thép và kết cấu

SPRINT 3: PROFESSIONAL CAD
Vẽ chi tiết kết cấu BTCT theo tiêu chuẩn:
- Bố trí cốt thép chính
- Đai/Stirrups
- Chi tiết thép phân bố
- Mặt cắt thép
- Leader notes với ký hiệu cốt thép
- Section views

Tiêu chuẩn:
- TCVN 5574:2018 - Kết cấu bê tông cốt thép
- TCVN 4453:1995 - Bản vẽ xây dựng
- ACI 315 - Detailing of Concrete Reinforcement
"""

import ezdxf
from ezdxf.enums import TextEntityAlignment
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
import math


class RebarGrade(Enum):
    """Cấp độ bền cốt thép theo TCVN"""
    CB240_T = ("CB240-T", 240, "Thép trơn")
    CB300_V = ("CB300-V", 300, "Thép vằn")
    CB400_V = ("CB400-V", 400, "Thép vằn cường độ cao")
    CB500_V = ("CB500-V", 500, "Thép vằn cường độ rất cao")
    
    def __init__(self, code: str, fy: int, description: str):
        self.code = code
        self.fy = fy  # MPa
        self.description = description


class RebarDiameter(Enum):
    """Đường kính cốt thép tiêu chuẩn (mm)"""
    D6 = 6
    D8 = 8
    D10 = 10
    D12 = 12
    D14 = 14
    D16 = 16
    D18 = 18
    D20 = 20
    D22 = 22
    D25 = 25
    D28 = 28
    D32 = 32
    D36 = 36
    D40 = 40


@dataclass
class RebarSpec:
    """Thông số cốt thép"""
    position: str       # Vị trí (A, B, C...)
    diameter: int       # mm
    spacing: int        # mm (0 nếu là thanh đơn)
    count: int          # Số thanh (0 nếu là theo khoảng cách)
    length: float       # m
    grade: RebarGrade = RebarGrade.CB300_V
    shape: str = "STRAIGHT"  # STRAIGHT, BENT, STIRRUP, HOOK
    
    @property
    def notation(self) -> str:
        """Ký hiệu cốt thép theo TCVN"""
        if self.spacing > 0:
            return f"Ø{self.diameter}a{self.spacing}"
        elif self.count > 0:
            return f"{self.count}Ø{self.diameter}"
        else:
            return f"Ø{self.diameter}"
    
    @property
    def full_notation(self) -> str:
        """Ký hiệu đầy đủ với vị trí"""
        return f"{self.position}: {self.notation}"
    
    @property
    def area_per_unit(self) -> float:
        """Diện tích thép trên mét dài (mm²/m)"""
        if self.spacing > 0:
            area_single = math.pi * (self.diameter / 2) ** 2
            return area_single * 1000 / self.spacing
        return 0


class StructuralDetailer:
    """
    Hệ thống vẽ chi tiết kết cấu
    
    Features:
    - Vẽ cốt thép trong mặt cắt
    - Bố trí stirrup/đai
    - Leader với ký hiệu thép
    - Section marks
    - Chi tiết uốn thép
    """
    
    # Layer cho kết cấu
    REBAR_LAYER = "STR_REBAR"
    REBAR_SECTION_LAYER = "STR_REBAR_SECTION"
    STIRRUP_LAYER = "STR_REBAR"
    ANNOTATION_LAYER = "ANNO_LEADER"
    
    # Màu sắc
    REBAR_COLOR = 1  # Red
    STIRRUP_COLOR = 1  # Red
    CONCRETE_COLOR = 8  # Gray
    
    def __init__(self, doc, scale_factor: float = 0.01):
        """
        Args:
            doc: ezdxf document
            scale_factor: Hệ số tỷ lệ cho annotation (0.01 cho 1:100)
        """
        self.doc = doc
        self.msp = doc.modelspace()
        self.scale = scale_factor
        self._ensure_layers()
    
    def _ensure_layers(self):
        """Đảm bảo layer tồn tại"""
        layers = {
            "STR_REBAR": (1, 25),      # Red, 0.25mm
            "STR_REBAR_SECTION": (1, 35),
            "STR_STIRRUP": (1, 18),
            "STR_CONCRETE": (8, 35),
            "ANNO_LEADER": (7, 18),
            "ANNO_REBAR": (7, 18),
        }
        
        for name, (color, lineweight) in layers.items():
            if name not in self.doc.layers:
                self.doc.layers.add(name, color=color, lineweight=lineweight)
    
    # ==========================================
    # REBAR DRAWING
    # ==========================================
    
    def draw_rebar_line(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        diameter: int = 12,
        layer: str = None
    ):
        """
        Vẽ thanh thép (đường)
        
        Args:
            start, end: Điểm đầu và cuối
            diameter: Đường kính (mm)
        """
        if layer is None:
            layer = self.REBAR_LAYER
        
        # Lineweight tỉ lệ với đường kính
        lw = min(int(diameter * 2), 70)  # Max 0.7mm
        
        self.msp.add_line(
            start, end,
            dxfattribs={
                "layer": layer,
                "lineweight": lw
            }
        )
    
    def draw_rebar_section(
        self,
        center: Tuple[float, float],
        diameter: int = 12,
        filled: bool = True,
        layer: str = None
    ):
        """
        Vẽ mặt cắt cốt thép (hình tròn)
        
        Args:
            center: Tâm
            diameter: Đường kính (mm)
            filled: Tô đặc hay không
        """
        if layer is None:
            layer = self.REBAR_SECTION_LAYER
        
        # Chuyển mm sang model units (m)
        radius = diameter / 2000
        
        # Vòng tròn
        circle = self.msp.add_circle(center, radius, dxfattribs={"layer": layer})
        
        # Tô đặc
        if filled:
            hatch = self.msp.add_hatch(color=self.REBAR_COLOR, dxfattribs={"layer": layer})
            hatch.paths.add_polyline_path([
                (center[0] + radius * math.cos(a), center[1] + radius * math.sin(a))
                for a in [i * math.pi / 10 for i in range(21)]
            ], is_closed=True)
            hatch.set_solid_fill()
        
        return circle
    
    def draw_rebar_array(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        diameter: int,
        spacing: int = None,
        count: int = None,
        offset_direction: str = "up",
        layer: str = None
    ):
        """
        Vẽ dãy cốt thép
        
        Args:
            start, end: Điểm đầu và cuối của dãy
            diameter: Đường kính (mm)
            spacing: Khoảng cách (mm) - ưu tiên
            count: Số thanh - dùng nếu không có spacing
            offset_direction: Hướng offset khi vẽ mặt cắt
        """
        if layer is None:
            layer = self.REBAR_SECTION_LAYER
        
        # Tính vector
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            return
        
        # Tính số thanh và khoảng cách
        if spacing is not None and spacing > 0:
            spacing_m = spacing / 1000
            count = int(length / spacing_m) + 1
        elif count is not None and count > 1:
            spacing_m = length / (count - 1)
        else:
            count = 1
            spacing_m = 0
        
        # Unit vector
        ux, uy = dx / length, dy / length
        
        # Vẽ từng thanh
        for i in range(count):
            if count > 1:
                t = i / (count - 1)
            else:
                t = 0.5
            
            x = start[0] + dx * t
            y = start[1] + dy * t
            
            self.draw_rebar_section((x, y), diameter, True, layer)
        
        return count
    
    def draw_stirrup(
        self,
        center: Tuple[float, float],
        width: float,
        height: float,
        diameter: int = 8,
        cover: float = 0.025,
        hook_length: float = None,
        layer: str = None
    ):
        """
        Vẽ đai/stirrup
        
        Args:
            center: Tâm tiết diện
            width, height: Kích thước trong của đai (m)
            diameter: Đường kính đai (mm)
            cover: Lớp bê tông bảo vệ (m)
            hook_length: Chiều dài móc (m), None = tự động
        """
        if layer is None:
            layer = self.STIRRUP_LAYER
        
        if hook_length is None:
            hook_length = diameter * 6 / 1000  # 6d hook
        
        # Bán kính uốn
        bend_r = diameter * 2 / 1000  # 2d bend
        
        # Tọa độ góc
        x1 = center[0] - width/2
        x2 = center[0] + width/2
        y1 = center[1] - height/2
        y2 = center[1] + height/2
        
        # Đai hình chữ nhật với móc
        points = [
            # Bắt đầu từ góc dưới trái, đi ngược chiều kim đồng hồ
            (x1 + bend_r, y1),
            (x2 - bend_r, y1),
            (x2, y1 + bend_r),
            (x2, y2 - bend_r),
            (x2 - bend_r, y2),
            (x1 + bend_r, y2),
            (x1, y2 - bend_r),
            (x1, y1 + bend_r),
            (x1 + bend_r, y1),
            # Hook
            (x1 + bend_r + hook_length * 0.7, y1 + hook_length * 0.7)
        ]
        
        # Lineweight
        lw = min(int(diameter * 2), 35)
        
        self.msp.add_lwpolyline(
            points,
            dxfattribs={"layer": layer, "lineweight": lw}
        )
        
        # Góc uốn (arcs)
        for corner in [(x1 + bend_r, y1 + bend_r),
                      (x2 - bend_r, y1 + bend_r),
                      (x2 - bend_r, y2 - bend_r),
                      (x1 + bend_r, y2 - bend_r)]:
            # Có thể thêm arc tại góc nếu cần chi tiết hơn
            pass
    
    def draw_multiple_stirrups(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        width: float,
        height: float,
        diameter: int = 8,
        spacing: int = 200,
        cover: float = 0.025,
        show_section: bool = True
    ):
        """
        Vẽ nhiều đai theo chiều dài
        
        Args:
            start, end: Điểm đầu và cuối
            width, height: Kích thước đai
            diameter: Đường kính đai
            spacing: Khoảng cách đai (mm)
            show_section: Hiển thị như mặt cắt (vẽ chấm)
        """
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            return
        
        spacing_m = spacing / 1000
        count = int(length / spacing_m) + 1
        
        ux, uy = dx / length, dy / length
        
        if show_section:
            # Vẽ đường đứt chỉ vị trí đai
            for i in range(count):
                t = i * spacing_m / length if length > 0 else 0
                if t > 1:
                    break
                
                x = start[0] + dx * t
                y = start[1] + dy * t
                
                # Đường đứt ngang chỉ vị trí đai
                perp_x, perp_y = -uy * 0.02, ux * 0.02
                self.msp.add_line(
                    (x - perp_x, y - perp_y),
                    (x + perp_x, y + perp_y),
                    dxfattribs={"layer": self.STIRRUP_LAYER, "lineweight": 18}
                )
        else:
            # Vẽ từng đai
            for i in range(min(count, 5)):  # Giới hạn 5 đai cho rõ ràng
                t = i * spacing_m / length if length > 0 else 0
                if t > 1:
                    break
                
                x = start[0] + dx * t
                y = start[1] + dy * t
                
                self.draw_stirrup((x, y), width, height, diameter, cover)
    
    # ==========================================
    # REBAR ANNOTATIONS
    # ==========================================
    
    def add_rebar_leader(
        self,
        rebar_position: Tuple[float, float],
        leader_end: Tuple[float, float],
        spec: RebarSpec,
        bend_point: Tuple[float, float] = None
    ):
        """
        Thêm leader với ký hiệu cốt thép
        
        Args:
            rebar_position: Vị trí thanh thép
            leader_end: Điểm cuối leader
            spec: Thông số cốt thép
            bend_point: Điểm gấp leader (optional)
        """
        # Xây dựng đường leader
        if bend_point:
            points = [rebar_position, bend_point, leader_end]
        else:
            points = [rebar_position, leader_end]
        
        # Vẽ đường leader
        self.msp.add_lwpolyline(
            points,
            dxfattribs={"layer": self.ANNOTATION_LAYER}
        )
        
        # Vẽ mũi tên
        self._draw_arrow(rebar_position, points[1])
        
        # Text notation
        text_height = 2.5 * self.scale
        notation = spec.full_notation
        
        # Xác định alignment
        if leader_end[0] > rebar_position[0]:
            align = TextEntityAlignment.LEFT
            text_pos = (leader_end[0] + 0.5 * self.scale, leader_end[1])
        else:
            align = TextEntityAlignment.RIGHT
            text_pos = (leader_end[0] - 0.5 * self.scale, leader_end[1])
        
        self.msp.add_text(
            notation,
            dxfattribs={
                "layer": "ANNO_REBAR",
                "height": text_height,
                "style": "STANDARD_VN"
            }
        ).set_placement(text_pos, align=align)
        
        # Thêm đường gạch dưới
        text_width = len(notation) * text_height * 0.6
        if align == TextEntityAlignment.LEFT:
            self.msp.add_line(
                leader_end,
                (leader_end[0] + text_width, leader_end[1]),
                dxfattribs={"layer": self.ANNOTATION_LAYER}
            )
        else:
            self.msp.add_line(
                (leader_end[0] - text_width, leader_end[1]),
                leader_end,
                dxfattribs={"layer": self.ANNOTATION_LAYER}
            )
    
    def _draw_arrow(
        self,
        point: Tuple[float, float],
        direction_point: Tuple[float, float],
        size: float = None
    ):
        """Vẽ mũi tên"""
        if size is None:
            size = 2.5 * self.scale
        
        dx = direction_point[0] - point[0]
        dy = direction_point[1] - point[1]
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            return
        
        ux, uy = dx / length, dy / length
        px, py = -uy, ux
        
        arrow_points = [
            point,
            (point[0] + size * ux + size * 0.3 * px,
             point[1] + size * uy + size * 0.3 * py),
            (point[0] + size * ux - size * 0.3 * px,
             point[1] + size * uy - size * 0.3 * py),
            point
        ]
        
        hatch = self.msp.add_hatch(dxfattribs={"layer": self.ANNOTATION_LAYER})
        hatch.paths.add_polyline_path(arrow_points, is_closed=True)
        hatch.set_solid_fill()
    
    def add_rebar_schedule_note(
        self,
        position: Tuple[float, float],
        rebars: List[RebarSpec],
        title: str = "BẢNG THỐNG KÊ CỐT THÉP"
    ):
        """
        Thêm bảng thống kê cốt thép
        
        Args:
            position: Vị trí góc trên trái
            rebars: Danh sách cốt thép
            title: Tiêu đề bảng
        """
        row_height = 5 * self.scale
        col_widths = [
            3 * self.scale,   # Position
            8 * self.scale,   # Notation
            5 * self.scale,   # Count
            6 * self.scale,   # Length
            8 * self.scale    # Total
        ]
        total_width = sum(col_widths)
        
        x, y = position
        
        # Title
        self.msp.add_text(
            title,
            dxfattribs={
                "layer": "ANNO_TEXT",
                "height": 3 * self.scale,
                "style": "TITLE"
            }
        ).set_placement(
            (x + total_width / 2, y + row_height),
            align=TextEntityAlignment.BOTTOM_CENTER
        )
        
        # Header
        headers = ["STT", "KÝ HIỆU", "SỐ LƯỢNG", "CHIỀU DÀI", "TỔNG"]
        y_header = y
        
        # Draw header row
        self.msp.add_lwpolyline([
            (x, y_header), (x + total_width, y_header),
            (x + total_width, y_header - row_height), (x, y_header - row_height),
            (x, y_header)
        ], close=True, dxfattribs={"layer": "ANNO_DIM"})
        
        # Header text
        x_pos = x
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            self.msp.add_text(
                header,
                dxfattribs={
                    "layer": "ANNO_TEXT",
                    "height": 2 * self.scale
                }
            ).set_placement(
                (x_pos + width / 2, y_header - row_height / 2),
                align=TextEntityAlignment.MIDDLE_CENTER
            )
            
            # Vertical line
            if i < len(headers) - 1:
                self.msp.add_line(
                    (x_pos + width, y_header),
                    (x_pos + width, y_header - row_height * (len(rebars) + 1)),
                    dxfattribs={"layer": "ANNO_DIM"}
                )
            
            x_pos += width
        
        # Data rows
        for i, rebar in enumerate(rebars):
            y_row = y_header - (i + 1) * row_height
            
            # Row box
            self.msp.add_line(
                (x, y_row), (x + total_width, y_row),
                dxfattribs={"layer": "ANNO_DIM"}
            )
            
            # Data
            total_length = rebar.count * rebar.length if rebar.count > 0 else rebar.length
            data = [
                rebar.position,
                rebar.notation,
                str(rebar.count) if rebar.count > 0 else "-",
                f"{rebar.length:.2f}",
                f"{total_length:.2f}"
            ]
            
            x_pos = x
            for j, (value, width) in enumerate(zip(data, col_widths)):
                self.msp.add_text(
                    value,
                    dxfattribs={
                        "layer": "ANNO_TEXT",
                        "height": 2 * self.scale
                    }
                ).set_placement(
                    (x_pos + width / 2, y_row - row_height / 2),
                    align=TextEntityAlignment.MIDDLE_CENTER
                )
                x_pos += width
        
        # Bottom line
        y_bottom = y_header - (len(rebars) + 1) * row_height
        self.msp.add_line(
            (x, y_bottom), (x + total_width, y_bottom),
            dxfattribs={"layer": "ANNO_DIM"}
        )
    
    # ==========================================
    # SECTION VIEWS
    # ==========================================
    
    def draw_wall_section(
        self,
        origin: Tuple[float, float],
        thickness: float,
        height: float,
        main_rebar_dia: int = 12,
        main_rebar_spacing: int = 200,
        dist_rebar_dia: int = 10,
        dist_rebar_spacing: int = 250,
        cover: float = 0.03,
        show_rebars: bool = True,
        show_annotations: bool = True,
        scale: float = 1.0
    ):
        """
        Vẽ mặt cắt tường với cốt thép
        
        Args:
            origin: Gốc (góc dưới trái)
            thickness: Chiều dày tường (m)
            height: Chiều cao tường (m)
            main_rebar_dia: Đường kính thép chính (mm)
            main_rebar_spacing: Khoảng cách thép chính (mm)
            dist_rebar_dia: Đường kính thép phân bố (mm)
            dist_rebar_spacing: Khoảng cách thép phân bố (mm)
            cover: Lớp bảo vệ (m)
            show_rebars: Hiển thị cốt thép
            show_annotations: Hiển thị ghi chú
        """
        x, y = origin
        t = thickness
        h = height
        c = cover
        
        # Đường bao bê tông
        concrete_points = [
            (x, y), (x + t, y), (x + t, y + h), (x, y + h), (x, y)
        ]
        self.msp.add_lwpolyline(
            concrete_points,
            close=True,
            dxfattribs={"layer": "STR_WALL", "lineweight": 50}
        )
        
        # Hatch bê tông
        hatch = self.msp.add_hatch(color=252, dxfattribs={"layer": "HATCH_CONCRETE"})
        hatch.paths.add_polyline_path(concrete_points[:-1], is_closed=True)
        hatch.set_pattern_fill("AR-CONC", scale=0.01 * scale)
        
        if show_rebars:
            # Thép dọc hai bên
            # Bên trái
            x_left = x + c + main_rebar_dia / 2000
            self.draw_rebar_array(
                (x_left, y + c),
                (x_left, y + h - c),
                main_rebar_dia,
                spacing=main_rebar_spacing
            )
            
            # Bên phải
            x_right = x + t - c - main_rebar_dia / 2000
            self.draw_rebar_array(
                (x_right, y + c),
                (x_right, y + h - c),
                main_rebar_dia,
                spacing=main_rebar_spacing
            )
            
            # Thép phân bố ngang (vẽ như đường)
            y_pos = y + c + dist_rebar_dia / 2000
            spacing_m = dist_rebar_spacing / 1000
            count = int((h - 2 * c) / spacing_m)
            
            for i in range(count):
                yi = y_pos + i * spacing_m
                self.draw_rebar_line(
                    (x + c, yi),
                    (x + t - c, yi),
                    dist_rebar_dia
                )
        
        if show_annotations:
            # Ghi chú thép
            # Thép dọc
            main_spec = RebarSpec(
                position="1",
                diameter=main_rebar_dia,
                spacing=main_rebar_spacing,
                count=0,
                length=h - 2 * c
            )
            
            self.add_rebar_leader(
                (x_left, y + h / 2),
                (x - 0.3, y + h / 2),
                main_spec
            )
            
            # Thép phân bố
            dist_spec = RebarSpec(
                position="2",
                diameter=dist_rebar_dia,
                spacing=dist_rebar_spacing,
                count=0,
                length=t - 2 * c
            )
            
            self.add_rebar_leader(
                (x + t / 2, y + c + spacing_m),
                (x + t + 0.3, y + c + spacing_m + 0.2),
                dist_spec,
                bend_point=(x + t / 2 + 0.15, y + c + spacing_m + 0.2)
            )
    
    def draw_slab_section(
        self,
        origin: Tuple[float, float],
        length: float,
        thickness: float,
        top_rebar_dia: int = 10,
        top_rebar_spacing: int = 200,
        bottom_rebar_dia: int = 12,
        bottom_rebar_spacing: int = 150,
        cover: float = 0.025,
        show_annotations: bool = True
    ):
        """
        Vẽ mặt cắt bản/sàn với cốt thép
        
        Args:
            origin: Gốc
            length: Chiều dài hiển thị
            thickness: Chiều dày bản (m)
            top_rebar_dia: Đường kính thép trên
            top_rebar_spacing: Khoảng cách thép trên
            bottom_rebar_dia: Đường kính thép dưới
            bottom_rebar_spacing: Khoảng cách thép dưới
        """
        x, y = origin
        L = length
        t = thickness
        c = cover
        
        # Đường bao
        self.msp.add_lwpolyline([
            (x, y), (x + L, y), (x + L, y + t), (x, y + t), (x, y)
        ], close=True, dxfattribs={"layer": "STR_SLAB", "lineweight": 35})
        
        # Hatch
        hatch = self.msp.add_hatch(color=252, dxfattribs={"layer": "HATCH_CONCRETE"})
        hatch.paths.add_polyline_path([
            (x, y), (x + L, y), (x + L, y + t), (x, y + t)
        ], is_closed=True)
        hatch.set_pattern_fill("AR-CONC", scale=0.008)
        
        # Thép dưới
        y_bottom = y + c + bottom_rebar_dia / 2000
        self.draw_rebar_array(
            (x + c, y_bottom),
            (x + L - c, y_bottom),
            bottom_rebar_dia,
            spacing=bottom_rebar_spacing
        )
        
        # Thép trên
        y_top = y + t - c - top_rebar_dia / 2000
        self.draw_rebar_array(
            (x + c, y_top),
            (x + L - c, y_top),
            top_rebar_dia,
            spacing=top_rebar_spacing
        )
        
        if show_annotations:
            # Annotation
            bottom_spec = RebarSpec("1", bottom_rebar_dia, bottom_rebar_spacing, 0, L - 2*c)
            top_spec = RebarSpec("2", top_rebar_dia, top_rebar_spacing, 0, L - 2*c)
            
            self.add_rebar_leader(
                (x + L / 2, y_bottom),
                (x + L / 2, y - 0.15),
                bottom_spec,
                (x + L / 2, y - 0.05)
            )
            
            self.add_rebar_leader(
                (x + L / 2, y_top),
                (x + L / 2, y + t + 0.15),
                top_spec,
                (x + L / 2, y + t + 0.05)
            )


def create_structural_detailer(doc, scale: float = 0.01) -> StructuralDetailer:
    """Tạo instance StructuralDetailer"""
    return StructuralDetailer(doc, scale)
