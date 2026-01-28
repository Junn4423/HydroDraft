"""
CAD Standards - Hệ thống tiêu chuẩn CAD chuyên nghiệp

SPRINT 3: PROFESSIONAL CAD
Tiêu chuẩn theo TCVN và ISO:
- Layer standards
- Dimension styles (ISO/TCVN)
- Text styles
- Line types & weights
- Scale management

Tiêu chuẩn áp dụng:
- TCVN 8-1:2002 - Tiêu chuẩn trình bày bản vẽ
- TCVN 8-24:2002 - Kiểu chữ
- ISO 128 - Technical drawings
- ISO 5457 - Sizes and layout of drawing sheets
"""

import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import math


class DrawingScale(Enum):
    """Tỷ lệ bản vẽ tiêu chuẩn"""
    SCALE_1_1 = (1, 1, "1:1")
    SCALE_1_2 = (1, 2, "1:2")
    SCALE_1_5 = (1, 5, "1:5")
    SCALE_1_10 = (1, 10, "1:10")
    SCALE_1_20 = (1, 20, "1:20")
    SCALE_1_25 = (1, 25, "1:25")
    SCALE_1_50 = (1, 50, "1:50")
    SCALE_1_100 = (1, 100, "1:100")
    SCALE_1_200 = (1, 200, "1:200")
    SCALE_1_250 = (1, 250, "1:250")
    SCALE_1_500 = (1, 500, "1:500")
    SCALE_1_1000 = (1, 1000, "1:1000")
    
    def __init__(self, numerator: int, denominator: int, text: str):
        self.numerator = numerator
        self.denominator = denominator
        self.text = text
    
    @property
    def factor(self) -> float:
        return self.numerator / self.denominator
    
    @classmethod
    def from_ratio(cls, ratio: float) -> 'DrawingScale':
        """Lấy tỷ lệ gần nhất"""
        scales = list(cls)
        return min(scales, key=lambda s: abs(s.factor - ratio))


@dataclass
class LayerDefinition:
    """Định nghĩa layer"""
    name: str
    color: int
    lineweight: int  # In 1/100 mm
    linetype: str = "Continuous"
    plot: bool = True
    description: str = ""


@dataclass
class DimStyleDefinition:
    """Định nghĩa DimStyle"""
    name: str
    text_height: float
    arrow_size: float
    extension_offset: float
    extension_overshoot: float
    dim_line_gap: float
    tick_size: float
    decimal_places: int
    unit_scale: float
    prefix: str = ""
    suffix: str = ""


@dataclass
class TextStyleDefinition:
    """Định nghĩa TextStyle"""
    name: str
    font: str
    height: float
    width_factor: float = 1.0
    oblique_angle: float = 0.0


