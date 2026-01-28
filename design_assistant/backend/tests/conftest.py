"""
Test configuration and fixtures
"""

import pytest
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_tank_input():
    """Sample tank design input"""
    return {
        "project_name": "Test Project",
        "tank_name": "BL-01",
        "tank_type": "sedimentation",
        "flow_rate": 1000,
        "detention_time": 2.0,
        "surface_loading_rate": 35,
        "depth": 3.0,
        "number_of_tanks": 2,
        "length_width_ratio": 3.0,
        "wall_thickness": 0.25,
        "bottom_thickness": 0.3,
        "generate_drawing": False
    }


@pytest.fixture
def sample_pipeline_input():
    """Sample pipeline design input"""
    return {
        "project_name": "Pipeline Test",
        "pipeline_name": "TN-01",
        "pipe_type": "gravity",
        "flow_type": "wastewater",
        "design_flow": 100,
        "material": "concrete",
        "min_cover_depth": 0.7,
        "manholes": [
            {"station": 0, "ground_level": 10.0, "name": "MH1"},
            {"station": 50, "ground_level": 9.8, "name": "MH2"},
            {"station": 100, "ground_level": 9.5, "name": "MH3"}
        ]
    }


@pytest.fixture
def sample_well_input():
    """Sample well design input"""
    return {
        "project_name": "Well Test",
        "well_name": "GQT-01",
        "well_type": "monitoring",
        "aquifer_depth": 30,
        "water_table_depth": 5,
        "target_yield": 10,
        "casing_material": "PVC"
    }


@pytest.fixture
def sample_project_info():
    """Sample project information"""
    return {
        "project_name": "Test XLNT Project",
        "project_code": "XLNT-2024-TEST",
        "client": "Test Client",
        "location": "Test Location",
        "prepared_by": "Test User"
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory"""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return str(output_dir)


@pytest.fixture
def cleanup_outputs():
    """Cleanup test outputs after tests"""
    yield
    # Cleanup logic here if needed
    import shutil
    test_dirs = [
        "./outputs/test_*",
    ]
    for pattern in test_dirs:
        import glob
        for path in glob.glob(pattern):
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
