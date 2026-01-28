"""
Professional DXF Generator V2 - Tạo bản vẽ CAD chuyên nghiệp

SPRINT 3: PROFESSIONAL CAD
Generator V2 tích hợp:
- Block library
- CAD standards (layers, styles, dims)
- Structural detailing (rebar)
- Validation engine
- Export guard

Output: Construction-ready DWG/DXF
"""

import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import os
import math
import uuid

from generators.cad_blocks import CADBlockLibrary, BlockType, setup_block_library
from generators.cad_standards import (
    CADStandards, CADDimensionSystem, DrawingScale, 
    setup_cad_standards
)
from generators.structural_detailing import (
    StructuralDetailer, RebarSpec, RebarGrade,
    create_structural_detailer
)
from generators.cad_validation import (
    CADValidationEngine, DrawingExportGuard, 
    ValidationResult, validate_drawing
)


@dataclass
class DrawingMetadata:
    """Metadata bản vẽ"""
    project_name: str
    drawing_title: str
    drawing_number: str
    scale: DrawingScale
    drawn_by: str
    checked_by: str = ""
    approved_by: str = ""
    revision: str = "A"
    date: str = None
    
    def __post_init__(self):
        if self.date is None:
            self.date = datetime.now().strftime("%d/%m/%Y")


@dataclass
class TankDrawingParams:
    """Tham số vẽ bể"""
    # Dimensions (m)
    length: float
    width: float
    water_depth: float
    total_depth: float
    wall_thickness: float
    bottom_thickness: float
    freeboard: float
    
    # Pipes (mm)
    inlet_diameter: int = 200
    outlet_diameter: int = 200
    
    # Reinforcement
    main_rebar_dia: int = 12
    main_rebar_spacing: int = 200
    dist_rebar_dia: int = 10
    dist_rebar_spacing: int = 250
    cover: float = 0.03
    
    # Levels (m)
    ground_level: float = 0.0
    bottom_level: float = None
    
    def __post_init__(self):
        if self.bottom_level is None:
            self.bottom_level = self.ground_level - self.total_depth - self.bottom_thickness


