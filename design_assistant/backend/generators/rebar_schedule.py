"""
Rebar Schedule Generator - Bảng thống kê cốt thép

Module tự động tạo bảng thống kê cốt thép (Rebar Schedule) 
và bảng khối lượng vật tư trên bản vẽ CAD.

Tính năng:
- Tính toán tổng khối lượng thép
- Tạo bảng thống kê theo tiêu chuẩn TCVN
- Vẽ bảng trực tiếp trên CAD (DXF)
- Xuất file Excel (optional)
- Chi tiết hình dạng uốn thép

Tiêu chuẩn:
- TCVN 4453:1995 - Bản vẽ xây dựng
- TCVN 5574:2018 - Kết cấu bê tông cốt thép
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import math


class RebarShape(Enum):
    """Hình dạng cốt thép tiêu chuẩn"""
    STRAIGHT = "A"          # Thanh thẳng
    BENT_90 = "B"          # Uốn 90°
    BENT_180 = "C"         # Uốn 180° (móc)
    U_SHAPE = "D"          # Hình chữ U
    L_SHAPE = "E"          # Hình chữ L
    Z_SHAPE = "F"          # Hình chữ Z
    STIRRUP = "G"          # Đai vuông
    STIRRUP_RECT = "H"     # Đai chữ nhật
    HOOK_BOTH = "J"        # Móc 2 đầu


@dataclass
class RebarShape3D:
    """Thông số hình dạng uốn 3D"""
    shape_code: RebarShape
    segments: List[Tuple[float, float]]  # [(length, angle), ...]
    hook_start: bool = False
    hook_end: bool = False
    bend_diameter_factor: float = 4.0  # d × factor
    
    def calculate_total_length(self, diameter: float) -> float:
        """Tính chiều dài khai triển"""
        total = sum(seg[0] for seg in self.segments)
        
        # Cộng thêm chiều dài uốn
        num_bends = len(self.segments) - 1
        bend_length = num_bends * math.pi * self.bend_diameter_factor * diameter / 2 / 1000
        
        # Móc
        if self.hook_start:
            total += 6.25 * diameter / 1000  # 6.25d cho móc tiêu chuẩn
        if self.hook_end:
            total += 6.25 * diameter / 1000
        
        return total + bend_length


@dataclass
class RebarItem:
    """Một loại cốt thép trong bảng thống kê"""
    mark: str               # Ký hiệu (1, 2, 3, ... hoặc A, B, C, ...)
    diameter: int           # Đường kính (mm)
    shape: RebarShape       # Hình dạng
    length: float           # Chiều dài (m)
    quantity: int           # Số lượng thanh
    spacing: int = 0        # Khoảng cách nếu là thép phân bố (mm)
    location: str = ""      # Vị trí (Thành, Đáy, ...)
    grade: str = "CB400-V"  # Mác thép
    
    # Kích thước uốn (nếu có)
    dimensions: Dict[str, float] = field(default_factory=dict)
    
    @property
    def area_per_bar(self) -> float:
        """Diện tích 1 thanh (mm²)"""
        return math.pi * self.diameter ** 2 / 4
    
    @property
    def total_area(self) -> float:
        """Tổng diện tích (mm²)"""
        return self.area_per_bar * self.quantity
    
    @property
    def weight_per_meter(self) -> float:
        """Trọng lượng 1m (kg/m)"""
        return self.area_per_bar * 7.85 / 1000  # 7850 kg/m³
    
    @property
    def total_weight(self) -> float:
        """Tổng trọng lượng (kg)"""
        return self.weight_per_meter * self.length * self.quantity
    
    @property
    def total_length(self) -> float:
        """Tổng chiều dài (m)"""
        return self.length * self.quantity
    
    @property
    def notation(self) -> str:
        """Ký hiệu đầy đủ"""
        if self.spacing > 0:
            return f"φ{self.diameter}a{self.spacing}"
        return f"{self.quantity}φ{self.diameter}"


@dataclass
class RebarSchedule:
    """Bảng thống kê cốt thép hoàn chỉnh"""
    element_name: str       # Tên cấu kiện (Bể lắng, Thành bể, ...)
    items: List[RebarItem] = field(default_factory=list)
    
    # Metadata
    drawing_no: str = ""
    project: str = ""
    date: str = ""
    scale: str = "1:100"
    
    @property
    def total_weight(self) -> float:
        """Tổng khối lượng thép (kg)"""
        return sum(item.total_weight for item in self.items)
    
    @property
    def weight_by_diameter(self) -> Dict[int, float]:
        """Khối lượng theo đường kính"""
        result = {}
        for item in self.items:
            d = item.diameter
            if d not in result:
                result[d] = 0
            result[d] += item.total_weight
        return result
    
    @property
    def weight_by_location(self) -> Dict[str, float]:
        """Khối lượng theo vị trí"""
        result = {}
        for item in self.items:
            loc = item.location or "Chưa xác định"
            if loc not in result:
                result[loc] = 0
            result[loc] += item.total_weight
        return result
    
    def to_table_data(self) -> List[List[str]]:
        """Chuyển thành dữ liệu bảng để vẽ"""
        rows = []
        for item in self.items:
            rows.append([
                item.mark,
                str(item.diameter),
                item.shape.value,
                f"{item.length:.2f}",
                str(item.quantity),
                f"{item.total_length:.2f}",
                f"{item.total_weight:.1f}",
                item.location
            ])
        return rows


class RebarScheduleGenerator:
    """
    Tạo bảng thống kê cốt thép
    """
    
    # Đường kính tiêu chuẩn
    STANDARD_DIAMETERS = [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32]
    
    # Trọng lượng đơn vị (kg/m)
    UNIT_WEIGHT = {
        6: 0.222, 8: 0.395, 10: 0.617, 12: 0.888, 14: 1.21,
        16: 1.58, 18: 2.00, 20: 2.47, 22: 2.98, 25: 3.85,
        28: 4.83, 32: 6.31, 36: 7.99, 40: 9.87
    }
    
    @classmethod
    def generate_for_tank_wall(
        cls,
        height: float,          # m
        width: float,           # m (chu vi hoặc chiều dài thành)
        thickness: float,       # m
        cover: float = 0.04,    # m
        main_bar: int = 12,     # Đường kính thép chính (mm)
        main_spacing: int = 150,# Khoảng cách thép chính (mm)
        dist_bar: int = 10,     # Đường kính thép phân bố (mm)
        dist_spacing: int = 200,# Khoảng cách thép phân bố (mm)
        two_layer: bool = True, # Hai lớp thép
        lap_length_factor: float = 40  # Chiều dài nối (xd)
    ) -> RebarSchedule:
        """
        Tạo bảng thống kê cho thành bể
        
        Args:
            height: Chiều cao thành (m)
            width: Chiều dài thành (m) hoặc chu vi nếu là bể
            thickness: Chiều dày thành (m)
            cover: Lớp bê tông bảo vệ (m)
            main_bar: Đường kính thép chính
            main_spacing: Khoảng cách thép chính
            dist_bar: Đường kính thép phân bố
            dist_spacing: Khoảng cách thép phân bố
            two_layer: Bố trí 2 lớp
            lap_length_factor: Hệ số chiều dài nối thép
        
        Returns:
            RebarSchedule: Bảng thống kê
        """
        items = []
        layers = 2 if two_layer else 1
        
        # Chiều dài neo vào đáy và mũ
        anchor_length = lap_length_factor * main_bar / 1000  # m
        
        # 1. Thép đứng chính (theo chiều cao)
        vertical_length = height + 2 * anchor_length
        vertical_count = int(width / (main_spacing / 1000)) + 1
        vertical_count *= layers  # Nhân 2 nếu 2 lớp
        
        items.append(RebarItem(
            mark="1",
            diameter=main_bar,
            shape=RebarShape.STRAIGHT,
            length=round(vertical_length, 2),
            quantity=vertical_count,
            spacing=main_spacing,
            location="Thành bể - Thép đứng",
            grade="CB400-V"
        ))
        
        # 2. Thép ngang phân bố
        horizontal_length = width + 2 * anchor_length
        horizontal_count = int(height / (dist_spacing / 1000)) + 1
        horizontal_count *= layers
        
        items.append(RebarItem(
            mark="2",
            diameter=dist_bar,
            shape=RebarShape.STRAIGHT,
            length=round(horizontal_length, 2),
            quantity=horizontal_count,
            spacing=dist_spacing,
            location="Thành bể - Thép ngang",
            grade="CB400-V"
        ))
        
        # 3. Thép góc (nếu là bể chữ nhật) - giả định 4 góc
        corner_length = 0.8  # m mỗi cạnh
        corner_total = corner_length * 2  # Hình L
        corner_count = int(height / (main_spacing / 1000)) + 1
        corner_count *= 4  # 4 góc
        
        items.append(RebarItem(
            mark="3",
            diameter=main_bar,
            shape=RebarShape.L_SHAPE,
            length=round(corner_total, 2),
            quantity=corner_count,
            location="Thành bể - Thép góc",
            grade="CB400-V",
            dimensions={"a": 0.8, "b": 0.8}
        ))
        
        return RebarSchedule(
            element_name="Thành bể",
            items=items
        )
    
    @classmethod
    def generate_for_tank_slab(
        cls,
        length: float,          # m
        width: float,           # m
        thickness: float,       # m
        cover: float = 0.05,    # m
        bottom_bar: int = 12,   # Đường kính thép dưới
        bottom_spacing: int = 150,
        top_bar: int = 10,      # Đường kính thép trên
        top_spacing: int = 200,
        has_top_layer: bool = True
    ) -> RebarSchedule:
        """Tạo bảng thống kê cho đáy bể"""
        items = []
        
        # 1. Thép dưới phương X
        length_x = length + 0.8  # + neo 2 đầu
        count_x = int(width / (bottom_spacing / 1000)) + 1
        
        items.append(RebarItem(
            mark="4",
            diameter=bottom_bar,
            shape=RebarShape.STRAIGHT,
            length=round(length_x, 2),
            quantity=count_x,
            spacing=bottom_spacing,
            location="Đáy bể - Thép dưới X",
            grade="CB400-V"
        ))
        
        # 2. Thép dưới phương Y
        length_y = width + 0.8
        count_y = int(length / (bottom_spacing / 1000)) + 1
        
        items.append(RebarItem(
            mark="5",
            diameter=bottom_bar,
            shape=RebarShape.STRAIGHT,
            length=round(length_y, 2),
            quantity=count_y,
            spacing=bottom_spacing,
            location="Đáy bể - Thép dưới Y",
            grade="CB400-V"
        ))
        
        # 3. Thép trên (nếu có)
        if has_top_layer:
            items.append(RebarItem(
                mark="6",
                diameter=top_bar,
                shape=RebarShape.STRAIGHT,
                length=round(length_x, 2),
                quantity=int(width / (top_spacing / 1000)) + 1,
                spacing=top_spacing,
                location="Đáy bể - Thép trên X",
                grade="CB400-V"
            ))
            
            items.append(RebarItem(
                mark="7",
                diameter=top_bar,
                shape=RebarShape.STRAIGHT,
                length=round(length_y, 2),
                quantity=int(length / (top_spacing / 1000)) + 1,
                spacing=top_spacing,
                location="Đáy bể - Thép trên Y",
                grade="CB400-V"
            ))
        
        return RebarSchedule(
            element_name="Đáy bể",
            items=items
        )
    
    @classmethod
    def generate_complete_tank_schedule(
        cls,
        tank_length: float,
        tank_width: float,
        tank_depth: float,
        wall_thickness: float = 0.25,
        bottom_thickness: float = 0.30,
        wall_main_bar: int = 12,
        wall_main_spacing: int = 150,
        bottom_bar: int = 12,
        bottom_spacing: int = 150
    ) -> RebarSchedule:
        """
        Tạo bảng thống kê cốt thép hoàn chỉnh cho bể
        
        Returns:
            RebarSchedule: Bảng thống kê đầy đủ
        """
        all_items = []
        mark_counter = 1
        
        # Thành dài (2 thành)
        wall_long = cls.generate_for_tank_wall(
            height=tank_depth,
            width=tank_length,
            thickness=wall_thickness,
            main_bar=wall_main_bar,
            main_spacing=wall_main_spacing
        )
        for item in wall_long.items:
            item.mark = str(mark_counter)
            item.quantity *= 2  # 2 thành dài
            item.location = "Thành dài - " + item.location.split(" - ")[-1]
            all_items.append(item)
            mark_counter += 1
        
        # Thành ngắn (2 thành)
        wall_short = cls.generate_for_tank_wall(
            height=tank_depth,
            width=tank_width,
            thickness=wall_thickness,
            main_bar=wall_main_bar,
            main_spacing=wall_main_spacing
        )
        for item in wall_short.items:
            item.mark = str(mark_counter)
            item.quantity *= 2  # 2 thành ngắn
            item.location = "Thành ngắn - " + item.location.split(" - ")[-1]
            all_items.append(item)
            mark_counter += 1
        
        # Đáy
        slab = cls.generate_for_tank_slab(
            length=tank_length + 2 * wall_thickness,
            width=tank_width + 2 * wall_thickness,
            thickness=bottom_thickness,
            bottom_bar=bottom_bar,
            bottom_spacing=bottom_spacing
        )
        for item in slab.items:
            item.mark = str(mark_counter)
            all_items.append(item)
            mark_counter += 1
        
        return RebarSchedule(
            element_name=f"Bể {tank_length}×{tank_width}×{tank_depth}m",
            items=all_items
        )


class RebarScheduleCADDrawer:
    """
    Vẽ bảng thống kê cốt thép trên CAD (DXF)
    """
    
    # Kích thước bảng
    TABLE_HEADER_HEIGHT = 10  # mm trên giấy
    TABLE_ROW_HEIGHT = 8      # mm trên giấy
    
    # Cột
    COLUMNS = [
        ("STT", 15),
        ("Ký hiệu", 25),
        ("Đ.kính", 20),
        ("H.dạng", 20),
        ("C.dài\n(m)", 25),
        ("Số\nlượng", 20),
        ("Tổng\ndài (m)", 25),
        ("K.lượng\n(kg)", 25),
        ("Ghi chú", 45)
    ]
    
    def __init__(self, doc, scale: float = 1.0):
        """
        Args:
            doc: ezdxf document
            scale: Tỷ lệ bản vẽ (1.0 = 1:1)
        """
        self.doc = doc
        self.msp = doc.modelspace()
        self.scale = scale
        self._ensure_layers()
    
    def _ensure_layers(self):
        """Đảm bảo các layer tồn tại"""
        layers = {
            "TABLE_FRAME": (7, 25),     # White, 0.25mm
            "TABLE_TEXT": (7, 18),      # White, thin
            "TABLE_HEADER": (3, 25),    # Green, 0.25mm
        }
        for name, (color, lw) in layers.items():
            if name not in self.doc.layers:
                self.doc.layers.add(name, color=color, lineweight=lw)
    
    def draw_schedule_table(
        self,
        schedule: RebarSchedule,
        position: Tuple[float, float],
        title: str = None
    ) -> Dict[str, Any]:
        """
        Vẽ bảng thống kê cốt thép
        
        Args:
            schedule: Bảng thống kê
            position: Vị trí góc trên trái (x, y)
            title: Tiêu đề bảng
            
        Returns:
            Dict: Thông tin về bảng đã vẽ
        """
        x0, y0 = position
        
        # Scale từ mm giấy sang model units
        # Giả định scale 1:100, 1mm giấy = 100mm thực = 0.1m
        paper_to_model = 0.1 * (100 / self.scale) if self.scale else 0.1
        
        header_h = self.TABLE_HEADER_HEIGHT * paper_to_model
        row_h = self.TABLE_ROW_HEIGHT * paper_to_model
        
        # Tính tổng chiều rộng
        total_width = sum(c[1] for c in self.COLUMNS) * paper_to_model
        
        # Số hàng dữ liệu
        num_rows = len(schedule.items)
        total_height = header_h + row_h * (num_rows + 2)  # +2 cho header và tổng
        
        # Vẽ tiêu đề bảng
        if title is None:
            title = f"BẢNG THỐNG KÊ CỐT THÉP - {schedule.element_name.upper()}"
        
        title_height = 5 * paper_to_model
        self.msp.add_text(
            title,
            dxfattribs={
                "layer": "TABLE_HEADER",
                "height": title_height,
                "style": "STANDARD"
            }
        ).set_placement(
            (x0 + total_width / 2, y0 + header_h * 0.5),
            align=ezdxf.enums.TextEntityAlignment.BOTTOM_CENTER
        )
        
        y_start = y0 - header_h
        
        # Vẽ khung bảng
        self._draw_table_frame(x0, y_start, total_width, total_height, header_h, row_h)
        
        # Vẽ header
        self._draw_header_row(x0, y_start, paper_to_model)
        
        # Vẽ dữ liệu
        y_current = y_start - header_h
        for i, item in enumerate(schedule.items):
            self._draw_data_row(x0, y_current, item, i + 1, paper_to_model)
            y_current -= row_h
        
        # Vẽ hàng tổng
        self._draw_total_row(x0, y_current, schedule, paper_to_model)
        
        return {
            "position": position,
            "width": total_width,
            "height": total_height,
            "rows": num_rows,
            "total_weight": schedule.total_weight
        }
    
    def _draw_table_frame(
        self, x0: float, y0: float, 
        width: float, height: float,
        header_h: float, row_h: float
    ):
        """Vẽ khung bảng"""
        import ezdxf
        
        # Khung ngoài
        self.msp.add_lwpolyline([
            (x0, y0), (x0 + width, y0),
            (x0 + width, y0 - height), (x0, y0 - height),
            (x0, y0)
        ], close=True, dxfattribs={"layer": "TABLE_FRAME", "lineweight": 35})
        
        # Đường ngang header
        self.msp.add_line(
            (x0, y0 - header_h),
            (x0 + width, y0 - header_h),
            dxfattribs={"layer": "TABLE_FRAME", "lineweight": 25}
        )
    
    def _draw_header_row(self, x0: float, y0: float, scale: float):
        """Vẽ hàng tiêu đề"""
        import ezdxf
        
        x_pos = x0
        text_h = 3 * scale
        
        for col_name, col_width in self.COLUMNS:
            w = col_width * scale
            
            # Đường dọc
            self.msp.add_line(
                (x_pos + w, y0),
                (x_pos + w, y0 - self.TABLE_HEADER_HEIGHT * scale),
                dxfattribs={"layer": "TABLE_FRAME"}
            )
            
            # Text
            self.msp.add_text(
                col_name.replace("\n", " "),
                dxfattribs={
                    "layer": "TABLE_HEADER",
                    "height": text_h
                }
            ).set_placement(
                (x_pos + w / 2, y0 - self.TABLE_HEADER_HEIGHT * scale / 2),
                align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER
            )
            
            x_pos += w
    
    def _draw_data_row(
        self, x0: float, y0: float,
        item: RebarItem, row_num: int, scale: float
    ):
        """Vẽ một hàng dữ liệu"""
        import ezdxf
        
        row_h = self.TABLE_ROW_HEIGHT * scale
        text_h = 2.5 * scale
        
        data = [
            str(row_num),
            item.mark,
            f"Φ{item.diameter}",
            item.shape.value,
            f"{item.length:.2f}",
            str(item.quantity),
            f"{item.total_length:.2f}",
            f"{item.total_weight:.1f}",
            item.location[:20] if len(item.location) > 20 else item.location
        ]
        
        x_pos = x0
        for i, (col_name, col_width) in enumerate(self.COLUMNS):
            w = col_width * scale
            
            # Đường dọc
            self.msp.add_line(
                (x_pos + w, y0),
                (x_pos + w, y0 - row_h),
                dxfattribs={"layer": "TABLE_FRAME", "lineweight": 18}
            )
            
            # Text
            self.msp.add_text(
                data[i] if i < len(data) else "",
                dxfattribs={
                    "layer": "TABLE_TEXT",
                    "height": text_h
                }
            ).set_placement(
                (x_pos + w / 2, y0 - row_h / 2),
                align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER
            )
            
            x_pos += w
        
        # Đường ngang dưới
        self.msp.add_line(
            (x0, y0 - row_h),
            (x_pos, y0 - row_h),
            dxfattribs={"layer": "TABLE_FRAME", "lineweight": 18}
        )
    
    def _draw_total_row(
        self, x0: float, y0: float,
        schedule: RebarSchedule, scale: float
    ):
        """Vẽ hàng tổng cộng"""
        import ezdxf
        
        row_h = self.TABLE_ROW_HEIGHT * scale
        text_h = 3 * scale
        
        # Tổng chiều dài và khối lượng
        total_length = sum(item.total_length for item in schedule.items)
        total_weight = schedule.total_weight
        
        x_pos = x0
        total_data = [
            "", "", "", "", "TỔNG CỘNG", "",
            f"{total_length:.1f}", f"{total_weight:.1f}", ""
        ]
        
        for i, (col_name, col_width) in enumerate(self.COLUMNS):
            w = col_width * scale
            
            self.msp.add_text(
                total_data[i],
                dxfattribs={
                    "layer": "TABLE_HEADER",
                    "height": text_h
                }
            ).set_placement(
                (x_pos + w / 2, y0 - row_h / 2),
                align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER
            )
            
            x_pos += w
    
    def draw_material_takeoff_table(
        self,
        schedule: RebarSchedule,
        position: Tuple[float, float],
        concrete_volume: float = 0,
        formwork_area: float = 0
    ) -> Dict[str, Any]:
        """
        Vẽ bảng khối lượng vật tư tổng hợp
        
        Args:
            schedule: Bảng thống kê thép
            position: Vị trí
            concrete_volume: Thể tích bê tông (m³)
            formwork_area: Diện tích ván khuôn (m²)
        """
        import ezdxf
        
        x0, y0 = position
        scale = 0.1  # Giả định
        
        # Tiêu đề
        title = "BẢNG KHỐI LƯỢNG VẬT TƯ"
        self.msp.add_text(
            title,
            dxfattribs={"layer": "TABLE_HEADER", "height": 5 * scale}
        ).set_placement((x0, y0), align=ezdxf.enums.TextEntityAlignment.TOP_LEFT)
        
        # Nội dung
        y_current = y0 - 10 * scale
        line_h = 6 * scale
        text_h = 3 * scale
        
        materials = [
            ("1", "Bê tông", f"{concrete_volume:.2f} m³", "B25"),
            ("2", "Cốt thép", f"{schedule.total_weight:.0f} kg", "CB400-V"),
            ("3", "Ván khuôn", f"{formwork_area:.1f} m²", "Gỗ/Thép")
        ]
        
        # Thép theo đường kính
        for dia, weight in sorted(schedule.weight_by_diameter.items()):
            materials.append((
                f"2.{dia}", f"  - Thép Φ{dia}", f"{weight:.1f} kg", ""
            ))
        
        for stt, name, qty, note in materials:
            self.msp.add_text(
                f"{stt}. {name}: {qty} ({note})" if note else f"{stt}. {name}: {qty}",
                dxfattribs={"layer": "TABLE_TEXT", "height": text_h}
            ).set_placement((x0, y_current), align=ezdxf.enums.TextEntityAlignment.TOP_LEFT)
            
            y_current -= line_h
        
        return {"position": position, "height": abs(y0 - y_current)}


# Import ezdxf for type hints
try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
except ImportError:
    pass
