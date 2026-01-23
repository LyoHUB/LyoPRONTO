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
from lyopronto.functions import Lpr0_FUN, Rp_FUN
from .utils import assert_physically_reasonable_output


# Test constants for dried percent validation (column 6 is percentage 0-100)
MIN_COMPLETION_PERCENT = 50.0  # Minimum acceptable completion (50%) for some tests

@pytest.fixture
def standard_inputs_nodt(standard_vial, standard_ht, standard_pchamber, standard_tshelf):
    """Default inputs for calc_unknownRp.py."""
    product = {'cSolid': 0.05, 'T_pr_crit': -25.0}  # No R0, A1, A2 provided
    return standard_vial, product, standard_ht, standard_pchamber, standard_tshelf

@pytest.fixture
def temperature_data():
    """Load temperature data from test_data/temperature.txt."""
    data_path = Path(__file__).parent.parent / 'test_data/temperature.txt'
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

class TestCalcUnknownRpBasic:
    """Basic functionality tests for parameter estimation."""
    
    
    
    def test_calc_unknownRp_basics(self, standard_inputs_nodt, temperature_data):
        """For calc_unknownRp.dry(), test that:
        - executes successfully
        - output has correct shape
        - output columns contain valid data
        - product_res contains valid resistance data
        - parameter estimation produces reasonable values
        - drying exceeds half completion
        - cake length reaches reasonable values, matches drying progress
        """
        vial, product, ht, Pchamber, Tshelf = standard_inputs_nodt
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
        
        # Output should have 7 columns (same as calc_knownRp)
        assert output.shape[1] == 7, f"Expected 7 columns, got {output.shape[1]}"
        
        # product_res should have 3 columns (time, Lck, Rp)
        assert product_res.shape[1] == 3, f"Expected 3 columns in product_res, got {product_res.shape[1]}"
        
        # Should have multiple time points
        assert len(output) > 10, "Should have multiple time points"
        assert len(product_res) > 10, "product_res should have multiple points"
        
        assert_physically_reasonable_output(output)
    
        # Column 0: Time
        assert np.all(product_res[:, 0] >= 0), "Time should be non-negative"
        
        # Column 1: Lck (cake length) should increase from 0
        assert product_res[0, 1] == pytest.approx(0.0, abs=1e-6), "Should start at Lck=0"
        assert np.all(np.diff(product_res[:, 1]) >= 0), "Lck should be non-decreasing"
        
        # Column 2: Rp (resistance) - NOTE: can be negative early during optimization
        # We just check that the final resistance is positive and reasonable
        assert product_res[-1, 2] > 0, "Final resistance should be positive"
        
        # Check that resistance is positive and reasonable
        # Negative values *do* occur in the early phase, if calculated with incorrect conditions
        # or simply because the measurements come from a real system.
        positive_count = np.sum(product_res[:, 2] > 0)
        assert positive_count > len(product_res) / 2, "Most resistances should be positive"
    
        # Fit Rp model: Rp = R0 + A1*Lck/(1 + A2*Lck)
        params, params_covariance = sp.curve_fit(Rp_FUN,
            product_res[:, 1],  # Lck
            product_res[:, 2],  # Rp
            p0=[1.0, 1.0, 0.0]
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
        
        # NOTE: column 6 is percentage (0-100)
        final_dried_percent = output[-1, 6]
        
        # Should reach near completion (within experimental data range)
        assert final_dried_percent > MIN_COMPLETION_PERCENT , \
            f"Estimates should reach at least {MIN_COMPLETION_PERCENT:.0f}% dry, got {final_dried_percent:.1f}%"
    
        # Calculate initial product height
        Lpr0 = Lpr0_FUN(vial['Vfill'], vial['Ap'], product['cSolid'])
        
        final_Lck = product_res[-1, 1]
        
        # Final cake length should be nonzero
        # Should not exceed original, since experimental data must end before complete drying)
        assert final_Lck > 0, "Cake length should have progressed"
        assert final_Lck <= Lpr0 * 1.01, "Cake length should not exceed initial height"

class TestCalcUnknownRpEdgeCases:
    """Test edge cases and different input scenarios."""
    
    def test_short_time_series(self, standard_inputs_nodt):
        """Test with minimal time points."""
        # Minimal time series (3 points)
        time = np.array([0.0, 1.0, 2.0])
        Tbot_exp = np.array([-40.0, -37.0, -35.0])
        
        # Should run without error
        output, product_res = calc_unknownRp.dry(*standard_inputs_nodt,
            time, Tbot_exp
        )
        
        assert output is not None
        assert len(output) == len(Tbot_exp)+1, "Should have exactly 3 time points to match temperature input"

        assert_physically_reasonable_output(output)
    
    def test_different_pressure(self, standard_inputs_nodt):
        """Test with different chamber pressure."""
        vial, product, ht, _, Tshelf = standard_inputs_nodt
        Pchamber = {'setpt': [0.10], 'dt_setpt': [1800.0], 'ramp_rate': 0.5}  # Lower pressure
        
        time = np.array([0.0, 1.0, 2.0, 3.0])
        Tbot_exp = np.array([-40.0, -38.0, -32.0, -25.0])
        
        output, product_res = calc_unknownRp.dry(
            vial, product, ht, Pchamber, Tshelf, time, Tbot_exp
        )
        
        # Check pressure in output (should be 100 mTorr)
        assert np.allclose(output[:, 4], 100.0, atol=1.0), "Pch should be ~100 mTorr"
        assert_physically_reasonable_output(output)
    
    def test_different_product_concentration(self, standard_inputs_nodt, temperature_data):
        """Test with different solute concentration."""
        vial, product, ht, Pchamber, Tshelf = standard_inputs_nodt
        product['cSolid'] = 0.15 # Higher concentration
        
        output, product_res = calc_unknownRp.dry(
            vial, product, ht, Pchamber, Tshelf, *temperature_data
        )
        
        assert output is not None
        # Higher concentration means less ice to sublimate, different drying time
        assert_physically_reasonable_output(output)

    def test_unknown_rp_condition_changes(self, timevarying_inputs_nodt, temperature_data):
        """Test shelf temperature and chamber pressure follow varying schedules."""
        vial, product, ht, _, __ = timevarying_inputs_nodt
    
        Tshelf = {
            'init': -35.0,
            'setpt': [-20.0, -10.0],  # Two ramp stages
            'dt_setpt': [120.0, 1200.0],  # 2 + 20 hours in [min]
            'ramp_rate': 0.5  # deg/min
        }
        
        Pchamber = {
            'setpt': [0.060, 0.080, 0.100],  # Three pressure stages
            'dt_setpt': [60.0, 120.0, 120.0],  # Time at each stage [min]
            'ramp_rate': 0.5  # Ramp rate [Torr/min]
        }
        output, product_res = calc_unknownRp.dry(vial, product, ht, Pchamber, Tshelf, *temperature_data)
        
        Tsh = output[:, 3]
        
        # Shelf temperature should start at init value
        assert abs(Tsh[0] - Tshelf['init']) < 1.0, \
            f"Initial Tsh should be near {Tshelf['init']}, got {Tsh[0]}"
        
        # Shelf temperature should change over time
        Tsh_range = np.max(Tsh) - np.min(Tsh)
        assert Tsh_range > 5.0, "Shelf temperature should vary during ramping"
    
        Pch = output[:, 4] / 1000  # Convert mTorr to Torr
        
        # Pressure should be within range of setpoints
        min_setpt = min(Pchamber['setpt'])
        max_setpt = max(Pchamber['setpt'])
        
        assert np.min(Pch) >= min_setpt, \
            f"Min pressure {np.min(Pch):.3f} below setpoint range"
        assert np.max(Pch) <= max_setpt, \
            f"Max pressure {np.max(Pch):.3f} above setpoint range"
    
        # This includes checks for drying progress, temperature, flux, etc.
        assert_physically_reasonable_output(output)


class TestCalcUnknownRpValidation:
    """Validation tests against known examples."""
    
    def test_matches_example_script(self, standard_inputs_nodt):
        """Test that results match ex_unknownRp_PD.py example."""
        # Use same inputs as ex_unknownRp_PD.py
        vial, product, ht, Pchamber, Tshelf = standard_inputs_nodt
        
        # Load temperature data
        data_path = Path(__file__).parent.parent / 'test_data/temperature.txt'
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
        
        # Simulation should reach reasonable drying progress, in 0 - 100 range
        final_dried_percent = output[-1, 6]
        assert 0 < final_dried_percent <= 100, \
            f"Final dried {final_dried_percent:.4f} outside expected range [0, 100]"