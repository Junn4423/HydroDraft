"""
BIM Bridge Module - Sprint 4: BIM & Enterprise Integration

Tạo dữ liệu JSON chuẩn cho:
- Revit (qua Dynamo/pyRevit)
- ArchiCAD
- Tekla Structures
- Các phần mềm BIM khác

Không tạo .rvt trực tiếp mà cung cấp:
1. BIM_Data.json - Dữ liệu chuẩn
2. Dynamo script - Nhập vào Revit
3. pyRevit plugin - Xử lý nâng cao
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json
import os
import uuid
import math


class BIMCategory(str, Enum):
    """Danh mục BIM theo Revit"""
    GENERIC_MODEL = "GenericModel"
    STRUCTURAL_FOUNDATION = "StructuralFoundations"
    STRUCTURAL_COLUMN = "StructuralColumns"
    STRUCTURAL_FRAMING = "StructuralFraming"
    WALLS = "Walls"
    FLOORS = "Floors"
    PIPES = "Pipes"
    PIPE_FITTINGS = "PipeFittings"
    MECHANICAL_EQUIPMENT = "MechanicalEquipment"
    PLUMBING_FIXTURES = "PlumbingFixtures"
    SITE = "Site"


class BIMLevel(str, Enum):
    """Mức độ chi tiết BIM"""
    LOD100 = "LOD100"  # Conceptual
    LOD200 = "LOD200"  # Approximate geometry
    LOD300 = "LOD300"  # Precise geometry
    LOD350 = "LOD350"  # Construction-ready
    LOD400 = "LOD400"  # Fabrication-ready


@dataclass
class BIMGeometry:
    """Geometry data cho BIM element"""
    geometry_type: str  # "Box", "Cylinder", "Extrusion", "Mesh"
    
    # Box
    length: float = 0.0
    width: float = 0.0
    height: float = 0.0
    
    # Cylinder
    radius: float = 0.0
    
    # Position
    origin_x: float = 0.0
    origin_y: float = 0.0
    origin_z: float = 0.0
    
    # Rotation (degrees)
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0
    
    # Mesh vertices (for complex geometry)
    vertices: List[Tuple[float, float, float]] = field(default_factory=list)
    faces: List[List[int]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "geometry_type": self.geometry_type,
            "dimensions": {
                "length": self.length,
                "width": self.width,
                "height": self.height,
                "radius": self.radius
            },
            "position": {
                "x": self.origin_x,
                "y": self.origin_y,
                "z": self.origin_z
            },
            "rotation": {
                "x": self.rotation_x,
                "y": self.rotation_y,
                "z": self.rotation_z
            },
            "mesh": {
                "vertices": self.vertices,
                "faces": self.faces
            } if self.vertices else None
        }


@dataclass
class BIMMaterial:
    """Vật liệu BIM"""
    name: str
    color: Tuple[int, int, int] = (128, 128, 128)  # RGB
    transparency: float = 0.0  # 0-1
    
    # Physical properties
    density: float = 0.0  # kg/m³
    thermal_conductivity: float = 0.0  # W/(m·K)
    
    # Structural properties (for concrete/steel)
    compressive_strength: float = 0.0  # MPa
    tensile_strength: float = 0.0  # MPa
    elastic_modulus: float = 0.0  # GPa
    
    # Revit material mapping
    revit_material_name: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "appearance": {
                "color": {"r": self.color[0], "g": self.color[1], "b": self.color[2]},
                "transparency": self.transparency
            },
            "physical": {
                "density": self.density,
                "thermal_conductivity": self.thermal_conductivity
            },
            "structural": {
                "compressive_strength": self.compressive_strength,
                "tensile_strength": self.tensile_strength,
                "elastic_modulus": self.elastic_modulus
            },
            "revit_material": self.revit_material_name
        }


@dataclass
class BIMParameter:
    """Shared parameter cho Revit"""
    name: str
    value: Any
    data_type: str  # "Text", "Number", "Length", "Area", "Volume", "Integer", "YesNo"
    group: str = "Data"  # Parameter group
    is_instance: bool = True  # Instance or Type parameter
    unit: str = ""
    description: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "value": self.value,
            "data_type": self.data_type,
            "group": self.group,
            "is_instance": self.is_instance,
            "unit": self.unit,
            "description": self.description
        }


@dataclass
class BIMElement:
    """BIM Element - Đối tượng chính"""
    element_id: str
    name: str
    category: BIMCategory
    family_name: str
    type_name: str
    
    # Geometry
    geometry: BIMGeometry = None
    
    # Material
    material: BIMMaterial = None
    
    # Level
    level_name: str = "Level 0"
    level_elevation: float = 0.0
    
    # Parameters
    parameters: List[BIMParameter] = field(default_factory=list)
    
    # Metadata
    lod: BIMLevel = BIMLevel.LOD300
    created_at: datetime = field(default_factory=datetime.now)
    
    # Relationships
    host_element_id: Optional[str] = None  # Parent element
    connected_elements: List[str] = field(default_factory=list)  # Connected IDs
    
    def add_parameter(self, name: str, value: Any, data_type: str = "Text", 
                      group: str = "Data", unit: str = ""):
        """Thêm parameter"""
        self.parameters.append(BIMParameter(
            name=name,
            value=value,
            data_type=data_type,
            group=group,
            unit=unit
        ))
    
    def to_dict(self) -> Dict:
        return {
            "element_id": self.element_id,
            "name": self.name,
            "category": self.category.value,
            "family_name": self.family_name,
            "type_name": self.type_name,
            "geometry": self.geometry.to_dict() if self.geometry else None,
            "material": self.material.to_dict() if self.material else None,
            "level": {
                "name": self.level_name,
                "elevation": self.level_elevation
            },
            "parameters": [p.to_dict() for p in self.parameters],
            "lod": self.lod.value,
            "created_at": self.created_at.isoformat(),
            "relationships": {
                "host_element_id": self.host_element_id,
                "connected_elements": self.connected_elements
            }
        }


@dataclass
class BIMLevel_def:
    """Định nghĩa Level trong Revit"""
    name: str
    elevation: float  # meters
    
    def to_dict(self) -> Dict:
        return {"name": self.name, "elevation": self.elevation}


class BIMBridge:
    """
    BIM Bridge - Tạo dữ liệu cho Revit/BIM software
    
    Workflow:
    1. HydroDraft tạo BIM_Data.json
    2. User import vào Revit qua Dynamo/pyRevit
    3. Revit tạo native elements từ JSON
    4. User chỉnh sửa trong Revit
    """
    
    def __init__(self, output_dir: str = "./outputs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Project info
        self.project_name = "HydroDraft Project"
        self.project_number = ""
        self.project_client = ""
        self.project_location = ""
        
        # Elements
        self.elements: List[BIMElement] = []
        self.levels: List[BIMLevel_def] = []
        self.materials: Dict[str, BIMMaterial] = {}
        
        # Default materials
        self._init_default_materials()
        self._init_default_levels()
    
    def _init_default_materials(self):
        """Khởi tạo vật liệu mặc định"""
        self.materials = {
            "Concrete_C25": BIMMaterial(
                name="Bê tông C25/30",
                color=(180, 180, 180),
                density=2500,
                compressive_strength=25,
                elastic_modulus=31,
                revit_material_name="Concrete - Cast-in-Place Concrete"
            ),
            "Concrete_C30": BIMMaterial(
                name="Bê tông C30/37",
                color=(170, 170, 170),
                density=2500,
                compressive_strength=30,
                elastic_modulus=33,
                revit_material_name="Concrete - Cast-in-Place Concrete"
            ),
            "Steel_CB300": BIMMaterial(
                name="Thép CB300-V",
                color=(80, 80, 80),
                density=7850,
                tensile_strength=300,
                elastic_modulus=200,
                revit_material_name="Steel"
            ),
            "HDPE": BIMMaterial(
                name="HDPE",
                color=(30, 30, 30),
                density=960,
                revit_material_name="Plastic - HDPE"
            ),
            "PVC": BIMMaterial(
                name="uPVC",
                color=(200, 200, 220),
                density=1400,
                revit_material_name="Plastic - PVC"
            ),
            "Water": BIMMaterial(
                name="Nước",
                color=(64, 164, 223),
                transparency=0.6,
                density=1000,
                revit_material_name="Water"
            )
        }
    
    def _init_default_levels(self):
        """Khởi tạo levels mặc định"""
        self.levels = [
            BIMLevel_def(name="Foundation", elevation=-3.0),
            BIMLevel_def(name="Level 0", elevation=0.0),
            BIMLevel_def(name="Ground", elevation=0.0),
            BIMLevel_def(name="Operating Floor", elevation=1.5),
            BIMLevel_def(name="Top of Wall", elevation=4.0),
        ]
    
    def set_project_info(self, name: str, number: str = "", 
                         client: str = "", location: str = ""):
        """Thiết lập thông tin dự án"""
        self.project_name = name
        self.project_number = number
        self.project_client = client
        self.project_location = location
    
    def add_level(self, name: str, elevation: float):
        """Thêm level"""
        self.levels.append(BIMLevel_def(name=name, elevation=elevation))
    
    def add_tank(
        self,
        name: str,
        length: float,
        width: float,
        depth: float,
        wall_thickness: float,
        foundation_thickness: float = 0.4,
        origin: Tuple[float, float, float] = (0, 0, 0),
        tank_type: str = "sedimentation",
        material_key: str = "Concrete_C30",
        design_params: Dict[str, Any] = None
    ) -> BIMElement:
        """
        Thêm bể vào mô hình BIM
        
        Args:
            name: Tên bể
            length: Chiều dài trong (m)
            width: Chiều rộng trong (m)
            depth: Chiều sâu (m)
            wall_thickness: Chiều dày tường (m)
            foundation_thickness: Chiều dày đáy (m)
            origin: Gốc tọa độ
            tank_type: Loại bể
            material_key: Key vật liệu
            design_params: Thông số thiết kế bổ sung
        """
        element_id = f"TANK_{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate outer dimensions
        outer_length = length + 2 * wall_thickness
        outer_width = width + 2 * wall_thickness
        total_height = depth + foundation_thickness
        
        # Create geometry
        geometry = BIMGeometry(
            geometry_type="Box",
            length=outer_length,
            width=outer_width,
            height=total_height,
            origin_x=origin[0],
            origin_y=origin[1],
            origin_z=origin[2] - foundation_thickness
        )
        
        # Get material
        material = self.materials.get(material_key)
        
        # Create element
        element = BIMElement(
            element_id=element_id,
            name=name,
            category=BIMCategory.GENERIC_MODEL,
            family_name="HydroDraft_Tank",
            type_name=f"Tank_{tank_type.capitalize()}",
            geometry=geometry,
            material=material,
            level_name="Level 0",
            level_elevation=0.0,
            lod=BIMLevel.LOD350
        )
        
        # Add parameters
        element.add_parameter("Tank_Type", tank_type, "Text", "HydroDraft")
        element.add_parameter("Inner_Length", length, "Length", "Dimensions", "m")
        element.add_parameter("Inner_Width", width, "Length", "Dimensions", "m")
        element.add_parameter("Depth", depth, "Length", "Dimensions", "m")
        element.add_parameter("Wall_Thickness", wall_thickness, "Length", "Dimensions", "m")
        element.add_parameter("Foundation_Thickness", foundation_thickness, "Length", "Dimensions", "m")
        element.add_parameter("Volume", length * width * depth, "Volume", "Calculated", "m³")
        element.add_parameter("Surface_Area", 2*(length*width + length*depth + width*depth), "Area", "Calculated", "m²")
        
        # Add design parameters
        if design_params:
            for key, value in design_params.items():
                dtype = "Number" if isinstance(value, (int, float)) else "Text"
                element.add_parameter(key, value, dtype, "Design")
        
        self.elements.append(element)
        return element
    
    def add_pipe(
        self,
        name: str,
        start_point: Tuple[float, float, float],
        end_point: Tuple[float, float, float],
        diameter: float,  # mm
        material_key: str = "HDPE",
        pipe_type: str = "gravity"
    ) -> BIMElement:
        """
        Thêm đoạn ống
        
        Args:
            name: Tên ống
            start_point: Điểm đầu (x, y, z) - meters
            end_point: Điểm cuối (x, y, z) - meters
            diameter: Đường kính ngoài (mm)
            material_key: Vật liệu
            pipe_type: Loại ống
        """
        element_id = f"PIPE_{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate length and direction
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        dz = end_point[2] - start_point[2]
        length = math.sqrt(dx**2 + dy**2 + dz**2)
        
        # Calculate rotation
        horizontal_length = math.sqrt(dx**2 + dy**2)
        rotation_z = math.degrees(math.atan2(dy, dx)) if horizontal_length > 0 else 0
        rotation_y = math.degrees(math.atan2(-dz, horizontal_length)) if length > 0 else 0
        
        # Midpoint for origin
        mid_x = (start_point[0] + end_point[0]) / 2
        mid_y = (start_point[1] + end_point[1]) / 2
        mid_z = (start_point[2] + end_point[2]) / 2
        
        geometry = BIMGeometry(
            geometry_type="Cylinder",
            radius=diameter / 2000,  # mm to m
            height=length,
            origin_x=mid_x,
            origin_y=mid_y,
            origin_z=mid_z,
            rotation_y=rotation_y,
            rotation_z=rotation_z
        )
        
        material = self.materials.get(material_key)
        
        element = BIMElement(
            element_id=element_id,
            name=name,
            category=BIMCategory.PIPES,
            family_name="HydroDraft_Pipe",
            type_name=f"Pipe_{material_key}_{int(diameter)}",
            geometry=geometry,
            material=material,
            lod=BIMLevel.LOD300
        )
        
        element.add_parameter("Pipe_Type", pipe_type, "Text", "HydroDraft")
        element.add_parameter("Diameter", diameter, "Length", "Dimensions", "mm")
        element.add_parameter("Length", length, "Length", "Dimensions", "m")
        element.add_parameter("Start_X", start_point[0], "Length", "Position")
        element.add_parameter("Start_Y", start_point[1], "Length", "Position")
        element.add_parameter("Start_Z", start_point[2], "Length", "Position")
        element.add_parameter("End_X", end_point[0], "Length", "Position")
        element.add_parameter("End_Y", end_point[1], "Length", "Position")
        element.add_parameter("End_Z", end_point[2], "Length", "Position")
        element.add_parameter("Slope", (start_point[2] - end_point[2]) / length * 100 if length > 0 else 0, "Number", "Calculated", "%")
        
        self.elements.append(element)
        return element
    
    def add_manhole(
        self,
        name: str,
        x: float,
        y: float,
        ground_level: float,
        invert_level: float,
        diameter: float = 1000,  # mm
        manhole_type: str = "standard"
    ) -> BIMElement:
        """
        Thêm hố ga/giếng thăm
        """
        element_id = f"MH_{uuid.uuid4().hex[:8].upper()}"
        
        depth = ground_level - invert_level
        
        geometry = BIMGeometry(
            geometry_type="Cylinder",
            radius=diameter / 2000,
            height=depth,
            origin_x=x,
            origin_y=y,
            origin_z=invert_level + depth / 2
        )
        
        element = BIMElement(
            element_id=element_id,
            name=name,
            category=BIMCategory.GENERIC_MODEL,
            family_name="HydroDraft_Manhole",
            type_name=f"Manhole_D{int(diameter)}",
            geometry=geometry,
            material=self.materials.get("Concrete_C25"),
            lod=BIMLevel.LOD300
        )
        
        element.add_parameter("Manhole_Type", manhole_type, "Text", "HydroDraft")
        element.add_parameter("Diameter", diameter, "Length", "Dimensions", "mm")
        element.add_parameter("Depth", depth, "Length", "Dimensions", "m")
        element.add_parameter("Ground_Level", ground_level, "Length", "Elevations", "m")
        element.add_parameter("Invert_Level", invert_level, "Length", "Elevations", "m")
        
        self.elements.append(element)
        return element
    
    def add_well(
        self,
        name: str,
        x: float,
        y: float,
        ground_level: float,
        total_depth: float,
        casing_diameter: float,
        well_type: str = "monitoring"
    ) -> BIMElement:
        """
        Thêm giếng quan trắc
        """
        element_id = f"WELL_{uuid.uuid4().hex[:8].upper()}"
        
        geometry = BIMGeometry(
            geometry_type="Cylinder",
            radius=casing_diameter / 2000,
            height=total_depth,
            origin_x=x,
            origin_y=y,
            origin_z=ground_level - total_depth / 2
        )
        
        element = BIMElement(
            element_id=element_id,
            name=name,
            category=BIMCategory.GENERIC_MODEL,
            family_name="HydroDraft_Well",
            type_name=f"Well_{well_type.capitalize()}",
            geometry=geometry,
            lod=BIMLevel.LOD300
        )
        
        element.add_parameter("Well_Type", well_type, "Text", "HydroDraft")
        element.add_parameter("Casing_Diameter", casing_diameter, "Length", "Dimensions", "mm")
        element.add_parameter("Total_Depth", total_depth, "Length", "Dimensions", "m")
        element.add_parameter("Ground_Level", ground_level, "Length", "Elevations", "m")
        element.add_parameter("Bottom_Level", ground_level - total_depth, "Length", "Elevations", "m")
        
        self.elements.append(element)
        return element
    
    def add_pump(
        self,
        name: str,
        x: float,
        y: float,
        z: float,
        pump_type: str = "submersible",
        capacity: float = 0,  # m³/h
        head: float = 0,  # m
        power: float = 0  # kW
    ) -> BIMElement:
        """
        Thêm bơm
        """
        element_id = f"PUMP_{uuid.uuid4().hex[:8].upper()}"
        
        geometry = BIMGeometry(
            geometry_type="Box",
            length=0.6,
            width=0.4,
            height=0.8,
            origin_x=x,
            origin_y=y,
            origin_z=z
        )
        
        element = BIMElement(
            element_id=element_id,
            name=name,
            category=BIMCategory.MECHANICAL_EQUIPMENT,
            family_name="HydroDraft_Pump",
            type_name=f"Pump_{pump_type.capitalize()}",
            geometry=geometry,
            lod=BIMLevel.LOD300
        )
        
        element.add_parameter("Pump_Type", pump_type, "Text", "HydroDraft")
        element.add_parameter("Capacity", capacity, "Number", "Performance", "m³/h")
        element.add_parameter("Head", head, "Length", "Performance", "m")
        element.add_parameter("Power", power, "Number", "Electrical", "kW")
        
        self.elements.append(element)
        return element
    
    def export_bim_data(self, filename: str = "BIM_Data.json") -> str:
        """
        Xuất file BIM_Data.json
        
        Returns:
            str: Đường dẫn file
        """
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = os.path.join(self.output_dir, filename)
        
        data = {
            "version": "1.0",
            "generator": "HydroDraft",
            "generated_at": datetime.now().isoformat(),
            "project": {
                "name": self.project_name,
                "number": self.project_number,
                "client": self.project_client,
                "location": self.project_location
            },
            "levels": [level.to_dict() for level in self.levels],
            "materials": {k: v.to_dict() for k, v in self.materials.items()},
            "elements": [elem.to_dict() for elem in self.elements],
            "statistics": {
                "total_elements": len(self.elements),
                "categories": self._count_by_category()
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _count_by_category(self) -> Dict[str, int]:
        """Đếm elements theo category"""
        counts = {}
        for elem in self.elements:
            cat = elem.category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts
    
    def generate_dynamo_script(self, filename: str = "HydroDraft_Import.dyn") -> str:
        """
        Tạo Dynamo script để import vào Revit
        
        Returns:
            str: Đường dẫn file
        """
        if not filename.endswith('.dyn'):
            filename += '.dyn'
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Dynamo script structure (JSON format)
        script = {
            "Uuid": str(uuid.uuid4()),
            "IsCustomNode": False,
            "Description": "HydroDraft BIM Import Script",
            "Name": "HydroDraft_Import",
            "ElementResolver": {
                "ResolutionMap": {}
            },
            "Inputs": [],
            "Outputs": [],
            "Nodes": self._generate_dynamo_nodes(),
            "Connectors": [],
            "Dependencies": [],
            "NodeLibraryDependencies": [
                {
                    "Name": "ProtoGeometry",
                    "Version": "2.12.0.5650",
                    "ReferenceType": "Package"
                }
            ],
            "Bindings": [],
            "View": {
                "Dynamo": {
                    "ScaleFactor": 1.0,
                    "HasRunWithoutCrash": True,
                    "IsVisibleInDynamoLibrary": True,
                    "Version": "2.12.0.5650"
                },
                "Camera": {
                    "EyeX": 0.0,
                    "EyeY": 100.0,
                    "EyeZ": 50.0
                }
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(script, f, indent=2)
        
        return filepath
    
    def _generate_dynamo_nodes(self) -> List[Dict]:
        """Tạo nodes cho Dynamo script"""
        nodes = []
        
        # File path input node
        nodes.append({
            "ConcreteType": "CoreNodeModels.Input.Filename, CoreNodeModels",
            "HintPath": "BIM_Data.json",
            "InputValue": "BIM_Data.json",
            "NodeType": "ExtensionNode",
            "Id": str(uuid.uuid4()),
            "Inputs": [],
            "Outputs": [{"Id": str(uuid.uuid4()), "Name": "path", "Type": "string"}],
            "Name": "File Path",
            "Description": "Đường dẫn file BIM_Data.json"
        })
        
        # Python script node for processing
        python_code = '''
# HydroDraft BIM Import Script for Dynamo
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('RevitServices')
from Autodesk.Revit.DB import *
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
import json

# Get Revit document
doc = DocumentManager.Instance.CurrentDBDocument

# Read BIM_Data.json
file_path = IN[0]
with open(file_path, 'r', encoding='utf-8') as f:
    bim_data = json.load(f)

created_elements = []
errors = []

# Start transaction
TransactionManager.Instance.EnsureInTransaction(doc)

try:
    for elem_data in bim_data.get('elements', []):
        try:
            name = elem_data.get('name', 'Unknown')
            category = elem_data.get('category', 'GenericModel')
            geometry = elem_data.get('geometry', {})
            
            # Create geometry based on type
            geom_type = geometry.get('geometry_type', 'Box')
            pos = geometry.get('position', {})
            dims = geometry.get('dimensions', {})
            
            x = pos.get('x', 0) * 3.28084  # m to ft
            y = pos.get('y', 0) * 3.28084
            z = pos.get('z', 0) * 3.28084
            
            point = XYZ(x, y, z)
            
            # Create DirectShape (generic geometry)
            ds_type = DirectShapeType.Create(doc, name, 
                ElementId(BuiltInCategory.OST_GenericModel))
            ds = DirectShape.CreateElement(doc, 
                ElementId(BuiltInCategory.OST_GenericModel))
            
            # Set geometry (simplified - box)
            if geom_type == 'Box':
                L = dims.get('length', 1) * 3.28084
                W = dims.get('width', 1) * 3.28084
                H = dims.get('height', 1) * 3.28084
                
                # Create box geometry
                box_min = XYZ(x - L/2, y - W/2, z)
                box_max = XYZ(x + L/2, y + W/2, z + H)
                
                # Note: Full implementation would use solid geometry
                
            # Add parameters from JSON
            for param in elem_data.get('parameters', []):
                param_name = param.get('name', '')
                param_value = param.get('value', '')
                # Set parameter value (requires shared parameter setup)
            
            created_elements.append(name)
            
        except Exception as e:
            errors.append(f"{name}: {str(e)}")

except Exception as e:
    errors.append(f"Transaction error: {str(e)}")

TransactionManager.Instance.TransactionTaskDone()

OUT = {
    "created": len(created_elements),
    "elements": created_elements,
    "errors": errors
}
'''
        
        nodes.append({
            "ConcreteType": "PythonNodeModels.PythonNode, PythonNodeModels",
            "NodeType": "PythonScriptNode",
            "Code": python_code,
            "Id": str(uuid.uuid4()),
            "Inputs": [{"Id": str(uuid.uuid4()), "Name": "IN[0]", "Type": "var"}],
            "Outputs": [{"Id": str(uuid.uuid4()), "Name": "OUT", "Type": "var"}],
            "Name": "HydroDraft Import",
            "Description": "Import BIM elements từ HydroDraft JSON"
        })
        
        return nodes
    
    def generate_pyrevit_script(self, filename: str = "HydroDraft_pyRevit.py") -> str:
        """
        Tạo pyRevit script để import vào Revit
        
        Returns:
            str: Đường dẫn file
        """
        if not filename.endswith('.py'):
            filename += '.py'
        
        filepath = os.path.join(self.output_dir, filename)
        
        script_content = '''# -*- coding: utf-8 -*-
"""
HydroDraft BIM Import Script for pyRevit

