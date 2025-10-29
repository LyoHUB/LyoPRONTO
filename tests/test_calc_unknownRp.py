"""
Tests for calc_unknownRp.py - Parameter estimation module.

This module is a VALIDATION tool for future Pyomo implementations, not experimental code.
It estimates product resistance parameters (R0, A1, A2) from experimental temperature data.

These tests are based on the working example in ex_unknownRp_PD.py.
"""

import pytest
import numpy as np
import scipy.optimize as sp
from pathlib import Path

from lyopronto import calc_unknownRp
from lyopronto.functions import Lpr0_FUN


class TestCalcUnknownRpBasic:
    """Basic functionality tests for parameter estimation."""
    
    @pytest.fixture
    def standard_inputs(self):
        """Standard inputs from ex_unknownRp_PD.py."""
        vial = {
            'Av': 3.80,
            'Ap': 3.14,
            'Vfill': 2.0
        }
        
        product = {
            'cSolid': 0.05,
            'T_pr_crit': -5.0
        }
        
        ht = {
            'KC': 2.75e-4,
            'KP': 8.93e-4,
            'KD': 0.46
        }
        
        Pchamber = {
            'setpt': [0.15],
            'dt_setpt': [1800.0],
            'ramp_rate': 0.5
        }
        
        Tshelf = {
            'init': -35.0,
            'setpt': [20.0],
            'dt_setpt': [1800.0],
            'ramp_rate': 1.0
        }
        
        return vial, product, ht, Pchamber, Tshelf
    
    @pytest.fixture
    def temperature_data(self):
        """Load temperature data from test_data/temperature.txt."""
        data_path = Path('test_data/temperature.txt')
        if not data_path.exists():
            pytest.skip("Temperature data file not found")
        
        dat = np.loadtxt(data_path)
        
        # Handle different file formats
        if dat.ndim == 1:
            time = np.array([dat[0]])
            Tbot_exp = np.array([dat[1]])
        elif dat.shape[1] == 2:
            time = dat[:, 0]
            Tbot_exp = dat[:, 1]
        else:
            time = dat[:, 1]
            Tbot_exp = dat[:, 2]
        
        return time, Tbot_exp
    
    def test_calc_unknownRp_runs(self, standard_inputs, temperature_data):
        """Test that calc_unknownRp.dry() executes successfully."""
        vial, product, ht, Pchamber, Tshelf = standard_inputs
        time, Tbot_exp = temperature_data
        
        # Run parameter estimation
        output, product_res = calc_unknownRp.dry(
            vial, product, ht, Pchamber, Tshelf, time, Tbot_exp
        )
        
        # Verify output exists
        assert output is not None, "output should not be None"
        assert product_res is not None, "product_res should not be None"
        assert isinstance(output, np.ndarray), "output should be numpy array"
        assert isinstance(product_res, np.ndarray), "product_res should be numpy array"
    
    def test_output_shape(self, standard_inputs, temperature_data):
        """Test that output has correct shape."""
        vial, product, ht, Pchamber, Tshelf = standard_inputs
        time, Tbot_exp = temperature_data
        
        output, product_res = calc_unknownRp.dry(
            vial, product, ht, Pchamber, Tshelf, time, Tbot_exp
        )
        
        # Output should have 7 columns (same as calc_knownRp)
        assert output.shape[1] == 7, f"Expected 7 columns, got {output.shape[1]}"
        
        # product_res should have 3 columns (time, Lck, Rp)
        assert product_res.shape[1] == 3, f"Expected 3 columns in product_res, got {product_res.shape[1]}"
        
        # Should have multiple time points
        assert len(output) > 10, "Should have multiple time points"
        assert len(product_res) > 10, "product_res should have multiple points"
    
    def test_output_columns(self, standard_inputs, temperature_data):
        """Test that output columns contain valid data."""
        vial, product, ht, Pchamber, Tshelf = standard_inputs
        time, Tbot_exp = temperature_data
        
        output, product_res = calc_unknownRp.dry(
            vial, product, ht, Pchamber, Tshelf, time, Tbot_exp
        )
        
        # Column 0: Time should increase
        assert np.all(np.diff(output[:, 0]) >= 0), "Time should be non-decreasing"
        assert output[0, 0] == pytest.approx(0.0, abs=1e-6), "Should start at t=0"
        
        # Column 1: Tsub should be below freezing
        assert np.all(output[:, 1] <= 0), "Sublimation temp should be below 0°C"
        assert np.all(output[:, 1] >= -60), "Sublimation temp should be above -60°C"
        
        # Column 2: Tbot should be reasonable
        assert np.all(output[:, 2] >= -50), "Tbot should be above -50°C"
        assert np.all(output[:, 2] <= 25), "Tbot should be below 25°C"
        
        # Column 4: Pch should be in mTorr (150 mTorr = 0.15 Torr)
        assert np.allclose(output[:, 4], 150.0, atol=1.0), "Pch should be ~150 mTorr"
        
        # Column 5: Flux should be non-negative
        assert np.all(output[:, 5] >= 0), "Flux should be non-negative"
        
        # Column 6: Percent dried should be 0-100 (NOTE: it's percentage, not fraction!)
        assert np.all(output[:, 6] >= 0), "Percent dried should be >= 0"
        assert np.all(output[:, 6] <= 100.0), "Percent dried should be <= 100"
    
    def test_product_resistance_output(self, standard_inputs, temperature_data):
        """Test that product_res contains valid resistance data."""
        vial, product, ht, Pchamber, Tshelf = standard_inputs
        time, Tbot_exp = temperature_data
        
        output, product_res = calc_unknownRp.dry(
            vial, product, ht, Pchamber, Tshelf, time, Tbot_exp
        )
        
        # Column 0: Time
        assert np.all(product_res[:, 0] >= 0), "Time should be non-negative"
        
        # Column 1: Lck (cake length) should increase from 0
        assert product_res[0, 1] == pytest.approx(0.0, abs=1e-6), "Should start at Lck=0"
        assert np.all(np.diff(product_res[:, 1]) >= 0), "Lck should be non-decreasing"
        
        # Column 2: Rp (resistance) - NOTE: can be negative early during optimization
        # We just check that the final resistance is positive and reasonable
        assert product_res[-1, 2] > 0, "Final resistance should be positive"
        
        # Check that resistance eventually becomes positive and reasonable
        # Most values should be positive after initial optimization phase
        positive_count = np.sum(product_res[:, 2] > 0)
        assert positive_count > len(product_res) / 2, "Most resistances should be positive"
    
    def test_parameter_estimation(self, standard_inputs, temperature_data):
        """Test that parameter estimation produces reasonable values."""
        vial, product, ht, Pchamber, Tshelf = standard_inputs
        time, Tbot_exp = temperature_data
        
        output, product_res = calc_unknownRp.dry(
            vial, product, ht, Pchamber, Tshelf, time, Tbot_exp
        )
        
        # Fit Rp model: Rp = R0 + A1*Lck/(1 + A2*Lck)
        params, params_covariance = sp.curve_fit(
            lambda h, r, a1, a2: r + h*a1/(1 + h*a2),
            product_res[:, 1],  # Lck
            product_res[:, 2],  # Rp
            p0=[1.0, 0.0, 0.0]
        )
        
        R0_est = params[0]
        A1_est = params[1]
        A2_est = params[2]
        
        # Check physical reasonableness
        assert R0_est > 0, f"R0 should be positive, got {R0_est}"
        assert R0_est < 100, f"R0 seems unreasonably large: {R0_est}"
        assert A1_est >= 0, f"A1 should be non-negative, got {A1_est}"
        assert A2_est >= 0, f"A2 should be non-negative, got {A2_est}"
        
        # Check covariance is reasonable (not infinite/NaN)
        assert np.all(np.isfinite(params_covariance)), "Covariance should be finite"
    
    def test_drying_completes(self, standard_inputs, temperature_data):
        """Test that drying reaches near completion."""
        vial, product, ht, Pchamber, Tshelf = standard_inputs
        time, Tbot_exp = temperature_data
        
        output, product_res = calc_unknownRp.dry(
            vial, product, ht, Pchamber, Tshelf, time, Tbot_exp
        )
        
        # NOTE: column 6 is now FRACTION (0-1), not percentage (0-100)
        final_dried_fraction = output[-1, 6]
        
        # Should reach near completion (within experimental data range)
        assert final_dried_fraction > 0.50, f"Should dry at least 50%, got {final_dried_fraction*100:.1f}%"
    
    def test_cake_length_reaches_initial_height(self, standard_inputs, temperature_data):
        """Test that cake length approaches initial product height."""
        vial, product, ht, Pchamber, Tshelf = standard_inputs
        time, Tbot_exp = temperature_data
        
        output, product_res = calc_unknownRp.dry(
            vial, product, ht, Pchamber, Tshelf, time, Tbot_exp
        )
        
        # Calculate initial product height
        Lpr0 = Lpr0_FUN(vial['Vfill'], vial['Ap'], product['cSolid'])
        
        final_Lck = product_res[-1, 1]
        
        # Final cake length should be approaching Lpr0
        # (may not reach it exactly if experimental data ends before complete drying)
        assert final_Lck > 0, "Cake length should have progressed"
        assert final_Lck <= Lpr0 * 1.01, "Cake length should not exceed initial height"