class CADStandards:
    """
    Quản lý tiêu chuẩn CAD
    
    Bao gồm:
    - 40+ layer tiêu chuẩn
    - 10+ DimStyle cho các tỷ lệ khác nhau
    - 5+ TextStyle
    - LineTypes và LineWeights
    """
    
    # ==========================================
    # LAYER STANDARDS (TCVN 8-1:2002 based)
    # ==========================================
    
    LAYER_DEFINITIONS: List[LayerDefinition] = [
        # Structural layers
        LayerDefinition("STR_WALL", 3, 50, "Continuous", True, "Tường/Thành"),
        LayerDefinition("STR_FOUNDATION", 2, 50, "Continuous", True, "Móng"),
        LayerDefinition("STR_SLAB", 4, 35, "Continuous", True, "Sàn/Bản"),
        LayerDefinition("STR_COLUMN", 3, 70, "Continuous", True, "Cột"),
        LayerDefinition("STR_BEAM", 3, 50, "Continuous", True, "Dầm"),
        LayerDefinition("STR_REBAR", 1, 25, "Continuous", True, "Cốt thép"),
        LayerDefinition("STR_REBAR_SECTION", 1, 35, "Continuous", True, "Mặt cắt thép"),
        LayerDefinition("STR_DETAIL", 7, 25, "Continuous", True, "Chi tiết KC"),
        
        # Pipe layers
        LayerDefinition("PIPE_MAIN", 1, 50, "Continuous", True, "Ống chính"),
        LayerDefinition("PIPE_BRANCH", 6, 35, "Continuous", True, "Ống nhánh"),
        LayerDefinition("PIPE_GRAVITY", 5, 50, "Continuous", True, "Ống tự chảy"),
        LayerDefinition("PIPE_PRESSURE", 1, 50, "Continuous", True, "Ống áp lực"),
        LayerDefinition("PIPE_SLUDGE", 33, 50, "Continuous", True, "Ống bùn"),
        LayerDefinition("PIPE_HIDDEN", 8, 25, "HIDDEN", True, "Ống khuất"),
        
        # Equipment layers
        LayerDefinition("EQUIP_VALVE", 1, 35, "Continuous", True, "Van"),
        LayerDefinition("EQUIP_PUMP", 3, 35, "Continuous", True, "Bơm"),
        LayerDefinition("EQUIP_INST", 6, 25, "Continuous", True, "Thiết bị đo"),
        LayerDefinition("EQUIP_OTHER", 4, 35, "Continuous", True, "Thiết bị khác"),
        
        # Annotation layers
        LayerDefinition("ANNO_DIM", 7, 18, "Continuous", True, "Kích thước"),
        LayerDefinition("ANNO_TEXT", 7, 18, "Continuous", True, "Văn bản"),
        LayerDefinition("ANNO_LEADER", 7, 18, "Continuous", True, "Leader/Ghi chú"),
        LayerDefinition("ANNO_GRID", 8, 25, "CENTER", True, "Lưới trục"),
        LayerDefinition("ANNO_ELEV", 7, 18, "Continuous", True, "Cao độ"),
        LayerDefinition("ANNO_TITLE", 7, 35, "Continuous", True, "Tiêu đề"),
        
        # Special layers
        LayerDefinition("CENTER", 1, 18, "CENTER", True, "Đường tâm"),
        LayerDefinition("HIDDEN", 8, 18, "HIDDEN", True, "Nét khuất"),
        LayerDefinition("PHANTOM", 6, 18, "PHANTOM", True, "Nét ảo"),
        LayerDefinition("BOUNDARY", 7, 70, "Continuous", True, "Đường biên"),
        
        # Hatch layers
        LayerDefinition("HATCH_CONCRETE", 8, 0, "Continuous", True, "Hatch bê tông"),
        LayerDefinition("HATCH_SOIL", 33, 0, "Continuous", True, "Hatch đất"),
        LayerDefinition("HATCH_GRAVEL", 43, 0, "Continuous", True, "Hatch sỏi"),
        LayerDefinition("HATCH_WATER", 5, 0, "Continuous", True, "Hatch nước"),
        LayerDefinition("HATCH_STEEL", 1, 0, "Continuous", True, "Hatch thép"),
        
        # Water levels
        LayerDefinition("WATER_LEVEL", 5, 25, "DASHED", True, "Mực nước"),
        LayerDefinition("WATER_HWL", 5, 35, "CONTINUOUS", True, "Mực nước cao"),
        LayerDefinition("WATER_LWL", 5, 25, "DASHED", True, "Mực nước thấp"),
        
        # Title block
        LayerDefinition("TITLEBLOCK", 7, 50, "Continuous", True, "Khung tên"),
        LayerDefinition("BORDER", 7, 70, "Continuous", True, "Khung viền"),
        
        # Non-plot layers
        LayerDefinition("DEFPOINTS", 7, 0, "Continuous", False, "Định nghĩa điểm"),
        LayerDefinition("VIEWPORT", 7, 0, "Continuous", False, "Viewport"),
        LayerDefinition("XREF", 8, 18, "Continuous", True, "Tham chiếu"),
    ]
    
    # ==========================================
    # DIMSTYLE DEFINITIONS (ISO 129 based)
    # ==========================================
    
    DIMSTYLE_DEFINITIONS: Dict[str, DimStyleDefinition] = {
        # Theo tỷ lệ bản vẽ
        "DIM_1_1": DimStyleDefinition(
            "DIM_1_1", 2.5, 2.5, 0.625, 1.25, 0.625, 0.0, 0, 1.0
        ),
        "DIM_1_10": DimStyleDefinition(
            "DIM_1_10", 2.5, 2.5, 0.625, 1.25, 0.625, 0.0, 2, 1.0
        ),
        "DIM_1_20": DimStyleDefinition(
            "DIM_1_20", 2.5, 2.5, 0.625, 1.25, 0.625, 0.0, 2, 1.0
        ),
        "DIM_1_25": DimStyleDefinition(
            "DIM_1_25", 2.5, 2.5, 0.625, 1.25, 0.625, 0.0, 2, 1.0
        ),
        "DIM_1_50": DimStyleDefinition(
            "DIM_1_50", 2.5, 2.5, 0.625, 1.25, 0.625, 0.0, 2, 1.0
        ),
        "DIM_1_100": DimStyleDefinition(
            "DIM_1_100", 2.5, 2.5, 0.625, 1.25, 0.625, 0.0, 2, 1.0
        ),
        "DIM_1_200": DimStyleDefinition(
            "DIM_1_200", 2.5, 2.5, 0.625, 1.25, 0.625, 0.0, 2, 1.0
        ),
        "DIM_1_500": DimStyleDefinition(
            "DIM_1_500", 2.5, 2.5, 0.625, 1.25, 0.625, 0.0, 1, 1.0
        ),
        
        # Chuyên dụng
        "DIM_ELEVATION": DimStyleDefinition(
            "DIM_ELEVATION", 2.0, 1.5, 0.5, 1.0, 0.5, 0.0, 3, 1.0, prefix="±"
        ),
        "DIM_REBAR": DimStyleDefinition(
            "DIM_REBAR", 2.0, 2.0, 0.5, 1.0, 0.5, 0.0, 0, 1.0, prefix="Ø"
        ),
        "DIM_DIAMETER": DimStyleDefinition(
            "DIM_DIAMETER", 2.5, 2.5, 0.625, 1.25, 0.625, 0.0, 0, 1.0, prefix="DN"
        ),
    }
    
    # ==========================================
    # TEXTSTYLE DEFINITIONS (TCVN 8-24:2002)
    # ==========================================
    
    TEXTSTYLE_DEFINITIONS: List[TextStyleDefinition] = [
        TextStyleDefinition("STANDARD_VN", "Arial", 0),
        TextStyleDefinition("ENGINEERING", "romans.shx", 0, 0.8, 0),
        TextStyleDefinition("TITLE", "Arial Black", 0, 1.0, 0),
        TextStyleDefinition("NOTE", "Arial", 0, 0.9, 0),
        TextStyleDefinition("DIMENSION", "Arial Narrow", 0, 0.9, 0),
        TextStyleDefinition("REBAR", "Arial", 0, 1.0, 0),
        TextStyleDefinition("ITALIC", "Arial", 0, 1.0, 15),
    ]
    
    # ==========================================
    # LINEWEIGHT STANDARDS (mm)
    # ==========================================
    
    LINEWEIGHTS = {
        "EXTRA_FINE": 13,    # 0.13 mm
        "FINE": 18,          # 0.18 mm  
        "MEDIUM": 25,        # 0.25 mm
        "WIDE": 35,          # 0.35 mm
        "EXTRA_WIDE": 50,    # 0.50 mm
        "BORDER": 70,        # 0.70 mm
        "SECTION_CUT": 100,  # 1.00 mm
    }
    
    # ==========================================
    # LINETYPE DEFINITIONS
    # ==========================================
    
    LINETYPES = {
        "CENTER": "CENTER",
        "CENTER2": "CENTER2",
        "CENTERX2": "CENTERX2",
        "HIDDEN": "HIDDEN",
        "HIDDEN2": "HIDDEN2",
        "HIDDENX2": "HIDDENX2",
        "DASHED": "DASHED",
        "DASHDOT": "DASHDOT",
        "PHANTOM": "PHANTOM",
        "DOT": "DOT",
        "DIVIDE": "DIVIDE",
        "BORDER": "BORDER"
    }
    
    def __init__(self, doc):
        self.doc = doc
        self.msp = doc.modelspace()
    
    def setup_all_standards(self):
        """Thiết lập toàn bộ tiêu chuẩn"""
        self._setup_units()
        self._setup_linetypes()
        self._setup_layers()
        self._setup_textstyles()
        self._setup_dimstyles()
    
    def _setup_units(self):
        """Thiết lập đơn vị"""
        self.doc.header['$INSUNITS'] = units.M
        self.doc.header['$LUNITS'] = 2  # Decimal
        self.doc.header['$LUPREC'] = 3  # 3 decimal places
        self.doc.header['$AUNITS'] = 0  # Degrees
        self.doc.header['$AUPREC'] = 2  # 2 decimal places
    
    def _setup_linetypes(self):
        """Tải các linetype"""
        try:
            self.doc.linetypes.load_linetypes()
        except:
            pass
        
        # Đảm bảo các linetype cơ bản tồn tại
        for lt_name in self.LINETYPES.values():
            try:
                if lt_name not in self.doc.linetypes:
                    if lt_name == "CENTER":
                        self.doc.linetypes.add(
                            lt_name, 
                            pattern=[1.25, -0.25, 0.25, -0.25],
                            description="Center ____ _ ____ _ ____ _"
                        )
                    elif lt_name == "HIDDEN":
                        self.doc.linetypes.add(
                            lt_name,
                            pattern=[0.25, -0.125],
                            description="Hidden __ __ __ __"
                        )
                    elif lt_name == "DASHED":
                        self.doc.linetypes.add(
                            lt_name,
                            pattern=[0.5, -0.25],
                            description="Dashed _ _ _ _"
                        )
                    elif lt_name == "PHANTOM":
                        self.doc.linetypes.add(
                            lt_name,
                            pattern=[1.25, -0.25, 0.25, -0.25, 0.25, -0.25],
                            description="Phantom _____ _ _ _____ _ _"
                        )
            except:
                pass
    
    def _setup_layers(self):
        """Tạo các layer"""
        for layer_def in self.LAYER_DEFINITIONS:
            if layer_def.name not in self.doc.layers:
                layer = self.doc.layers.add(
                    layer_def.name,
                    color=layer_def.color,
                    lineweight=layer_def.lineweight,
                    linetype=layer_def.linetype
                )
                layer.off_for_plotting = not layer_def.plot
    
    def _setup_textstyles(self):
        """Tạo các text style"""
        for style_def in self.TEXTSTYLE_DEFINITIONS:
            if style_def.name not in self.doc.styles:
                style = self.doc.styles.add(
                    style_def.name,
                    font=style_def.font
                )
                if style_def.height > 0:
                    style.dxf.height = style_def.height
                style.dxf.width = style_def.width_factor
                style.dxf.oblique = style_def.oblique_angle
    
    def _setup_dimstyles(self):
        """Tạo các dimension style"""
        for name, dim_def in self.DIMSTYLE_DEFINITIONS.items():
            if name not in self.doc.dimstyles:
                dimstyle = self.doc.dimstyles.new(name)
                
                # Text
                dimstyle.dxf.dimtxt = dim_def.text_height
                dimstyle.dxf.dimtxsty = "DIMENSION"
                
                # Arrows
                dimstyle.dxf.dimasz = dim_def.arrow_size
                dimstyle.dxf.dimtsz = dim_def.tick_size
                
                # Extension lines
                dimstyle.dxf.dimexo = dim_def.extension_offset
                dimstyle.dxf.dimexe = dim_def.extension_overshoot
                
                # Dimension lines
                dimstyle.dxf.dimgap = dim_def.dim_line_gap
                
                # Units & precision
                dimstyle.dxf.dimdec = dim_def.decimal_places
                dimstyle.dxf.dimlfac = dim_def.unit_scale
                
                # Prefix/Suffix
                if dim_def.prefix:
                    dimstyle.dxf.dimpost = dim_def.prefix + "<>"
                if dim_def.suffix:
                    dimstyle.dxf.dimpost = "<>" + dim_def.suffix
                
                # Colors
                dimstyle.dxf.dimclrd = 7  # Dimension line
                dimstyle.dxf.dimclre = 7  # Extension line
                dimstyle.dxf.dimclrt = 7  # Text
    
    def get_scale_factor(self, scale: DrawingScale) -> Tuple[float, float]:
        """
        Lấy hệ số tỷ lệ cho text và dim
        
        Returns:
            (text_scale, dim_scale)
        """
        base_text_height = 2.5  # mm on paper
        return (
            base_text_height * scale.denominator / 1000,  # Convert to meters
            scale.factor
        )
    
    def get_dimstyle_for_scale(self, scale: DrawingScale) -> str:
        """Lấy DimStyle phù hợp với tỷ lệ"""
        scale_name = f"DIM_1_{scale.denominator}"
        if scale_name in self.DIMSTYLE_DEFINITIONS:
            return scale_name
        return "DIM_1_100"  # Default
    
    def get_text_height(self, scale: DrawingScale, purpose: str = "note") -> float:
        """
        Lấy chiều cao chữ theo tỷ lệ
        
        Args:
            scale: Tỷ lệ bản vẽ
            purpose: "title" | "subtitle" | "note" | "dimension"
        """
        # Height in mm on paper
        heights = {
            "title": 7.0,
            "subtitle": 5.0,
            "note": 3.5,
            "dimension": 2.5,
            "small": 2.0
        }
        
        h_paper = heights.get(purpose, 3.5)
        return h_paper * scale.denominator / 1000  # Convert to model units (m)


