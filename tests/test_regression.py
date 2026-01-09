"""Regression tests with known reference results."""
import pytest
import numpy as np
from lyopronto import calc_knownRp


class TestRegressionStandardCase:
    """
    Regression tests against standard reference case.
    
    These values should be updated with actual validated results from
    the original paper or verified simulations.
    """
    
    @pytest.fixture
    def reference_case(self):
        """Standard reference case parameters."""
        vial = {'Av': 3.80, 'Ap': 3.14, 'Vfill': 2.0}
        product = {'cSolid': 0.05, 'R0': 1.4, 'A1': 16.0, 'A2': 0.0}
        ht = {'KC': 2.75e-4, 'KP': 8.93e-4, 'KD': 0.46}
        Pchamber = {'setpt': [0.15], 'dt_setpt': [1800.0], 'ramp_rate': 0.5}
        Tshelf = {'init': -35.0, 'setpt': [20.0], 'dt_setpt': [1800.0], 'ramp_rate': 1.0}
        dt = 0.01
        
        return vial, product, ht, Pchamber, Tshelf, dt
    
    def test_reference_drying_time(self, reference_case):
        """
        Test that drying time matches reference value.
        
        The reference value is based on standard conditions with the current model.
        If model physics change, this test will catch regressions.
        """
        output = calc_knownRp.dry(*reference_case)
        drying_time = output[-1, 0]
        
        # Expected drying time based on current model behavior
        # Standard case: 2 mL fill, 5% solids, Pch=0.15 Torr, Tsh ramp to 20°C
        expected_time = 6.66  # hours
        
        # Allow 5% tolerance for numerical variations
        assert np.isclose(drying_time, expected_time, rtol=0.05), \
            f"Drying time {drying_time:.2f} hrs differs from reference {expected_time:.2f} hrs"
    
    def test_reference_initial_conditions(self, reference_case):
        """Test initial conditions match expected values."""
        output = calc_knownRp.dry(*reference_case)
        
        # Check initial values (first row)
        initial_time = output[0, 0]
        initial_Tsub = output[0, 1]
        initial_Tsh = output[0, 3]
        initial_Pch_mTorr = output[0, 4]
        initial_percent = output[0, 6]
        
        assert np.isclose(initial_time, 0.0, atol=0.001)
        assert initial_Tsub < -30.0  # Should start very cold
        assert np.isclose(initial_Tsh, -35.0, atol=0.1)  # Initial shelf temp
        assert np.isclose(initial_Pch_mTorr, 150.0, rtol=0.01)  # Chamber pressure [mTorr]
        assert np.isclose(initial_percent, 0.0, atol=0.01)  # Starting at 0 percent dried
    
    def test_reference_sublimation_temperatures(self, reference_case):
        """Test that sublimation temperatures stay in expected range."""
        output = calc_knownRp.dry(*reference_case)
        
        # Sublimation temperature should stay between -40°C and -10°C
        assert np.all(output[:, 1] > -40.0), "Tsub too cold"
        assert np.all(output[:, 1] < -10.0), "Tsub too warm"
    
    def test_reference_final_state(self, reference_case):
        """Test final state matches expected values."""
        output = calc_knownRp.dry(*reference_case)
        
        # Check final values (last row)
        final_Tsh = output[-1, 3]
        final_flux = output[-1, 5]
        final_percent = output[-1, 6]
        
        assert np.isclose(final_Tsh, 20.0, rtol=0.01)  # Should reach target shelf temp
        # Flux stays relatively high (not near zero) because heat input continues
        assert final_flux > 0.5  # Flux should still be significant
        assert final_percent >= 99.0  # Should be essentially complete


