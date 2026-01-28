"""
Generators module - Tạo bản vẽ CAD/BIM

SPRINT 3: PROFESSIONAL CAD
Modules:
- dxf_generator: Generator V1 (basic)
- dxf_generator_v2: Generator V2 (professional)
- cad_blocks: Block library
- cad_standards: Layers, styles, dims
- structural_detailing: Rebar detailing
- cad_validation: Validation engine
- cad_3d_generator: 3D CAD
- ifc_generator: IFC/BIM export

SPRINT 4: BIM & ENTERPRISE
Modules:
- bim_bridge: BIM data export for Revit (Dynamo/pyRevit)
- version_manager: Engineering version control
- pdf_report: PDF technical report generation
- viewer_config: 3D viewer configuration (IFC.js)
"""

# V1 Generators (backward compatible)
from .dxf_generator import DXFGenerator
from .cad_3d_generator import CAD3DGenerator
from .ifc_generator import IFCGenerator

# V2 Professional CAD (Sprint 3)
from .cad_blocks import (
    CADBlockLibrary, 
    BlockType, 
    setup_block_library
)
from .cad_standards import (
    CADStandards, 
    CADDimensionSystem, 
    DrawingScale,
    setup_cad_standards
)
from .structural_detailing import (
    StructuralDetailer,
    RebarSpec,
    RebarGrade,
    RebarDiameter,
    create_structural_detailer
)
from .cad_validation import (
    CADValidationEngine,
    DrawingExportGuard,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    ValidationCategory,
    validate_drawing
)
from .dxf_generator_v2 import (
    ProfessionalDXFGenerator,
    DrawingMetadata,
    TankDrawingParams,
    create_professional_generator
)

# Sprint 4: BIM & Enterprise
from .bim_bridge import (
    BIMBridge,
    BIMElement,
    BIMGeometry,
    BIMMaterial,
    BIMCategory,
    BIMLevel,
    create_bim_bridge
)
from .version_manager import (
    VersionManager,
    DesignSnapshot,
    VersionDiff,
    VersionStatus,
    ChangeType,
    get_version_manager
)
from .pdf_report import (
    PDFReportGenerator,
    ReportConfig,
    ReportType,
    ReportLanguage,
    create_pdf_generator
)
from .viewer_config import (
    ViewerConfig,
    ViewerSettings,
    CameraPosition,
    SectionConfig,
    generate_viewer_html,
    generate_react_viewer_component
)
