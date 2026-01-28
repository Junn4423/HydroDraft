"""
CAD 3D Generator - Tạo mô hình 3D với pythonOCC

Tạo các loại mô hình:
- Bể 3D
- Đường ống 3D
- Giếng 3D
"""

from typing import Dict, Any, List, Tuple, Optional
import os
import math

# pythonOCC imports (optional)
try:
    from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Trsf, gp_Ax1
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
    from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge
    from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakePipe
    from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Compound
    from OCC.Core.BRep import BRep_Builder
    from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
    from OCC.Core.IFSelect import IFSelect_RetDone
    from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
    OCC_AVAILABLE = True
except ImportError:
    # Fallback khi pythonOCC không có: tắt tính năng 3D nhưng vẫn cho phép import module
    OCC_AVAILABLE = False
    TopoDS_Shape = Any  # type: ignore
    TopoDS_Compound = Any  # type: ignore
    print("pythonOCC khong duoc cai dat. Bo qua cac tinh nang 3D.")


class CAD3DGenerator:
    """
    Tạo mô hình CAD 3D
    
    Sử dụng pythonOCC (OpenCASCADE) để tạo:
    - Solid bodies
    - Boolean operations
    - Export STEP/IGES
    """
    
    def __init__(self, output_dir: str = "./outputs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.shapes: List[Any] = []
        self.compound = None
    
    def create_tank_3d(
        self,
        length: float,
        width: float,
        total_depth: float,
        wall_thickness: float,
        bottom_thickness: float,
        origin: Tuple[float, float, float] = (0, 0, 0)
    ) -> Optional['TopoDS_Shape']:
        """
        Tạo mô hình 3D bể bê tông
        
        Args:
            length: Chiều dài trong (m)
            width: Chiều rộng trong (m)
            total_depth: Tổng chiều sâu (m)
            wall_thickness: Chiều dày thành (m)
            bottom_thickness: Chiều dày đáy (m)
            origin: Gốc tọa độ (x, y, z)
            
        Returns:
            TopoDS_Shape: Mô hình 3D bể
        """
        if not OCC_AVAILABLE:
            return self._create_tank_3d_fallback(
                length, width, total_depth, wall_thickness, bottom_thickness, origin
            )
        
        ox, oy, oz = origin
        t = wall_thickness
        bt = bottom_thickness
        
        # Kích thước ngoài
        L_out = length + 2 * t
        W_out = width + 2 * t
        H_out = total_depth + bt
        
        # 1. Tạo khối hộp ngoài
        outer_box = BRepPrimAPI_MakeBox(
            gp_Pnt(ox, oy, oz - bt),
            L_out, W_out, H_out
        ).Shape()
        
        # 2. Tạo khối hộp trong (để cắt)
        inner_box = BRepPrimAPI_MakeBox(
            gp_Pnt(ox + t, oy + t, oz),
            length, width, total_depth + 0.1  # +0.1 để cắt qua đỉnh
        ).Shape()
        
        # 3. Boolean cut
        tank_shell = BRepAlgoAPI_Cut(outer_box, inner_box).Shape()
        
        self.shapes.append(tank_shell)
        return tank_shell
    
    def create_pipe_3d(
        self,
        start_point: Tuple[float, float, float],
        end_point: Tuple[float, float, float],
        outer_diameter: float,  # mm
        wall_thickness: float = 0  # mm, 0 = solid pipe
    ) -> Optional['TopoDS_Shape']:
        """
        Tạo đường ống 3D
        
        Args:
            start_point: Điểm đầu (x, y, z)
            end_point: Điểm cuối (x, y, z)
            outer_diameter: Đường kính ngoài (mm)
            wall_thickness: Chiều dày thành ống (mm), 0 = ống đặc
            
        Returns:
            TopoDS_Shape: Mô hình 3D ống
        """
        if not OCC_AVAILABLE:
            return self._create_pipe_3d_fallback(
                start_point, end_point, outer_diameter, wall_thickness
            )
        
        # Chuyển đổi đơn vị mm -> m
        r_out = outer_diameter / 1000 / 2
        t = wall_thickness / 1000
        
        p1 = gp_Pnt(*start_point)
        p2 = gp_Pnt(*end_point)
        
        # Tính vector hướng và chiều dài
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        dz = end_point[2] - start_point[2]
        length = math.sqrt(dx**2 + dy**2 + dz**2)
        
        if length < 0.001:
            return None
        
        # Tạo hệ trục tọa độ
        direction = gp_Dir(dx/length, dy/length, dz/length)
        axis = gp_Ax2(p1, direction)
        
        # Tạo ống ngoài
        outer_cyl = BRepPrimAPI_MakeCylinder(axis, r_out, length).Shape()
        
        if t > 0 and t < r_out:
            # Tạo ống trong và cắt
            r_in = r_out - t
            inner_cyl = BRepPrimAPI_MakeCylinder(axis, r_in, length).Shape()
            pipe = BRepAlgoAPI_Cut(outer_cyl, inner_cyl).Shape()
        else:
            pipe = outer_cyl
        
        self.shapes.append(pipe)
        return pipe
    
    def create_pipe_network_3d(
        self,
        segments: List[Dict],
        manholes: List[Dict]
    ) -> Optional['TopoDS_Shape']:
        """
        Tạo mạng lưới đường ống 3D
        
        Args:
            segments: Danh sách đoạn ống
            manholes: Danh sách giếng thăm
            
        Returns:
            TopoDS_Shape: Mô hình 3D mạng lưới
        """
        if not OCC_AVAILABLE:
            return None
        
        builder = BRep_Builder()
        compound = TopoDS_Compound()
        builder.MakeCompound(compound)
        
        # Tạo các đoạn ống
        for i, seg in enumerate(segments):
            if i < len(manholes) - 1:
                mh_start = manholes[i]
                mh_end = manholes[i + 1]
                
                # Giả định x, y từ station (đơn giản hóa - tuyến thẳng)
                start_point = (mh_start["station"], 0, mh_start["invert_level"])
                end_point = (mh_end["station"], 0, mh_end["invert_level"])
                
                pipe = self.create_pipe_3d(
                    start_point=start_point,
                    end_point=end_point,
                    outer_diameter=seg["diameter"]
                )
                
                if pipe:
                    builder.Add(compound, pipe)
        
        # Tạo giếng thăm
        for mh in manholes:
            # Giếng hình trụ
            mh_shape = self.create_manhole_3d(
                x=mh["station"],
                y=0,
                ground_level=mh["ground_level"],
                invert_level=mh["invert_level"],
                diameter=mh.get("diameter", 1000)
            )
            
            if mh_shape:
                builder.Add(compound, mh_shape)
        
        self.compound = compound
        return compound
    
    def create_manhole_3d(
        self,
        x: float,
        y: float,
        ground_level: float,
        invert_level: float,
        diameter: float = 1000  # mm
    ) -> Optional['TopoDS_Shape']:
        """
        Tạo giếng thăm 3D
        
        Args:
            x, y: Tọa độ
            ground_level: Cao độ mặt đất (m)
            invert_level: Cao độ đáy (m)
            diameter: Đường kính giếng (mm)
            
        Returns:
            TopoDS_Shape: Mô hình 3D giếng
        """
        if not OCC_AVAILABLE:
            return None
        
        r = diameter / 1000 / 2
        h = ground_level - invert_level
        wall_t = 0.15  # Chiều dày thành giếng 15cm
        
        # Tạo hình trụ ngoài
        axis = gp_Ax2(gp_Pnt(x, y, invert_level), gp_Dir(0, 0, 1))
        outer_cyl = BRepPrimAPI_MakeCylinder(axis, r, h).Shape()
        
        # Tạo hình trụ trong
        inner_cyl = BRepPrimAPI_MakeCylinder(axis, r - wall_t, h + 0.1).Shape()
        
        # Cắt
        manhole = BRepAlgoAPI_Cut(outer_cyl, inner_cyl).Shape()
        
        return manhole
    
    def create_well_3d(
        self,
        x: float,
        y: float,
        ground_level: float,
        total_depth: float,
        casing_diameter: float,  # mm
        screen_length: float = 0
    ) -> Optional['TopoDS_Shape']:
        """
        Tạo giếng quan trắc 3D
        
        Args:
            x, y: Tọa độ
            ground_level: Cao độ mặt đất (m)
            total_depth: Tổng chiều sâu (m)
            casing_diameter: Đường kính ống chống (mm)
            screen_length: Chiều dài ống lọc (m)
            
        Returns:
            TopoDS_Shape: Mô hình 3D giếng
        """
        if not OCC_AVAILABLE:
            return None
        
        r = casing_diameter / 1000 / 2
        wall_t = 0.005  # 5mm cho ống PVC
        
        # Tạo ống chống (casing)
        axis = gp_Ax2(gp_Pnt(x, y, ground_level - total_depth), gp_Dir(0, 0, 1))
        outer_cyl = BRepPrimAPI_MakeCylinder(axis, r, total_depth).Shape()
        inner_cyl = BRepPrimAPI_MakeCylinder(axis, r - wall_t, total_depth + 0.1).Shape()
        
        well = BRepAlgoAPI_Cut(outer_cyl, inner_cyl).Shape()
        
        self.shapes.append(well)
        return well
    
    def export_step(self, filename: str) -> Optional[str]:
        """
        Xuất file STEP
        
        Args:
            filename: Tên file
            
        Returns:
            str: Đường dẫn file
        """
        if not OCC_AVAILABLE:
            return None
        
        if not filename.endswith('.step') and not filename.endswith('.stp'):
            filename += '.step'
        
        filepath = os.path.join(self.output_dir, filename)
        
        writer = STEPControl_Writer()
        
        # Thêm tất cả shapes
        for shape in self.shapes:
            writer.Transfer(shape, STEPControl_AsIs)
        
        # Thêm compound nếu có
        if self.compound:
            writer.Transfer(self.compound, STEPControl_AsIs)
        
        status = writer.Write(filepath)
        
        if status == IFSelect_RetDone:
            return filepath
        return None
    
    def _create_tank_3d_fallback(
        self,
        length: float,
        width: float,
        total_depth: float,
        wall_thickness: float,
        bottom_thickness: float,
        origin: Tuple[float, float, float]
    ) -> Dict[str, Any]:
        """
        Phương thức fallback khi không có pythonOCC
        Trả về thông số hình học thay vì shape
        """
        ox, oy, oz = origin
        t = wall_thickness
        bt = bottom_thickness
        
        return {
            "type": "tank",
            "geometry": {
                "outer_dimensions": {
                    "length": length + 2 * t,
                    "width": width + 2 * t,
                    "height": total_depth + bt
                },
                "inner_dimensions": {
                    "length": length,
                    "width": width,
                    "height": total_depth
                },
                "wall_thickness": t,
                "bottom_thickness": bt,
                "origin": {"x": ox, "y": oy, "z": oz}
            },
            "vertices": self._generate_tank_vertices(
                length, width, total_depth, wall_thickness, bottom_thickness, origin
            )
        }
    
    def _create_pipe_3d_fallback(
        self,
        start_point: Tuple[float, float, float],
        end_point: Tuple[float, float, float],
        outer_diameter: float,
        wall_thickness: float
    ) -> Dict[str, Any]:
        """
        Phương thức fallback cho đường ống
        """
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        dz = end_point[2] - start_point[2]
        length = math.sqrt(dx**2 + dy**2 + dz**2)
        
        return {
            "type": "pipe",
            "geometry": {
                "start_point": {"x": start_point[0], "y": start_point[1], "z": start_point[2]},
                "end_point": {"x": end_point[0], "y": end_point[1], "z": end_point[2]},
                "length": length,
                "outer_diameter": outer_diameter,
                "inner_diameter": outer_diameter - 2 * wall_thickness if wall_thickness > 0 else outer_diameter,
                "wall_thickness": wall_thickness
            }
        }
    
    def _generate_tank_vertices(
        self,
        length: float,
        width: float,
        total_depth: float,
        wall_thickness: float,
        bottom_thickness: float,
        origin: Tuple[float, float, float]
    ) -> Dict[str, List]:
        """
        Tạo danh sách đỉnh cho mô hình bể
        """
        ox, oy, oz = origin
        t = wall_thickness
        bt = bottom_thickness
        
        L = length + 2 * t
        W = width + 2 * t
        H = total_depth + bt
        
        # Đỉnh hộp ngoài
        outer_vertices = [
            (ox, oy, oz - bt),
            (ox + L, oy, oz - bt),
            (ox + L, oy + W, oz - bt),
            (ox, oy + W, oz - bt),
            (ox, oy, oz + total_depth),
            (ox + L, oy, oz + total_depth),
            (ox + L, oy + W, oz + total_depth),
            (ox, oy + W, oz + total_depth)
        ]
        
        # Đỉnh lòng bể
        inner_vertices = [
            (ox + t, oy + t, oz),
            (ox + t + length, oy + t, oz),
            (ox + t + length, oy + t + width, oz),
            (ox + t, oy + t + width, oz),
            (ox + t, oy + t, oz + total_depth),
            (ox + t + length, oy + t, oz + total_depth),
            (ox + t + length, oy + t + width, oz + total_depth),
            (ox + t, oy + t + width, oz + total_depth)
        ]
        
        return {
            "outer": outer_vertices,
            "inner": inner_vertices
        }
    
    def clear(self) -> None:
        """Xóa tất cả shapes"""
        self.shapes = []
        self.compound = None
