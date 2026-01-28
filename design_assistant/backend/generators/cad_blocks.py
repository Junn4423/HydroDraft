"""
CAD Block Library - Thư viện block CAD chuyên nghiệp

SPRINT 3: PROFESSIONAL CAD
Block-Based Architecture theo tiêu chuẩn TCVN và ISO

Tính năng:
- Block tiêu chuẩn cho: Valve, Manhole, Tank, Pump, Waterstop
- Đầy đủ thuộc tính (attributes)
- Tỷ lệ tự động
- Xoay theo hướng
- Layer chuẩn

Tiêu chuẩn:
- TCVN 4036:1985 - Ký hiệu đường ống
- TCVN 8479:2010 - Thiết kế cấp thoát nước
- ISO 14617 - Graphical symbols for diagrams
"""

import ezdxf
from ezdxf import units
from ezdxf.math import Vec3
from ezdxf.enums import TextEntityAlignment
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
import math


class BlockType(Enum):
    """Loại block"""
    VALVE_GATE = "VALVE_GATE"
    VALVE_CHECK = "VALVE_CHECK"
    VALVE_BUTTERFLY = "VALVE_BUTTERFLY"
    VALVE_BALL = "VALVE_BALL"
    VALVE_CONTROL = "VALVE_CONTROL"
    VALVE_PRESSURE_RELIEF = "VALVE_RELIEF"
    
    MANHOLE_CIRCULAR = "MH_CIRCULAR"
    MANHOLE_RECTANGULAR = "MH_RECT"
    MANHOLE_DROP = "MH_DROP"
    MANHOLE_JUNCTION = "MH_JUNCTION"
    
    PUMP_CENTRIFUGAL = "PUMP_CENTRI"
    PUMP_SUBMERSIBLE = "PUMP_SUBM"
    PUMP_VERTICAL = "PUMP_VERT"
    
    TANK_RECTANGULAR = "TANK_RECT"
    TANK_CIRCULAR = "TANK_CIRC"
    
    FLOWMETER = "FLOWMETER"
    LEVEL_GAUGE = "LEVEL_GAUGE"
    PRESSURE_GAUGE = "PRESSURE_GAUGE"
    
    WATERSTOP_PVC = "WATERSTOP_PVC"
    WATERSTOP_RUBBER = "WATERSTOP_RUBBER"
    WATERSTOP_METAL = "WATERSTOP_METAL"
    
    REBAR_SECTION = "REBAR_SECTION"
    REBAR_STIRRUP = "REBAR_STIRRUP"
    
    ELEVATION_MARK = "ELEVATION_MARK"
    GRID_AXIS = "GRID_AXIS"
    SECTION_MARK = "SECTION_MARK"
    DETAIL_MARK = "DETAIL_MARK"
    NORTH_ARROW = "NORTH_ARROW"


@dataclass
class BlockAttribute:
    """Thuộc tính block"""
    tag: str
    prompt: str
    default: str
    height: float = 0.25
    rotation: float = 0
    halign: int = 0  # 0=left, 1=center, 2=right
    valign: int = 0  # 0=baseline, 1=bottom, 2=middle, 3=top