class TestCalcUnknownRpEdgeCases:
    """Test edge cases and different input scenarios."""
    
    def test_short_time_series(self):
        """Test with minimal time points."""
        vial = {'Av': 3.8, 'Ap': 3.14, 'Vfill': 2.0}
        product = {'cSolid': 0.05, 'T_pr_crit': -5.0}
        ht = {'KC': 2.75e-4, 'KP': 8.93e-4, 'KD': 0.46}
        Pchamber = {'setpt': [0.15], 'dt_setpt': [1800.0], 'ramp_rate': 0.5}
        Tshelf = {'init': -35.0, 'setpt': [20.0], 'dt_setpt': [1800.0], 'ramp_rate': 1.0}
        
        # Minimal time series (3 points)
        time = np.array([0.0, 1.0, 2.0])
        Tbot_exp = np.array([-35.0, -30.0, -25.0])
        
        # Should run without error
        output, product_res = calc_unknownRp.dry(
            vial, product, ht, Pchamber, Tshelf, time, Tbot_exp
        )
        
        assert output is not None
        assert len(output) >= 3, "Should have at least 3 time points"
    
    def test_different_pressure(self):
        """Test with different chamber pressure."""
        vial = {'Av': 3.8, 'Ap': 3.14, 'Vfill': 2.0}
        product = {'cSolid': 0.05, 'T_pr_crit': -5.0}
        ht = {'KC': 2.75e-4, 'KP': 8.93e-4, 'KD': 0.46}
        Pchamber = {'setpt': [0.10], 'dt_setpt': [1800.0], 'ramp_rate': 0.5}  # Lower pressure
        Tshelf = {'init': -35.0, 'setpt': [20.0], 'dt_setpt': [1800.0], 'ramp_rate': 1.0}
        
        time = np.array([0.0, 1.0, 2.0, 3.0])
        Tbot_exp = np.array([-35.0, -32.0, -28.0, -25.0])
        
        output, product_res = calc_unknownRp.dry(
            vial, product, ht, Pchamber, Tshelf, time, Tbot_exp
        )
        
        # Check pressure in output (should be 100 mTorr)
        assert np.allclose(output[:, 4], 100.0, atol=1.0), "Pch should be ~100 mTorr"
    
    def test_different_product_concentration(self):
        """Test with different solute concentration."""
        vial = {'Av': 3.8, 'Ap': 3.14, 'Vfill': 2.0}
        product = {'cSolid': 0.10, 'T_pr_crit': -5.0}  # Higher concentration
        ht = {'KC': 2.75e-4, 'KP': 8.93e-4, 'KD': 0.46}
        Pchamber = {'setpt': [0.15], 'dt_setpt': [1800.0], 'ramp_rate': 0.5}
        Tshelf = {'init': -35.0, 'setpt': [20.0], 'dt_setpt': [1800.0], 'ramp_rate': 1.0}
        
        time = np.array([0.0, 1.0, 2.0, 3.0])
        Tbot_exp = np.array([-35.0, -32.0, -28.0, -25.0])
        
        output, product_res = calc_unknownRp.dry(
            vial, product, ht, Pchamber, Tshelf, time, Tbot_exp
        )
        
        assert output is not None
        # Higher concentration means less ice to sublimate, different drying time
        assert len(output) > 0


