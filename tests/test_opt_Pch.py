"""
Comprehensive tests for opt_Pch.py - Pressure optimization module.

This module optimizes chamber pressure while fixing shelf temperature.
Tests based on working example_optimizer.py structure.
"""

import pytest
import numpy as np
from lyopronto import opt_Pch, constant
from .utils import assert_physically_reasonable_output, assert_complete_drying, assert_incomplete_drying


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
        'T_pr_crit': -25.0,   # Critical product temperature [degC]
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
    Pchamber = {
        'min': 0.05,  # Minimum chamber pressure [Torr]
        'max': 1.0,  # Maximum chamber pressure [Torr]
    }
    
    # Shelf temperature settings (FIXED for opt_Pch)
    # Multi-step profile: start at -35°C, ramp to -20°C, then 0°C
    Tshelf = {
        'init': -35.0,                        # Initial shelf temperature [degC]
        'setpt': np.array([-10.0]),    # Set points [degC]
        'dt_setpt': np.array([3600]),    # Hold times [min]
        'ramp_rate': 1.0                      # Ramp rate [degC/min]
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


class TestOptPchBasic:
    """Basic functionality tests for opt_Pch module."""
    
    def test_pressure_optimization(self, standard_opt_pch_inputs):
        """Test that opt_Pch.dry executes,  output has correct structure, and 
        each output column contains valid data. Then, check that
        pressure is optimized (varies over time), shelf temperature follows 
        specified profile, and product temperature stays below critical temperature."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)

        assert output is not None, "opt_Pch.dry should return output"
        assert isinstance(output, np.ndarray), "Output should be numpy array"

        # Should have 7 columns: time, Tsub, Tbot, Tsh, Pch, flux, percent_dried
        assert output.shape[1] == 7, f"Expected 7 columns, got {output.shape[1]}"
        
        # Should have multiple time points
        assert output.shape[0] > 1, "Should have multiple time points"
        
        assert_physically_reasonable_output(output)
    
        # Pressure (column 4) should vary as optimization proceeds
        Pch_values = output[:, 4]
        assert np.std(Pch_values) > 0, "Pressure should vary (be optimized)"
        
        # Pressure should respect minimum bound (50 mTorr = 0.05 Torr)
        assert np.all(Pch_values >= Pchamber['min']*constant.Torr_to_mTorr), "Pressure should be >= min bound"
    
        # Shelf temperature (column 3) should start at init
        assert np.abs(output[0, 3] - Tshelf['init']) < 1.0, \
            f"Initial Tsh should be ~{Tshelf['init']}°C"
        
        # Shelf temperature should increase over time (following ramp)
        # Note: May not reach final setpoint if drying completes first
        assert output[-1, 3] > output[0, 3], \
            "Shelf temperature should increase from initial value"

        # Tbot (column 2) should stay at or below T_pr_crit
        T_crit = product['T_pr_crit']
        assert np.all(output[:, 2] <= T_crit), \
            f"Product temperature should be <= {T_crit}°C (critical)"
    
        assert_complete_drying(output)

        # Drying time should be reasonable (0.5 to 10 hours)
        drying_time = output[-1, 0]
        assert 0.5 < drying_time < 20, \
            f"Drying time {drying_time:.2f} hr should be reasonable (0.5-20 hr)"
        
        # Average flux should be positive and reasonable
        avg_flux = output[:, 5].mean()
        assert 0.1 < avg_flux < 10, \
            f"Average flux {avg_flux:.2f} kg/hr/m² should be reasonable (0.1-10)"

    def test_pressure_optimization_nomax(self, standard_opt_pch_inputs):
        """Test that opt_Pch.dry works without a maximum pressure constraint."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        # Remove max pressure constraint
        del Pchamber['max']
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)

        assert_physically_reasonable_output(output)
        
        assert_complete_drying(output)

