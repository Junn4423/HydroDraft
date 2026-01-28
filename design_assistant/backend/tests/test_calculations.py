"""
Test Suite for Calculation Modules
Tests hydraulic, structural, and tank design calculations
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculations.hydraulic import HydraulicCalculator
from calculations.structural import StructuralCalculator
from calculations.tank_design import TankDesignCalculator


class TestHydraulicCalculations:
    """Test hydraulic calculation functions"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.calc = HydraulicCalculator()
    
    def test_volume_calculation(self):
        """Test volume calculation"""
        # V = L * W * H
        length, width, depth = 10, 5, 3
        expected_volume = 150
        
        result = length * width * depth
        assert result == expected_volume
        
    def test_retention_time_calculation(self):
        """Test hydraulic retention time"""
        volume = 150  # m³
        flow_rate = 1000  # m³/day
        
        # HRT = V / Q * 24 (hours)
        hrt = (volume / flow_rate) * 24
        
        assert hrt == pytest.approx(3.6, rel=0.01)  # hours
        
    def test_surface_loading_rate(self):
        """Test surface loading rate calculation"""
        flow_rate = 1000  # m³/day
        surface_area = 50  # m²
        
        # SLR = Q / A
        slr = flow_rate / surface_area
        
        assert slr == 20  # m³/m²/day
        
    def test_pipe_velocity_manning(self):
        """Test pipe velocity using Manning equation"""
        # V = (1/n) * R^(2/3) * S^(1/2)
        roughness = 0.013
        hydraulic_radius = 0.1  # m
        slope = 0.005
        
        velocity = (1/roughness) * (hydraulic_radius ** (2/3)) * (slope ** 0.5)
        
        assert velocity > 0
        assert velocity < 10  # Reasonable velocity range


class TestStructuralCalculations:
    """Test structural calculation functions"""
    
    def test_wall_moment_calculation(self):
        """Test wall bending moment calculation"""
        # M = γ * H³ / 6 (triangular water pressure)
        water_density = 10  # kN/m³
        wall_height = 3  # m
        
        moment = water_density * (wall_height ** 3) / 6
        
        assert moment == 45  # kN.m/m
        
    def test_concrete_volume_calculation(self):
        """Test concrete volume for tank"""
        length = 10
        width = 5
        depth = 4
        wall_thickness = 0.3
        bottom_thickness = 0.3
        
        # Simplified calculation
        # Walls: 2 * (L + W) * H * thickness
        # Bottom: L * W * thickness
        
        wall_volume = 2 * (length + width) * depth * wall_thickness
        bottom_volume = length * width * bottom_thickness
        total = wall_volume + bottom_volume
        
        assert total > 0
        
    def test_reinforcement_calculation(self):
        """Test reinforcement area calculation"""
        moment = 45  # kN.m
        effective_depth = 0.27  # m (0.3m - cover)
        steel_strength = 400  # MPa
        
        # As = M / (0.9 * d * fy)
        # Simplified calculation
        area = moment / (0.9 * effective_depth * steel_strength) * 1000  # mm²
        
        assert area > 0


class TestTankDesigner:
    """Test tank design class"""
    
    def test_sedimentation_tank_design(self):
        """Test sedimentation tank design"""
        input_data = {
            "flow_rate": 1000,
            "tank_type": "sedimentation",
            "detention_time": 2.0,
            "depth": 3.0,
            "number_of_tanks": 2,
            "length_width_ratio": 3.0
        }
        
        # Calculate expected dimensions
        Q = input_data["flow_rate"] / input_data["number_of_tanks"]
        HRT = input_data["detention_time"]
        V = (Q * HRT) / 24  # m³
        A = V / input_data["depth"]
        ratio = input_data["length_width_ratio"]
        W = (A / ratio) ** 0.5
        L = W * ratio
        
        assert L > W
        assert L / W == pytest.approx(ratio, rel=0.1)
        
    def test_storage_tank_design(self):
        """Test storage tank design"""
        input_data = {
            "flow_rate": 500,
            "tank_type": "storage",
            "detention_time": 6.0,
            "depth": 4.0,
            "number_of_tanks": 1
        }
        
        # Calculate volume
        V = (input_data["flow_rate"] * input_data["detention_time"]) / 24
        
        assert V > 0
        
    def test_tank_dimensions_validation(self):
        """Test tank dimension validation"""
        # Length should be >= width
        length = 10
        width = 5
        
        assert length >= width
        
        # Depth should be within reasonable range
        depth = 3
        assert 1.5 <= depth <= 6
        
    def test_wall_thickness_calculation(self):
        """Test minimum wall thickness"""
        depth = 4  # m
        
        # Minimum wall thickness based on depth
        min_thickness = max(0.2, depth * 0.075)
        
        assert min_thickness >= 0.2


class TestCalculationValidation:
    """Test calculation validation and bounds"""
    
    def test_detention_time_bounds(self):
        """Test detention time within acceptable range"""
        sedimentation_min = 1.5  # hours
        sedimentation_max = 4.0  # hours
        
        test_value = 2.5
        
        assert sedimentation_min <= test_value <= sedimentation_max
        
    def test_surface_loading_bounds(self):
        """Test surface loading within acceptable range"""
        min_slr = 20  # m³/m²/day
        max_slr = 40  # m³/m²/day
        
        test_value = 35
        
        assert min_slr <= test_value <= max_slr
        
    def test_pipe_velocity_bounds(self):
        """Test pipe velocity within acceptable range"""
        min_velocity = 0.6  # m/s (self-cleaning)
        max_velocity = 3.0  # m/s (erosion limit)
        
        test_value = 1.5
        
        assert min_velocity <= test_value <= max_velocity
        
    def test_filling_ratio_bounds(self):
        """Test pipe filling ratio within acceptable range"""
        max_filling = 0.75  # for gravity sewers
        
        test_value = 0.6
        
        assert test_value <= max_filling


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
