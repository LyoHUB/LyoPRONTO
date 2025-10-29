"""
Comprehensive tests for opt_Pch.py - Pressure optimization module.

This module optimizes chamber pressure while fixing shelf temperature.
Tests based on working example_optimizer.py structure.
"""

import pytest
import numpy as np
from lyopronto import opt_Pch


# Test constants for numerical comparison
DECIMAL_PRECISION = 6  # Decimal places for floating-point comparison in assert_array_almost_equal


@pytest.fixture
def standard_opt_pch_inputs():
    """Standard inputs for opt_Pch testing (pressure optimization)."""
    # Vial geometry
    vial = {
        'Av': 3.8,     # Vial area [cm**2]
        'Ap': 3.14,    # Product area [cm**2]
        'Vfill': 2.0   # Fill volume [mL]
    }
    
    # Product properties
    product = {
        'T_pr_crit': -5.0,   # Critical product temperature [degC]
        'cSolid': 0.05,      # Solid content [g/mL]
        'R0': 1.4,           # Product resistance coefficient R0 [cm**2-hr-Torr/g]
        'A1': 16.0,          # Product resistance coefficient A1 [1/cm]
        'A2': 0.0            # Product resistance coefficient A2 [1/cm**2]
    }
    
    # Vial heat transfer coefficients
    ht = {
        'KC': 0.000275,   # Kc [cal/s/K/cm**2]
        'KP': 0.000893,   # Kp [cal/s/K/cm**2]/Torr
        'KD': 0.46        # Kd dimensionless
    }
    
    # Chamber pressure optimization settings
    # NOTE: Minimum pressure for optimization (website suggests 0.05 to 1000 Torr)
    Pchamber = {
        'min': 0.05  # Minimum chamber pressure [Torr]
    }
    
    # Shelf temperature settings (FIXED for opt_Pch)
    # Multi-step profile: start at -35°C, ramp to -20°C, then 120°C
    Tshelf = {
        'init': -35.0,                        # Initial shelf temperature [degC]
        'setpt': np.array([-20.0, 120.0]),    # Set points [degC]
        'dt_setpt': np.array([300, 1800]),    # Hold times [min]
        'ramp_rate': 1.0                      # Ramp rate [degC]/min
    }
    
    # Equipment capability
    eq_cap = {
        'a': -0.182,   # Equipment capability coefficient a [kg]/hr
        'b': 11.7      # Equipment capability coefficient b [kg]/hr/Torr
    }
    
    # Number of vials
    nVial = 398
    
    # Time step
    dt = 0.01   # Time step [hr]
    
    return vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial


class TestOptPchBasic:
    """Basic functionality tests for opt_Pch module."""
    
    def test_opt_pch_runs(self, standard_opt_pch_inputs):
        """Test that opt_Pch.dry executes successfully."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert output is not None, "opt_Pch.dry should return output"
        assert isinstance(output, np.ndarray), "Output should be numpy array"
    
    def test_output_shape(self, standard_opt_pch_inputs):
        """Test that output has correct shape and structure."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Should have 7 columns: time, Tsub, Tbot, Tsh, Pch, flux, percent_dried
        assert output.shape[1] == 7, f"Expected 7 columns, got {output.shape[1]}"
        
        # Should have multiple time points
        assert output.shape[0] > 1, "Should have multiple time points"
    
    def test_output_columns(self, standard_opt_pch_inputs):
        """Test that each output column contains valid data."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Column 0: Time should increase
        assert np.all(np.diff(output[:, 0]) > 0), "Time should increase monotonically"
        
        # Column 1: Tsub should be below 0°C
        assert np.all(output[:, 1] < 0), "Sublimation temperature should be below 0°C"
        
        # Column 2: Tbot should be reasonable
        assert np.all(output[:, 2] >= -50), "Tbot should be above -50°C"
        assert np.all(output[:, 2] <= 25), "Tbot should be below 25°C"
        
        # Column 3: Tsh follows the shelf temperature profile
        assert np.all(output[:, 3] >= -50), "Tsh should be above -50°C"
        assert np.all(output[:, 3] <= 130), "Tsh should be below 130°C"
        
        # Column 4: Pch should be positive and [mTorr]
        assert np.all(output[:, 4] > 0), "Chamber pressure should be positive"
        # Pch should be >= min pressure (0.05 Torr = 50 mTorr)
        assert np.all(output[:, 4] >= 50), f"Pch should be >= 50 mTorr (min), got min {output[:, 4].min()}"
        
        # Column 5: Flux should be non-negative
        assert np.all(output[:, 5] >= 0), "Sublimation flux should be non-negative"
        
        # Column 6: Percent dried should be 0-100
        assert np.all(output[:, 6] >= 0), "Percent dried should be >= 0"
        assert np.all(output[:, 6] <= 100.0), "Percent dried should be <= 100"
    
    def test_pressure_optimization(self, standard_opt_pch_inputs):
        """Test that pressure is optimized (varies over time)."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Pressure (column 4) should vary as optimization proceeds
        Pch_values = output[:, 4]
        assert np.std(Pch_values) > 0, "Pressure should vary (be optimized)"
        
        # Pressure should respect minimum bound (50 mTorr = 0.05 Torr)
        assert np.all(Pch_values >= 50), "Pressure should be >= min bound"
    
    def test_shelf_temperature_follows_profile(self, standard_opt_pch_inputs):
        """Test that shelf temperature follows the specified profile."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Shelf temperature (column 3) should start at init
        assert np.abs(output[0, 3] - Tshelf['init']) < 1.0, \
            f"Initial Tsh should be ~{Tshelf['init']}°C"
        
        # Shelf temperature should increase over time (following ramp)
        # Note: May not reach final setpoint if drying completes first
        assert output[-1, 3] > output[0, 3], \
            "Shelf temperature should increase from initial value"
    
    def test_product_temperature_constraint(self, standard_opt_pch_inputs):
        """Test that product temperature stays at or below critical temperature."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Tbot (column 2) should stay at or below T_pr_crit
        T_crit = product['T_pr_crit']
        assert np.all(output[:, 2] <= T_crit + 0.5), \
            f"Product temperature should be <= {T_crit}°C (critical)"
    
    def test_drying_completes(self, standard_opt_pch_inputs):
        """Test that drying reaches near completion."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Fraction dried (column 6) should reach > 0.99 (was percentage 0-100, now fraction 0-1)
        final_dried = output[-1, 6]
        assert final_dried > 0.99, f"Should dry to >99%, got {final_dried*100:.1f}%"


class TestOptPchEdgeCases:
    """Edge case tests for opt_Pch module."""
    
    @pytest.mark.slow
    def test_low_critical_temperature(self, standard_opt_pch_inputs):
        """Test with very low critical temperature (-20°C)."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        # Lower critical temperature
        product['T_pr_crit'] = -20.0
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert output.shape[0] > 1, "Should complete drying"
        assert np.all(output[:, 2] <= -19.5), "Should respect lower T_crit"
    
    @pytest.mark.slow
    def test_high_resistance_product(self, standard_opt_pch_inputs):
        """Test with high resistance product."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        # Increase resistance
        product['R0'] = 3.0
        product['A1'] = 30.0
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert output.shape[0] > 1, "Should complete drying"
        # Higher resistance should lead to longer drying time
        assert output[-1, 0] > 1.0, "High resistance should take longer to dry"
    
    def test_single_shelf_temperature_setpoint(self, standard_opt_pch_inputs):
        """Test with single shelf temperature setpoint."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        # Single setpoint
        Tshelf['setpt'] = np.array([0.0])
        Tshelf['dt_setpt'] = np.array([1800])
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert output.shape[0] > 1, "Should complete with single setpoint"
        assert output[-1, 6] > 0.99, "Should complete drying"
    
    def test_higher_min_pressure(self, standard_opt_pch_inputs):
        """Test with higher minimum pressure constraint (0.10 Torr)."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        # Higher minimum pressure
        Pchamber['min'] = 0.10  # Torr = 100 mTorr
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert output.shape[0] > 1, "Should complete drying"
        # All pressures should be >= 100 mTorr
        assert np.all(output[:, 4] >= 100), "Pressure should respect higher min bound"


class TestOptPchValidation:
    """Validation tests comparing opt_Pch behavior."""
    
    def test_pressure_decreases_with_progress(self, standard_opt_pch_inputs):
        """Test that optimized pressure generally increases as drying progresses.
        
        Reason: As cake length increases, resistance increases, so optimizer
        allows higher pressure to maintain sublimation rate.
        """
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Compare early vs late pressure
        early_Pch = output[:len(output)//4, 4].mean()  # First quarter
        late_Pch = output[3*len(output)//4:, 4].mean()  # Last quarter
        
        # Late pressure should generally be higher (but allow some tolerance)
        # This is because resistance increases with cake length
        assert late_Pch >= early_Pch * 0.8, \
            f"Late pressure ({late_Pch:.1f}) should be >= early ({early_Pch:.1f})"
    
    def test_optimization_finds_reasonable_solution(self, standard_opt_pch_inputs):
        """Test that optimization finds physically reasonable solution."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Drying time should be reasonable (0.5 to 10 hours)
        drying_time = output[-1, 0]
        assert 0.5 < drying_time < 10, \
            f"Drying time {drying_time:.2f} hr should be reasonable (0.5-10 hr)"
        
        # Average flux should be positive and reasonable
        avg_flux = output[:, 5].mean()
        assert 0.1 < avg_flux < 10, \
            f"Average flux {avg_flux:.2f} kg/hr/m² should be reasonable (0.1-10)"
    
    @pytest.mark.slow
    def test_consistent_results(self, standard_opt_pch_inputs):
        """Test that repeated runs give consistent results."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        # Run twice
        output1 = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        output2 = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Results should be identical (deterministic optimization)
        np.testing.assert_array_almost_equal(output1, output2, decimal=DECIMAL_PRECISION)
