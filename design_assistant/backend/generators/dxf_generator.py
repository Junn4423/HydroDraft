"""
DXF Generator - Tạo bản vẽ 2D với ezdxf

Tạo các loại bản vẽ:
- Mặt bằng (Plan view)
- Mặt cắt (Section view)
- Chi tiết (Detail)
- Trắc dọc (Profile)
"""

import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import os
import math

class DXFGenerator:
    """
    Tạo bản vẽ DXF/DWG 2D
    
    Chuẩn layer theo tiền tố:
    - STR_  : Kết cấu
    - PIPE_ : Đường ống
    - DIM_  : Kích thước
    - TEXT_ : Văn bản
    - WATER_: Mực nước
    - HATCH_: Mặt cắt vật liệu
    """
    
    # Màu layer theo tiêu chuẩn
    LAYER_COLORS = {
        "STR_WALL": 3,          # Xanh lá - Thành
        "STR_FOUNDATION": 2,    # Vàng - Móng
        "STR_SLAB": 4,          # Cyan - Bản
        "PIPE_MAIN": 1,         # Đỏ - Ống chính
        "PIPE_BRANCH": 6,       # Magenta - Ống nhánh
        "DIM_": 7,              # Trắng - Kích thước
        "TEXT_TITLE": 7,        # Trắng - Tiêu đề
        "TEXT_NOTE": 8,         # Xám - Ghi chú
        "WATER_LEVEL": 5,       # Xanh dương - Mực nước
        "HATCH_CONCRETE": 8,    # Xám - Bê tông
        "HATCH_SOIL": 33,       # Nâu - Đất
        "CENTER": 1,            # Đỏ - Đường tâm
        "HIDDEN": 8,            # Xám - Nét khuất
    }
    
    # Kiểu đường
    LINE_TYPES = {
        "CENTER": "CENTER",
        "HIDDEN": "HIDDEN",
        "DASHED": "DASHED",
        "PHANTOM": "PHANTOM"
    }
    
    def __init__(self, output_dir: str = "./outputs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.doc = None
        self.msp = None
    
    def create_new_drawing(self, version: str = "R2018") -> None:
        """Tạo bản vẽ mới"""
        self.doc = ezdxf.new(version)
        self.doc.units = units.M  # Đơn vị mét
        self.msp = self.doc.modelspace()
        
        # Setup layers
        self._setup_layers()
        
        # Setup text styles
        self._setup_text_styles()
        
        # Setup dimension styles
        self._setup_dim_styles()
    
    def _setup_layers(self) -> None:
        """Tạo các layer tiêu chuẩn"""
        for layer_name, color in self.LAYER_COLORS.items():
            if layer_name not in self.doc.layers:
                self.doc.layers.add(layer_name, color=color)
    
    def _setup_text_styles(self) -> None:
        """Tạo kiểu chữ"""
        # Kiểu chữ tiêu chuẩn
        if "STANDARD_VN" not in self.doc.styles:
            self.doc.styles.add("STANDARD_VN", font="Arial")
        
        # Kiểu chữ kỹ thuật
        if "ENGINEERING" not in self.doc.styles:
            self.doc.styles.add("ENGINEERING", font="romans.shx")
    
    def _setup_dim_styles(self) -> None:
        """Tạo kiểu kích thước"""
        if "DIM_1_100" not in self.doc.dimstyles:
            dim_style = self.doc.dimstyles.new("DIM_1_100")
            dim_style.dxf.dimtxt = 2.5  # Chiều cao chữ 2.5mm
            dim_style.dxf.dimasz = 2.5  # Kích thước mũi tên
            dim_style.dxf.dimexe = 1.5  # Vượt quá đường ghi chú
            dim_style.dxf.dimexo = 0.5  # Offset từ gốc
            dim_style.dxf.dimgap = 1.0  # Khoảng cách text
    
    def _ensure_drawing(self) -> None:
        """Đảm bảo bản vẽ đã được tạo"""
        if self.doc is None or self.msp is None:
            self.create_new_drawing()
    
    def draw_tank_plan(
        self,
        length: float,
        width: float,
        wall_thickness: float,
        inlet_diameter: float = 200,
        outlet_diameter: float = 200,
        origin: Tuple[float, float] = (0, 0),
        scale: float = 1.0,
        include_dimensions: bool = True,
        include_annotations: bool = True
    ) -> None:
        """
        Vẽ mặt bằng bể
        
        Args:
            length: Chiều dài trong (m)
            width: Chiều rộng trong (m)
            wall_thickness: Chiều dày thành (m)
            inlet_diameter: Đường kính ống vào (mm)
            outlet_diameter: Đường kính ống ra (mm)
            origin: Gốc tọa độ
            scale: Tỷ lệ
            include_dimensions: Thêm kích thước
            include_annotations: Thêm ghi chú
        """
        self._ensure_drawing()
        
        ox, oy = origin
        s = scale
        t = wall_thickness
        
        # Kích thước ngoài
        L_out = length + 2 * t
        W_out = width + 2 * t
        
        # 1. Vẽ đường bao ngoài (thành)
        outer_points = [
            (ox, oy),
            (ox + L_out * s, oy),
            (ox + L_out * s, oy + W_out * s),
            (ox, oy + W_out * s),
            (ox, oy)
        ]
        self.msp.add_lwpolyline(outer_points, dxfattribs={"layer": "STR_WALL"})
        
        # 2. Vẽ đường bao trong
        inner_points = [
            (ox + t * s, oy + t * s),
            (ox + (t + length) * s, oy + t * s),
            (ox + (t + length) * s, oy + (t + width) * s),
            (ox + t * s, oy + (t + width) * s),
            (ox + t * s, oy + t * s)
        ]
        self.msp.add_lwpolyline(inner_points, dxfattribs={"layer": "STR_WALL"})
        
        # 3. Hatch bê tông thành
        hatch = self.msp.add_hatch(color=252, dxfattribs={"layer": "HATCH_CONCRETE"})
        # Đường bao ngoài
        hatch.paths.add_polyline_path(outer_points[:-1], is_closed=True)
        # Đường bao trong (đảo ngược để tạo lỗ)
        hatch.paths.add_polyline_path(inner_points[:-1], is_closed=True)
        hatch.set_pattern_fill("AR-CONC", scale=0.01)
        
        # 4. Vẽ đường tâm
        cx = ox + L_out * s / 2
        cy = oy + W_out * s / 2
        
        # Đường tâm dọc
        self.msp.add_line(
            (cx, oy - 1 * s), (cx, oy + W_out * s + 1 * s),
            dxfattribs={"layer": "CENTER", "linetype": "CENTER"}
        )
        # Đường tâm ngang
        self.msp.add_line(
            (ox - 1 * s, cy), (ox + L_out * s + 1 * s, cy),
            dxfattribs={"layer": "CENTER", "linetype": "CENTER"}
        )
        
        # 5. Vẽ ống vào (bên trái)
        inlet_x = ox
        inlet_y = cy
        inlet_r = inlet_diameter / 1000 / 2 * s
        self.msp.add_circle(
            (inlet_x, inlet_y), inlet_r,
            dxfattribs={"layer": "PIPE_MAIN"}
        )
        
        # 6. Vẽ ống ra (bên phải)
        outlet_x = ox + L_out * s
        outlet_y = cy
        outlet_r = outlet_diameter / 1000 / 2 * s
        self.msp.add_circle(
            (outlet_x, outlet_y), outlet_r,
            dxfattribs={"layer": "PIPE_MAIN"}
        )
        
        # 7. Kích thước
        if include_dimensions:
            self._add_dimension(
                (ox + t * s, oy - 1.5 * s),
                (ox + (t + length) * s, oy - 1.5 * s),
                f"{length:.2f}",
                offset=-1.5 * s
            )
            self._add_dimension(
                (ox, oy - 2.5 * s),
                (ox + L_out * s, oy - 2.5 * s),
                f"{L_out:.2f}",
                offset=-2.5 * s
            )
            self._add_dimension(
                (ox - 1.5 * s, oy + t * s),
                (ox - 1.5 * s, oy + (t + width) * s),
                f"{width:.2f}",
                vertical=True,
                offset=-1.5 * s
            )
        
        # 8. Ghi chú
        if include_annotations:
            # Tiêu đề
            self.msp.add_text(
                "MẶT BẰNG BỂ",
                dxfattribs={
                    "layer": "TEXT_TITLE",
                    "style": "STANDARD_VN",
                    "height": 0.5 * s
                }
            ).set_placement(
                (cx, oy + W_out * s + 3 * s),
                align=TextEntityAlignment.MIDDLE_CENTER
            )
            
            # Ghi chú ống
            self.msp.add_text(
                f"Ống vào DN{int(inlet_diameter)}",
                dxfattribs={
                    "layer": "TEXT_NOTE",
                    "style": "STANDARD_VN",
                    "height": 0.25 * s
                }
            ).set_placement(
                (ox - 0.5 * s, inlet_y + 0.5 * s),
                align=TextEntityAlignment.RIGHT
            )
            
            self.msp.add_text(
                f"Ống ra DN{int(outlet_diameter)}",
                dxfattribs={
                    "layer": "TEXT_NOTE",
                    "style": "STANDARD_VN",
                    "height": 0.25 * s
                }
            ).set_placement(
                (outlet_x + 0.5 * s, outlet_y + 0.5 * s),
                align=TextEntityAlignment.LEFT
            )
    
    def draw_tank_section(
        self,
        length: float,
        total_depth: float,
        water_depth: float,
        wall_thickness: float,
        bottom_thickness: float,
        freeboard: float,
        foundation_level: float = 0.0,
        origin: Tuple[float, float] = (0, 0),
        scale: float = 1.0
    ) -> None:
        """
        Vẽ mặt cắt dọc bể
        
        Args:
            length: Chiều dài trong (m)
            total_depth: Tổng chiều sâu (m)
            water_depth: Chiều sâu nước (m)
            wall_thickness: Chiều dày thành (m)
            bottom_thickness: Chiều dày đáy (m)
            freeboard: Chiều cao an toàn (m)
            foundation_level: Cao độ đáy móng (m)
            origin: Gốc tọa độ
            scale: Tỷ lệ
        """
        self._ensure_drawing()
        
        ox, oy = origin
        s = scale
        t = wall_thickness
        bt = bottom_thickness
        
        L_out = length + 2 * t
        H_total = total_depth + bt
        
        # 1. Vẽ thành trái
        left_wall = [
            (ox, oy),
            (ox + t * s, oy),
            (ox + t * s, oy + total_depth * s),
            (ox, oy + total_depth * s),
            (ox, oy)
        ]
        self.msp.add_lwpolyline(left_wall, dxfattribs={"layer": "STR_WALL"})
        
        # 2. Vẽ thành phải
        right_wall = [
            (ox + (t + length) * s, oy),
            (ox + L_out * s, oy),
            (ox + L_out * s, oy + total_depth * s),
            (ox + (t + length) * s, oy + total_depth * s),
            (ox + (t + length) * s, oy)
        ]
        self.msp.add_lwpolyline(right_wall, dxfattribs={"layer": "STR_WALL"})
        
        # 3. Vẽ đáy
        bottom = [
            (ox, oy),
            (ox + L_out * s, oy),
            (ox + L_out * s, oy - bt * s),
            (ox, oy - bt * s),
            (ox, oy)
        ]
        self.msp.add_lwpolyline(bottom, dxfattribs={"layer": "STR_FOUNDATION"})
        
        # 4. Hatch bê tông
        # Thành trái
        hatch_left = self.msp.add_hatch(dxfattribs={"layer": "HATCH_CONCRETE"})
        hatch_left.paths.add_polyline_path(left_wall[:-1], is_closed=True)
        hatch_left.set_pattern_fill("AR-CONC", scale=0.01)
        
        # Thành phải
        hatch_right = self.msp.add_hatch(dxfattribs={"layer": "HATCH_CONCRETE"})
        hatch_right.paths.add_polyline_path(right_wall[:-1], is_closed=True)
        hatch_right.set_pattern_fill("AR-CONC", scale=0.01)
        
        # Đáy
        hatch_bottom = self.msp.add_hatch(dxfattribs={"layer": "HATCH_CONCRETE"})
        hatch_bottom.paths.add_polyline_path(bottom[:-1], is_closed=True)
        hatch_bottom.set_pattern_fill("AR-CONC", scale=0.01)
        
        # 5. Vẽ mực nước
        water_y = oy + (total_depth - freeboard) * s
        self.msp.add_line(
            (ox + t * s, water_y),
            (ox + (t + length) * s, water_y),
            dxfattribs={"layer": "WATER_LEVEL", "linetype": "DASHED"}
        )
        
        # 6. Đường mực đất (nếu bể chôn)
        ground_y = oy + total_depth * s
        self.msp.add_line(
            (ox - 2 * s, ground_y),
            (ox + L_out * s + 2 * s, ground_y),
            dxfattribs={"layer": "STR_FOUNDATION"}
        )
        
        # 7. Kích thước
        # Chiều cao
        self._add_dimension(
            (ox - 1 * s, oy),
            (ox - 1 * s, oy + total_depth * s),
            f"{total_depth:.2f}",
            vertical=True,
            offset=-1 * s
        )
        
        # Chiều dài
        self._add_dimension(
            (ox + t * s, oy - bt * s - 1 * s),
            (ox + (t + length) * s, oy - bt * s - 1 * s),
            f"{length:.2f}",
            offset=-1 * s
        )
        
        # 8. Cao độ
        self._add_elevation_mark(ox - 2 * s, oy + total_depth * s, foundation_level + total_depth, s)
        self._add_elevation_mark(ox - 2 * s, water_y, foundation_level + water_depth, s)
        self._add_elevation_mark(ox - 2 * s, oy - bt * s, foundation_level - bt, s)
        
        # 9. Tiêu đề
        self.msp.add_text(
            "MẶT CẮT A-A",
            dxfattribs={
                "layer": "TEXT_TITLE",
                "style": "STANDARD_VN",
                "height": 0.5 * s
            }
        ).set_placement(
            (ox + L_out * s / 2, oy - bt * s - 3 * s),
            align=TextEntityAlignment.MIDDLE_CENTER
        )
    
    def draw_pipe_profile(
        self,
        segments: List[Dict],
        manholes: List[Dict],
        origin: Tuple[float, float] = (0, 0),
        h_scale: float = 1.0,    # Tỷ lệ ngang
        v_scale: float = 10.0,   # Tỷ lệ đứng (phóng đại)
        v_exaggeration: float = 10.0
    ) -> None:
        """
        Vẽ trắc dọc đường ống
        
        Args:
            segments: Danh sách đoạn ống
            manholes: Danh sách giếng thăm
            origin: Gốc tọa độ
            h_scale: Tỷ lệ ngang
            v_scale: Tỷ lệ đứng
            v_exaggeration: Độ phóng đại đứng
        """
        self._ensure_drawing()
        
        ox, oy = origin
        hs = h_scale
        vs = v_scale * v_exaggeration
        
        # Tìm cao độ min/max
        all_elevations = []
        for mh in manholes:
            all_elevations.append(mh["ground_level"])
            all_elevations.append(mh["invert_level"])
        
        z_min = min(all_elevations) - 1
        z_max = max(all_elevations) + 1
        
        # 1. Vẽ đường mặt đất
        ground_points = []
        for mh in manholes:
            x = ox + mh["station"] * hs
            y = oy + (mh["ground_level"] - z_min) * vs
            ground_points.append((x, y))
        
        self.msp.add_lwpolyline(ground_points, dxfattribs={"layer": "STR_FOUNDATION"})
        
        # 2. Vẽ đường ống (cao độ đáy)
        pipe_points = []
        for mh in manholes:
            x = ox + mh["station"] * hs
            y = oy + (mh["invert_level"] - z_min) * vs
            pipe_points.append((x, y))
        
        self.msp.add_lwpolyline(pipe_points, dxfattribs={"layer": "PIPE_MAIN", "color": 1})
        
        # 3. Vẽ giếng thăm
        for mh in manholes:
            x = ox + mh["station"] * hs
            y_ground = oy + (mh["ground_level"] - z_min) * vs
            y_invert = oy + (mh["invert_level"] - z_min) * vs
            
            # Vẽ đường thẳng đứng
            self.msp.add_line(
                (x, y_invert), (x, y_ground),
                dxfattribs={"layer": "STR_WALL"}
            )
            
            # Ghi tên giếng
            self.msp.add_text(
                mh["id"],
                dxfattribs={
                    "layer": "TEXT_NOTE",
                    "height": 0.3 * hs
                }
            ).set_placement(
                (x, y_ground + 0.5 * hs),
                align=TextEntityAlignment.BOTTOM_CENTER
            )
        
        # 4. Bảng thông số
        self._draw_profile_table(ox, oy - 3 * hs, manholes, segments, hs)
    
    def _draw_profile_table(
        self,
        x: float,
        y: float,
        manholes: List[Dict],
        segments: List[Dict],
        scale: float
    ) -> None:
        """Vẽ bảng thông số trắc dọc"""
        row_height = 1.0 * scale
        col_width = 3.0 * scale
        
        rows = [
            "Lý trình",
            "Cao độ mặt đất",
            "Cao độ đáy ống",
            "Độ sâu chôn",
            "Độ dốc (%)",
            "Đường kính",
            "Chiều dài"
        ]
        
        # Vẽ header
        for i, row_name in enumerate(rows):
            y_row = y - i * row_height
            self.msp.add_line((x, y_row), (x + col_width, y_row), dxfattribs={"layer": "DIM_"})
            self.msp.add_text(
                row_name,
                dxfattribs={"layer": "TEXT_NOTE", "height": 0.2 * scale}
            ).set_placement((x + 0.1 * scale, y_row - 0.7 * row_height))
        
        # Vẽ dữ liệu
        for j, mh in enumerate(manholes):
            x_col = x + col_width + j * col_width
            
            # Đường kẻ dọc
            self.msp.add_line(
                (x_col, y), (x_col, y - len(rows) * row_height),
                dxfattribs={"layer": "DIM_"}
            )
            
            # Dữ liệu
            # Tính toán độ sâu chôn từ cao độ mặt đất và cao độ đáy ống
            calculated_depth = mh.get('depth', mh['ground_level'] - mh['invert_level'])
            data = [
                f"{mh['station']:.1f}",
                f"{mh['ground_level']:.3f}",
                f"{mh['invert_level']:.3f}",
                f"{calculated_depth:.2f}",
                "",  # Độ dốc - điền sau
                "",  # Đường kính
                ""   # Chiều dài
            ]
            
            # Thêm dữ liệu đoạn ống (nếu có segment tiếp theo)
            if j < len(segments):
                seg = segments[j]
                data[4] = f"{seg['slope']:.2f}"
                data[5] = f"DN{int(seg['diameter'])}"
                data[6] = f"{seg['length']:.1f}"
            
            for i, value in enumerate(data):
                y_row = y - i * row_height
                self.msp.add_text(
                    value,
                    dxfattribs={"layer": "TEXT_NOTE", "height": 0.2 * scale}
                ).set_placement((x_col + 0.1 * scale, y_row - 0.7 * row_height))
    
    def _add_dimension(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        text: str,
        offset: float = 0,
        vertical: bool = False
    ) -> None:
        """Thêm kích thước"""
        if vertical:
            dim = self.msp.add_linear_dim(
                base=((p1[0] + p2[0])/2 + offset, (p1[1] + p2[1])/2),
                p1=p1,
                p2=p2,
                angle=90,
                override={"dimtxt": 0.25}
            )
        else:
            mid_y = (p1[1] + p2[1])/2 + offset
            dim = self.msp.add_linear_dim(
                base=((p1[0] + p2[0])/2, mid_y),
                p1=p1,
                p2=p2,
                override={"dimtxt": 0.25}
            )
    
    def _add_elevation_mark(
        self,
        x: float,
        y: float,
        elevation: float,
        scale: float
    ) -> None:
        """Thêm ký hiệu cao độ"""
        # Vẽ tam giác
        points = [
            (x, y),
            (x - 0.3 * scale, y - 0.3 * scale),
            (x - 0.3 * scale, y + 0.3 * scale),
            (x, y)
        ]
        self.msp.add_lwpolyline(points, dxfattribs={"layer": "DIM_"})
        
        # Ghi cao độ
        self.msp.add_text(
            f"+{elevation:.3f}" if elevation >= 0 else f"{elevation:.3f}",
            dxfattribs={
                "layer": "TEXT_NOTE",
                "height": 0.2 * scale
            }
        ).set_placement(
            (x - 0.5 * scale, y),
            align=TextEntityAlignment.RIGHT
        )
    
    def add_title_block(
        self,
        project_name: str,
        drawing_title: str,
        scale: str,
        drawn_by: str = "HydroDraft",
        date: str = None,
        position: Tuple[float, float] = (0, 0)
    ) -> None:
        """Thêm khung tên bản vẽ"""
        if date is None:
            date = datetime.now().strftime("%d/%m/%Y")
        
        x, y = position
        
        # Khung ngoài
        self.msp.add_lwpolyline([
            (x, y), (x + 180, y), (x + 180, y + 40),
            (x, y + 40), (x, y)
        ], dxfattribs={"layer": "DIM_"})
        
        # Nội dung
        texts = [
            (project_name, (x + 90, y + 35), 5),
            (drawing_title, (x + 90, y + 25), 4),
            (f"Tỷ lệ: {scale}", (x + 30, y + 10), 3),
            (f"Người vẽ: {drawn_by}", (x + 90, y + 10), 3),
            (f"Ngày: {date}", (x + 150, y + 10), 3)
        ]
        
        for text, pos, height in texts:
            self.msp.add_text(
                text,
                dxfattribs={
                    "layer": "TEXT_TITLE",
                    "height": height
                }
            ).set_placement(pos, align=TextEntityAlignment.MIDDLE_CENTER)
    
    def draw_well_section(
        self,
        total_depth: float,
        casing_diameter: float,
        borehole_diameter: float,
        screen_top: float,
        screen_bottom: float,
        grout_depth: float,
        bentonite_top: float,
        bentonite_bottom: float,
        gravel_top: float,
        ground_level: float = 0.0,
        protective_height: float = 0.5,
        geology: List[Dict] = None,
        origin: Tuple[float, float] = (0, 0),
        scale: float = 1.0
    ) -> None:
        """
        Vẽ mặt cắt giếng quan trắc
        
        Args:
            total_depth: Tổng chiều sâu giếng (m)
            casing_diameter: Đường kính ống chống (mm)
            borehole_diameter: Đường kính lỗ khoan (mm)
            screen_top: Đỉnh ống lọc (m dưới mặt đất)
            screen_bottom: Đáy ống lọc (m dưới mặt đất)
            grout_depth: Chiều sâu vữa trám (m)
            bentonite_top: Đỉnh lớp bentonite (m)
            bentonite_bottom: Đáy lớp bentonite (m)
            gravel_top: Đỉnh lớp sỏi lọc (m)
            ground_level: Cao độ mặt đất
            protective_height: Chiều cao ống bảo vệ trên mặt đất (m)
            geology: Cột địa tầng
            origin: Gốc tọa độ
            scale: Tỷ lệ
        """
        self._ensure_drawing()
        
        ox, oy = origin
        s = scale
        
        # Chuyển đổi mm sang m
        casing_r = casing_diameter / 1000 / 2
        borehole_r = borehole_diameter / 1000 / 2
        
        # 1. Vẽ lỗ khoan (đường bao ngoài)
        borehole_left = ox - borehole_r * s
        borehole_right = ox + borehole_r * s
        
        # Đường viền lỗ khoan
        self.msp.add_line(
            (borehole_left, oy), (borehole_left, oy - total_depth * s),
            dxfattribs={"layer": "HATCH_SOIL", "linetype": "DASHED"}
        )
        self.msp.add_line(
            (borehole_right, oy), (borehole_right, oy - total_depth * s),
            dxfattribs={"layer": "HATCH_SOIL", "linetype": "DASHED"}
        )
        
        # 2. Vẽ ống bảo vệ (trên mặt đất)
        protective_r = (casing_diameter + 50) / 1000 / 2
        protective_left = ox - protective_r * s
        protective_right = ox + protective_r * s
        
        protective_points = [
            (protective_left, oy + protective_height * s),
            (protective_left, oy - 0.3 * s),
            (protective_right, oy - 0.3 * s),
            (protective_right, oy + protective_height * s),
        ]
        self.msp.add_lwpolyline(
            protective_points, close=True,
            dxfattribs={"layer": "STR_WALL", "lineweight": 50}
        )
        
        # Nắp giếng
        self.msp.add_line(
            (protective_left - 0.05 * s, oy + protective_height * s),
            (protective_right + 0.05 * s, oy + protective_height * s),
            dxfattribs={"layer": "STR_WALL", "lineweight": 70}
        )
        
        # 3. Vẽ ống chống (casing)
        casing_left = ox - casing_r * s
        casing_right = ox + casing_r * s
        
        # Phần ống chống (từ trên xuống đến screen_top)
        self.msp.add_line(
            (casing_left, oy + protective_height * s * 0.8),
            (casing_left, oy - screen_top * s),
            dxfattribs={"layer": "PIPE_MAIN", "lineweight": 35}
        )
        self.msp.add_line(
            (casing_right, oy + protective_height * s * 0.8),
            (casing_right, oy - screen_top * s),
            dxfattribs={"layer": "PIPE_MAIN", "lineweight": 35}
        )
        
        # 4. Vẽ ống lọc (screen) - có khe
        screen_depth = screen_bottom - screen_top
        slot_spacing = 0.1 * s  # Khoảng cách giữa các khe
        num_slots = int(screen_depth * s / slot_spacing / 2)
        
        for i in range(num_slots):
            y_slot = oy - (screen_top + i * 0.2) * s
            # Khe bên trái
            self.msp.add_line(
                (casing_left - 0.02 * s, y_slot),
                (casing_left + 0.02 * s, y_slot),
                dxfattribs={"layer": "PIPE_MAIN"}
            )
            # Khe bên phải
            self.msp.add_line(
                (casing_right - 0.02 * s, y_slot),
                (casing_right + 0.02 * s, y_slot),
                dxfattribs={"layer": "PIPE_MAIN"}
            )
        
        # Đường viền ống lọc
        self.msp.add_line(
            (casing_left, oy - screen_top * s),
            (casing_left, oy - screen_bottom * s),
            dxfattribs={"layer": "PIPE_MAIN", "lineweight": 35}
        )
        self.msp.add_line(
            (casing_right, oy - screen_top * s),
            (casing_right, oy - screen_bottom * s),
            dxfattribs={"layer": "PIPE_MAIN", "lineweight": 35}
        )
        
        # 5. Đáy giếng (bottom cap)
        self.msp.add_line(
            (casing_left, oy - total_depth * s),
            (casing_right, oy - total_depth * s),
            dxfattribs={"layer": "PIPE_MAIN", "lineweight": 50}
        )
        
        # 6. Hatch vữa trám (grout)
        if grout_depth > 0.5:
            grout_points_left = [
                (borehole_left, oy - 0.3 * s),
                (casing_left, oy - 0.3 * s),
                (casing_left, oy - grout_depth * s),
                (borehole_left, oy - grout_depth * s),
            ]
            grout_points_right = [
                (casing_right, oy - 0.3 * s),
                (borehole_right, oy - 0.3 * s),
                (borehole_right, oy - grout_depth * s),
                (casing_right, oy - grout_depth * s),
            ]
            
            hatch_grout_l = self.msp.add_hatch(dxfattribs={"layer": "HATCH_CONCRETE"})
            hatch_grout_l.paths.add_polyline_path(grout_points_left, is_closed=True)
            hatch_grout_l.set_pattern_fill("AR-CONC", scale=0.005)
            
            hatch_grout_r = self.msp.add_hatch(dxfattribs={"layer": "HATCH_CONCRETE"})
            hatch_grout_r.paths.add_polyline_path(grout_points_right, is_closed=True)
            hatch_grout_r.set_pattern_fill("AR-CONC", scale=0.005)
        
        # 7. Hatch bentonite seal
        if bentonite_bottom > bentonite_top:
            bent_points_left = [
                (borehole_left, oy - bentonite_top * s),
                (casing_left, oy - bentonite_top * s),
                (casing_left, oy - bentonite_bottom * s),
                (borehole_left, oy - bentonite_bottom * s),
            ]
            bent_points_right = [
                (casing_right, oy - bentonite_top * s),
                (borehole_right, oy - bentonite_top * s),
                (borehole_right, oy - bentonite_bottom * s),
                (casing_right, oy - bentonite_bottom * s),
            ]
            
            hatch_bent_l = self.msp.add_hatch(color=8, dxfattribs={"layer": "HATCH_SOIL"})
            hatch_bent_l.paths.add_polyline_path(bent_points_left, is_closed=True)
            hatch_bent_l.set_pattern_fill("ANSI31", scale=0.01)
            
            hatch_bent_r = self.msp.add_hatch(color=8, dxfattribs={"layer": "HATCH_SOIL"})
            hatch_bent_r.paths.add_polyline_path(bent_points_right, is_closed=True)
            hatch_bent_r.set_pattern_fill("ANSI31", scale=0.01)
        
        # 8. Hatch sỏi lọc (gravel pack)
        gravel_points_left = [
            (borehole_left, oy - gravel_top * s),
            (casing_left, oy - gravel_top * s),
            (casing_left, oy - total_depth * s),
            (borehole_left, oy - total_depth * s),
        ]
        gravel_points_right = [
            (casing_right, oy - gravel_top * s),
            (borehole_right, oy - gravel_top * s),
            (borehole_right, oy - total_depth * s),
            (casing_right, oy - total_depth * s),
        ]
        
        hatch_gravel_l = self.msp.add_hatch(dxfattribs={"layer": "HATCH_SOIL"})
        hatch_gravel_l.paths.add_polyline_path(gravel_points_left, is_closed=True)
        hatch_gravel_l.set_pattern_fill("GRAVEL", scale=0.02)
        
        hatch_gravel_r = self.msp.add_hatch(dxfattribs={"layer": "HATCH_SOIL"})
        hatch_gravel_r.paths.add_polyline_path(gravel_points_right, is_closed=True)
        hatch_gravel_r.set_pattern_fill("GRAVEL", scale=0.02)
        
        # 9. Vẽ mặt đất
        ground_ext = 2 * s
        self.msp.add_line(
            (ox - ground_ext, oy), (borehole_left, oy),
            dxfattribs={"layer": "STR_FOUNDATION", "lineweight": 50}
        )
        self.msp.add_line(
            (borehole_right, oy), (ox + ground_ext, oy),
            dxfattribs={"layer": "STR_FOUNDATION", "lineweight": 50}
        )
        
        # Hatch đất mặt
        ground_hatch_left = [
            (ox - ground_ext, oy),
            (ox - ground_ext, oy + 0.2 * s),
            (borehole_left, oy + 0.2 * s),
            (borehole_left, oy),
        ]
        ground_hatch_right = [
            (borehole_right, oy),
            (borehole_right, oy + 0.2 * s),
            (ox + ground_ext, oy + 0.2 * s),
            (ox + ground_ext, oy),
        ]
        
        hatch_ground_l = self.msp.add_hatch(color=33, dxfattribs={"layer": "HATCH_SOIL"})
        hatch_ground_l.paths.add_polyline_path(ground_hatch_left, is_closed=True)
        hatch_ground_l.set_pattern_fill("EARTH", scale=0.05)
        
        hatch_ground_r = self.msp.add_hatch(color=33, dxfattribs={"layer": "HATCH_SOIL"})
        hatch_ground_r.paths.add_polyline_path(ground_hatch_right, is_closed=True)
        hatch_ground_r.set_pattern_fill("EARTH", scale=0.05)
        
        # 10. Thêm kích thước và ghi chú
        dim_offset = borehole_r * s + 0.5 * s
        
        # Kích thước tổng chiều sâu
        self.msp.add_linear_dim(
            base=(ox + dim_offset + 0.3 * s, oy - total_depth * s / 2),
            p1=(ox + dim_offset, oy),
            p2=(ox + dim_offset, oy - total_depth * s),
            angle=90,
            override={"dimtxt": 0.15 * s}
        ).render()
        
        # Ghi chú các lớp
        annotations = [
            (oy + protective_height * s / 2, "Ống bảo vệ"),
            (oy - grout_depth * s / 2, "Vữa trám"),
            (oy - (bentonite_top + bentonite_bottom) * s / 2, "Bentonite"),
            (oy - (screen_top + screen_bottom) * s / 2, "Ống lọc"),
            (oy - (gravel_top + total_depth) * s / 2, "Sỏi lọc"),
        ]
        
        for y_pos, text in annotations:
            self.msp.add_text(
                text,
                dxfattribs={"layer": "TEXT_NOTE", "height": 0.12 * s}
            ).set_placement(
                (ox - dim_offset - 0.2 * s, y_pos),
                align=TextEntityAlignment.MIDDLE_RIGHT
            )
        
        # 11. Đường tâm
        self.msp.add_line(
            (ox, oy + protective_height * s + 0.3 * s),
            (ox, oy - total_depth * s - 0.3 * s),
            dxfattribs={"layer": "CENTER", "linetype": "CENTER"}
        )
        
        # 12. Thông số kỹ thuật
        info_x = ox + ground_ext + 0.5 * s
        info_y = oy
        info_texts = [
            f"THÔNG SỐ KỸ THUẬT:",
            f"Tổng chiều sâu: {total_depth} m",
            f"ĐK ống chống: Ø{casing_diameter} mm",
            f"ĐK lỗ khoan: Ø{borehole_diameter} mm",
            f"Ống lọc: {screen_top}-{screen_bottom} m",
            f"Cao độ mặt đất: {ground_level:+.2f} m",
        ]
        
        for i, text in enumerate(info_texts):
            self.msp.add_text(
                text,
                dxfattribs={
                    "layer": "TEXT_NOTE",
                    "height": 0.12 * s if i > 0 else 0.15 * s
                }
            ).set_placement(
                (info_x, info_y - i * 0.25 * s),
                align=TextEntityAlignment.TOP_LEFT
            )
    
    def draw_well_plan(
        self,
        casing_diameter: float,
        borehole_diameter: float,
        protective_diameter: float = None,
        origin: Tuple[float, float] = (0, 0),
        scale: float = 1.0
    ) -> None:
        """
        Vẽ mặt bằng giếng quan trắc
        
        Args:
            casing_diameter: Đường kính ống chống (mm)
            borehole_diameter: Đường kính lỗ khoan (mm)
            protective_diameter: Đường kính ống bảo vệ (mm)
            origin: Gốc tọa độ
            scale: Tỷ lệ
        """
        self._ensure_drawing()
        
        ox, oy = origin
        s = scale
        
        if protective_diameter is None:
            protective_diameter = casing_diameter + 100
        
        # Chuyển đổi mm sang m
        casing_r = casing_diameter / 1000 / 2 * s
        borehole_r = borehole_diameter / 1000 / 2 * s
        protective_r = protective_diameter / 1000 / 2 * s
        
        # 1. Vẽ lỗ khoan (đường nét đứt)
        self.msp.add_circle(
            (ox, oy), borehole_r,
            dxfattribs={"layer": "HATCH_SOIL", "linetype": "DASHED"}
        )
        
        # 2. Vẽ ống bảo vệ
        self.msp.add_circle(
            (ox, oy), protective_r,
            dxfattribs={"layer": "STR_WALL", "lineweight": 50}
        )
        
        # 3. Vẽ ống chống
        self.msp.add_circle(
            (ox, oy), casing_r,
            dxfattribs={"layer": "PIPE_MAIN", "lineweight": 35}
        )
        
        # 4. Vẽ đường tâm
        cross_size = borehole_r + 0.1 * s
        self.msp.add_line(
            (ox - cross_size, oy), (ox + cross_size, oy),
            dxfattribs={"layer": "CENTER", "linetype": "CENTER"}
        )
        self.msp.add_line(
            (ox, oy - cross_size), (ox, oy + cross_size),
            dxfattribs={"layer": "CENTER", "linetype": "CENTER"}
        )
        
        # 5. Ghi chú đường kính
        self.msp.add_text(
            f"Ø{casing_diameter}",
            dxfattribs={"layer": "TEXT_NOTE", "height": 0.1 * s}
        ).set_placement(
            (ox, oy - casing_r - 0.1 * s),
            align=TextEntityAlignment.TOP_CENTER
        )
    
    def save(self, filename: str) -> str:
        """Lưu file DXF"""
        if not filename.endswith('.dxf'):
            filename += '.dxf'
        
        filepath = os.path.join(self.output_dir, filename)
        self.doc.saveas(filepath)
        
        return filepath