class TestOptPchEdgeCases:
    """Edge case tests for opt_Pch module."""
    
    # @pytest.mark.skip(reason="TODO: needs some feasibility checking")
    def test_low_critical_temperature(self, standard_opt_pch_inputs):
        """Test with very low critical temperature (-35°C)."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        # Lower critical temperature
        product['T_pr_crit'] = -35.0
        Pchamber['min'] = 0.001  # Lower min pressure to 1 mTorr
        Pchamber['max'] = 2.00  # Raise max pressure to 2.00 Torr
        Tshelf['setpt'] = [-30] # Lower shelf temperature to make feasible
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert_complete_drying(output)
        assert np.all(output[:, 2] <= product['T_pr_crit']), "Should respect lower T_crit"

        assert_physically_reasonable_output(output)

    def test_insufficient_time(self, standard_opt_pch_inputs):
        """Test with very low critical temperature (-35°C)."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        Tshelf['dt_setpt'] = [120] # Less drying time
        
        with pytest.warns(UserWarning, match="Drying incomplete"):
            output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert_incomplete_drying(output)

        assert_physically_reasonable_output(output)
    
    @pytest.mark.slow
    def test_high_resistance_product(self, standard_opt_pch_inputs):
        """Test with high resistance product."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        # Increase resistance
        product['R0'] = 3.0
        product['A1'] = 30.0
        # Drop shelf temperature to make constraint feasible
        Tshelf['setpt'] = np.array([-20.0])
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)

        assert_physically_reasonable_output(output)
        
        assert_complete_drying(output)
        # Higher resistance should lead to longer drying time
        # TODO pin this to a value from default run conditions
        assert output[-1, 0] > 1.0, "High resistance should take longer to dry"
    
    def test_multi_shelf_temperature_setpoints(self, standard_opt_pch_inputs):
        """Test with multiple shelf temperature setpoints."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        # Two setpoints
        Tshelf['setpt'] = np.array([-20.0, 0.0, -10.0])
        Tshelf['dt_setpt'] = np.array([120, 120, 1200])
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)

        assert_physically_reasonable_output(output)
        
        assert_complete_drying(output)
    
    def test_higher_min_pressure(self, standard_opt_pch_inputs):
        """Test with higher minimum pressure constraint (0.10 Torr)."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        # Higher minimum pressure
        Pchamber['min'] = 0.10  # Torr = 100 mTorr
        # Needs a lower shelf temperature to complete drying
        Tshelf['setpt'] = np.array([-20.0])
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)

        assert_physically_reasonable_output(output)
        
        assert_complete_drying(output)
        # All pressures should be >= 100 mTorr
        assert np.all(output[:, 4] >= 100), "Pressure should respect higher min bound"

    def test_incomplete_optimization(self, standard_opt_pch_inputs):
        """Test with higher minimum pressure constraint (0.10 Torr)."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        # Higher minimum pressure
        Pchamber['min'] = 0.10  # Torr = 100 mTorr
        # With higher shelf temperature, CANNOT complete drying and adhere to constraints
        Tshelf['setpt'] = [0]
        
        with pytest.warns(UserWarning, match="Optimization failed"):
            output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        assert_incomplete_drying(output)
        # All pressures should be >= 100 mTorr
        assert np.all(output[:, 4] >= 100), "Pressure should respect higher min bound"

    def test_narrow_pressure_range(self, standard_opt_pch_inputs):
        """Test with narrow pressure optimization range."""
        vial, product, ht, _, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        new_Pch = {'min': 0.070, 'max': 0.090}
        product['T_pr_crit'] = -30.0  # Lower critical temperature to challenge
        Tshelf['setpt'] = [-20.0]    # Lower shelf temperature to make feasible
        
        output = opt_Pch.dry( vial, product, ht, new_Pch, Tshelf, dt, eq_cap, nVial)
        
        Pch = output[:, 4] / 1000
        assert np.all((Pch >= 0.070) & (Pch <= 0.090))

    def test_tight_equipment_constraint(self, standard_opt_pch_inputs):
        """Test with tighter equipment capability constraint.  """
        vial, product, ht, Pchamber, Tshelf, dt, _, nVial = standard_opt_pch_inputs
        # Reduce equipment capability
        tight_eq_cap = {
            'a' : -0.3, #[kg/hr]
            'b' : 5.0,   #[kg/hr/Torr]
        }
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, tight_eq_cap, nVial)
        
        # Should run without errors and show some progress despite tighter constraint
        assert output is not None
        assert_complete_drying(output)
        assert_physically_reasonable_output(output)

    @pytest.mark.slow
    def test_consistent_results(self, standard_opt_pch_inputs):
        """Test that repeated runs give consistent results."""
        # Run twice
        output1 = opt_Pch.dry(*standard_opt_pch_inputs)
        output2 = opt_Pch.dry(*standard_opt_pch_inputs)
        
        # Results should be identical (deterministic optimization)
        np.testing.assert_array_almost_equal(output1, output2, decimal=DECIMAL_PRECISION)

    #TODO: check whether this is actually expected. If so, merge with basic test above to avoid rerunning unnecessarily
    @pytest.mark.skip(reason="TODO: check that this is expected, and if so why")
    def test_pressure_decreases_with_progress(self, standard_opt_pch_inputs):
        """Test that optimized pressure generally increases as drying progresses.
        
        Reason: TODO check this
        """
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Compare early vs late pressure
        early_Pch = output[:len(output)//4, 4].mean()  # First quarter
        late_Pch = output[3*len(output)//4:, 4].mean()  # Last quarter
        
        # Late pressure should generally be higher
        assert late_Pch >= early_Pch, \
            f"Late pressure ({late_Pch:.1f}) should be >= early ({early_Pch:.1f})"
    
class TestOptPchReference:
    @pytest.mark.skip(reason="Reference test not yet implemented")
    def test_opt_pch_reference(self):
        # TODO test against an example case in test_data, to be created
        pass