Cách sử dụng:
1. Đặt file này vào thư mục pyRevit extension
2. Chạy lệnh từ Revit
3. Chọn file BIM_Data.json từ HydroDraft
"""

__title__ = "HydroDraft\\nImport"
__doc__ = "Import BIM data từ HydroDraft JSON"
__author__ = "HydroDraft"

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from pyrevit import revit, forms, script
import json
import os

# Constants
M_TO_FT = 3.28084
MM_TO_FT = 0.00328084

doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()


def select_json_file():
    """Cho phép user chọn file JSON"""
    return forms.pick_file(
        file_ext='json',
        title='Chọn file BIM_Data.json từ HydroDraft'
    )


def load_bim_data(filepath):
    """Load dữ liệu BIM từ JSON"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_levels(bim_data):
    """Tạo levels từ BIM data"""
    created = []
    levels_data = bim_data.get('levels', [])
    
    collector = FilteredElementCollector(doc).OfClass(Level)
    existing_levels = {lvl.Name: lvl for lvl in collector}
    
    with revit.Transaction('HydroDraft - Create Levels'):
        for lvl_data in levels_data:
            name = lvl_data['name']
            elevation = lvl_data['elevation'] * M_TO_FT
            
            if name not in existing_levels:
                new_level = Level.Create(doc, elevation)
                new_level.Name = name
                created.append(name)
    
    return created