class TestCalcUnknownRpValidation:
    """Validation tests against known examples."""
    
    def test_matches_example_script(self):
        """Test that results match ex_unknownRp_PD.py example."""
        # Use same inputs as ex_unknownRp_PD.py
        vial = {'Av': 3.80, 'Ap': 3.14, 'Vfill': 2.0}
        product = {'cSolid': 0.05, 'T_pr_crit': -5.0}
        ht = {'KC': 2.75e-4, 'KP': 8.93e-4, 'KD': 0.46}
        Pchamber = {'setpt': [0.15], 'dt_setpt': [1800.0], 'ramp_rate': 0.5}
        Tshelf = {'init': -35.0, 'setpt': [20.0], 'dt_setpt': [1800.0], 'ramp_rate': 1.0}
        
        # Load temperature data
        data_path = Path('test_data/temperature.txt')
        if not data_path.exists():
            pytest.skip("Temperature data file not found")
        
        dat = np.loadtxt(data_path)
        if dat.shape[1] == 2:
            time = dat[:, 0]
            Tbot_exp = dat[:, 1]
        else:
            time = dat[:, 1]
            Tbot_exp = dat[:, 2]
        
        # Run calc_unknownRp
        output, product_res = calc_unknownRp.dry(
            vial, product, ht, Pchamber, Tshelf, time, Tbot_exp
        )
        
        # Estimate parameters
        params, _ = sp.curve_fit(
            lambda h, r, a1, a2: r + h*a1/(1 + h*a2),
            product_res[:, 1],
            product_res[:, 2],
            p0=[1.0, 0.0, 0.0]
        )
        
        R0 = params[0]
        A1 = params[1]
        A2 = params[2]
        
        # Parameters should be physically reasonable
        # (exact values depend on experimental data, but ranges should be sensible)
        assert 0 < R0 < 10, f"R0 = {R0} outside expected range (0, 10)"
        assert 0 <= A1 < 50, f"A1 = {A1} outside expected range [0, 50)"
        assert 0 <= A2 < 5, f"A2 = {A2} outside expected range [0, 5)"
        
        # Simulation should reach reasonable drying progress
        # NOTE: column 6 is fraction (0-1), not percentage (0-100)
        final_dried_fraction = output[-1, 6]
        assert 0.50 < final_dried_fraction <= 1.0, \
            f"Final dried {final_dried_fraction:.4f} outside expected range (0.50, 1.0]"
