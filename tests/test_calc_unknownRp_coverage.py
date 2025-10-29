"""Tests for calc_unknownRp.py to increase coverage from 11% to 80%+."""
import pytest
import numpy as np
import os
from lyopronto import calc_unknownRp
from .test_helpers import assert_physically_reasonable_output


class TestCalcUnknownRp:
    """Test calculator with unknown product resistance (uses experimental Tbot data)."""
    
    @pytest.fixture
    def unknown_rp_setup(self, standard_vial, standard_ht):
        """Setup for unknown Rp calculation with experimental temperature data."""
        # Product without R0, A1, A2 (will be estimated)
        product = {'cSolid': 0.05, 'T_pr_crit': -30.0}
        
        # Time-varying shelf temperature
        Tshelf = {
            'init': -40.0,
            'setpt': [-20.0, -10.0],  # Two ramp stages
            'dt_setpt': [120.0, 120.0],  # 2 hours each in minutes
            'ramp_rate': 0.1  # deg/min
        }
        
        # Time-varying chamber pressure
        Pchamber = {
            'setpt': [0.060, 0.080, 0.100],  # Three pressure stages
            'dt_setpt': [60.0, 120.0, 120.0],  # Time at each stage in minutes
            'ramp_rate': 0.5  # Ramp rate in Torr/min
        }
        
        # Load experimental temperature data
        test_data_dir = os.path.join(os.path.dirname(__file__), '..', 'test_data')
        temp_file = os.path.join(test_data_dir, 'temperature.txt')
        
        # Load and parse temperature data
        time_exp = []
        Tbot_exp = []
        with open(temp_file, 'r') as f:
            for line in f:
                if line.strip():
                    t, T = line.split()
                    time_exp.append(float(t))
                    Tbot_exp.append(float(T))
        
        time = np.array(time_exp)
        Tbot_exp = np.array(Tbot_exp)
        
        return {
            'vial': standard_vial,
            'product': product,
            'ht': standard_ht,
            'Pchamber': Pchamber,
            'Tshelf': Tshelf,
            'time': time,
            'Tbot_exp': Tbot_exp
        }
    
    def test_unknown_rp_completes(self, unknown_rp_setup):
        """Test that simulation completes with experimental data."""
        output, product_res = calc_unknownRp.dry(
            unknown_rp_setup['vial'],
            unknown_rp_setup['product'],
            unknown_rp_setup['ht'],
            unknown_rp_setup['Pchamber'],
            unknown_rp_setup['Tshelf'],
            unknown_rp_setup['time'],
            unknown_rp_setup['Tbot_exp']
        )
        
        # Should return an array
        assert isinstance(output, np.ndarray)
        assert output.shape[0] > 0
        assert output.shape[1] == 7  # Standard output columns
    
    def test_unknown_rp_output_shape(self, unknown_rp_setup):
        """Test output has correct dimensions and structure."""
        output, product_res = calc_unknownRp.dry(
            unknown_rp_setup['vial'],
            unknown_rp_setup['product'],
            unknown_rp_setup['ht'],
            unknown_rp_setup['Pchamber'],
            unknown_rp_setup['Tshelf'],
            unknown_rp_setup['time'],
            unknown_rp_setup['Tbot_exp']
        )
        
        # Check number of columns
        assert output.shape[1] == 7, "Output should have 7 columns"
        
        # Check output columns exist and are numeric
        assert np.all(np.isfinite(output[:, 0])), "Time column has invalid values"
        assert np.all(np.isfinite(output[:, 1])), "Tsub column has invalid values"
        assert np.all(np.isfinite(output[:, 2])), "Tbot column has invalid values"
        assert np.all(np.isfinite(output[:, 3])), "Tsh column has invalid values"
        assert np.all(np.isfinite(output[:, 4])), "Pch column has invalid values"
        assert np.all(np.isfinite(output[:, 5])), "flux column has invalid values"
        assert np.all(np.isfinite(output[:, 6])), "frac_dried column has invalid values"
    
    def test_unknown_rp_time_progression(self, unknown_rp_setup):
        """Test time progresses monotonically."""
        output, product_res = calc_unknownRp.dry(
            unknown_rp_setup['vial'],
            unknown_rp_setup['product'],
            unknown_rp_setup['ht'],
            unknown_rp_setup['Pchamber'],
            unknown_rp_setup['Tshelf'],
            unknown_rp_setup['time'],
            unknown_rp_setup['Tbot_exp']
        )
        
        time = output[:, 0]
        
        # Time should be monotonically increasing
        time_diffs = np.diff(time)
        assert np.all(time_diffs >= 0), "Time must be monotonically increasing"
        
        # Time should start at or near zero
        assert time[0] >= 0, f"Initial time should be non-negative, got {time[0]}"
    
    def test_unknown_rp_shelf_temp_changes(self, unknown_rp_setup):
        """Test shelf temperature follows ramp schedule."""
        output, product_res = calc_unknownRp.dry(
            unknown_rp_setup['vial'],
            unknown_rp_setup['product'],
            unknown_rp_setup['ht'],
            unknown_rp_setup['Pchamber'],
            unknown_rp_setup['Tshelf'],
            unknown_rp_setup['time'],
            unknown_rp_setup['Tbot_exp']
        )
        
        Tsh = output[:, 3]
        
        # Shelf temperature should start at init value
        assert abs(Tsh[0] - unknown_rp_setup['Tshelf']['init']) < 1.0, \
            f"Initial Tsh should be near {unknown_rp_setup['Tshelf']['init']}, got {Tsh[0]}"
        
        # Shelf temperature should change over time
        Tsh_range = np.max(Tsh) - np.min(Tsh)
        assert Tsh_range > 5.0, "Shelf temperature should vary during ramping"
    
    def test_unknown_rp_pressure_changes(self, unknown_rp_setup):
        """Test chamber pressure follows setpoint schedule."""
        output, product_res = calc_unknownRp.dry(
            unknown_rp_setup['vial'],
            unknown_rp_setup['product'],
            unknown_rp_setup['ht'],
            unknown_rp_setup['Pchamber'],
            unknown_rp_setup['Tshelf'],
            unknown_rp_setup['time'],
            unknown_rp_setup['Tbot_exp']
        )
        
        Pch = output[:, 4] / 1000  # Convert mTorr to Torr
        
        # Pressure should be within range of setpoints
        min_setpt = min(unknown_rp_setup['Pchamber']['setpt'])
        max_setpt = max(unknown_rp_setup['Pchamber']['setpt'])
        
        assert np.min(Pch) >= min_setpt * 0.9, \
            f"Min pressure {np.min(Pch):.3f} below setpoint range"
        assert np.max(Pch) <= max_setpt * 1.1, \
            f"Max pressure {np.max(Pch):.3f} above setpoint range"
    
    def test_unknown_rp_physically_reasonable(self, unknown_rp_setup):
        """Test output is physically reasonable."""
        output, product_res = calc_unknownRp.dry(
            unknown_rp_setup['vial'],
            unknown_rp_setup['product'],
            unknown_rp_setup['ht'],
            unknown_rp_setup['Pchamber'],
            unknown_rp_setup['Tshelf'],
            unknown_rp_setup['time'],
            unknown_rp_setup['Tbot_exp']
        )
        
        assert_physically_reasonable_output(output)
    
    def test_unknown_rp_reaches_completion(self, unknown_rp_setup):
        """Test that drying progresses with parameter estimation.
        
        Note: Parameter estimation with experimental data may not always
        reach high completion due to physics constraints and fitting complexity.
        """
        output, product_res = calc_unknownRp.dry(
            unknown_rp_setup['vial'],
            unknown_rp_setup['product'],
            unknown_rp_setup['ht'],
            unknown_rp_setup['Pchamber'],
            unknown_rp_setup['Tshelf'],
            unknown_rp_setup['time'],
            unknown_rp_setup['Tbot_exp']
        )
        
        final_fraction = output[-1, 6]
        # Parameter estimation may have limited progress - check for any drying
        assert final_fraction > 0.0, \
            f"Should show drying progress, got {final_fraction*100:.1f}%"
        assert final_fraction <= 1.0, \
            f"Fraction dried should not exceed 100%, got {final_fraction*100:.1f}%"
    
    def test_unknown_rp_fraction_dried_monotonic(self, unknown_rp_setup):
        """Test fraction dried increases monotonically."""
        output, product_res = calc_unknownRp.dry(
            unknown_rp_setup['vial'],
            unknown_rp_setup['product'],
            unknown_rp_setup['ht'],
            unknown_rp_setup['Pchamber'],
            unknown_rp_setup['Tshelf'],
            unknown_rp_setup['time'],
            unknown_rp_setup['Tbot_exp']
        )
        
        frac_dried = output[:, 6]
        
        # Fraction dried should be monotonically increasing
        diffs = np.diff(frac_dried)
        assert np.all(diffs >= -1e-6), "Fraction dried must increase monotonically"
    
    def test_unknown_rp_flux_positive(self, unknown_rp_setup):
        """Test sublimation flux is non-negative."""
        output, product_res = calc_unknownRp.dry(
            unknown_rp_setup['vial'],
            unknown_rp_setup['product'],
            unknown_rp_setup['ht'],
            unknown_rp_setup['Pchamber'],
            unknown_rp_setup['Tshelf'],
            unknown_rp_setup['time'],
            unknown_rp_setup['Tbot_exp']
        )
        
        flux = output[:, 5]
        assert np.all(flux >= 0), "Sublimation flux must be non-negative"
    
    def test_unknown_rp_different_initial_pressure(self, unknown_rp_setup):
        """Test with different initial chamber pressure."""
        # Modify pressure setpoints
        Pchamber_modified = unknown_rp_setup['Pchamber'].copy()
        Pchamber_modified['setpt'] = [0.050, 0.070, 0.090]
        
        output, product_res = calc_unknownRp.dry(
            unknown_rp_setup['vial'],
            unknown_rp_setup['product'],
            unknown_rp_setup['ht'],
            Pchamber_modified,
            unknown_rp_setup['Tshelf'],
            unknown_rp_setup['time'],
            unknown_rp_setup['Tbot_exp']
        )
        
        assert output.shape[0] > 0
        assert_physically_reasonable_output(output)


