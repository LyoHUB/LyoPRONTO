"""
Tests for LyoPRONTO optimizer functionality.

These tests validate the optimizer examples that match the web interface
optimizer functionality with fixed chamber pressure and shelf temperature optimization.
"""

import pytest
import numpy as np
import pandas as pd
from lyopronto import opt_Tsh
from .utils import assert_physically_reasonable_output


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
        return df
    
    def test_optimizer_basics(self, optimizer_params, reference_results):
        """Test that optimizer: 
        - runs to completion.
        - outputs correct shape and columns.
        - keeps product temperature at or below critical temperature.
        - keeps shelf temperature within specified bounds.
        - keeps chamber pressure at fixed setpoint.
        - matches drying time with reference output."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = optimizer_params
        
        output = opt_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Should return valid output
        assert output is not None
        assert output.size > 0
        
        # Check that drying completes
        percent_dried = output[:, 6]
        assert percent_dried[-1] >= 99, f"Drying incomplete: {percent_dried[-1]}% dried"

        # Check shape (should have 7 columns)
        assert output.shape[1] == 7
        
        # Check that all values are finite
        assert_physically_reasonable_output(output, Tmax=120)
    
        T_bot = output[:, 2]  # Vial bottom (product) temperature
        T_crit = product['T_pr_crit']
        
        # Product temperature should not exceed critical temperature
        # Allow small tolerance for numerical precision
        assert np.all(T_bot <= T_crit + 0.01), \
            f"Product temperature exceeded critical: max={T_bot.max():.2f}°C, crit={T_crit}°C"
    
        T_shelf = output[:, 3]
        
        # Shelf temperature should be within min/max bounds
        assert np.all(T_shelf >= Tshelf['min'] - 0.01), \
            f"Shelf temperature below minimum: min_T={T_shelf.min():.2f}°C"
        assert np.all(T_shelf <= Tshelf['max'] + 0.01), \
            f"Shelf temperature above maximum: max_T={T_shelf.max():.2f}°C"
    
        P_chamber_mTorr = output[:, 4]
        P_setpoint_mTorr = Pchamber['setpt'][0] * 1000  # Convert Torr to mTorr
        
        # Chamber pressure should remain at setpoint (allowing small tolerance)
        assert np.all(np.abs(P_chamber_mTorr - P_setpoint_mTorr) < 1.0), \
            f"Chamber pressure deviated from setpoint: range={P_chamber_mTorr.min():.1f}-{P_chamber_mTorr.max():.1f} mTorr"
    def test_optimizer_matches_reference_trajectory(self, optimizer_params, reference_results):
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = optimizer_params
        
        output = opt_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        
        # Compare at specific time points
        ref_times = reference_results['Time [hr]'].values
        ref_dried = reference_results['Percent Dried'].values
        
        # Sample a few time points for comparison
        test_times = [0.5, 1.0, 1.5, 2.0]
        
        for test_time in test_times:
            if test_time > output[-1, 0]:
                continue  # Skip if beyond simulation time
                
            # Find closest time in results
            idx_result = np.argmin(np.abs(output[:, 0] - test_time))
            dried_result = output[idx_result, 6]
            
            # Find closest time in reference
            idx_ref = np.argmin(np.abs(ref_times - test_time))
            dried_ref = ref_dried[idx_ref]
            
            # Allow 5% tolerance on percent dried
            assert abs(dried_result - dried_ref) < 5.0, \
                f"Percent dried mismatch at t={test_time}hr: got {dried_result:.1f}%, expected {dried_ref:.1f}%"
    
        time_hr = output[:, 0]
        ref_time = reference_results['Time [hr]'].values
        
        # Final time should match reference (within tolerance)
        final_time = time_hr[-1]
        ref_final_time = ref_time[-1]
        
        # Allow 1% tolerance on final time
        time_tolerance = 0.01 * ref_final_time
        assert abs(final_time - ref_final_time) < time_tolerance, \
            f"Final time mismatch: got {final_time:.4f} hr, expected {ref_final_time:.4f} hr"
        
        ref_T_bot = reference_results['Vial Bottom Temperature [C]'].values
        T_bot = output[:, 2]
        
        # Maximum product temperature should match reference (within tolerance)
        max_T_bot = T_bot.max()
        ref_max_T_bot = ref_T_bot.max()
        
        # Allow 0.5°C tolerance on maximum temperature
        assert abs(max_T_bot - ref_max_T_bot) < 0.5, \
            f"Max product temp mismatch: got {max_T_bot:.2f}°C, expected {ref_max_T_bot:.2f}°C"
    
    
    @pytest.mark.skip(reason="Example script not yet implemented")
    def test_optimizer_example_script_runs(self):
        """Test that the optimizer example script runs successfully."""
        # Import and run the example
        import sys
        sys.path.insert(0, 'examples')
        
        from example_optimizer import run_optimizer_example
        
        results = run_optimizer_example()
        
        # Verify results
        assert results is not None
        assert results.size > 0
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