def create_tank_element(elem_data):
    """Tạo element bể"""
    geometry = elem_data.get('geometry', {})
    dims = geometry.get('dimensions', {})
    pos = geometry.get('position', {})
    
    # Get dimensions in feet
    length = dims.get('length', 1) * M_TO_FT
    width = dims.get('width', 1) * M_TO_FT
    height = dims.get('height', 1) * M_TO_FT
    
    x = pos.get('x', 0) * M_TO_FT
    y = pos.get('y', 0) * M_TO_FT
    z = pos.get('z', 0) * M_TO_FT
    
    # Create box geometry using Solid
    profile_loops = []
    
    # Create rectangular profile
    p1 = XYZ(x - length/2, y - width/2, z)
    p2 = XYZ(x + length/2, y - width/2, z)
    p3 = XYZ(x + length/2, y + width/2, z)
    p4 = XYZ(x - length/2, y + width/2, z)
    
    lines = [
        Line.CreateBound(p1, p2),
        Line.CreateBound(p2, p3),
        Line.CreateBound(p3, p4),
        Line.CreateBound(p4, p1)
    ]
    
    profile = CurveLoop()
    for line in lines:
        profile.Append(line)
    
    profile_loops.append(profile)
    
    # Extrude
    extrusion_dir = XYZ(0, 0, 1)
    solid = GeometryCreationUtilities.CreateExtrusionGeometry(
        profile_loops, extrusion_dir, height
    )
    
    return solid


