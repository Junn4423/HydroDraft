"""
IFC Generator - Tạo mô hình BIM với ifcopenshell

Tạo các đối tượng IFC theo chuẩn IFC4:
- IfcProject với đầy đủ thông tin dự án
- IfcSite với tọa độ địa lý
- IfcBuilding với phân loại công trình
- IfcTank với thuộc tính thủy lực
- IfcPipeSegment với thông số kỹ thuật
- IfcFlowTerminal cho các thiết bị

Tuân thủ tiêu chuẩn:
- IFC4 Add2 TC1
- buildingSMART Data Dictionary
- TCVN 12820:2019 (BIM)
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import os
import uuid
import time
import math

# ifcopenshell imports (optional)
try:
    import ifcopenshell
    import ifcopenshell.api
    import ifcopenshell.util.element
    IFC_AVAILABLE = True
except ImportError:
    IFC_AVAILABLE = False
    print("ifcopenshell khong duoc cai dat. Bo qua chuc nang IFC.")


# Định nghĩa Property Sets chuẩn cho công trình xử lý nước
TANK_PROPERTY_SETS = {
    "Pset_TankCommon": {
        "Reference": "str",
        "Status": "str",  # NEW, EXISTING, DEMOLISH
        "NominalCapacity": "float",  # m³
        "OperationalTemperatureRange": "str",
        "NominalDepth": "float",  # m
        "NumberOfSections": "int",
    },
    "Pset_TankTypeWaterTreatment": {
        "TreatmentProcess": "str",  # Sedimentation, Aeration, etc
        "DesignFlow": "float",  # m³/day
        "HydraulicRetentionTime": "float",  # hours
        "SurfaceLoadingRate": "float",  # m³/m²/day
        "WeirLoadingRate": "float",  # m³/m/day
        "SludgeVolume": "float",  # m³
        "AerationSystem": "str",
        "Efficiency": "float",  # %
    },
    "Pset_StructuralReinforcement": {
        "ConcreteGrade": "str",  # C25/30, C30/37, etc
        "SteelGrade": "str",  # CB400-V, CB500-V
        "WallReinforcement": "str",  # Ø12@150
        "BottomReinforcement": "str",
        "CoverThickness": "float",  # mm
        "JointSpacing": "float",  # m
    },
}

PIPE_PROPERTY_SETS = {
    "Pset_PipeSegmentCommon": {
        "Reference": "str",
        "Status": "str",
        "NominalDiameter": "float",  # mm
        "InnerDiameter": "float",  # mm
        "OuterDiameter": "float",  # mm
        "Length": "float",  # m
        "Slope": "float",  # %
        "DesignVelocity": "float",  # m/s
        "DesignFlow": "float",  # l/s
        "PressureClass": "str",
    },
    "Pset_PipeMaterial": {
        "Material": "str",  # HDPE, uPVC, DUCTILE IRON
        "Grade": "str",  # PE100, PN10
        "Manufacturer": "str",
        "Standard": "str",  # TCVN, ISO
    },
}


class IFCGenerator:
    """
    Tạo mô hình IFC/BIM chuyên nghiệp cho công trình xử lý nước
    
    Hỗ trợ đầy đủ các entity IFC4:
    - IfcProject: Dự án với metadata
    - IfcSite: Công trường với tọa độ WGS84
    - IfcBuilding: Công trình với phân loại
    - IfcBuildingStorey: Các cao độ
    - IfcTank: Bể xử lý với thông số thủy lực
    - IfcPipeSegment: Đường ống với thông số kỹ thuật
    - IfcBuildingElementProxy: Các cấu kiện khác
    
    Metadata:
    - Author, Organization
    - Application version
    - Creation/modification timestamps
    - Project classification (OmniClass, Uniclass)
    """
    
    def __init__(self, output_dir: str = "./outputs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.ifc_file = None
        self.project = None
        self.site = None
        self.building = None
        self.storey = None
        self.elements = []
        
        # Metadata
        self.author = "HydroDraft"
        self.organization = "Water Treatment Engineering"
        self.application = "HydroDraft BIM Generator v1.0"
    
    def create_new_model(
        self,
        project_name: str = "Dự án Xử lý Nước",
        site_name: str = "Công trường",
        building_name: str = "Trạm xử lý",
        project_number: str = None,
        client_name: str = None,
        location: Dict[str, float] = None,  # {"lat": 10.xx, "lon": 106.xx}
        design_phase: str = "THIẾT KẾ KỸ THUẬT"
    ) -> None:
        """
        Tạo mô hình IFC mới với cấu trúc đầy đủ
        
        Args:
            project_name: Tên dự án
            site_name: Tên công trường
            building_name: Tên công trình
            project_number: Mã dự án
            client_name: Tên chủ đầu tư
            location: Tọa độ địa lý (WGS84)
            design_phase: Giai đoạn thiết kế
        """
        if not IFC_AVAILABLE:
            self._create_model_fallback(project_name, site_name, building_name)
            return
        
        # Tạo file IFC mới với schema IFC4
        self.ifc_file = ifcopenshell.file(schema="IFC4")
        
        # Tạo Owner History
        person = self.ifc_file.createIfcPerson(
            None, "HydroDraft", None, None, None, None, None, None
        )
        organization = self.ifc_file.createIfcOrganization(
            None, self.organization, "Thiết kế công trình xử lý nước", None, None
        )
        person_org = self.ifc_file.createIfcPersonAndOrganization(person, organization, None)
        
        application = self.ifc_file.createIfcApplication(
            organization,
            "1.0",
            self.application,
            "HydroDraft"
        )
        
        owner_history = self.ifc_file.createIfcOwnerHistory(
            person_org,
            application,
            "READWRITE",
            None,
            None,
            None,
            None,
            int(time.time())
        )
        
        # Tạo Project
        self.project = ifcopenshell.api.run(
            "root.create_entity",
            self.ifc_file,
            ifc_class="IfcProject",
            name=project_name
        )
        
        # Thêm description cho project
        if project_number:
            self.project.Description = f"Mã dự án: {project_number}"
        if design_phase:
            self.project.Phase = design_phase
        
        # Thiết lập đơn vị (mét, độ C, giây)
        ifcopenshell.api.run(
            "unit.assign_unit",
            self.ifc_file,
            length={"is_metric": True, "raw": "METERS"},
            area={"is_metric": True, "raw": "SQUARE_METRES"},
            volume={"is_metric": True, "raw": "CUBIC_METRES"}
        )
        
        # Tạo Site với tọa độ nếu có
        self.site = ifcopenshell.api.run(
            "root.create_entity",
            self.ifc_file,
            ifc_class="IfcSite",
            name=site_name
        )
        
        # Thêm tọa độ địa lý
        if location:
            lat = location.get("lat", 10.8231)  # Default: TP.HCM
            lon = location.get("lon", 106.6297)
            # Convert to IFC format (degrees, minutes, seconds, millionths)
            lat_deg = int(lat)
            lat_min = int((lat - lat_deg) * 60)
            lat_sec = int(((lat - lat_deg) * 60 - lat_min) * 60)
            lat_ms = int((((lat - lat_deg) * 60 - lat_min) * 60 - lat_sec) * 1000000)
            
            lon_deg = int(lon)
            lon_min = int((lon - lon_deg) * 60)
            lon_sec = int(((lon - lon_deg) * 60 - lon_min) * 60)
            lon_ms = int((((lon - lon_deg) * 60 - lon_min) * 60 - lon_sec) * 1000000)
            
            self.site.RefLatitude = (lat_deg, lat_min, lat_sec, lat_ms)
            self.site.RefLongitude = (lon_deg, lon_min, lon_sec, lon_ms)
            self.site.RefElevation = location.get("elevation", 0.0)
        
        ifcopenshell.api.run(
            "aggregate.assign_object",
            self.ifc_file,
            product=self.site,
            relating_object=self.project
        )
        
        # Thêm thuộc tính cho Site
        self._add_element_properties(self.site, "Pset_SiteCommon", {
            "Reference": site_name,
            "BuildableArea": 0.0,
            "TotalArea": 0.0,
        })
        
        # Tạo Building
        self.building = ifcopenshell.api.run(
            "root.create_entity",
            self.ifc_file,
            ifc_class="IfcBuilding",
            name=building_name
        )
        self.building.Description = "Trạm xử lý nước thải"
        self.building.CompositionType = "ELEMENT"
        
        ifcopenshell.api.run(
            "aggregate.assign_object",
            self.ifc_file,
            product=self.building,
            relating_object=self.site
        )
        
        # Thêm thuộc tính Building
        self._add_element_properties(self.building, "Pset_BuildingCommon", {
            "Reference": building_name,
            "BuildingID": project_number or str(uuid.uuid4())[:8],
            "IsLandmarked": False,
            "YearOfConstruction": datetime.now().year,
            "OccupancyType": "INDUSTRIAL",
        })
        
        # Tạo Storey (cao độ 0.000)
        self.storey = ifcopenshell.api.run(
            "root.create_entity",
            self.ifc_file,
            ifc_class="IfcBuildingStorey",
            name="Cao độ ±0.000"
        )
        self.storey.Elevation = 0.0
        
        ifcopenshell.api.run(
            "aggregate.assign_object",
            self.ifc_file,
            product=self.storey,
            relating_object=self.building
        )
    
    def add_tank(
        self,
        name: str,
        length: float,
        width: float,
        depth: float,
        wall_thickness: float,
        origin: Tuple[float, float, float] = (0, 0, 0),
        tank_type: str = "sedimentation",
        hydraulic_data: Dict[str, Any] = None,
        structural_data: Dict[str, Any] = None,
        properties: Dict[str, Any] = None
    ) -> Optional[Any]:
        """
        Thêm bể vào mô hình IFC với đầy đủ thuộc tính kỹ thuật
        
        Args:
            name: Tên/ký hiệu bể (VD: "BE-01", "SEDIMENT-1")
            length: Chiều dài trong (m)
            width: Chiều rộng trong (m)
            depth: Chiều sâu nước (m)
            wall_thickness: Chiều dày thành (m)
            origin: Gốc tọa độ (x, y, z)
            tank_type: Loại bể (sedimentation, aeration, storage, etc)
            hydraulic_data: Dữ liệu thủy lực
                - design_flow: Lưu lượng thiết kế (m³/ngày)
                - retention_time: Thời gian lưu (giờ)
                - surface_loading: Tải trọng bề mặt (m³/m²/ngày)
                - weir_loading: Tải trọng máng tràn (m³/m/ngày)
            structural_data: Dữ liệu kết cấu
                - concrete_grade: Mác bê tông
                - steel_grade: Mác thép
                - wall_reinforcement: Cốt thép thành
                - bottom_reinforcement: Cốt thép đáy
            properties: Thuộc tính bổ sung khác
            
        Returns:
            IFC entity hoặc None
        """
        if not IFC_AVAILABLE or not self.ifc_file:
            return self._add_tank_fallback(
                name, length, width, depth, wall_thickness, origin, tank_type, properties
            )
        
        # Tạo entity IfcTank
        tank = ifcopenshell.api.run(
            "root.create_entity",
            self.ifc_file,
            ifc_class="IfcTank",
            name=name
        )
        
        # Thiết lập PredefinedType
        tank_predefined_types = {
            "sedimentation": "BASIN",
            "storage": "STORAGE",
            "aeration": "VESSEL",
            "buffer": "STORAGE",
            "filtration": "VESSEL",
        }
        tank.PredefinedType = tank_predefined_types.get(tank_type, "USERDEFINED")
        
        # Thêm description
        tank.Description = f"Bể {tank_type.capitalize()} - {name}"
        
        # Gán vào storey
        ifcopenshell.api.run(
            "spatial.assign_container",
            self.ifc_file,
            product=tank,
            relating_structure=self.storey
        )
        
        # Tạo hình học
        t = wall_thickness
        outer_length = length + 2 * t
        outer_width = width + 2 * t
        total_depth = depth + 0.3 + t  # depth + freeboard + bottom
        
        # Tạo representation (đơn giản hóa - hộp)
        representation = self._create_box_representation(
            outer_length, outer_width, total_depth,
            origin[0], origin[1], origin[2]
        )
        
        if representation:
            ifcopenshell.api.run(
                "geometry.assign_representation",
                self.ifc_file,
                product=tank,
                representation=representation
            )
        
        # Tính toán các thông số
        volume = length * width * depth
        surface_area = length * width
        
        # Thêm Property Set chung (Pset_TankCommon)
        common_props = {
            "Reference": name,
            "Status": "NEW",
            "NominalCapacity": round(volume, 2),
            "NominalDepth": depth,
            "NumberOfSections": 1,
        }
        self._add_element_properties(tank, "Pset_TankCommon", common_props)
        
        # Thêm Property Set thủy lực (Custom)
        hyd = hydraulic_data or {}
        hydraulic_props = {
            "Loại_bể": tank_type,
            "Chiều_dài_trong": length,
            "Chiều_rộng_trong": width,
            "Chiều_sâu_nước": depth,
            "Chiều_dày_thành": wall_thickness,
            "Thể_tích": round(volume, 2),
            "Diện_tích_bề_mặt": round(surface_area, 2),
            "Lưu_lượng_thiết_kế": hyd.get("design_flow", 0),
            "Thời_gian_lưu": hyd.get("retention_time", 0),
            "Tải_trọng_bề_mặt": hyd.get("surface_loading", 0),
            "Tải_trọng_máng_tràn": hyd.get("weir_loading", 0),
        }
        self._add_element_properties(tank, "Pset_TankHydraulic", hydraulic_props)
        
        # Thêm Property Set kết cấu (Custom)
        struct = structural_data or {}
        if struct:
            structural_props = {
                "Mác_bê_tông": struct.get("concrete_grade", "C25/30"),
                "Mác_thép": struct.get("steel_grade", "CB400-V"),
                "Cốt_thép_thành": struct.get("wall_reinforcement", "Ø12@150"),
                "Cốt_thép_đáy": struct.get("bottom_reinforcement", "Ø12@150"),
                "Lớp_bảo_vệ": struct.get("cover", 50),
                "Chiều_dày_đáy": struct.get("bottom_thickness", 0.3),
                "Khối_lượng_bê_tông": struct.get("concrete_volume", 0),
                "Khối_lượng_thép": struct.get("steel_weight", 0),
            }
            self._add_element_properties(tank, "Pset_TankStructural", structural_props)
        
        # Thêm các thuộc tính bổ sung
        if properties:
            self._add_element_properties(tank, "Pset_TankCustom", properties)
        
        # Lưu vào danh sách elements
        self.elements.append({
            "entity": tank,
            "type": "tank",
            "name": name
        })
        
        return tank
    
    def add_pipe_segment(
        self,
        name: str,
        start_point: Tuple[float, float, float],
        end_point: Tuple[float, float, float],
        diameter: float,  # mm
        material: str = "HDPE",
        pipe_class: str = "PN10",
        flow_data: Dict[str, Any] = None,
        properties: Dict[str, Any] = None
    ) -> Optional[Any]:
        """
        Thêm đoạn ống vào mô hình IFC với đầy đủ thông số kỹ thuật
        
        Args:
            name: Tên đoạn ống (VD: "PIPE-001", "MAIN-01")
            start_point: Điểm đầu (x, y, z) - m
            end_point: Điểm cuối (x, y, z) - m
            diameter: Đường kính danh nghĩa (mm)
            material: Vật liệu (HDPE, uPVC, DUCTILE_IRON, STEEL, etc)
            pipe_class: Cấp áp lực (PN6, PN10, PN16, etc)
            flow_data: Dữ liệu dòng chảy
                - flow_rate: Lưu lượng (l/s)
                - velocity: Vận tốc (m/s)
                - head_loss: Tổn thất cột nước (m)
                - fill_ratio: Độ đầy ống (%)
            properties: Thuộc tính bổ sung
            
        Returns:
            IFC entity hoặc None
        """
        if not IFC_AVAILABLE or not self.ifc_file:
            return self._add_pipe_fallback(
                name, start_point, end_point, diameter, material, properties
            )
        
        # Tạo entity IfcPipeSegment
        pipe = ifcopenshell.api.run(
            "root.create_entity",
            self.ifc_file,
            ifc_class="IfcPipeSegment",
            name=name
        )
        
        # Thiết lập PredefinedType
        pipe.PredefinedType = "RIGIDSEGMENT"
        
        # Gán vào storey
        ifcopenshell.api.run(
            "spatial.assign_container",
            self.ifc_file,
            product=pipe,
            relating_structure=self.storey
        )
        
        # Tính toán thông số
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        dz = end_point[2] - start_point[2]
        length = math.sqrt(dx**2 + dy**2 + dz**2)
        horizontal_length = math.sqrt(dx**2 + dy**2)
        
        # Tính độ dốc
        slope = 0
        if horizontal_length > 0:
            slope = round((dz / horizontal_length) * 100, 2)  # %
        
        # Tính đường kính trong (ước tính)
        wall_thickness_map = {
            "HDPE": 0.1,  # 10% đường kính
            "uPVC": 0.08,
            "DUCTILE_IRON": 0.05,
            "STEEL": 0.03,
        }
        wall_ratio = wall_thickness_map.get(material, 0.1)
        inner_diameter = diameter * (1 - 2 * wall_ratio)
        
        # Thêm Property Set chung
        common_props = {
            "Reference": name,
            "Status": "NEW",
            "NominalDiameter": diameter,
            "InnerDiameter": round(inner_diameter, 1),
            "OuterDiameter": diameter,
            "Length": round(length, 2),
            "Slope": slope,
        }
        self._add_element_properties(pipe, "Pset_PipeSegmentCommon", common_props)
        
        # Thêm thuộc tính vật liệu
        material_props = {
            "Vật_liệu": material,
            "Cấp_áp_lực": pipe_class,
            "Tiêu_chuẩn": "TCVN" if material in ["uPVC", "HDPE"] else "ISO",
            "Khả_năng_chịu_áp": int(pipe_class.replace("PN", "")) if "PN" in pipe_class else 10,
        }
        self._add_element_properties(pipe, "Pset_PipeMaterial", material_props)
        
        # Thêm dữ liệu dòng chảy nếu có
        flow = flow_data or {}
        if flow:
            flow_props = {
                "Lưu_lượng": flow.get("flow_rate", 0),
                "Vận_tốc": flow.get("velocity", 0),
                "Tổn_thất_cột_nước": flow.get("head_loss", 0),
                "Độ_đầy_ống": flow.get("fill_ratio", 0),
                "Cao_độ_đầu": start_point[2],
                "Cao_độ_cuối": end_point[2],
                "Chênh_cao": round(dz, 3),
            }
            self._add_element_properties(pipe, "Pset_PipeFlow", flow_props)
        
        # Thêm thuộc tính bổ sung
        if properties:
            self._add_element_properties(pipe, "Pset_PipeCustom", properties)
        
        # Lưu vào danh sách elements
        self.elements.append({
            "entity": pipe,
            "type": "pipe",
            "name": name
        })
        
        return pipe
    
    def add_manhole(
        self,
        name: str,
        x: float,
        y: float,
        ground_level: float,
        invert_level: float,
        diameter: float = 1000,  # mm
        properties: Dict[str, Any] = None
    ) -> Optional[Any]:
        """
        Thêm giếng thăm vào mô hình IFC
        
        Args:
            name: Tên/ID giếng
            x, y: Tọa độ
            ground_level: Cao độ mặt đất (m)
            invert_level: Cao độ đáy (m)
            diameter: Đường kính (mm)
            properties: Thuộc tính bổ sung
            
        Returns:
            IFC entity hoặc None
        """
        if not IFC_AVAILABLE or not self.ifc_file:
            return self._add_manhole_fallback(
                name, x, y, ground_level, invert_level, diameter, properties
            )
        
        # Sử dụng IfcBuildingElementProxy cho giếng thăm
        manhole = ifcopenshell.api.run(
            "root.create_entity",
            self.ifc_file,
            ifc_class="IfcBuildingElementProxy",
            name=name
        )
        
        # Gán vào storey
        ifcopenshell.api.run(
            "spatial.assign_container",
            self.ifc_file,
            product=manhole,
            relating_structure=self.storey
        )
        
        # Thêm thuộc tính
        depth = ground_level - invert_level
        self._add_element_properties(manhole, "Pset_ManholeChamber", {
            "Loại": "Giếng thăm",
            "Tọa độ X": x,
            "Tọa độ Y": y,
            "Cao độ mặt đất": ground_level,
            "Cao độ đáy": invert_level,
            "Chiều sâu": round(depth, 2),
            "Đường kính": diameter,
            **(properties or {})
        })
        
        return manhole
    
    def add_well(
        self,
        name: str,
        x: float,
        y: float,
        ground_level: float,
        total_depth: float,
        casing_diameter: float,
        well_type: str = "monitoring",
        properties: Dict[str, Any] = None
    ) -> Optional[Any]:
        """
        Thêm giếng quan trắc vào mô hình IFC
        
        Args:
            name: Tên giếng
            x, y: Tọa độ
            ground_level: Cao độ mặt đất (m)
            total_depth: Chiều sâu (m)
            casing_diameter: Đường kính ống chống (mm)
            well_type: Loại giếng
            properties: Thuộc tính bổ sung
            
        Returns:
            IFC entity hoặc None
        """
        if not IFC_AVAILABLE or not self.ifc_file:
            return self._add_well_fallback(
                name, x, y, ground_level, total_depth, casing_diameter, well_type, properties
            )
        
        # Sử dụng IfcBuildingElementProxy cho giếng
        well = ifcopenshell.api.run(
            "root.create_entity",
            self.ifc_file,
            ifc_class="IfcBuildingElementProxy",
            name=name
        )
        
        # Gán vào storey
        ifcopenshell.api.run(
            "spatial.assign_container",
            self.ifc_file,
            product=well,
            relating_structure=self.storey
        )
        
        # Thêm thuộc tính
        self._add_element_properties(well, "Pset_MonitoringWell", {
            "Loại giếng": well_type,
            "Tọa độ X": x,
            "Tọa độ Y": y,
            "Cao độ mặt đất": ground_level,
            "Chiều sâu": total_depth,
            "Cao độ đáy": ground_level - total_depth,
            "Đường kính ống chống": casing_diameter,
            **(properties or {})
        })
        
        return well
    
    def _create_box_representation(
        self,
        length: float,
        width: float,
        height: float,
        x: float,
        y: float,
        z: float
    ) -> Optional[Any]:
        """Tạo representation hình hộp"""
        if not IFC_AVAILABLE:
            return None
        
        # Tạo placement
        context = self.ifc_file.by_type("IfcGeometricRepresentationContext")[0]
        
        # Tạo extruded area solid
        profile = self.ifc_file.createIfcRectangleProfileDef(
            "AREA",
            None,
            None,
            length,
            width
        )
        
        direction = self.ifc_file.createIfcDirection([0.0, 0.0, 1.0])
        
        solid = self.ifc_file.createIfcExtrudedAreaSolid(
            profile,
            None,
            direction,
            height
        )
        
        representation = self.ifc_file.createIfcShapeRepresentation(
            context,
            "Body",
            "SweptSolid",
            [solid]
        )
        
        return representation
    
    def _add_tank_properties(self, tank: Any, properties: Dict[str, Any]) -> None:
        """Thêm thuộc tính cho bể"""
        if not IFC_AVAILABLE:
            return
        
        self._add_element_properties(tank, "Pset_TankCommon", properties)
    
    def _add_pipe_properties(self, pipe: Any, properties: Dict[str, Any]) -> None:
        """Thêm thuộc tính cho ống"""
        if not IFC_AVAILABLE:
            return
        
        self._add_element_properties(pipe, "Pset_PipeSegmentCommon", properties)
    
    def _add_element_properties(
        self,
        element: Any,
        pset_name: str,
        properties: Dict[str, Any]
    ) -> None:
        """Thêm property set cho element"""
        if not IFC_AVAILABLE or not self.ifc_file:
            return
        
        # Tạo property set
        pset = ifcopenshell.api.run(
            "pset.add_pset",
            self.ifc_file,
            product=element,
            name=pset_name
        )
        
        # Thêm các thuộc tính
        ifcopenshell.api.run(
            "pset.edit_pset",
            self.ifc_file,
            pset=pset,
            properties=properties
        )
    
    def save(self, filename: str) -> Optional[str]:
        """
        Lưu file IFC
        
        Args:
            filename: Tên file
            
        Returns:
            str: Đường dẫn file hoặc None
        """
        if not IFC_AVAILABLE or not self.ifc_file:
            return self._save_fallback(filename)
        
        if not filename.endswith('.ifc'):
            filename += '.ifc'
        
        filepath = os.path.join(self.output_dir, filename)
        self.ifc_file.write(filepath)
        
        return filepath
    
    # Các phương thức fallback khi không có ifcopenshell
    def _create_model_fallback(
        self,
        project_name: str,
        site_name: str,
        building_name: str
    ) -> None:
        """Fallback khi không có ifcopenshell"""
        self.ifc_data = {
            "schema": "IFC4",
            "project": {
                "name": project_name,
                "created": datetime.now().isoformat()
            },
            "site": {"name": site_name},
            "building": {"name": building_name},
            "elements": []
        }
    
    def _add_tank_fallback(
        self,
        name: str,
        length: float,
        width: float,
        depth: float,
        wall_thickness: float,
        origin: Tuple[float, float, float],
        tank_type: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback cho add_tank"""
        element = {
            "type": "IfcTank",
            "name": name,
            "geometry": {
                "length": length,
                "width": width,
                "depth": depth,
                "wall_thickness": wall_thickness,
                "origin": origin
            },
            "properties": {
                "tank_type": tank_type,
                "volume": length * width * depth,
                **(properties or {})
            }
        }
        
        if hasattr(self, 'ifc_data'):
            self.ifc_data["elements"].append(element)
        
        return element
    
    def _add_pipe_fallback(
        self,
        name: str,
        start_point: Tuple[float, float, float],
        end_point: Tuple[float, float, float],
        diameter: float,
        material: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback cho add_pipe_segment"""
        import math
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        dz = end_point[2] - start_point[2]
        length = math.sqrt(dx**2 + dy**2 + dz**2)
        
        element = {
            "type": "IfcPipeSegment",
            "name": name,
            "geometry": {
                "start_point": start_point,
                "end_point": end_point,
                "diameter": diameter,
                "length": round(length, 2)
            },
            "properties": {
                "material": material,
                **(properties or {})
            }
        }
        
        if hasattr(self, 'ifc_data'):
            self.ifc_data["elements"].append(element)
        
        return element
    
    def _add_manhole_fallback(
        self,
        name: str,
        x: float,
        y: float,
        ground_level: float,
        invert_level: float,
        diameter: float,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback cho add_manhole"""
        element = {
            "type": "IfcBuildingElementProxy",
            "name": name,
            "predefined_type": "Manhole",
            "geometry": {
                "x": x,
                "y": y,
                "ground_level": ground_level,
                "invert_level": invert_level,
                "diameter": diameter,
                "depth": ground_level - invert_level
            },
            "properties": properties or {}
        }
        
        if hasattr(self, 'ifc_data'):
            self.ifc_data["elements"].append(element)
        
        return element
    
    def _add_well_fallback(
        self,
        name: str,
        x: float,
        y: float,
        ground_level: float,
        total_depth: float,
        casing_diameter: float,
        well_type: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback cho add_well"""
        element = {
            "type": "IfcBuildingElementProxy",
            "name": name,
            "predefined_type": "Well",
            "geometry": {
                "x": x,
                "y": y,
                "ground_level": ground_level,
                "total_depth": total_depth,
                "casing_diameter": casing_diameter
            },
            "properties": {
                "well_type": well_type,
                **(properties or {})
            }
        }
        
        if hasattr(self, 'ifc_data'):
            self.ifc_data["elements"].append(element)
        
        return element
    
    def _save_fallback(self, filename: str) -> str:
        """Fallback save - xuất JSON thay vì IFC"""
        import json
        
        if not filename.endswith('.json'):
            filename = filename.replace('.ifc', '') + '_ifc_data.json'
        
        filepath = os.path.join(self.output_dir, filename)
        
        if hasattr(self, 'ifc_data'):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.ifc_data, f, ensure_ascii=False, indent=2)
        
        return filepath
