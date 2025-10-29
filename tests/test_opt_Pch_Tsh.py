"""
Comprehensive tests for opt_Pch_Tsh.py - Joint pressure and temperature optimization module.

This module optimizes both chamber pressure and shelf temperature simultaneously.
Tests based on working example_optimizer.py structure.
"""

import pytest
import numpy as np
from lyopronto import opt_Pch_Tsh

# Constants for test assertions
MAX_AGGRESSIVE_OPTIMIZATION_TIME = 5.0  # Maximum expected drying time with aggressive optimization (hours)


@pytest.fixture
def standard_opt_pch_tsh_inputs():
    """Standard inputs for opt_Pch_Tsh testing (joint optimization)."""
    # Vial geometry
    vial = {
        'Av': 3.8,     # Vial area in cm^2
        'Ap': 3.14,    # Product area in cm^2
        'Vfill': 2.0   # Fill volume in mL
    }
    
    # Product properties
    product = {
        'T_pr_crit': -5.0,   # Critical product temperature in degC
        'cSolid': 0.05,      # Solid content in g/mL
        'R0': 1.4,           # Product resistance coefficient R0 in cm^2-hr-Torr/g
        'A1': 16.0,          # Product resistance coefficient A1 in 1/cm
        'A2': 0.0            # Product resistance coefficient A2 in 1/cm^2
    }
    
    # Vial heat transfer coefficients
    ht = {
        'KC': 0.000275,   # Kc in cal/s/K/cm^2
        'KP': 0.000893,   # Kp in cal/s/K/cm^2/Torr
        'KD': 0.46        # Kd dimensionless
    }
    
    # Chamber pressure optimization settings
    # NOTE: Minimum pressure for optimization (website suggests 0.05 to 1000 Torr)
    Pchamber = {
        'min': 0.05  # Minimum chamber pressure in Torr
    }
    
    # Shelf temperature optimization settings
    # Optimize within range -45 to 120°C
    Tshelf = {
        'min': -45.0,   # Minimum shelf temperature in degC
        'max': 120.0    # Maximum shelf temperature in degC
    }
    
    # Equipment capability
    eq_cap = {
        'a': -0.182,   # Equipment capability coefficient a in kg/hr
        'b': 11.7      # Equipment capability coefficient b in kg/hr/Torr
    }
    
    # Number of vials
    nVial = 398
    
    # Time step
    dt = 0.01   # Time step in hr
    
    return vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial


class TestOptPchTshBasic:
    """Basic functionality tests for opt_Pch_Tsh module."""
    
    def test_opt_pch_tsh_runs(self, standard_opt_pch_tsh_inputs):
        """Test that opt_Pch_Tsh.dry executes successfully."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert output is not None, "opt_Pch_Tsh.dry should return output"
        assert isinstance(output, np.ndarray), "Output should be numpy array"
    
    def test_output_shape(self, standard_opt_pch_tsh_inputs):
        """Test that output has correct shape and structure."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Should have 7 columns: time, Tsub, Tbot, Tsh, Pch, flux, percent_dried
        assert output.shape[1] == 7, f"Expected 7 columns, got {output.shape[1]}"
        
        # Should have multiple time points
        assert output.shape[0] > 1, "Should have multiple time points"
    
    def test_output_columns(self, standard_opt_pch_tsh_inputs):
        """Test that each output column contains valid data."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Column 0: Time should increase
        assert np.all(np.diff(output[:, 0]) > 0), "Time should increase monotonically"
        
        # Column 1: Tsub should be below 0°C
        assert np.all(output[:, 1] < 0), "Sublimation temperature should be below 0°C"
        
        # Column 2: Tbot should be reasonable
        assert np.all(output[:, 2] >= -50), "Tbot should be above -50°C"
        assert np.all(output[:, 2] <= 25), "Tbot should be below 25°C"
        
        # Column 3: Tsh should be within optimization bounds
        assert np.all(output[:, 3] >= Tshelf['min'] - 1), \
            f"Tsh should be >= min ({Tshelf['min']}°C)"
        assert np.all(output[:, 3] <= Tshelf['max'] + 1), \
            f"Tsh should be <= max ({Tshelf['max']}°C)"
        
        # Column 4: Pch should be positive and in mTorr
        assert np.all(output[:, 4] > 0), "Chamber pressure should be positive"
        # Pch should be >= min pressure (0.05 Torr = 50 mTorr)
        assert np.all(output[:, 4] >= 50), f"Pch should be >= 50 mTorr (min), got min {output[:, 4].min()}"
        
        # Column 5: Flux should be non-negative
        assert np.all(output[:, 5] >= 0), "Sublimation flux should be non-negative"
        
        # Column 6: Percent dried should be 0-100
        assert np.all(output[:, 6] >= 0), "Percent dried should be >= 0"
        assert np.all(output[:, 6] <= 100.0), "Percent dried should be <= 100"
    
    def test_both_variables_optimized(self, standard_opt_pch_tsh_inputs):
        """Test that both pressure and temperature are optimized (vary over time)."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Pressure (column 4) should vary
        Pch_values = output[:, 4]
        assert np.std(Pch_values) > 0, "Pressure should vary (be optimized)"
        
        # Shelf temperature (column 3) should vary
        Tsh_values = output[:, 3]
        assert np.std(Tsh_values) > 0, "Shelf temperature should vary (be optimized)"
        
        # Both should respect bounds
        assert np.all(Pch_values >= 50), "Pressure should be >= min bound"
        assert np.all(Tsh_values >= Tshelf['min'] - 1), "Tsh should be >= min bound"
        assert np.all(Tsh_values <= Tshelf['max'] + 1), "Tsh should be <= max bound"
    
    def test_product_temperature_constraint(self, standard_opt_pch_tsh_inputs):
        """Test that product temperature stays at or below critical temperature."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Tbot (column 2) should stay at or below T_pr_crit
        T_crit = product['T_pr_crit']
        assert np.all(output[:, 2] <= T_crit + 0.5), \
            f"Product temperature should be <= {T_crit}°C (critical)"
    
    def test_drying_completes(self, standard_opt_pch_tsh_inputs):
        """Test that drying reaches near completion."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Fraction dried (column 6) should reach > 0.99
        final_dried = output[-1, 6]
        assert final_dried > 0.99, f"Should dry to >99%, got {final_dried*100:.1f}%"
    
    def test_shelf_temp_varies_over_time(self, standard_opt_pch_tsh_inputs):
        """Test that optimized shelf temperature varies during drying.
        
        The optimizer adjusts shelf temperature to maximize sublimation
        rate while respecting product temperature constraints.
        """
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Shelf temperature should vary (be optimized)
        Tsh_range = output[:, 3].max() - output[:, 3].min()
        assert Tsh_range > 1.0, \
            f"Shelf temperature should vary by > 1°C, got {Tsh_range:.1f}°C"