def create_pipe_element(elem_data):
    """Tạo element ống"""
    params = {p['name']: p['value'] for p in elem_data.get('parameters', [])}
    
    start = XYZ(
        params.get('Start_X', 0) * M_TO_FT,
        params.get('Start_Y', 0) * M_TO_FT,
        params.get('Start_Z', 0) * M_TO_FT
    )
    end = XYZ(
        params.get('End_X', 0) * M_TO_FT,
        params.get('End_Y', 0) * M_TO_FT,
        params.get('End_Z', 0) * M_TO_FT
    )
    
    diameter = params.get('Diameter', 200) * MM_TO_FT
    
    # Create line curve
    pipe_line = Line.CreateBound(start, end)
    
    return pipe_line, diameter


def create_elements(bim_data):
    """Tạo các elements từ BIM data"""
    created = []
    errors = []
    
    elements = bim_data.get('elements', [])
    
    with revit.Transaction('HydroDraft - Import Elements'):
        for elem_data in elements:
            try:
                name = elem_data.get('name', 'Unknown')
                category_str = elem_data.get('category', 'GenericModel')
                
                # Map category
                if category_str == 'Pipes':
                    # Use Revit MEP Pipe
                    pipe_line, diameter = create_pipe_element(elem_data)
                    # Note: Full implementation would use MEP API
                    created.append(f"Pipe: {name}")
                    
                elif category_str == 'GenericModel':
                    # Use DirectShape
                    cat_id = ElementId(BuiltInCategory.OST_GenericModel)
                    
                    # Create DirectShape
                    ds = DirectShape.CreateElement(doc, cat_id)
                    
                    geom_type = elem_data.get('geometry', {}).get('geometry_type', 'Box')
                    
                    if geom_type == 'Box':
                        solid = create_tank_element(elem_data)
                        if solid:
                            ds.SetShape([solid])
                    
                    ds.SetName(name)
                    created.append(f"Tank: {name}")
                
                elif category_str == 'MechanicalEquipment':
                    created.append(f"Equipment: {name} (placeholder)")
                
            except Exception as e:
                errors.append(f"{name}: {str(e)}")
    
    return created, errors