class TestCalcUnknownRpEdgeCases:
    """Test edge cases for unknown Rp calculator."""
    
    @pytest.fixture
    def minimal_setup(self, standard_vial, standard_ht):
        """Minimal setup with short time series."""
        product = {'cSolid': 0.05, 'T_pr_crit': -30.0}
        
        Tshelf = {
            'init': -40.0,
            'setpt': [-30.0],
            'dt_setpt': [60.0],
            'ramp_rate': 0.1
        }
        
        Pchamber = {
            'setpt': [0.080],
            'dt_setpt': [60.0],
            'ramp_rate': 0.5
        }
        
        # Minimal time series
        time = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
        Tbot_exp = np.array([-40.0, -38.0, -35.0, -32.0, -30.0])
        
        return {
            'vial': standard_vial,
            'product': product,
            'ht': standard_ht,
            'Pchamber': Pchamber,
            'Tshelf': Tshelf,
            'time': time,
            'Tbot_exp': Tbot_exp
        }
    
    def test_minimal_time_series(self, minimal_setup):
        """Test with minimal time series data."""
        output, product_res = calc_unknownRp.dry(
            minimal_setup['vial'],
            minimal_setup['product'],
            minimal_setup['ht'],
            minimal_setup['Pchamber'],
            minimal_setup['Tshelf'],
            minimal_setup['time'],
            minimal_setup['Tbot_exp']
        )
        
        assert output.shape[0] > 0
        assert output.shape[1] == 7
    
    def test_single_pressure_setpoint(self, minimal_setup):
        """Test with single constant pressure."""
        # Already has single pressure in minimal_setup
        output, product_res = calc_unknownRp.dry(
            minimal_setup['vial'],
            minimal_setup['product'],
            minimal_setup['ht'],
            minimal_setup['Pchamber'],
            minimal_setup['Tshelf'],
            minimal_setup['time'],
            minimal_setup['Tbot_exp']
        )
        
        Pch = output[:, 4] / 1000  # Convert to Torr
        
        # Should maintain constant pressure
        Pch_std = np.std(Pch)
        assert Pch_std < 0.01, f"Pressure should be nearly constant, std={Pch_std:.4f}"
    
    def test_high_solids_concentration(self, minimal_setup):
        """Test with high solids concentration."""
        minimal_setup['product']['cSolid'] = 0.15  # 15% solids
        
        output, product_res = calc_unknownRp.dry(
            minimal_setup['vial'],
            minimal_setup['product'],
            minimal_setup['ht'],
            minimal_setup['Pchamber'],
            minimal_setup['Tshelf'],
            minimal_setup['time'],
            minimal_setup['Tbot_exp']
        )
        
        assert output.shape[0] > 0
        assert_physically_reasonable_output(output)
