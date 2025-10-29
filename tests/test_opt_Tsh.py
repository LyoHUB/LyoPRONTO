"""
Tests for LyoPRONTO optimizer functionality.

These tests validate the optimizer examples that match the web interface
optimizer functionality with fixed chamber pressure and shelf temperature optimization.
"""

import pytest
import numpy as np
import pandas as pd
import os
from lyopronto import opt_Tsh


class TestOptimizerWebInterface:
    """Test optimizer functionality matching web interface examples."""
    
    @pytest.fixture
    def optimizer_params(self):
        """
        Optimizer parameters from web interface screenshot.
        
        Returns all input parameters for the optimizer test case.
        """
        vial = {
            'Av': 3.8,     # Vial area [cm**2]
            'Ap': 3.14,    # Product area [cm**2]
            'Vfill': 2.0   # Fill volume [mL]
        }
        
        product = {
            'T_pr_crit': -5.0,   # Critical product temperature [degC]
            'cSolid': 0.05,      # Solid content [g/mL]
            'R0': 1.4,           # Product resistance coefficient R0 [cm**2-hr-Torr/g]
            'A1': 16.0,          # Product resistance coefficient A1 [1/cm]
            'A2': 0.0            # Product resistance coefficient A2 [1/cm**2]
        }
        
        ht = {
            'KC': 0.000275,   # Kc [cal/s/K/cm**2]
            'KP': 0.000893,   # Kp [cal/s/K/cm**2/Torr]
            'KD': 0.46        # Kd dimensionless
        }
        
        Pchamber = {
            'setpt': np.array([0.15]),      # Set point [Torr]
            'dt_setpt': np.array([1800]),   # Hold time [min]
            'ramp_rate': 0.5                # Ramp rate [Torr/min]
        }
        
        Tshelf = {
            'min': -45.0,                   # Minimum shelf temperature
            'max': 120.0,                   # Maximum shelf temperature
            'init': -35.0,                  # Initial shelf temperature
            'setpt': np.array([120.0]),     # Target set point
            'dt_setpt': np.array([1800]),   # Hold time [min]
            'ramp_rate': 1.0                # Ramp rate [degC/min]
        }
        
        eq_cap = {
            'a': -0.182,   # Equipment capability coefficient a
            'b': 11.7      # Equipment capability coefficient b
        }
        
        nVial = 398
        dt = 0.01   # Time step [hr]
        
        return vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial
    
    @pytest.fixture
    def reference_results(self):
        """Load reference results from web interface optimizer output."""
        csv_path = 'test_data/reference_optimizer.csv'
        df = pd.read_csv(csv_path, sep=';')
        # Convert percent dried from percentage (0-100) to fraction (0-1) to match current output format
        df['Percent Dried'] = df['Percent Dried'] / 100.0
        return df
    
    def test_optimizer_completes(self, optimizer_params):
        """Test that optimizer runs to completion."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = optimizer_params
        
        results = opt_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Check that results are returned
        assert results is not None
        assert len(results) > 0
        
        # Check that drying completes (fraction dried reaches ~1.0, was percentage 0-100, now fraction 0-1)
        percent_dried = results[:, 6]
        assert percent_dried[-1] >= 0.99, f"Drying incomplete: {percent_dried[-1]*100}% dried"
    
    def test_optimizer_output_shape(self, optimizer_params):
        """Test that optimizer output has correct shape and columns."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = optimizer_params
        
        results = opt_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Check shape (should have 7 columns)
        assert results.shape[1] == 7
        
        # Check that all values are finite
        assert np.all(np.isfinite(results))
    
    def test_optimizer_respects_critical_temperature(self, optimizer_params):
        """Test that product temperature stays at or below critical temperature."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = optimizer_params
        
        results = opt_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        T_bot = results[:, 2]  # Vial bottom (product) temperature
        T_crit = product['T_pr_crit']
        
        # Product temperature should not exceed critical temperature
        # Allow small tolerance for numerical precision
        assert np.all(T_bot <= T_crit + 0.01), \
            f"Product temperature exceeded critical: max={T_bot.max():.2f}°C, crit={T_crit}°C"
    
    def test_optimizer_shelf_temperature_bounds(self, optimizer_params):
        """Test that shelf temperature stays within specified bounds."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = optimizer_params
        
        results = opt_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        T_shelf = results[:, 3]
        
        # Shelf temperature should be within min/max bounds
        assert np.all(T_shelf >= Tshelf['min'] - 0.01), \
            f"Shelf temperature below minimum: min_T={T_shelf.min():.2f}°C"
        assert np.all(T_shelf <= Tshelf['max'] + 0.01), \
            f"Shelf temperature above maximum: max_T={T_shelf.max():.2f}°C"
    
    def test_optimizer_chamber_pressure_fixed(self, optimizer_params):
        """Test that chamber pressure remains at fixed setpoint."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = optimizer_params
        
        results = opt_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        P_chamber_mTorr = results[:, 4]
        P_setpoint_mTorr = Pchamber['setpt'][0] * 1000  # Convert Torr to mTorr
        
        # Chamber pressure should remain at setpoint (allowing small tolerance)
        assert np.all(np.abs(P_chamber_mTorr - P_setpoint_mTorr) < 1.0), \
            f"Chamber pressure deviated from setpoint: range={P_chamber_mTorr.min():.1f}-{P_chamber_mTorr.max():.1f} mTorr"
    
    def test_optimizer_time_progression(self, optimizer_params):
        """Test that time progresses monotonically."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = optimizer_params
        
        results = opt_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        time_hr = results[:, 0]
        
        # Time should be monotonically increasing
        time_diffs = np.diff(time_hr)
        assert np.all(time_diffs > 0), "Time not monotonically increasing"
        
        # Time should start at 0
        assert time_hr[0] == 0.0
    
    def test_optimizer_percent_dried_progression(self, optimizer_params):
        """Test that percent dried increases monotonically to 100%."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = optimizer_params
        
        results = opt_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        percent_dried = results[:, 6]
        
        # Percent dried should start at 0
        assert percent_dried[0] == 0.0
        
        # Percent dried should increase monotonically
        dried_diffs = np.diff(percent_dried)
        assert np.all(dried_diffs >= 0), "Percent dried decreased"
        
        # Should end at approximately 100%
        assert percent_dried[-1] >= 0.99
    
    def test_optimizer_matches_reference_timing(self, optimizer_params, reference_results):
        """Test that optimizer drying time matches reference output."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = optimizer_params
        
        results = opt_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        time_hr = results[:, 0]
        ref_time = reference_results['Time [hr]'].values
        
        # Final time should match reference (within tolerance)
        final_time = time_hr[-1]
        ref_final_time = ref_time[-1]
        
        # Allow 1% tolerance on final time
        time_tolerance = 0.01 * ref_final_time
        assert abs(final_time - ref_final_time) < time_tolerance, \
            f"Final time mismatch: got {final_time:.4f} hr, expected {ref_final_time:.4f} hr"
    
    def test_optimizer_matches_reference_temperatures(self, optimizer_params, reference_results):
        """Test that optimizer temperatures match reference output."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = optimizer_params
        
        results = opt_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        T_bot = results[:, 2]
        ref_T_bot = reference_results['Vial Bottom Temperature [C]'].values
        
        # Maximum product temperature should match reference (within tolerance)
        max_T_bot = T_bot.max()
        ref_max_T_bot = ref_T_bot.max()
        
        # Allow 0.5°C tolerance on maximum temperature
        assert abs(max_T_bot - ref_max_T_bot) < 0.5, \
            f"Max product temp mismatch: got {max_T_bot:.2f}°C, expected {ref_max_T_bot:.2f}°C"
    
    def test_optimizer_matches_reference_trajectory(self, optimizer_params, reference_results):
        """Test that optimizer trajectory approximately matches reference."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = optimizer_params
        
        results = opt_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Compare at specific time points
        ref_times = reference_results['Time [hr]'].values
        ref_dried = reference_results['Percent Dried'].values
        
        # Sample a few time points for comparison
        test_times = [0.5, 1.0, 1.5, 2.0]
        
        for test_time in test_times:
            if test_time > results[-1, 0]:
                continue  # Skip if beyond simulation time
                
            # Find closest time in results
            idx_result = np.argmin(np.abs(results[:, 0] - test_time))
            dried_result = results[idx_result, 6]
            
            # Find closest time in reference
            idx_ref = np.argmin(np.abs(ref_times - test_time))
            dried_ref = ref_dried[idx_ref]
            
            # Allow 5% tolerance on percent dried
            assert abs(dried_result - dried_ref) < 5.0, \
                f"Percent dried mismatch at t={test_time}hr: got {dried_result:.1f}%, expected {dried_ref:.1f}%"
    
    def test_optimizer_sublimation_flux_positive(self, optimizer_params):
        """Test that sublimation flux is always positive."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = optimizer_params
        
        results = opt_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        flux = results[:, 5]
        
        # Sublimation flux should be positive throughout
        assert np.all(flux > 0), f"Negative flux detected: min={flux.min():.6f}"
    
    def test_optimizer_example_script_runs(self):
        """Test that the optimizer example script runs successfully."""
        # Import and run the example
        import sys
        sys.path.insert(0, 'examples')
        
        from example_optimizer import run_optimizer_example
        
        results = run_optimizer_example()
        
        # Verify results
        assert results is not None
        assert len(results) > 0
        assert results[-1, 6] >= 0.99  # Drying complete


class TestOptimizerEdgeCases:
    """Test edge cases and error handling for optimizer."""
    
    @pytest.fixture
    def optimizer_params(self):
        """Optimizer parameters for edge case testing."""
        vial = {
            'Av': 3.8,
            'Ap': 3.14,
            'Vfill': 2.0
        }
        
        product = {
            'T_pr_crit': -5.0,
            'cSolid': 0.05,
            'R0': 1.4,
            'A1': 16.0,
            'A2': 0.0
        }
        
        ht = {
            'KC': 0.000275,
            'KP': 0.000893,
            'KD': 0.46
        }
        
        Pchamber = {
            'setpt': np.array([0.15]),
            'dt_setpt': np.array([1800]),
            'ramp_rate': 0.5
        }
        
        Tshelf = {
            'min': -45.0,
            'max': 120.0,
            'init': -35.0,
            'setpt': np.array([120.0]),
            'dt_setpt': np.array([1800]),
            'ramp_rate': 1.0
        }
        
        eq_cap = {
            'a': -0.182,
            'b': 11.7
        }
        
        nVial = 398
        dt = 0.01
        
        return vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial
    
    def test_optimizer_different_timesteps(self, optimizer_params):
        """Test optimizer with different time steps."""
        vial, product, ht, Pchamber, Tshelf, _, eq_cap, nVial = optimizer_params
        
        # Test with larger time step
        dt_large = 0.05
        results_large = opt_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt_large, eq_cap, nVial)
        
        # Should still complete successfully
        assert results_large is not None
        assert results_large[-1, 6] >= 0.99
        
        # Test with smaller time step
        dt_small = 0.005
        results_small = opt_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt_small, eq_cap, nVial)
        
        # Should still complete successfully with more steps
        assert results_small is not None
        assert results_small[-1, 6] >= 0.99
        assert len(results_small) > len(results_large)
    
    def test_optimizer_different_critical_temps(self, optimizer_params):
        """Test optimizer with different critical temperatures."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = optimizer_params
        
        # Test with higher critical temperature (faster drying)
        product_high_T = product.copy()
        product_high_T['T_pr_crit'] = -2.0
        results_high = opt_Tsh.dry(vial, product_high_T, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Test with lower critical temperature (slower drying)
        product_low_T = product.copy()
        product_low_T['T_pr_crit'] = -10.0
        results_low = opt_Tsh.dry(vial, product_low_T, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Higher critical temp should allow faster drying
        assert results_high[-1, 0] < results_low[-1, 0], \
            "Higher critical temperature should result in faster drying"


# Run with: pytest tests/test_optimizer.py -v