def add_parameters_to_elements(bim_data):
    """Thêm parameters vào elements đã tạo"""
    # Note: Requires shared parameter file setup
    pass


def main():
    """Main function"""
    output.print_md("# HydroDraft BIM Import")
    
    # Select file
    json_file = select_json_file()
    if not json_file:
        forms.alert('Không có file được chọn')
        return
    
    output.print_md(f"**File:** {json_file}")
    
    # Load data
    try:
        bim_data = load_bim_data(json_file)
    except Exception as e:
        forms.alert(f'Lỗi đọc file: {str(e)}')
        return
    
    # Project info
    project = bim_data.get('project', {})
    output.print_md(f"**Dự án:** {project.get('name', 'N/A')}")
    
    stats = bim_data.get('statistics', {})
    output.print_md(f"**Số lượng elements:** {stats.get('total_elements', 0)}")
    
    # Create levels
    levels_created = create_levels(bim_data)
    if levels_created:
        output.print_md(f"**Levels tạo mới:** {', '.join(levels_created)}")
    
    # Create elements
    created, errors = create_elements(bim_data)
    
    # Report
    output.print_md("## Kết quả")
    output.print_md(f"✅ **Thành công:** {len(created)} elements")
    
    if created:
        for item in created:
            output.print_md(f"  - {item}")
    
    if errors:
        output.print_md(f"❌ **Lỗi:** {len(errors)}")
        for err in errors:
            output.print_md(f"  - {err}")
    
    forms.alert(
        f'Import hoàn tất!\\n\\nThành công: {len(created)}\\nLỗi: {len(errors)}',
        title='HydroDraft Import'
    )


if __name__ == '__main__':
    main()
'''
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return filepath


# Convenience function
def create_bim_bridge(output_dir: str = "./outputs") -> BIMBridge:
    """Factory function"""
    return BIMBridge(output_dir)
