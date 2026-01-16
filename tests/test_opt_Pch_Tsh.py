"""
Comprehensive tests for opt_Pch_Tsh.py - Joint pressure and temperature optimization module.

This module optimizes both chamber pressure and shelf temperature simultaneously.
Tests based on working example_optimizer.py structure.
"""

import pytest
import numpy as np
from lyopronto import opt_Pch_Tsh, opt_Pch, constant, opt_Tsh
from .utils import assert_physically_reasonable_output

# Constants for test assertions
MAX_AGGRESSIVE_OPTIMIZATION_TIME = 5.0  # Maximum expected drying time with aggressive optimization [hr]

@pytest.fixture
def standard_opt_pch_tsh_inputs():
    """Standard inputs for opt_Pch_Tsh testing (joint optimization)."""
    # Vial geometry
    vial = {
        'Av': 3.8,     # Vial area [cm**2]
        'Ap': 3.14,    # Product area [cm**2]
        'Vfill': 2.0   # Fill volume [mL]
    }
    
    # Product properties
    product = {
        'T_pr_crit': -15.0,   # Critical product temperature [degC]
        'cSolid': 0.05,      # Solid content [g/mL]
        'R0': 1.4,           # Product resistance coefficient R0 [cm**2-hr-Torr/g]
        'A1': 16.0,          # Product resistance coefficient A1 [1/cm]
        'A2': 0.0            # Product resistance coefficient A2 [1/cm**2]
    }
    
    # Vial heat transfer coefficients
    ht = {
        'KC': 0.000275,   # Kc [cal/s/K/cm**2]
        'KP': 0.000893,   # Kp [cal/s/K/cm**2/Torr]
        'KD': 0.46        # Kd dimensionless
    }
    
    # Chamber pressure optimization settings
    # NOTE: Minimum pressure for optimization (website suggests 0.05 to 1000 [Torr])
    Pchamber = {
        'min': 0.05,  # Minimum chamber pressure [Torr]
        'max': 2.00   # Maximum chamber pressure [Torr]
    }
    
    # Shelf temperature optimization settings
    # Optimize within range -45 to 120°C
    Tshelf = {
        'min': -45.0,   # Minimum shelf temperature [degC]
        'max': 120.0    # Maximum shelf temperature [degC]
    }
    
    # Equipment capability
    eq_cap = {
        'a': -0.182,   # Equipment capability coefficient a [kg]/hr
        'b': 11.7      # Equipment capability coefficient b [kg/hr/Torr]
    }
    
    # Number of vials
    nVial = 398
    
    # Time step
    dt = 0.01   # Time step [hr]
    
    return vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial

def opt_both_consistency(output, setup):
    vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = setup

    assert output is not None, "opt_Pch_Tsh.dry should return output"
    assert isinstance(output, np.ndarray), "Output should be numpy array"

    # Should have 7 columns: time, Tsub, Tbot, Tsh, Pch, flux, percent_dried
    assert output.shape[1] == 7, f"Expected 7 columns, got {output.shape[1]}"
    
    # Should have multiple time points
    assert output.shape[0] > 1, "Should have multiple time points"

    assert_physically_reasonable_output(output, Tmax=120)

    # Pch should be >= min pressure (0.05 Torr = 50 mTorr)
    assert np.all(output[:, 4] >= Pchamber['min']*constant.Torr_to_mTorr), f"Pch should be >= 50 mTorr (min), got min {output[:, 4].min()}"
    
    # Column 5: Flux should be non-negative
    assert np.all(output[:, 5] >= 0), "Sublimation flux should be non-negative"
    
    # Column 6: Percent dried should be 0-100
    assert np.all(output[:, 6] >= 0), "Percent dried should be >= 0"
    assert np.all(output[:, 6] <= 100.0), "Percent dried should be <= 100"

    # Pressure (column 4) should vary
    Pch_values = output[:, 4]
    assert np.std(Pch_values) > 0, "Pressure should vary (be optimized)"
    
    # Shelf temperature (column 3) should vary
    Tsh_values = output[:, 3]
    assert np.std(Tsh_values) > 0, "Shelf temperature should vary (be optimized)"
    
    # Both should respect bounds
    assert np.all(Pch_values >= Pchamber['min']*constant.Torr_to_mTorr), "Pressure should be >= min bound"
    if hasattr(Pchamber, 'max'):
        assert np.all(Pch_values <= Pchamber['max']*constant.Torr_to_mTorr), "Pressure should be <= max bound"
    assert np.all(Tsh_values >= Tshelf['min']), "Tsh should be >= min bound"
    assert np.all(Tsh_values <= Tshelf['max']), "Tsh should be <= max bound"

    # Tbot (column 2) should stay at or below T_pr_crit
    T_crit = product['T_pr_crit']
    assert np.all(output[:, 2] <= T_crit+0.01), \
        f"Product temperature should be <= {T_crit}°C (critical)"

    # Percent dried (column 6) should reach > 99.0
    final_dried = output[-1, 6]
    assert final_dried > 99, f"Should dry to >99%, got {final_dried:.1f}%"

    
    # Should not exceed equipment capability (with small tolerance)
    # Equipment capability at different pressures
    Pch = output[:, 4] / 1000  # [Torr]
    actual_cap = eq_cap['a'] + eq_cap['b'] * Pch  # [kg/hr]
    # Total sublimation rate per vial
    flux = output[:, 5]  # Sublimation flux [kg/hr/m**2]
    Ap_m2 = vial['Ap'] * constant.cm_To_m**2  # Convert [cm**2] to [m**2]
    dmdt = flux * Ap_m2  # [kg/hr/vial]
    violations = dmdt - actual_cap
    
    assert np.all(violations <= 0), \
        f"Equipment capability exceeded by {np.max(violations):.3e} kg/hr"