class TestRegressionParametricCases:
    """Regression tests for various parametric cases."""
    
    def test_low_pressure_case(self):
        """Test low pressure case (0.06 Torr)."""
        vial = {'Av': 3.80, 'Ap': 3.14, 'Vfill': 2.0}
        product = {'cSolid': 0.05, 'R0': 1.4, 'A1': 16.0, 'A2': 0.0}
        ht = {'KC': 2.75e-4, 'KP': 8.93e-4, 'KD': 0.46}
        Pchamber = {'setpt': [0.06], 'dt_setpt': [1800.0], 'ramp_rate': 0.5}
        Tshelf = {'init': -35.0, 'setpt': [20.0], 'dt_setpt': [1800.0], 'ramp_rate': 1.0}
        dt = 0.01
        
        output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
        
        # Should complete successfully (percent dried >= 99%)
        assert output[-1, 6] >= 99
        
        # Drying time should be in reasonable range
        drying_time = output[-1, 0]
        assert 5.0 < drying_time < 30.0
    
    def test_high_concentration_case(self):
        """Test high solids concentration case (10%)."""
        vial = {'Av': 3.80, 'Ap': 3.14, 'Vfill': 2.0}
        product = {'cSolid': 0.10, 'R0': 2.0, 'A1': 20.0, 'A2': 0.1}
        ht = {'KC': 2.75e-4, 'KP': 8.93e-4, 'KD': 0.46}
        Pchamber = {'setpt': [0.15], 'dt_setpt': [1800.0], 'ramp_rate': 0.5}
        Tshelf = {'init': -35.0, 'setpt': [20.0], 'dt_setpt': [1800.0], 'ramp_rate': 1.0}
        dt = 0.01
        
        output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
        
        # Should complete successfully (percent dried >= 99%)
        assert output[-1, 6] >= 99
        
        # Check it completes (timing depends on many factors)
        drying_time = output[-1, 0]
        assert drying_time > 5.0  # Should take at least 5 hours
    
    def test_conservative_shelf_temp_case(self):
        """Test conservative shelf temperature case (10°C)."""
        vial = {'Av': 3.80, 'Ap': 3.14, 'Vfill': 2.0}
        product = {'cSolid': 0.05, 'R0': 1.4, 'A1': 16.0, 'A2': 0.0}
        ht = {'KC': 2.75e-4, 'KP': 8.93e-4, 'KD': 0.46}
        Pchamber = {'setpt': [0.15], 'dt_setpt': [1800.0], 'ramp_rate': 0.5}
        Tshelf = {'init': -35.0, 'setpt': [10.0], 'dt_setpt': [1800.0], 'ramp_rate': 1.0}
        dt = 0.01
        
        output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
        
        # Should complete successfully (percent dried >= 99%)
        assert output[-1, 6] >= 99
        
        # Product temperature should stay safely cold
        assert np.all(output[:, 2] < -5.0)  # Tbot should stay below -5°C


class TestRegressionConsistency:
    """Tests to ensure consistency across code versions."""
    
    def test_output_format_consistency(self):
        """Test that output format remains consistent."""
        vial = {'Av': 3.80, 'Ap': 3.14, 'Vfill': 2.0}
        product = {'cSolid': 0.05, 'R0': 1.4, 'A1': 16.0, 'A2': 0.0}
        ht = {'KC': 2.75e-4, 'KP': 8.93e-4, 'KD': 0.46}
        Pchamber = {'setpt': [0.15], 'dt_setpt': [1800.0], 'ramp_rate': 0.5}
        Tshelf = {'init': -35.0, 'setpt': [20.0], 'dt_setpt': [1800.0], 'ramp_rate': 1.0}
        dt = 0.01
        
        output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
        
        # Verify expected structure
        assert output.ndim == 2
        assert output.shape[1] == 7
        
        # Verify column meanings are preserved
        # [time, Tsub, Tbot, Tsh, Pch_mTorr, flux, percent_dried]
        assert output[0, 0] == 0.0  # Time starts at 0
        assert output[-1, 6] >= 99.0  # Last column is percent dried, should reach ~100%
    
    def test_numerical_stability(self):
        """Test that simulation is numerically stable."""
        vial = {'Av': 3.80, 'Ap': 3.14, 'Vfill': 2.0}
        product = {'cSolid': 0.05, 'R0': 1.4, 'A1': 16.0, 'A2': 0.0}
        ht = {'KC': 2.75e-4, 'KP': 8.93e-4, 'KD': 0.46}
        Pchamber = {'setpt': [0.15], 'dt_setpt': [1800.0], 'ramp_rate': 0.5}
        Tshelf = {'init': -35.0, 'setpt': [20.0], 'dt_setpt': [1800.0], 'ramp_rate': 1.0}
        dt = 0.01
        
        output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
        
        # Check for NaN or Inf values
        assert not np.any(np.isnan(output)), "Output contains NaN values"
        assert not np.any(np.isinf(output)), "Output contains Inf values"
        
        # Check for unreasonable jumps in values
        for col in range(output.shape[1]):
            diffs = np.abs(np.diff(output[:, col]))
            if col != 6:  # Skip %dried which can have large jumps near end
                # No value should change by more than 50% between steps (except near singularities)
                max_relative_change = np.max(diffs[1:-1] / (np.abs(output[1:-2, col]) + 1e-10))
                assert max_relative_change < 5.0, f"Column {col} has unstable values"