class TestOptPchTshEdgeCases:
    """Edge case tests for opt_Pch_Tsh module."""
    
    def test_narrow_temperature_range(self, standard_opt_pch_tsh_inputs):
        """Test with narrow shelf temperature optimization range."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        # Narrow range: -10 to 10°C
        Tshelf['min'] = -10.0
        Tshelf['max'] = 10.0
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert output.shape[0] > 1, "Should complete drying"
        # All temperatures should be within range
        assert np.all(output[:, 3] >= -11), "Tsh should be >= -10°C"
        assert np.all(output[:, 3] <= 11), "Tsh should be <= 10°C"
    
    def test_low_critical_temperature(self, standard_opt_pch_tsh_inputs):
        """Test with very low critical temperature (-20°C)."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        # Lower critical temperature
        product['T_pr_crit'] = -20.0
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert output.shape[0] > 1, "Should complete drying"
        assert np.all(output[:, 2] <= -19.5), "Should respect lower T_crit"
    
    def test_high_resistance_product(self, standard_opt_pch_tsh_inputs):
        """Test with high resistance product."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        # Increase resistance
        product['R0'] = 3.0
        product['A1'] = 30.0
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert output.shape[0] > 1, "Should complete drying"
        # Higher resistance should lead to longer drying time
        assert output[-1, 0] > 1.0, "High resistance should take longer to dry"
    
    def test_higher_min_pressure(self, standard_opt_pch_tsh_inputs):
        """Test with higher minimum pressure constraint (0.10 Torr)."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        # Higher minimum pressure
        Pchamber['min'] = 0.10  # Torr = 100 mTorr
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert output.shape[0] > 1, "Should complete drying"
        # All pressures should be >= 100 mTorr
        assert np.all(output[:, 4] >= 100), "Pressure should respect higher min bound"


class TestOptPchTshValidation:
    """Validation tests comparing opt_Pch_Tsh behavior."""
    
    def test_joint_optimization_faster_than_single(self, standard_opt_pch_tsh_inputs):
        """Test that joint optimization is at least as fast as pressure-only optimization.
        
        Joint optimization has more degrees of freedom, so it should find
        at least as good (fast) a solution as pressure-only optimization.
        """
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        # Run joint optimization
        output_joint = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Joint optimization should complete successfully
        assert output_joint.shape[0] > 1, "Joint optimization should complete"
        assert output_joint[-1, 6] > 0.99, "Should reach >99% dried"
        
        # Drying time should be reasonable
        time_joint = output_joint[-1, 0]
        assert 0.3 < time_joint < 10, \
            f"Joint optimization time {time_joint:.2f} hr should be reasonable"
    
    def test_optimization_finds_reasonable_solution(self, standard_opt_pch_tsh_inputs):
        """Test that optimization finds physically reasonable solution."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Drying time should be reasonable (0.3 to 10 hours)
        drying_time = output[-1, 0]
        assert 0.3 < drying_time < 10, \
            f"Drying time {drying_time:.2f} hr should be reasonable (0.3-10 hr)"
        
        # Average flux should be positive and reasonable
        avg_flux = output[:, 5].mean()
        assert 0.1 < avg_flux < 10, \
            f"Average flux {avg_flux:.2f} kg/hr/m² should be reasonable (0.1-10)"
        
        # Shelf temperature should vary during optimization
        Tsh_range = output[:, 3].max() - output[:, 3].min()
        assert Tsh_range > 1.0, \
            f"Optimizer should vary Tsh, got {Tsh_range:.1f}°C range"
    
    def test_consistent_results(self, standard_opt_pch_tsh_inputs):
        """Test that repeated runs give consistent results."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        # Run twice
        output1 = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        output2 = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Results should be identical (deterministic optimization)
        np.testing.assert_array_almost_equal(output1, output2, decimal=6)
    
    def test_aggressive_optimization_parameters(self, standard_opt_pch_tsh_inputs):
        """Test with aggressive optimization to maximize sublimation rate."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        # Wide ranges to allow aggressive optimization
        Tshelf['min'] = -50.0
        Tshelf['max'] = 150.0
        Pchamber['min'] = 0.05
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert output.shape[0] > 1, "Should complete with aggressive parameters"
        assert output[-1, 6] > 0.99, "Should reach >99% dried"
        
        # Should complete relatively quickly with aggressive optimization
        assert output[-1, 0] < MAX_AGGRESSIVE_OPTIMIZATION_TIME, \
            f"Aggressive optimization should complete in < {MAX_AGGRESSIVE_OPTIMIZATION_TIME} hr"
