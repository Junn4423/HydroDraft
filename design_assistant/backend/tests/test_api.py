"""
Test Suite for HydroDraft Backend API
Covers all major API endpoints and functionality
"""

import pytest
from fastapi.testclient import TestClient
import json
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoints"""
    
    def test_health_endpoint(self):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        
    def test_api_health_endpoint(self):
        """Test API health check"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestTankDesignAPI:
    """Test tank design endpoints"""
    
    def test_tank_design_basic(self):
        """Test basic tank design"""
        payload = {
            "project_name": "Test Project",
            "tank_name": "BL-01",
            "tank_type": "sedimentation",
            "flow_rate": 1000,
            "detention_time": 2.0,
            "depth": 3.0,
            "number_of_tanks": 2,
            "length_width_ratio": 3.0,
            "wall_thickness": 0.25,
            "bottom_thickness": 0.3,
            "generate_drawing": False
        }
        
        response = client.post("/api/v1/design/tank/", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "job_id" in data
        assert "status" in data
        assert "dimensions" in data
        assert "hydraulic_results" in data
        
    def test_tank_design_with_drawing(self):
        """Test tank design with DXF generation"""
        payload = {
            "project_name": "Test Project",
            "tank_name": "BL-02",
            "tank_type": "storage",
            "flow_rate": 500,
            "detention_time": 4.0,
            "depth": 4.0,
            "number_of_tanks": 1,
            "generate_drawing": True
        }
        
        response = client.post("/api/v1/design/tank/", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "job_id" in data
        
    def test_tank_design_validation_error(self):
        """Test validation error for invalid input"""
        payload = {
            "project_name": "",
            "tank_name": "",
            "flow_rate": -100,  # Invalid negative flow rate
        }
        
        response = client.post("/api/v1/design/tank/", json=payload)
        assert response.status_code == 422  # Validation error
        
    def test_tank_calculate_endpoint(self):
        """Test quick calculation endpoint"""
        payload = {
            "project_name": "Quick Calc",
            "tank_name": "QC-01",
            "tank_type": "sedimentation",
            "flow_rate": 1000,
            "detention_time": 2.0,
            "depth": 3.0,
            "number_of_tanks": 2
        }
        
        response = client.post("/api/v1/design/tank/calculate", json=payload)
        assert response.status_code == 200


class TestPipelineDesignAPI:
    """Test pipeline design endpoints"""
    
    def test_pipeline_design_basic(self):
        """Test basic pipeline design"""
        payload = {
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
        
        response = client.post("/api/v1/design/pipeline/", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "job_id" in data
        assert "total_length" in data
        assert "segments" in data


class TestWellDesignAPI:
    """Test well design endpoints"""
    
    def test_well_design_basic(self):
        """Test basic well design"""
        payload = {
            "project_name": "Well Test",
            "well_name": "GQT-01",
            "well_type": "monitoring",
            "x_coordinate": 100.0,
            "y_coordinate": 100.0,
            "ground_level": 10.0,
            "total_depth": 30.0,
            "casing_diameter": 110,
            "casing_material": "PVC",
            "screen_slot_size": 0.5,
            "generate_drawing": False
        }
        
        response = client.post("/api/v1/design/well/", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "job_id" in data
        assert "design" in data


class TestCADAPI:
    """Test CAD export endpoints"""
    
    def test_get_cad_dimstyles(self):
        """Test getting CAD dimension styles"""
        response = client.get("/api/v1/cad/v2/dimstyles")
        assert response.status_code == 200
        
    def test_get_cad_layers(self):
        """Test getting CAD layers"""
        response = client.get("/api/v1/cad/v2/layers")
        assert response.status_code == 200
        
    def test_get_cad_blocks(self):
        """Test getting CAD blocks"""
        response = client.get("/api/v1/cad/v2/blocks")
        assert response.status_code == 200
        
    def test_create_tank_drawing(self):
        """Test creating tank CAD drawing"""
        payload = {
            "project_name": "CAD Test",
            "drawing_title": "Test Drawing",
            "drawing_number": "TD-01",
            "length": 10,
            "width": 5,
            "water_depth": 3,
            "total_depth": 4,
            "wall_thickness": 0.3,
            "include_plan": True,
            "include_section": True
        }
        
        response = client.post("/api/v1/cad/v2/tank", json=payload)
        assert response.status_code == 200


class TestBIMAPI:
    """Test BIM export endpoints"""
    
    def test_export_tank_bim(self):
        """Test exporting tank to BIM"""
        payload = {
            "name": "Tank-01",
            "length": 10,
            "width": 5,
            "depth": 4,
            "wall_thickness": 0.3,
            "foundation_thickness": 0.4,
            "tank_type": "sedimentation",
            "origin": [0, 0, 0]
        }
        
        response = client.post("/api/v1/bim/export/tank", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "elements" in data or "files" in data
        
    def test_export_project_bim(self):
        """Test exporting project to BIM"""
        payload = {
            "project_name": "BIM Test Project",
            "project_number": "BIM-001",
            "tanks": [{
                "name": "Tank-01",
                "length": 10,
                "width": 5,
                "depth": 4,
                "wall_thickness": 0.3,
                "foundation_thickness": 0.4,
                "tank_type": "sedimentation",
                "origin": [0, 0, 0]
            }],
            "pipes": []
        }
        
        response = client.post("/api/v1/bim/export/project", json=payload)
        assert response.status_code == 200


class TestExportAPI:
    """Test file export endpoints"""
    
    def test_export_formats_list(self):
        """Test getting available export formats"""
        response = client.get("/api/v1/export/formats")
        assert response.status_code == 200
        data = response.json()
        
        assert "2D_CAD" in data
        assert "3D_CAD" in data
        assert "BIM" in data


class TestVersionAPI:
    """Test version management endpoints"""
    
    def test_create_version(self):
        """Test creating a new version"""
        payload = {
            "project_id": "TEST-001",
            "input_params": {"flow_rate": 1000, "tank_type": "sedimentation"},
            "calculation_log": {"step1": "calculated dimensions"},
            "description": "Initial version",
            "tag": "v1.0.0"
        }
        
        response = client.post("/api/v1/versions/create", json=payload)
        assert response.status_code == 200
        
    def test_list_versions(self):
        """Test listing versions for a project"""
        response = client.get("/api/v1/versions/TEST-001/list")
        assert response.status_code == 200


class TestReportsAPI:
    """Test report generation endpoints"""
    
    def test_generate_technical_report(self):
        """Test generating technical report"""
        payload = {
            "project_name": "Report Test",
            "project_code": "RPT-001",
            "client": "Test Client",
            "location": "Test Location",
            "prepared_by": "Test User",
            "project_data": {
                "design_type": "tank",
                "dimensions": {"length": 10, "width": 5}
            }
        }
        
        response = client.post("/api/v1/reports/technical", json=payload)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