class ProfessionalDXFGenerator:
    """
    Generator bản vẽ CAD chuyên nghiệp
    
    Features:
    - Professional layers & styles
    - Block-based symbols
    - Reinforcement detailing
    - Proper dimensions & annotations
    - Validation before export
    """
    
    def __init__(self, output_dir: str = "./outputs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.doc = None
        self.msp = None
        self.standards = None
        self.blocks = None
        self.detailer = None
        self.dim_system = None
        self.metadata = None
        self.scale = DrawingScale.SCALE_1_100
    
    def create_new_drawing(
        self,
        metadata: DrawingMetadata = None,
        version: str = "R2018"
    ):
        """Tạo bản vẽ mới với đầy đủ tiêu chuẩn"""
        self.doc = ezdxf.new(version)
        self.doc.header['$INSUNITS'] = units.M
        self.msp = self.doc.modelspace()
        
        if metadata:
            self.metadata = metadata
            self.scale = metadata.scale
        else:
            self.scale = DrawingScale.SCALE_1_100
        
        # Setup standards
        self.standards = setup_cad_standards(self.doc)
        
        # Setup blocks
        self.blocks = setup_block_library(self.doc)
        
        # Setup detailer
        self.detailer = create_structural_detailer(
            self.doc, 
            scale=1.0 / self.scale.denominator
        )
        
        # Setup dimension system
        self.dim_system = CADDimensionSystem(self.doc, self.scale)
    
    def _ensure_drawing(self):
        """Đảm bảo bản vẽ đã được khởi tạo"""
        if self.doc is None:
            self.create_new_drawing()
    
    # ==========================================
    # TANK DRAWINGS
    # ==========================================
    
    def draw_tank_complete(
        self,
        params: TankDrawingParams,
        metadata: DrawingMetadata,
        include_plan: bool = True,
        include_section: bool = True,
        include_rebar: bool = True
    ) -> str:
        """
        Vẽ bản vẽ bể hoàn chỉnh
        
        Args:
            params: Tham số bể
            metadata: Metadata bản vẽ
            include_plan: Bao gồm mặt bằng
            include_section: Bao gồm mặt cắt
            include_rebar: Bao gồm chi tiết thép
        """
        self.create_new_drawing(metadata)
        
        s = self.scale.denominator / 100  # Scale factor for spacing
        
        # Layout positions
        plan_origin = (0, 0)
        section_origin = (
            params.length + params.wall_thickness * 2 + 5 * s,
            0
        )
        detail_origin = (0, -params.width - params.wall_thickness * 2 - 8 * s)
        
        # Draw views
        if include_plan:
            self._draw_tank_plan_professional(params, plan_origin)
        
        if include_section:
            self._draw_tank_section_professional(params, section_origin, include_rebar)
        
        # Title block
        self._add_title_block(metadata, (0, -15 * s))
        
        # Generate unique filename
        job_id = str(uuid.uuid4())[:8]
        filename = f"tank_{metadata.drawing_number}_{job_id}.dxf"
        
        return self._save_with_validation(filename, "tank")
    
    def _draw_tank_plan_professional(
        self,
        params: TankDrawingParams,
        origin: Tuple[float, float]
    ):
        """Vẽ mặt bằng bể chuyên nghiệp"""
        ox, oy = origin
        L = params.length
        W = params.width
        t = params.wall_thickness
        
        L_out = L + 2 * t
        W_out = W + 2 * t
        
        # 1. Concrete walls
        outer_points = [
            (ox, oy), (ox + L_out, oy),
            (ox + L_out, oy + W_out), (ox, oy + W_out), (ox, oy)
        ]
        self.msp.add_lwpolyline(
            outer_points, close=True,
            dxfattribs={"layer": "STR_WALL", "lineweight": 50}
        )
        
        inner_points = [
            (ox + t, oy + t), (ox + t + L, oy + t),
            (ox + t + L, oy + t + W), (ox + t, oy + t + W), (ox + t, oy + t)
        ]
        self.msp.add_lwpolyline(
            inner_points, close=True,
            dxfattribs={"layer": "STR_WALL", "lineweight": 35}
        )
        
        # 2. Hatch concrete
        hatch = self.msp.add_hatch(color=252, dxfattribs={"layer": "HATCH_CONCRETE"})
        hatch.paths.add_polyline_path(outer_points[:-1], is_closed=True)
        hatch.paths.add_polyline_path(inner_points[:-1], is_closed=True)
        hatch.set_pattern_fill("AR-CONC", scale=0.02)
        
        # 3. Center lines
        cx = ox + L_out / 2
        cy = oy + W_out / 2
        ext = 1.0  # Extension
        
        self.msp.add_line(
            (cx, oy - ext), (cx, oy + W_out + ext),
            dxfattribs={"layer": "CENTER", "linetype": "CENTER"}
        )
        self.msp.add_line(
            (ox - ext, cy), (ox + L_out + ext, cy),
            dxfattribs={"layer": "CENTER", "linetype": "CENTER"}
        )
        
        # 4. Inlet pipe with valve block
        inlet_x = ox
        inlet_y = cy
        inlet_r = params.inlet_diameter / 2000
        
        self.msp.add_circle(
            (inlet_x, inlet_y), inlet_r,
            dxfattribs={"layer": "PIPE_MAIN", "lineweight": 35}
        )
        
        # Insert valve block
        self.blocks.insert_valve(
            "gate",
            (inlet_x - 0.5, inlet_y),
            f"V-IN",
            params.inlet_diameter,
            scale=0.5,
            rotation=90
        )
        
        # 5. Outlet pipe
        outlet_x = ox + L_out
        outlet_y = cy
        outlet_r = params.outlet_diameter / 2000
        
        self.msp.add_circle(
            (outlet_x, outlet_y), outlet_r,
            dxfattribs={"layer": "PIPE_MAIN", "lineweight": 35}
        )
        
        self.blocks.insert_valve(
            "gate",
            (outlet_x + 0.5, outlet_y),
            f"V-OUT",
            params.outlet_diameter,
            scale=0.5,
            rotation=90
        )
        
        # 6. Dimensions
        offset = 0.8
        
        # Inner length
        self.dim_system.add_linear_dim(
            (ox + t, oy - offset),
            (ox + t + L, oy - offset),
            offset=-offset
        )
        
        # Outer length
        self.dim_system.add_linear_dim(
            (ox, oy - offset * 2),
            (ox + L_out, oy - offset * 2),
            offset=-offset * 2
        )
        
        # Inner width
        self.dim_system.add_linear_dim(
            (ox - offset, oy + t),
            (ox - offset, oy + t + W),
            offset=-offset
        )
        
        # Outer width
        self.dim_system.add_linear_dim(
            (ox - offset * 2, oy),
            (ox - offset * 2, oy + W_out),
            offset=-offset * 2
        )
        
        # Wall thickness
        self.dim_system.add_linear_dim(
            (ox, oy + W_out + offset),
            (ox + t, oy + W_out + offset),
            offset=offset,
            text_override=f"{t*1000:.0f}"
        )
        
        # 7. Grid axes
        self.dim_system.add_grid_axis((ox - 1.5, oy), "1", "vertical")
        self.dim_system.add_grid_axis((ox - 1.5, oy + W_out), "2", "vertical")
        self.dim_system.add_grid_axis((ox, oy - 1.5), "A", "horizontal")
        self.dim_system.add_grid_axis((ox + L_out, oy - 1.5), "B", "horizontal")
        
        # 8. Title
        text_height = self.standards.get_text_height(self.scale, "subtitle")
        self.msp.add_text(
            "MẶT BẰNG BỂ",
            dxfattribs={
                "layer": "ANNO_TITLE",
                "height": text_height,
                "style": "TITLE"
            }
        ).set_placement(
            (cx, oy + W_out + 2.5),
            align=TextEntityAlignment.BOTTOM_CENTER
        )
        
        # Scale notation
        note_height = self.standards.get_text_height(self.scale, "note")
        self.msp.add_text(
            f"TỶ LỆ {self.scale.text}",
            dxfattribs={
                "layer": "ANNO_TEXT",
                "height": note_height,
                "style": "NOTE"
            }
        ).set_placement(
            (cx, oy + W_out + 2.0),
            align=TextEntityAlignment.TOP_CENTER
        )
        
        # 9. Pipe annotations
        self.dim_system.add_leader(
            [(inlet_x - 0.3, inlet_y + inlet_r + 0.1),
             (inlet_x - 0.8, inlet_y + 0.5)],
            f"ỐNG VÀO DN{params.inlet_diameter}"
        )
        
        self.dim_system.add_leader(
            [(outlet_x + 0.3, outlet_y + outlet_r + 0.1),
             (outlet_x + 0.8, outlet_y + 0.5)],
            f"ỐNG RA DN{params.outlet_diameter}"
        )
        
        # 10. Section mark
        self.dim_system.add_section_mark(
            (ox - 0.3, cy),
            (ox + L_out + 0.3, cy),
            "A"
        )
    
    def _draw_tank_section_professional(
        self,
        params: TankDrawingParams,
        origin: Tuple[float, float],
        include_rebar: bool = True
    ):
        """Vẽ mặt cắt bể chuyên nghiệp với cốt thép"""
        ox, oy = origin
        L = params.length
        t = params.wall_thickness
        bt = params.bottom_thickness
        H = params.total_depth
        Hw = params.water_depth
        fb = params.freeboard
        
        L_out = L + 2 * t
        
        # 1. Left wall
        left_wall = [
            (ox, oy - bt), (ox + t, oy - bt),
            (ox + t, oy + H), (ox, oy + H), (ox, oy - bt)
        ]
        self.msp.add_lwpolyline(
            left_wall, close=True,
            dxfattribs={"layer": "STR_WALL", "lineweight": 50}
        )
        
        # 2. Right wall
        right_wall = [
            (ox + t + L, oy - bt), (ox + L_out, oy - bt),
            (ox + L_out, oy + H), (ox + t + L, oy + H), (ox + t + L, oy - bt)
        ]
        self.msp.add_lwpolyline(
            right_wall, close=True,
            dxfattribs={"layer": "STR_WALL", "lineweight": 50}
        )
        
        # 3. Bottom slab
        bottom = [
            (ox, oy - bt), (ox + L_out, oy - bt),
            (ox + L_out, oy), (ox, oy), (ox, oy - bt)
        ]
        self.msp.add_lwpolyline(
            bottom, close=True,
            dxfattribs={"layer": "STR_FOUNDATION", "lineweight": 50}
        )
        
        # 4. Hatch concrete
        for points in [left_wall, right_wall, bottom]:
            hatch = self.msp.add_hatch(color=252, dxfattribs={"layer": "HATCH_CONCRETE"})
            hatch.paths.add_polyline_path(points[:-1], is_closed=True)
            hatch.set_pattern_fill("AR-CONC", scale=0.015)
        
        # 5. Water level
        water_y = oy + Hw
        self.msp.add_line(
            (ox + t, water_y), (ox + t + L, water_y),
            dxfattribs={"layer": "WATER_LEVEL", "linetype": "DASHED", "lineweight": 25}
        )
        
        # Water hatch
        water_hatch = self.msp.add_hatch(color=5, dxfattribs={"layer": "HATCH_WATER"})
        water_hatch.paths.add_polyline_path([
            (ox + t, oy), (ox + t + L, oy),
            (ox + t + L, water_y), (ox + t, water_y)
        ], is_closed=True)
        water_hatch.set_pattern_fill("ANSI31", scale=0.03)
        
        # 6. Ground line
        ground_y = oy + H
        self.msp.add_line(
            (ox - 1, ground_y), (ox + L_out + 1, ground_y),
            dxfattribs={"layer": "STR_FOUNDATION", "lineweight": 70}
        )
        
        # Ground hatch
        gh = self.msp.add_hatch(color=33, dxfattribs={"layer": "HATCH_SOIL"})
        gh.paths.add_polyline_path([
            (ox - 1, ground_y), (ox + L_out + 1, ground_y),
            (ox + L_out + 1, ground_y + 0.15), (ox - 1, ground_y + 0.15)
        ], is_closed=True)
        gh.set_pattern_fill("EARTH", scale=0.05)
        
        # 7. Reinforcement (if enabled)
        if include_rebar:
            c = params.cover
            rd = params.main_rebar_dia
            rs = params.main_rebar_spacing
            
            # Left wall rebar
            self.detailer.draw_rebar_array(
                (ox + c + rd/2000, oy),
                (ox + c + rd/2000, oy + H - c),
                rd, spacing=rs
            )
            self.detailer.draw_rebar_array(
                (ox + t - c - rd/2000, oy),
                (ox + t - c - rd/2000, oy + H - c),
                rd, spacing=rs
            )
            
            # Right wall rebar
            self.detailer.draw_rebar_array(
                (ox + t + L + c + rd/2000, oy),
                (ox + t + L + c + rd/2000, oy + H - c),
                rd, spacing=rs
            )
            self.detailer.draw_rebar_array(
                (ox + L_out - c - rd/2000, oy),
                (ox + L_out - c - rd/2000, oy + H - c),
                rd, spacing=rs
            )
            
            # Bottom slab rebar
            bottom_rd = params.dist_rebar_dia
            self.detailer.draw_rebar_array(
                (ox + c, oy - bt + c + bottom_rd/2000),
                (ox + L_out - c, oy - bt + c + bottom_rd/2000),
                bottom_rd, spacing=rs
            )
            self.detailer.draw_rebar_array(
                (ox + c, oy - c - bottom_rd/2000),
                (ox + L_out - c, oy - c - bottom_rd/2000),
                bottom_rd, spacing=rs
            )
            
            # Rebar annotations
            wall_spec = RebarSpec("1", rd, rs, 0, H - c)
            self.detailer.add_rebar_leader(
                (ox + c + rd/2000, oy + H/2),
                (ox - 0.8, oy + H/2 + 0.3),
                wall_spec,
                (ox - 0.3, oy + H/2 + 0.3)
            )
            
            slab_spec = RebarSpec("2", bottom_rd, rs, 0, L_out - 2*c)
            self.detailer.add_rebar_leader(
                (ox + L_out/2, oy - bt + c + bottom_rd/2000),
                (ox + L_out/2, oy - bt - 0.5),
                slab_spec,
                (ox + L_out/2, oy - bt - 0.2)
            )
        
        # 8. Dimensions
        # Height
        self.dim_system.add_linear_dim(
            (ox - 0.8, oy), (ox - 0.8, oy + H),
            offset=-0.8
        )
        
        # Water depth
        self.dim_system.add_linear_dim(
            (ox - 1.5, oy), (ox - 1.5, water_y),
            offset=-1.5
        )
        
        # Bottom thickness
        self.dim_system.add_linear_dim(
            (ox - 0.8, oy - bt), (ox - 0.8, oy),
            offset=-0.8
        )
        
        # Inner length
        self.dim_system.add_linear_dim(
            (ox + t, oy - bt - 0.8),
            (ox + t + L, oy - bt - 0.8),
            offset=-0.8
        )
        
        # Wall thickness
        self.dim_system.add_linear_dim(
            (ox, oy + H + 0.5),
            (ox + t, oy + H + 0.5),
            offset=0.5
        )
        
        # 9. Elevation marks
        self.dim_system.add_elevation_mark(
            (ox - 2, oy + H),
            params.ground_level
        )
        self.dim_system.add_elevation_mark(
            (ox - 2, water_y),
            params.ground_level - (H - Hw)
        )
        self.dim_system.add_elevation_mark(
            (ox - 2, oy),
            params.ground_level - H
        )
        self.dim_system.add_elevation_mark(
            (ox - 2, oy - bt),
            params.bottom_level
        )
        
        # 10. Title
        text_height = self.standards.get_text_height(self.scale, "subtitle")
        self.msp.add_text(
            "MẶT CẮT A-A",
            dxfattribs={
                "layer": "ANNO_TITLE",
                "height": text_height,
                "style": "TITLE"
            }
        ).set_placement(
            (ox + L_out/2, oy - bt - 2.5),
            align=TextEntityAlignment.TOP_CENTER
        )
        
        note_height = self.standards.get_text_height(self.scale, "note")
        self.msp.add_text(
            f"TỶ LỆ {self.scale.text}",
            dxfattribs={
                "layer": "ANNO_TEXT",
                "height": note_height,
                "style": "NOTE"
            }
        ).set_placement(
            (ox + L_out/2, oy - bt - 2.8),
            align=TextEntityAlignment.TOP_CENTER
        )
        
        # 11. Notes
        notes = [
            f"- Bê tông: B25 (M300)",
            f"- Thép: {params.main_rebar_dia}mm - CB300-V",
            f"- Lớp bảo vệ: {int(params.cover*1000)}mm",
            f"- Chiều sâu nước: {Hw:.2f}m"
        ]
        
        note_y = oy + H + 1.5
        for i, note in enumerate(notes):
            self.msp.add_text(
                note,
                dxfattribs={
                    "layer": "ANNO_TEXT",
                    "height": note_height * 0.8,
                    "style": "NOTE"
                }
            ).set_placement(
                (ox + L_out + 1, note_y - i * 0.4),
                align=TextEntityAlignment.LEFT
            )
    
    def _add_title_block(
        self,
        metadata: DrawingMetadata,
        position: Tuple[float, float]
    ):
        """Thêm khung tên bản vẽ"""
        x, y = position
        w, h = 18, 4  # cm scale
        
        # Border
        self.msp.add_lwpolyline([
            (x, y), (x + w, y), (x + w, y - h), (x, y - h), (x, y)
        ], close=True, dxfattribs={"layer": "TITLEBLOCK", "lineweight": 50})
        
        # Horizontal dividers
        self.msp.add_line((x, y - h/2), (x + w, y - h/2), 
                         dxfattribs={"layer": "TITLEBLOCK"})
        
        # Vertical dividers
        self.msp.add_line((x + w*0.6, y), (x + w*0.6, y - h), 
                         dxfattribs={"layer": "TITLEBLOCK"})
        
        th = self.standards.get_text_height(self.scale, "note")
        
        # Project name
        self.msp.add_text(
            metadata.project_name,
            dxfattribs={"layer": "ANNO_TITLE", "height": th * 1.2, "style": "TITLE"}
        ).set_placement((x + w*0.3, y - h*0.25), align=TextEntityAlignment.MIDDLE_CENTER)
        
        # Drawing title
        self.msp.add_text(
            metadata.drawing_title,
            dxfattribs={"layer": "ANNO_TITLE", "height": th, "style": "TITLE"}
        ).set_placement((x + w*0.3, y - h*0.75), align=TextEntityAlignment.MIDDLE_CENTER)
        
        # Scale
        self.msp.add_text(
            f"TL: {metadata.scale.text}",
            dxfattribs={"layer": "ANNO_TEXT", "height": th * 0.8, "style": "NOTE"}
        ).set_placement((x + w*0.8, y - h*0.25), align=TextEntityAlignment.MIDDLE_CENTER)
        
        # Drawn by
        self.msp.add_text(
            f"Vẽ: {metadata.drawn_by}",
            dxfattribs={"layer": "ANNO_TEXT", "height": th * 0.7, "style": "NOTE"}
        ).set_placement((x + w*0.8, y - h*0.5), align=TextEntityAlignment.MIDDLE_CENTER)
        
        # Date
        self.msp.add_text(
            f"Ngày: {metadata.date}",
            dxfattribs={"layer": "ANNO_TEXT", "height": th * 0.7, "style": "NOTE"}
        ).set_placement((x + w*0.8, y - h*0.75), align=TextEntityAlignment.MIDDLE_CENTER)
        
        # Drawing number
        self.msp.add_text(
            metadata.drawing_number,
            dxfattribs={"layer": "ANNO_TITLE", "height": th * 0.9, "style": "ENGINEERING"}
        ).set_placement((x + w - 0.5, y - h + 0.3), align=TextEntityAlignment.BOTTOM_RIGHT)
    
    def _save_with_validation(
        self,
        filename: str,
        drawing_type: str = "general"
    ) -> str:
        """Lưu file với validation"""
        guard = DrawingExportGuard(self.doc)
        result = guard.check_can_export(drawing_type)
        
        # Always save (log warnings but don't block)
        filepath = os.path.join(self.output_dir, filename)
        self.doc.saveas(filepath)
        
        # Log validation results
        if not result.is_valid:
            print(f"[CAD Validation] {result.total_issues} issues found")
            for issue in result.issues:
                print(f"  [{issue.severity.value}] {issue.code}: {issue.message}")
        
        return filepath
    
    def validate_current_drawing(self, drawing_type: str = "general") -> ValidationResult:
        """Validate bản vẽ hiện tại"""
        if self.doc is None:
            raise ValueError("No drawing created yet")
        
        return validate_drawing(self.doc, drawing_type)


# Factory function
def create_professional_generator(output_dir: str = "./outputs") -> ProfessionalDXFGenerator:
    """Tạo instance generator"""
    return ProfessionalDXFGenerator(output_dir)