class CADBlockLibrary:
    """
    Thư viện block CAD chuyên nghiệp
    
    Sử dụng:
        library = CADBlockLibrary(doc)
        library.create_all_blocks()
        library.insert_block("VALVE_GATE", (x, y), scale=1.0, rotation=0)
    """
    
    # Layer cho từng loại block
    BLOCK_LAYERS = {
        "VALVE": "EQUIP_VALVE",
        "PUMP": "EQUIP_PUMP",
        "MANHOLE": "STRUCT_MH",
        "TANK": "STRUCT_TANK",
        "INSTRUMENT": "EQUIP_INST",
        "WATERSTOP": "STRUCT_DETAIL",
        "REBAR": "STRUCT_REBAR",
        "ANNOTATION": "ANNO_DIM",
        "GRID": "ANNO_GRID"
    }
    
    def __init__(self, doc):
        self.doc = doc
        self.msp = doc.modelspace()
        self._ensure_layers()
        self._blocks_created = set()
    
    def _ensure_layers(self):
        """Đảm bảo các layer tồn tại"""
        layer_colors = {
            "EQUIP_VALVE": 1,       # Red
            "EQUIP_PUMP": 3,        # Green
            "EQUIP_INST": 6,        # Magenta
            "STRUCT_MH": 4,         # Cyan
            "STRUCT_TANK": 2,       # Yellow
            "STRUCT_DETAIL": 7,     # White
            "STRUCT_REBAR": 1,      # Red
            "ANNO_DIM": 7,          # White
            "ANNO_GRID": 8,         # Gray
            "ANNO_TEXT": 7,         # White
        }
        
        for layer_name, color in layer_colors.items():
            if layer_name not in self.doc.layers:
                self.doc.layers.add(layer_name, color=color)
    
    def create_all_blocks(self):
        """Tạo tất cả block tiêu chuẩn"""
        # Valves
        self._create_gate_valve_block()
        self._create_check_valve_block()
        self._create_butterfly_valve_block()
        self._create_ball_valve_block()
        self._create_control_valve_block()
        self._create_relief_valve_block()
        
        # Manholes
        self._create_circular_manhole_block()
        self._create_rectangular_manhole_block()
        self._create_drop_manhole_block()
        
        # Pumps
        self._create_centrifugal_pump_block()
        self._create_submersible_pump_block()
        
        # Instruments
        self._create_flowmeter_block()
        self._create_level_gauge_block()
        self._create_pressure_gauge_block()
        
        # Waterstops
        self._create_waterstop_pvc_block()
        self._create_waterstop_rubber_block()
        
        # Rebar symbols
        self._create_rebar_section_block()
        self._create_stirrup_block()
        
        # Annotation marks
        self._create_elevation_mark_block()
        self._create_grid_axis_block()
        self._create_section_mark_block()
        self._create_north_arrow_block()
    
    # =====================
    # VALVE BLOCKS
    # =====================
    
    def _create_gate_valve_block(self):
        """Block van cổng (Gate Valve) - ISO 14617"""
        name = BlockType.VALVE_GATE.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        
        # Thân van (2 tam giác đối đỉnh)
        size = 0.5
        # Tam giác trái
        block.add_lwpolyline([
            (-size, 0), (0, size/2), (0, -size/2), (-size, 0)
        ], close=True, dxfattribs={"layer": "EQUIP_VALVE"})
        
        # Tam giác phải
        block.add_lwpolyline([
            (size, 0), (0, size/2), (0, -size/2), (size, 0)
        ], close=True, dxfattribs={"layer": "EQUIP_VALVE"})
        
        # Thân ngang (stem)
        block.add_line((0, 0), (0, size), dxfattribs={"layer": "EQUIP_VALVE"})
        
        # Tay vặn
        block.add_line((-size/3, size), (size/3, size), 
                      dxfattribs={"layer": "EQUIP_VALVE", "lineweight": 35})
        
        # Attribute: Tag
        attdef = block.add_attdef(
            tag="TAG",
            text="V-XX",
            insert=(0, -size - 0.2),
            dxfattribs={
                "layer": "ANNO_TEXT",
                "height": 0.2
            }
        )
        attdef.dxf.halign = 1  # Center
        
        self._blocks_created.add(name)
    
    def _create_check_valve_block(self):
        """Block van một chiều (Check Valve) - ISO 14617"""
        name = BlockType.VALVE_CHECK.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        size = 0.5
        
        # Vòng tròn
        block.add_circle((0, 0), size/2, dxfattribs={"layer": "EQUIP_VALVE"})
        
        # Tam giác chỉ hướng
        block.add_lwpolyline([
            (-size/4, -size/4), (size/4, 0), (-size/4, size/4)
        ], close=True, dxfattribs={"layer": "EQUIP_VALVE"})
        
        # Attribute
        attdef = block.add_attdef(
            tag="TAG",
            text="CV-XX",
            insert=(0, -size - 0.15),
            dxfattribs={"layer": "ANNO_TEXT", "height": 0.18}
        )
        attdef.dxf.halign = 1
        
        self._blocks_created.add(name)
    
    def _create_butterfly_valve_block(self):
        """Block van bướm (Butterfly Valve)"""
        name = BlockType.VALVE_BUTTERFLY.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        size = 0.5
        
        # Hai đường thẳng song song
        block.add_line((-size, -size/3), (-size, size/3), 
                      dxfattribs={"layer": "EQUIP_VALVE", "lineweight": 50})
        block.add_line((size, -size/3), (size, size/3), 
                      dxfattribs={"layer": "EQUIP_VALVE", "lineweight": 50})
        
        # Đĩa van (đường chéo)
        block.add_line((-size*0.8, -size/3), (size*0.8, size/3), 
                      dxfattribs={"layer": "EQUIP_VALVE", "lineweight": 35})
        
        # Trục
        block.add_line((0, 0), (0, size*0.8), dxfattribs={"layer": "EQUIP_VALVE"})
        
        # Attribute
        attdef = block.add_attdef(
            tag="TAG",
            text="BV-XX",
            insert=(0, -size/2 - 0.15),
            dxfattribs={"layer": "ANNO_TEXT", "height": 0.18}
        )
        attdef.dxf.halign = 1
        
        self._blocks_created.add(name)
    
    def _create_ball_valve_block(self):
        """Block van bi (Ball Valve)"""
        name = BlockType.VALVE_BALL.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        size = 0.4
        
        # Vòng tròn (thân van)
        block.add_circle((0, 0), size, dxfattribs={"layer": "EQUIP_VALVE"})
        
        # Đường ngang qua tâm
        block.add_line((-size, 0), (size, 0), 
                      dxfattribs={"layer": "EQUIP_VALVE", "lineweight": 35})
        
        # Trục xoay
        block.add_line((0, 0), (0, size*1.2), dxfattribs={"layer": "EQUIP_VALVE"})
        block.add_line((-size/3, size*1.2), (size/3, size*1.2), 
                      dxfattribs={"layer": "EQUIP_VALVE", "lineweight": 35})
        
        self._blocks_created.add(name)
    
    def _create_control_valve_block(self):
        """Block van điều khiển (Control Valve)"""
        name = BlockType.VALVE_CONTROL.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        size = 0.5
        
        # Giống gate valve nhưng thêm actuator
        # Thân van
        block.add_lwpolyline([
            (-size, 0), (0, size/2), (0, -size/2), (-size, 0)
        ], close=True, dxfattribs={"layer": "EQUIP_VALVE"})
        block.add_lwpolyline([
            (size, 0), (0, size/2), (0, -size/2), (size, 0)
        ], close=True, dxfattribs={"layer": "EQUIP_VALVE"})
        
        # Thân ngang
        block.add_line((0, 0), (0, size*0.6), dxfattribs={"layer": "EQUIP_VALVE"})
        
        # Actuator (hình chữ nhật)
        act_w = size * 0.6
        act_h = size * 0.4
        act_y = size * 0.8
        block.add_lwpolyline([
            (-act_w/2, act_y), (act_w/2, act_y),
            (act_w/2, act_y + act_h), (-act_w/2, act_y + act_h),
            (-act_w/2, act_y)
        ], close=True, dxfattribs={"layer": "EQUIP_VALVE"})
        
        # Chữ A (automatic)
        block.add_text("A", dxfattribs={
            "layer": "ANNO_TEXT", "height": 0.15
        }).set_placement((0, act_y + act_h/2), align=TextEntityAlignment.MIDDLE_CENTER)
        
        self._blocks_created.add(name)
    
    def _create_relief_valve_block(self):
        """Block van xả áp (Pressure Relief Valve)"""
        name = BlockType.VALVE_PRESSURE_RELIEF.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        size = 0.5
        
        # Tam giác
        block.add_lwpolyline([
            (0, -size/2), (size/2, size/2), (-size/2, size/2), (0, -size/2)
        ], close=True, dxfattribs={"layer": "EQUIP_VALVE"})
        
        # Mũi tên hướng lên
        block.add_line((0, size/2), (0, size), dxfattribs={"layer": "EQUIP_VALVE"})
        block.add_lwpolyline([
            (-size/6, size*0.8), (0, size), (size/6, size*0.8)
        ], dxfattribs={"layer": "EQUIP_VALVE"})
        
        self._blocks_created.add(name)
    
    # =====================
    # MANHOLE BLOCKS
    # =====================
    
    def _create_circular_manhole_block(self):
        """Block giếng thăm tròn (mặt bằng)"""
        name = BlockType.MANHOLE_CIRCULAR.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        
        # Vòng ngoài (thành)
        block.add_circle((0, 0), 0.6, dxfattribs={"layer": "STRUCT_MH", "lineweight": 50})
        
        # Vòng trong (nắp)
        block.add_circle((0, 0), 0.4, dxfattribs={"layer": "STRUCT_MH"})
        
        # Đường tâm
        block.add_line((-0.8, 0), (0.8, 0), 
                      dxfattribs={"layer": "ANNO_GRID", "linetype": "CENTER"})
        block.add_line((0, -0.8), (0, 0.8), 
                      dxfattribs={"layer": "ANNO_GRID", "linetype": "CENTER"})
        
        # Attributes
        attdef_id = block.add_attdef(
            tag="MH_ID",
            text="MH-XX",
            insert=(0, 0.9),
            dxfattribs={"layer": "ANNO_TEXT", "height": 0.25}
        )
        attdef_id.dxf.halign = 1
        
        attdef_il = block.add_attdef(
            tag="INVERT",
            text="IL +0.000",
            insert=(0, -0.9),
            dxfattribs={"layer": "ANNO_TEXT", "height": 0.18}
        )
        attdef_il.dxf.halign = 1
        
        self._blocks_created.add(name)
    
    def _create_rectangular_manhole_block(self):
        """Block giếng thăm chữ nhật (mặt bằng)"""
        name = BlockType.MANHOLE_RECTANGULAR.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        w, h = 0.8, 1.0
        
        # Thành ngoài
        block.add_lwpolyline([
            (-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2), (-w/2, -h/2)
        ], close=True, dxfattribs={"layer": "STRUCT_MH", "lineweight": 50})
        
        # Nắp (hình tròn ở giữa)
        block.add_circle((0, 0), 0.3, dxfattribs={"layer": "STRUCT_MH"})
        
        # Đường tâm
        block.add_line((-w, 0), (w, 0), 
                      dxfattribs={"layer": "ANNO_GRID", "linetype": "CENTER"})
        block.add_line((0, -h), (0, h), 
                      dxfattribs={"layer": "ANNO_GRID", "linetype": "CENTER"})
        
        # Attributes
        attdef = block.add_attdef(
            tag="MH_ID",
            text="MH-XX",
            insert=(0, h/2 + 0.3),
            dxfattribs={"layer": "ANNO_TEXT", "height": 0.25}
        )
        attdef.dxf.halign = 1
        
        self._blocks_created.add(name)
    
    def _create_drop_manhole_block(self):
        """Block giếng thăm có bậc (drop manhole)"""
        name = BlockType.MANHOLE_DROP.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        
        # Giống circular nhưng có ký hiệu bậc
        block.add_circle((0, 0), 0.6, dxfattribs={"layer": "STRUCT_MH", "lineweight": 50})
        block.add_circle((0, 0), 0.4, dxfattribs={"layer": "STRUCT_MH"})
        
        # Ký hiệu bậc (mũi tên xuống)
        block.add_line((0, 0.2), (0, -0.2), dxfattribs={"layer": "STRUCT_MH"})
        block.add_lwpolyline([
            (-0.1, -0.1), (0, -0.2), (0.1, -0.1)
        ], dxfattribs={"layer": "STRUCT_MH"})
        
        # Chữ "D" (Drop)
        block.add_text("D", dxfattribs={
            "layer": "ANNO_TEXT", "height": 0.15
        }).set_placement((0.25, 0.25), align=TextEntityAlignment.LEFT)
        
        self._blocks_created.add(name)
    
    # =====================
    # PUMP BLOCKS
    # =====================
    
    def _create_centrifugal_pump_block(self):
        """Block bơm ly tâm - ISO 14617"""
        name = BlockType.PUMP_CENTRIFUGAL.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        r = 0.4
        
        # Vòng tròn (thân bơm)
        block.add_circle((0, 0), r, dxfattribs={"layer": "EQUIP_PUMP", "lineweight": 35})
        
        # Tam giác chỉ hướng bơm
        block.add_lwpolyline([
            (-r*0.5, -r*0.3), (r*0.3, 0), (-r*0.5, r*0.3)
        ], close=True, dxfattribs={"layer": "EQUIP_PUMP"})
        
        # Ống hút (trái)
        block.add_line((-r-0.3, 0), (-r, 0), 
                      dxfattribs={"layer": "EQUIP_PUMP", "lineweight": 25})
        
        # Ống đẩy (trên)
        block.add_line((0, r), (0, r+0.3), 
                      dxfattribs={"layer": "EQUIP_PUMP", "lineweight": 25})
        
        # Attribute
        attdef = block.add_attdef(
            tag="PUMP_ID",
            text="P-XX",
            insert=(0, -r-0.2),
            dxfattribs={"layer": "ANNO_TEXT", "height": 0.2}
        )
        attdef.dxf.halign = 1
        
        self._blocks_created.add(name)
    
    def _create_submersible_pump_block(self):
        """Block bơm chìm"""
        name = BlockType.PUMP_SUBMERSIBLE.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        w, h = 0.3, 0.6
        
        # Thân bơm (hình chữ nhật)
        block.add_lwpolyline([
            (-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2), (-w/2, -h/2)
        ], close=True, dxfattribs={"layer": "EQUIP_PUMP", "lineweight": 35})
        
        # Đầu ra (trên)
        block.add_line((0, h/2), (0, h/2+0.2), 
                      dxfattribs={"layer": "EQUIP_PUMP", "lineweight": 25})
        
        # Chữ "S" bên trong
        block.add_text("S", dxfattribs={
            "layer": "EQUIP_PUMP", "height": 0.15
        }).set_placement((0, 0), align=TextEntityAlignment.MIDDLE_CENTER)
        
        # Attribute
        attdef = block.add_attdef(
            tag="PUMP_ID",
            text="SP-XX",
            insert=(0, -h/2-0.2),
            dxfattribs={"layer": "ANNO_TEXT", "height": 0.18}
        )
        attdef.dxf.halign = 1
        
        self._blocks_created.add(name)
    
    # =====================
    # INSTRUMENT BLOCKS
    # =====================
    
    def _create_flowmeter_block(self):
        """Block đồng hồ đo lưu lượng - ISA 5.1"""
        name = BlockType.FLOWMETER.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        r = 0.3
        
        # Vòng tròn
        block.add_circle((0, 0), r, dxfattribs={"layer": "EQUIP_INST"})
        
        # Chữ FI (Flow Indicator) hoặc FT (Flow Transmitter)
        block.add_text("FI", dxfattribs={
            "layer": "EQUIP_INST", "height": 0.15
        }).set_placement((0, 0), align=TextEntityAlignment.MIDDLE_CENTER)
        
        # Attribute
        attdef = block.add_attdef(
            tag="INST_TAG",
            text="FI-XXX",
            insert=(0, -r-0.15),
            dxfattribs={"layer": "ANNO_TEXT", "height": 0.15}
        )
        attdef.dxf.halign = 1
        
        self._blocks_created.add(name)
    
    def _create_level_gauge_block(self):
        """Block đo mực nước"""
        name = BlockType.LEVEL_GAUGE.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        r = 0.3
        
        block.add_circle((0, 0), r, dxfattribs={"layer": "EQUIP_INST"})
        block.add_text("LI", dxfattribs={
            "layer": "EQUIP_INST", "height": 0.15
        }).set_placement((0, 0), align=TextEntityAlignment.MIDDLE_CENTER)
        
        self._blocks_created.add(name)
    
    def _create_pressure_gauge_block(self):
        """Block đồng hồ áp suất"""
        name = BlockType.PRESSURE_GAUGE.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        r = 0.3
        
        block.add_circle((0, 0), r, dxfattribs={"layer": "EQUIP_INST"})
        block.add_text("PI", dxfattribs={
            "layer": "EQUIP_INST", "height": 0.15
        }).set_placement((0, 0), align=TextEntityAlignment.MIDDLE_CENTER)
        
        self._blocks_created.add(name)
    
    # =====================
    # WATERSTOP BLOCKS
    # =====================
    
    def _create_waterstop_pvc_block(self):
        """Block waterstop PVC"""
        name = BlockType.WATERSTOP_PVC.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        
        # Hình dạng waterstop PVC (có gờ)
        points = [
            (0, -0.15), (0.05, -0.1), (0.1, -0.15), (0.1, 0.15),
            (0.05, 0.1), (0, 0.15), (-0.05, 0.1), (-0.1, 0.15),
            (-0.1, -0.15), (-0.05, -0.1), (0, -0.15)
        ]
        block.add_lwpolyline(points, close=True, 
                            dxfattribs={"layer": "STRUCT_DETAIL", "lineweight": 25})
        
        self._blocks_created.add(name)
    
    def _create_waterstop_rubber_block(self):
        """Block waterstop cao su"""
        name = BlockType.WATERSTOP_RUBBER.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        
        # Hình oval
        block.add_ellipse(
            center=(0, 0),
            major_axis=(0.1, 0),
            ratio=0.5,
            dxfattribs={"layer": "STRUCT_DETAIL", "lineweight": 25}
        )
        
        # Hatch đen - sử dụng polyline path xấp xỉ ellipse
        hatch = block.add_hatch(color=250, dxfattribs={"layer": "STRUCT_DETAIL"})
        # Tạo polyline xấp xỉ ellipse
        ellipse_pts = [
            (0.1 * math.cos(a), 0.05 * math.sin(a)) 
            for a in [i * math.pi / 18 for i in range(37)]
        ]
        hatch.paths.add_polyline_path(ellipse_pts, is_closed=True)
        hatch.set_solid_fill()
        
        self._blocks_created.add(name)
    
    # =====================
    # REBAR BLOCKS
    # =====================
    
    def _create_rebar_section_block(self):
        """Block mặt cắt cốt thép"""
        name = BlockType.REBAR_SECTION.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        
        # Vòng tròn (thép)
        block.add_circle((0, 0), 0.05, dxfattribs={"layer": "STRUCT_REBAR"})
        
        # Fill đen
        hatch = block.add_hatch(color=1, dxfattribs={"layer": "STRUCT_REBAR"})
        hatch.paths.add_polyline_path([
            (0.05 * math.cos(a), 0.05 * math.sin(a)) 
            for a in [i * math.pi / 10 for i in range(21)]
        ], is_closed=True)
        hatch.set_solid_fill()
        
        self._blocks_created.add(name)
    
    def _create_stirrup_block(self):
        """Block đai/thép đai"""
        name = BlockType.REBAR_STIRRUP.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        
        # Hình chữ nhật với móc
        w, h = 0.3, 0.4
        hook = 0.05
        
        block.add_lwpolyline([
            (-w/2 + hook, -h/2),
            (w/2, -h/2),
            (w/2, h/2),
            (-w/2, h/2),
            (-w/2, -h/2),
            (-w/2 + hook, -h/2),
            (-w/2 + hook, -h/2 + hook)  # Hook
        ], dxfattribs={"layer": "STRUCT_REBAR"})
        
        self._blocks_created.add(name)
    
    # =====================
    # ANNOTATION BLOCKS
    # =====================
    
    def _create_elevation_mark_block(self):
        """Block ký hiệu cao độ"""
        name = BlockType.ELEVATION_MARK.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        size = 0.3
        
        # Tam giác chỉ lên
        block.add_lwpolyline([
            (0, 0), (-size/2, -size), (size/2, -size), (0, 0)
        ], close=True, dxfattribs={"layer": "ANNO_DIM"})
        
        # Attribute cao độ
        attdef = block.add_attdef(
            tag="ELEVATION",
            text="+0.000",
            insert=(size/2 + 0.1, -size/2),
            dxfattribs={"layer": "ANNO_TEXT", "height": 0.2}
        )
        
        self._blocks_created.add(name)
    
    def _create_grid_axis_block(self):
        """Block ký hiệu trục"""
        name = BlockType.GRID_AXIS.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        r = 0.4
        
        # Vòng tròn
        block.add_circle((0, 0), r, dxfattribs={"layer": "ANNO_GRID", "lineweight": 35})
        
        # Attribute tên trục
        attdef = block.add_attdef(
            tag="AXIS_NAME",
            text="A",
            insert=(0, 0),
            dxfattribs={"layer": "ANNO_TEXT", "height": 0.3}
        )
        attdef.dxf.halign = 1
        attdef.dxf.valign = 2
        
        self._blocks_created.add(name)
    
    def _create_section_mark_block(self):
        """Block ký hiệu mặt cắt"""
        name = BlockType.SECTION_MARK.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        r = 0.35
        
        # Vòng tròn nửa tô đen
        block.add_circle((0, 0), r, dxfattribs={"layer": "ANNO_DIM", "lineweight": 25})
        
        # Nửa tròn tô đen (hướng nhìn)
        import math
        half_circle = [(r * math.cos(a), r * math.sin(a)) 
                       for a in [i * math.pi / 20 for i in range(-10, 11)]]
        hatch = block.add_hatch(color=7, dxfattribs={"layer": "ANNO_DIM"})
        hatch.paths.add_polyline_path(half_circle + [(0, 0)], is_closed=True)
        hatch.set_solid_fill()
        
        # Mũi tên
        block.add_line((0, 0), (r + 0.3, 0), dxfattribs={"layer": "ANNO_DIM"})
        block.add_lwpolyline([
            (r + 0.2, 0.05), (r + 0.3, 0), (r + 0.2, -0.05)
        ], dxfattribs={"layer": "ANNO_DIM"})
        
        # Attribute tên mặt cắt
        attdef = block.add_attdef(
            tag="SECTION_NAME",
            text="A",
            insert=(0, 0),
            dxfattribs={"layer": "ANNO_TEXT", "height": 0.25}
        )
        attdef.dxf.halign = 1
        attdef.dxf.valign = 2
        
        self._blocks_created.add(name)
    
    def _create_north_arrow_block(self):
        """Block mũi tên hướng Bắc"""
        name = BlockType.NORTH_ARROW.value
        if name in self.doc.blocks:
            return
        
        block = self.doc.blocks.new(name=name)
        
        # Mũi tên
        block.add_lwpolyline([
            (0, 0), (-0.15, -0.5), (0, -0.4), (0.15, -0.5), (0, 0)
        ], close=True, dxfattribs={"layer": "ANNO_DIM"})
        
        # Nửa tô đen
        hatch = block.add_hatch(color=7, dxfattribs={"layer": "ANNO_DIM"})
        hatch.paths.add_polyline_path([
            (0, 0), (0.15, -0.5), (0, -0.4)
        ], is_closed=True)
        hatch.set_solid_fill()
        
        # Chữ N
        block.add_text("N", dxfattribs={
            "layer": "ANNO_TEXT", "height": 0.2
        }).set_placement((0, 0.15), align=TextEntityAlignment.BOTTOM_CENTER)
        
        self._blocks_created.add(name)
    
    # =====================
    # INSERT METHODS
    # =====================
    
    def insert_block(
        self,
        block_type: Union[BlockType, str],
        insert_point: Tuple[float, float],
        scale: float = 1.0,
        rotation: float = 0.0,
        attributes: Dict[str, str] = None,
        layer: str = None
    ) -> Any:
        """
        Chèn block vào bản vẽ
        
        Args:
            block_type: Loại block
            insert_point: Điểm chèn (x, y)
            scale: Tỷ lệ
            rotation: Góc xoay (độ)
            attributes: Giá trị thuộc tính {"TAG": "V-01", ...}
            layer: Layer (mặc định theo loại block)
            
        Returns:
            Block reference entity
        """
        if isinstance(block_type, BlockType):
            name = block_type.value
        else:
            name = block_type
        
        # Đảm bảo block đã được tạo
        if name not in self._blocks_created:
            self.create_all_blocks()
        
        # Xác định layer
        if layer is None:
            for prefix, layer_name in self.BLOCK_LAYERS.items():
                if prefix in name:
                    layer = layer_name
                    break
            if layer is None:
                layer = "0"
        
        # Chèn block
        block_ref = self.msp.add_blockref(
            name,
            insert_point,
            dxfattribs={
                "layer": layer,
                "xscale": scale,
                "yscale": scale,
                "rotation": rotation
            }
        )
        
        # Thêm attributes nếu có
        if attributes and name in self.doc.blocks:
            block_def = self.doc.blocks[name]
            attdefs = list(block_def.query('ATTDEF'))
            
            if attdefs:
                for attdef in attdefs:
                    tag = attdef.dxf.tag
                    value = attributes.get(tag, attdef.dxf.text)
                    
                    # Tính toán vị trí attribute
                    att_pos = Vec3(attdef.dxf.insert)
                    att_pos = att_pos * scale
                    
                    # Xoay nếu cần
                    if rotation != 0:
                        rad = math.radians(rotation)
                        x = att_pos.x * math.cos(rad) - att_pos.y * math.sin(rad)
                        y = att_pos.x * math.sin(rad) + att_pos.y * math.cos(rad)
                        att_pos = Vec3(x, y, 0)
                    
                    final_pos = (insert_point[0] + att_pos.x, insert_point[1] + att_pos.y)
                    
                    block_ref.add_attrib(
                        tag=tag,
                        text=str(value),
                        insert=final_pos,
                        dxfattribs={
                            "height": attdef.dxf.height * scale,
                            "rotation": rotation,
                            "layer": attdef.dxf.layer
                        }
                    )
        
        return block_ref
    
    def insert_valve(
        self,
        valve_type: str,
        position: Tuple[float, float],
        tag: str,
        diameter: int = None,
        scale: float = 1.0,
        rotation: float = 0.0
    ):
        """Tiện ích chèn valve"""
        type_map = {
            "gate": BlockType.VALVE_GATE,
            "check": BlockType.VALVE_CHECK,
            "butterfly": BlockType.VALVE_BUTTERFLY,
            "ball": BlockType.VALVE_BALL,
            "control": BlockType.VALVE_CONTROL,
            "relief": BlockType.VALVE_PRESSURE_RELIEF
        }
        
        block_type = type_map.get(valve_type.lower(), BlockType.VALVE_GATE)
        attrs = {"TAG": tag}
        
        return self.insert_block(block_type, position, scale, rotation, attrs)
    
    def insert_manhole(
        self,
        position: Tuple[float, float],
        mh_id: str,
        invert_level: float = None,
        mh_type: str = "circular",
        scale: float = 1.0
    ):
        """Tiện ích chèn manhole"""
        type_map = {
            "circular": BlockType.MANHOLE_CIRCULAR,
            "rectangular": BlockType.MANHOLE_RECTANGULAR,
            "drop": BlockType.MANHOLE_DROP
        }
        
        block_type = type_map.get(mh_type.lower(), BlockType.MANHOLE_CIRCULAR)
        attrs = {"MH_ID": mh_id}
        if invert_level is not None:
            attrs["INVERT"] = f"IL {invert_level:+.3f}"
        
        return self.insert_block(block_type, position, scale, 0, attrs)
    
    def insert_pump(
        self,
        position: Tuple[float, float],
        pump_id: str,
        pump_type: str = "centrifugal",
        scale: float = 1.0,
        rotation: float = 0.0
    ):
        """Tiện ích chèn pump"""
        type_map = {
            "centrifugal": BlockType.PUMP_CENTRIFUGAL,
            "submersible": BlockType.PUMP_SUBMERSIBLE
        }
        
        block_type = type_map.get(pump_type.lower(), BlockType.PUMP_CENTRIFUGAL)
        attrs = {"PUMP_ID": pump_id}
        
        return self.insert_block(block_type, position, scale, rotation, attrs)


# Hàm tiện ích
def setup_block_library(doc) -> CADBlockLibrary:
    """Khởi tạo thư viện block cho bản vẽ"""
    library = CADBlockLibrary(doc)
    library.create_all_blocks()
    return library