class CADDimensionSystem:
    """
    Hệ thống ghi kích thước chuyên nghiệp
    
    Features:
    - Linear dimensions
    - Aligned dimensions
    - Angular dimensions
    - Radius/Diameter
    - Ordinate dimensions
    - Leaders with text
    """
    
    def __init__(self, doc, scale: DrawingScale = DrawingScale.SCALE_1_100):
        self.doc = doc
        self.msp = doc.modelspace()
        self.scale = scale
        self.standards = CADStandards(doc)
        
        # Đảm bảo text style DIMENSION tồn tại
        if "DIMENSION" not in self.doc.styles:
            self.doc.styles.add("DIMENSION", font="Arial")
        
        # Đảm bảo dimstyle tồn tại
        self.dimstyle = self.standards.get_dimstyle_for_scale(scale)
        if self.dimstyle not in self.doc.dimstyles:
            # Tạo dimstyle cơ bản nếu chưa tồn tại
            dimstyle = self.doc.dimstyles.new(self.dimstyle)
            dimstyle.dxf.dimtxt = 2.5
            dimstyle.dxf.dimtxsty = "DIMENSION"
            dimstyle.dxf.dimasz = 2.5
            dimstyle.dxf.dimexo = 0.625
            dimstyle.dxf.dimexe = 1.25
            dimstyle.dxf.dimgap = 0.625
    
    def add_linear_dim(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        offset: float = None,
        text_override: str = None,
        layer: str = "ANNO_DIM"
    ):
        """
        Thêm kích thước tuyến tính
        
        Args:
            p1, p2: Hai điểm đo
            offset: Khoảng cách đường kích thước (auto nếu None)
            text_override: Ghi đè text
        """
        if offset is None:
            offset = 0.5 * self.scale.denominator / 100  # Auto offset
        
        # Xác định hướng
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        
        if abs(dx) > abs(dy):
            # Horizontal
            base = ((p1[0] + p2[0]) / 2, p1[1] + offset)
            angle = 0
        else:
            # Vertical
            base = (p1[0] + offset, (p1[1] + p2[1]) / 2)
            angle = 90
        
        override = {"dimstyle": self.dimstyle}
        
        dim = self.msp.add_linear_dim(
            base=base,
            p1=p1,
            p2=p2,
            angle=angle,
            text=text_override if text_override else "<>",
            override=override,
            dxfattribs={"layer": layer}
        )
        dim.render()
        return dim
    
    def add_aligned_dim(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        offset: float = None,
        text_override: str = None,
        layer: str = "ANNO_DIM"
    ):
        """Thêm kích thước căn theo đường"""
        if offset is None:
            offset = 0.3 * self.scale.denominator / 100
        
        # Calculate perpendicular offset point
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.sqrt(dx*dx + dy*dy)
        
        if length > 0:
            nx = -dy / length * offset
            ny = dx / length * offset
        else:
            nx, ny = 0, offset
        
        mid_x = (p1[0] + p2[0]) / 2 + nx
        mid_y = (p1[1] + p2[1]) / 2 + ny
        
        override = {"dimstyle": self.dimstyle}
        
        dim = self.msp.add_aligned_dim(
            p1=p1,
            p2=p2,
            distance=offset,
            text=text_override if text_override else "<>",
            override=override,
            dxfattribs={"layer": layer}
        )
        dim.render()
        return dim
    
    def add_diameter_dim(
        self,
        center: Tuple[float, float],
        radius: float,
        angle: float = 45,
        text_override: str = None,
        layer: str = "ANNO_DIM"
    ):
        """Thêm kích thước đường kính"""
        override = {"dimstyle": self.dimstyle}
        
        dim = self.msp.add_diameter_dim(
            center=center,
            radius=radius,
            angle=angle,
            text=text_override if text_override else "<>",
            override=override,
            dxfattribs={"layer": layer}
        )
        dim.render()
        return dim
    
    def add_radius_dim(
        self,
        center: Tuple[float, float],
        radius: float,
        angle: float = 45,
        text_override: str = None,
        layer: str = "ANNO_DIM"
    ):
        """Thêm kích thước bán kính"""
        override = {"dimstyle": self.dimstyle}
        
        dim = self.msp.add_radius_dim(
            center=center,
            radius=radius,
            angle=angle,
            text=text_override if text_override else "<>",
            override=override,
            dxfattribs={"layer": layer}
        )
        dim.render()
        return dim
    
    def add_angular_dim(
        self,
        center: Tuple[float, float],
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        offset: float = None,
        layer: str = "ANNO_DIM"
    ):
        """Thêm kích thước góc"""
        if offset is None:
            r1 = math.sqrt((p1[0]-center[0])**2 + (p1[1]-center[1])**2)
            offset = r1 * 1.5
        
        dim = self.msp.add_angular_dim_cra(
            center=center,
            radius=offset,
            start_angle=math.degrees(math.atan2(p1[1]-center[1], p1[0]-center[0])),
            end_angle=math.degrees(math.atan2(p2[1]-center[1], p2[0]-center[0])),
            override={"dimstyle": self.dimstyle},
            dxfattribs={"layer": layer}
        )
        dim.render()
        return dim
    
    def add_leader(
        self,
        points: List[Tuple[float, float]],
        text: str,
        layer: str = "ANNO_LEADER"
    ):
        """
        Thêm leader với ghi chú
        
        Args:
            points: Danh sách điểm của leader [start, ..., end]
            text: Nội dung ghi chú
        """
        # Vẽ đường leader
        self.msp.add_lwpolyline(
            points,
            dxfattribs={"layer": layer}
        )
        
        # Thêm mũi tên ở điểm đầu
        if len(points) >= 2:
            p0, p1 = points[0], points[1]
            dx = p1[0] - p0[0]
            dy = p1[1] - p0[1]
            length = math.sqrt(dx*dx + dy*dy)
            
            if length > 0:
                arrow_size = 0.15 * self.scale.denominator / 100
                ux, uy = dx/length, dy/length
                # Perpendicular
                px, py = -uy, ux
                
                arrow_points = [
                    p0,
                    (p0[0] + arrow_size*ux + arrow_size*0.3*px,
                     p0[1] + arrow_size*uy + arrow_size*0.3*py),
                    (p0[0] + arrow_size*ux - arrow_size*0.3*px,
                     p0[1] + arrow_size*uy - arrow_size*0.3*py),
                    p0
                ]
                
                hatch = self.msp.add_hatch(dxfattribs={"layer": layer})
                hatch.paths.add_polyline_path(arrow_points, is_closed=True)
                hatch.set_solid_fill()
        
        # Thêm text
        text_height = self.standards.get_text_height(self.scale, "note")
        last_point = points[-1]
        
        self.msp.add_text(
            text,
            dxfattribs={
                "layer": "ANNO_TEXT",
                "height": text_height,
                "style": "NOTE"
            }
        ).set_placement(
            (last_point[0] + 0.1 * self.scale.denominator / 100, last_point[1]),
            align=TextEntityAlignment.LEFT
        )
    
    def add_elevation_mark(
        self,
        position: Tuple[float, float],
        elevation: float,
        layer: str = "ANNO_ELEV"
    ):
        """Thêm ký hiệu cao độ"""
        s = self.scale.denominator / 100
        
        # Tam giác
        tri_size = 0.15 * s
        points = [
            position,
            (position[0] - tri_size/2, position[1] - tri_size),
            (position[0] + tri_size/2, position[1] - tri_size),
            position
        ]
        self.msp.add_lwpolyline(points, close=True, dxfattribs={"layer": layer})
        
        # Text cao độ
        text_height = self.standards.get_text_height(self.scale, "dimension")
        
        if elevation >= 0:
            text = f"+{elevation:.3f}"
        else:
            text = f"{elevation:.3f}"
        
        self.msp.add_text(
            text,
            dxfattribs={
                "layer": "ANNO_TEXT",
                "height": text_height,
                "style": "DIMENSION"
            }
        ).set_placement(
            (position[0] + tri_size, position[1] - tri_size/2),
            align=TextEntityAlignment.LEFT
        )
    
    def add_grid_axis(
        self,
        position: Tuple[float, float],
        axis_name: str,
        direction: str = "horizontal",
        layer: str = "ANNO_GRID"
    ):
        """
        Thêm ký hiệu trục
        
        Args:
            position: Vị trí bubble
            axis_name: Tên trục (A, B, 1, 2, ...)
            direction: "horizontal" | "vertical"
        """
        s = self.scale.denominator / 100
        r = 0.3 * s
        
        # Vòng tròn
        self.msp.add_circle(position, r, dxfattribs={"layer": layer, "lineweight": 35})
        
        # Tên trục
        text_height = 0.25 * s
        self.msp.add_text(
            axis_name,
            dxfattribs={
                "layer": "ANNO_TEXT",
                "height": text_height,
                "style": "TITLE"
            }
        ).set_placement(position, align=TextEntityAlignment.MIDDLE_CENTER)
    
    def add_section_mark(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        section_name: str,
        sheet_ref: str = None,
        layer: str = "ANNO_DIM"
    ):
        """
        Thêm ký hiệu mặt cắt
        
        Args:
            start, end: Điểm đầu và cuối đường cắt
            section_name: Tên mặt cắt (A, B, ...)
            sheet_ref: Tham chiếu sheet (optional)
        """
        s = self.scale.denominator / 100
        r = 0.25 * s
        
        # Đường cắt (CENTER linetype)
        self.msp.add_line(start, end, dxfattribs={
            "layer": layer,
            "linetype": "DASHDOT",
            "lineweight": 35
        })
        
        # Bubble đầu
        self.msp.add_circle(start, r, dxfattribs={"layer": layer, "lineweight": 25})
        
        # Fill nửa hướng nhìn
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        angle = math.atan2(dy, dx)
        
        # Half circle fill
        half_points = []
        for i in range(11):
            a = angle + math.pi/2 + i * math.pi / 10
            half_points.append((start[0] + r * math.cos(a), start[1] + r * math.sin(a)))
        half_points.append(start)
        
        hatch = self.msp.add_hatch(dxfattribs={"layer": layer})
        hatch.paths.add_polyline_path(half_points, is_closed=True)
        hatch.set_solid_fill()
        
        # Text
        text_height = 0.2 * s
        self.msp.add_text(
            section_name,
            dxfattribs={"layer": "ANNO_TEXT", "height": text_height, "style": "TITLE"}
        ).set_placement(start, align=TextEntityAlignment.MIDDLE_CENTER)
        
        # Bubble cuối
        self.msp.add_circle(end, r, dxfattribs={"layer": layer, "lineweight": 25})
        
        # Fill ngược lại
        half_points_end = []
        for i in range(11):
            a = angle - math.pi/2 + i * math.pi / 10
            half_points_end.append((end[0] + r * math.cos(a), end[1] + r * math.sin(a)))
        half_points_end.append(end)
        
        hatch2 = self.msp.add_hatch(dxfattribs={"layer": layer})
        hatch2.paths.add_polyline_path(half_points_end, is_closed=True)
        hatch2.set_solid_fill()
        
        self.msp.add_text(
            section_name,
            dxfattribs={"layer": "ANNO_TEXT", "height": text_height, "style": "TITLE"}
        ).set_placement(end, align=TextEntityAlignment.MIDDLE_CENTER)


def setup_cad_standards(doc) -> CADStandards:
    """Khởi tạo và áp dụng tiêu chuẩn CAD"""
    standards = CADStandards(doc)
    standards.setup_all_standards()
    return standards
