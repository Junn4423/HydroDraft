"""
Calculations module - Động cơ tính toán thiết kế

SPRINT 2: TRANSPARENT ENGINEERING
- Mọi tính toán đều có log chi tiết
- Công thức LaTeX
- Tham chiếu tiêu chuẩn
- Kiểm tra vi phạm tự động
"""

# Legacy modules (backward compatibility)
from .hydraulic import HydraulicCalculator
from .tank_design import TankDesignCalculator
from .pipe_design import PipeDesignCalculator
from .structural import StructuralCalculator

# SPRINT 2: Traceable modules
from .calculation_log import (
    CalculationLog,
    CalculationStep,
    Violation,
    CalculationStatus,
    ViolationSeverity,
    CalculationLogger,
    EngineeringConstants
)

from .hydraulic_traceable import (
    TraceableHydraulicEngine,
    TraceableFlowResult,
    TraceableHeadLossResult
)

from .structural_traceable import (
    TraceableStructuralEngine,
    WallDesignResult,
    StabilityResult
)

from .tank_design_traceable import (
    TraceableTankDesignEngine,
    TankDesignResult
)

from .safety_layer import (
    SafetyEnforcementLayer,
    DesignValidator,
    OverrideRecord,
    SafetyCheckResult,
    get_safety_layer
)

# SPRINT 5: Advanced modules
from .plate_moment_tables import (
    PlateMomentTables,
    AdvancedWallDesign,
    MomentResult,
    PlateGeometry
)

from .crack_control import (
    CrackWidthChecker,
    CrackWidthCalculatorTCVN,
    CrackCheckResult,
    ExposureClass
)

from .tank_optimizer import (
    TankCostOptimizer,
    AutoSizingCalculator,
    TankType,
    MaterialCost,
    TankConstraints,
    OptimizationResult
)

# Aliases for V2 (new traceable versions)
HydraulicCalculatorV2 = TraceableHydraulicEngine
StructuralCalculatorV2 = TraceableStructuralEngine
TankDesignCalculatorV2 = TraceableTankDesignEngine