class TestOptPchTshBasic:
    """Basic functionality tests for opt_Pch_Tsh module."""
    
    def test_opt_pch_tsh_basics(self, standard_opt_pch_tsh_inputs):
        """Test that: 
        - opt_Pch_Tsh.dry executes successfully
        - output has correct shape and structure
        - each output column contains valid data
        - both pressure and temperature are optimized (vary over time)
        - product temperature stays at or below critical temperature
        - drying reaches near completion
        """
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        opt_both_consistency(output, standard_opt_pch_tsh_inputs)
    
    def test_opt_pch_tsh_tight_ranges(self, standard_opt_pch_tsh_inputs):
        """Test with tight optimization ranges."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        # Set tight ranges
        Pchamber['min'] = 0.40
        Pchamber['max'] = 0.70
        Tshelf['min'] = -20.0
        Tshelf['max'] = 0.0
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        opt_both_consistency(output, (vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial))

class TestOptPchTshEdgeCases:
    """Edge case tests for opt_Pch_Tsh module."""
    
    def test_narrow_temperature_range(self, standard_opt_pch_tsh_inputs):
        """Test with narrow shelf temperature optimization range."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        # Narrow range: -10 to 10°C
        Tshelf['min'] = -10.0
        Tshelf['max'] = 10.0
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert output[-1, 6] > 99, "Should complete drying"
        # All temperatures should be within range
        assert np.all(output[:, 3] >= -10), "Tsh should be >= -10°C"
        assert np.all(output[:, 3] <= 10), "Tsh should be <= 10°C"
    
    def test_low_critical_temperature(self, standard_opt_pch_tsh_inputs):
        """Test with very low critical temperature (-35°C)."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        # Lower critical temperature
        product['T_pr_crit'] = -35.0
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert output[-1, 6] > 99, "Should complete drying"
        assert np.all(output[:, 2] <= -35.0+0.01), "Should respect lower T_crit"
    
    def test_high_resistance_product(self, standard_opt_pch_tsh_inputs):
        """Test with high resistance product."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        # Increase resistance
        product['R0'] = 3.0
        product['A1'] = 30.0
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert output[-1, 6] > 99, "Should complete drying"
        # Higher resistance should lead to longer drying time
        assert output[-1, 0] > 1.0, "High resistance should take longer to dry"
    
    def test_higher_min_pressure(self, standard_opt_pch_tsh_inputs):
        """Test with higher minimum pressure constraint (0.10 Torr)."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        
        # Higher minimum pressure
        Pchamber['min'] = 0.10  # [Torr] = 100 [mTorr]
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert output[-1, 6] > 99, "Should complete drying"
        # All pressures should be >= 100 [mTorr]
        assert np.all(output[:, 4] >= 100), "Pressure should respect higher min bound"
        opt_both_consistency(output, (vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial))

    def test_concentrated_product(self, standard_opt_pch_tsh_inputs):
        """Test with high solids concentration."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_tsh_inputs
        product['cSolid'] = 0.15  # 15% solids

        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)

        assert_physically_reasonable_output(output)
        opt_both_consistency(output, (vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial))

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

        # Run pressure-only optimization with fixed shelf temperature
        Tshelf_fixed = {
            'init': -35,
            'setpt': [-20],  # Fixed shelf temperature at -20°C
            'dt_setpt': [3600],  # Long time at fixed temperature
            'ramp_rate': 1.0,
        }
        output_pressure_only = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf_fixed, dt, eq_cap, nVial)
        Pchamber_fixed = {
            'setpt': [0.5],  # Fixed pressure at 0.5 Torr
            'dt_setpt': [3600],  # Long time at fixed pressure
        }
        output_temperature_only = opt_Tsh.dry(vial, product, ht, Pchamber_fixed, Tshelf, dt, eq_cap, nVial)
        
        # Both optimizations should complete successfully
        assert output_joint[-1, 6] > 99, "Joint optimization should reach >99% dried"
        assert output_pressure_only[-1, 6] > 99, "P-only optimization should reach >99% dried"
        assert output_temperature_only[-1, 6] > 99, "T-only optimization should reach >99% dried"

        # Joint optimization drying time should be <= pressure-only drying time
        assert output_joint[-1, 0] <= output_pressure_only[-1, 0], "Joint optimization should beat P-only optimization"
        assert output_joint[-1, 0] <= output_temperature_only[-1, 0], "Joint optimization should beat T-only optimization"
    
    @pytest.mark.slow
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
        Pchamber['min'] = 0.01
        
        output = opt_Pch_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)

        assert_physically_reasonable_output(output, Tmax=150)
        
        assert output[-1, 6] > 99, "Should complete drying"
        
        # Should complete relatively quickly with aggressive optimization
        assert output[-1, 0] < MAX_AGGRESSIVE_OPTIMIZATION_TIME, \
            f"Aggressive optimization should complete in < {MAX_AGGRESSIVE_OPTIMIZATION_TIME} hr"
