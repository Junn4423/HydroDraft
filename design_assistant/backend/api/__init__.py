"""
API Module - Tổng hợp các routers
"""

from .tank_router import router as tank_router
from .pipeline_router import router as pipeline_router
from .well_router import router as well_router
from .export_router import router as export_router

__all__ = [
    "tank_router",
    "pipeline_router", 
    "well_router",
    "export_router"
]
