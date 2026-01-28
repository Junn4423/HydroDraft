"""
Test Advanced Design Modules

Test các module nâng cao:
- PCA Table Lookup
- Crack Width Control
- Tank Cost Optimizer
- Validation Dashboard
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculations.plate_moment_tables import PlateMomentTables, AdvancedWallDesign
from calculations.crack_control import CrackWidthChecker, CrackCheckResult
from calculations.tank_optimizer import TankCostOptimizer, AutoSizingCalculator, TankType, MaterialCost
from api.validation_dashboard import TankValidationBuilder, VersionComparer


class TestPlateMomentTables:
    """Test module tra bảng PCA"""
    
    def test_wall_moment_calculation(self):
        """Test tính moment thành bể"""
        result = PlateMomentTables.calculate_wall_moment(
            height=4.0,
            width=8.0,
            water_depth=3.5
        )
        
        assert result.Mx_positive > 0
        assert result.My_positive > 0
        assert result.alpha_x > 0
        assert result.alpha_y > 0
        print(f"\n✓ Mx+ = {result.Mx_positive} kN.m/m")
        print(f"✓ My+ = {result.My_positive} kN.m/m")
        print(f"✓ Hệ số αx = {result.alpha_x}, αy = {result.alpha_y}")
    
    def test_moment_envelope(self):
        """Test tính envelope moment"""
        results = PlateMomentTables.get_moment_envelope(
            height=4.0,
            width=8.0,
            water_depth=3.5
        )
        
        assert len(results) > 0
        print(f"\n✓ Số tổ hợp tải: {len(results)}")
        
        for name, m in results.items():
            print(f"  - {name}: Mx+={m.Mx_positive}, My+={m.My_positive}")
    
    def test_interpolation(self):
        """Test nội suy hệ số"""
        # Ratio = 1.25 (giữa 1.0 và 1.5)
        coeffs = PlateMomentTables.interpolate_coefficients(
            PlateMomentTables.WALL_TRIANGULAR_LOAD_3FIXED_1FREE,
            1.25
        )
        
        assert len(coeffs) == 4
        assert all(c > 0 for c in coeffs)
        print(f"\n✓ Hệ số nội suy tại b/a=1.25: {coeffs}")


class TestCrackWidthChecker:
    """Test module kiểm tra nứt"""
    
    def test_basic_crack_check(self):
        """Test kiểm tra nứt cơ bản"""
        result = CrackWidthChecker.check_crack_width(
            moment=50,      # kN.m
            width=1000,     # mm
            height=250,     # mm
            As=800,         # mm²
            cover=40,       # mm
            bar_diameter=12,
            concrete_grade="B25",
            steel_grade="CB400-V",
            environment="water_retaining"
        )
        
        assert isinstance(result, CrackCheckResult)
        assert result.acr_calculated > 0
        assert result.acr_limit == 0.2  # Bể chứa nước
        print(f"\n✓ acr = {result.acr_calculated} mm")
        print(f"✓ Giới hạn = {result.acr_limit} mm")
        print(f"✓ Trạng thái: {result.status}")
        print(f"✓ σs = {result.sigma_s} MPa")
    
    def test_crack_check_fail(self):
        """Test trường hợp không đạt"""
        result = CrackWidthChecker.check_crack_width(
            moment=100,     # Moment lớn
            width=1000,
            height=200,     # Tiết diện mỏng
            As=400,         # Thép ít
            cover=30,
            bar_diameter=10,
            environment="water_retaining"
        )
        
        if not result.is_satisfied:
            assert len(result.suggestions) > 0
            print(f"\n✓ Không đạt: acr = {result.acr_calculated} > {result.acr_limit}")
            print(f"✓ Khuyến nghị: {result.suggestions[0]}")
    
    def test_design_for_crack_control(self):
        """Test thiết kế theo điều kiện nứt"""
        result = CrackWidthChecker.design_for_crack_control(
            moment=60,
            width=1000,
            height=300,
            cover=40,
            environment="water_retaining"
        )
        
        if result["status"] == "OK":
            assert "bar_diameter" in result
            assert "spacing" in result
            print(f"\n✓ Thiết kế: {result['notation']}")
            print(f"✓ As = {result['As_provided']} mm²")


class TestTankCostOptimizer:
    """Test module tối ưu hóa chi phí"""
    
    def test_calculate_cost(self):
        """Test tính chi phí"""
        result = TankCostOptimizer.calculate_cost(
            length=10,
            width=5,
            water_depth=4
        )
        
        assert result["total_cost"] > 0
        assert result["concrete_volume"] > 0
        assert result["steel_weight"] > 0
        print(f"\n✓ Chi phí: {result['total_cost']:,.0f} VND")
        print(f"✓ Bê tông: {result['concrete_volume']} m³")
        print(f"✓ Thép: {result['steel_weight']} kg")
        print(f"✓ Chi phí/m³: {result['cost_per_m3']:,.0f} VND/m³")
    
    def test_optimize_dimensions(self):
        """Test tối ưu kích thước"""
        result = TankCostOptimizer.optimize_dimensions(
            volume_required=200,  # m³
            tank_type=TankType.SEDIMENTATION,
            precision="coarse"
        )
        
        assert result.length > 0
        assert result.width > 0
        assert result.total_cost > 0
        assert result.volume_provided >= 200 * 0.95
        
        print(f"\n✓ Kích thước tối ưu: {result.length}×{result.width}×{result.water_depth}m")
        print(f"✓ Thể tích: {result.volume_provided} m³")
        print(f"✓ Chi phí: {result.total_cost:,.0f} VND")
        print(f"✓ Tiết kiệm: {result.savings_vs_default}%")
    
    def test_auto_sizing(self):
        """Test auto-sizing từ lưu lượng"""
        result = AutoSizingCalculator.auto_design_from_flow(
            flow_rate=5000,  # m³/ngày
            tank_type=TankType.SEDIMENTATION,
            num_tanks=2
        )
        
        assert "dimensions" in result
        assert "cost" in result
        assert "hydraulics" in result
        
        dims = result["dimensions"]
        print(f"\n✓ Lưu lượng: 5000 m³/ngày")
        print(f"✓ Kích thước: {dims['length']}×{dims['width']}×{dims['total_depth']}m")
        print(f"✓ Chi phí: {result['cost']['total_cost_per_tank']:,.0f} VND/bể")
    
    def test_compare_alternatives(self):
        """Test so sánh phương án"""
        result = TankCostOptimizer.compare_alternatives(volume_required=150)
        
        assert "comparison" in result
        assert "recommendation" in result
        assert len(result["comparison"]) > 0
        
        print(f"\n✓ Số phương án: {len(result['comparison'])}")
        print(f"✓ Khuyến nghị: {result['recommendation']['name']}")


class TestValidationDashboard:
    """Test module validation dashboard"""
    
    def test_quick_check(self):
        """Test kiểm tra nhanh"""
        dashboard = TankValidationBuilder.create_quick_check(
            length=12,
            width=6,
            depth=4,
            wall_thickness=0.3,
            flow_rate=3000,
            tank_type="sedimentation"
        )
        
        assert dashboard.total_checks > 0
        print(f"\n✓ Tổng số kiểm tra: {dashboard.total_checks}")
        print(f"✓ Đạt: {dashboard.passed_checks}")
        print(f"✓ Không đạt: {dashboard.failed_checks}")
        print(f"✓ Tỷ lệ: {dashboard.pass_rate:.1f}%")
    
    def test_dashboard_to_dict(self):
        """Test xuất dashboard ra dict"""
        dashboard = TankValidationBuilder.create_quick_check(
            length=10, width=5, depth=3.5,
            wall_thickness=0.25, flow_rate=2000
        )
        
        data = dashboard.to_dict()
        
        assert "summary" in data
        assert "items_by_category" in data
        print(f"\n✓ Dashboard data: {list(data.keys())}")
    
    def test_version_compare(self):
        """Test so sánh phương án"""
        design_a = {
            "dimensions": {"length": 10, "width": 5, "water_depth": 4, "wall_thickness": 0.25},
            "cost": {"total_cost_per_tank": 500_000_000},
            "quantities": {"concrete_per_tank": 50, "steel_per_tank": 5000, "formwork_per_tank": 200}
        }
        
        design_b = {
            "dimensions": {"length": 12, "width": 6, "water_depth": 3, "wall_thickness": 0.30},
            "cost": {"total_cost_per_tank": 600_000_000},
            "quantities": {"concrete_per_tank": 60, "steel_per_tank": 6000, "formwork_per_tank": 250}
        }
        
        comparison = VersionComparer.compare_designs(
            design_a, design_b,
            name_a="Bể sâu", name_b="Bể nông"
        )
        
        assert "winner" in comparison
        assert "comparison_items" in comparison
        
        print(f"\n✓ Phương án tốt hơn: {comparison['winner']}")
        print(f"✓ Kết luận: {comparison['recommendation']}")


# Run tests
if __name__ == "__main__":
    print("=" * 60)
    print("TEST ADVANCED DESIGN MODULES")
    print("=" * 60)
    
    # Test 1: PCA Tables
    print("\n\n" + "=" * 60)
    print("1. TEST PCA MOMENT TABLES")
    print("=" * 60)
    
    test1 = TestPlateMomentTables()
    try:
        test1.test_wall_moment_calculation()
        print("✓ test_wall_moment_calculation PASSED")
    except Exception as e:
        print(f"✗ test_wall_moment_calculation FAILED: {e}")
    
    try:
        test1.test_moment_envelope()
        print("✓ test_moment_envelope PASSED")
    except Exception as e:
        print(f"✗ test_moment_envelope FAILED: {e}")
    
    try:
        test1.test_interpolation()
        print("✓ test_interpolation PASSED")
    except Exception as e:
        print(f"✗ test_interpolation FAILED: {e}")
    
    # Test 2: Crack Width
    print("\n\n" + "=" * 60)
    print("2. TEST CRACK WIDTH CONTROL")
    print("=" * 60)
    
    test2 = TestCrackWidthChecker()
    try:
        test2.test_basic_crack_check()
        print("✓ test_basic_crack_check PASSED")
    except Exception as e:
        print(f"✗ test_basic_crack_check FAILED: {e}")
    
    try:
        test2.test_crack_check_fail()
        print("✓ test_crack_check_fail PASSED")
    except Exception as e:
        print(f"✗ test_crack_check_fail FAILED: {e}")
    
    try:
        test2.test_design_for_crack_control()
        print("✓ test_design_for_crack_control PASSED")
    except Exception as e:
        print(f"✗ test_design_for_crack_control FAILED: {e}")
    
    # Test 3: Tank Optimizer
    print("\n\n" + "=" * 60)
    print("3. TEST TANK COST OPTIMIZER")
    print("=" * 60)
    
    test3 = TestTankCostOptimizer()
    try:
        test3.test_calculate_cost()
        print("✓ test_calculate_cost PASSED")
    except Exception as e:
        print(f"✗ test_calculate_cost FAILED: {e}")
    
    try:
        test3.test_optimize_dimensions()
        print("✓ test_optimize_dimensions PASSED")
    except Exception as e:
        print(f"✗ test_optimize_dimensions FAILED: {e}")
    
    try:
        test3.test_auto_sizing()
        print("✓ test_auto_sizing PASSED")
    except Exception as e:
        print(f"✗ test_auto_sizing FAILED: {e}")
    
    try:
        test3.test_compare_alternatives()
        print("✓ test_compare_alternatives PASSED")
    except Exception as e:
        print(f"✗ test_compare_alternatives FAILED: {e}")
    
    # Test 4: Validation Dashboard
    print("\n\n" + "=" * 60)
    print("4. TEST VALIDATION DASHBOARD")
    print("=" * 60)
    
    test4 = TestValidationDashboard()
    try:
        test4.test_quick_check()
        print("✓ test_quick_check PASSED")
    except Exception as e:
        print(f"✗ test_quick_check FAILED: {e}")
    
    try:
        test4.test_dashboard_to_dict()
        print("✓ test_dashboard_to_dict PASSED")
    except Exception as e:
        print(f"✗ test_dashboard_to_dict FAILED: {e}")
    
    try:
        test4.test_version_compare()
        print("✓ test_version_compare PASSED")
    except Exception as e:
        print(f"✗ test_version_compare FAILED: {e}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)
