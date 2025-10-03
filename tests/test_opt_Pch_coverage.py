"""Tests for opt_Pch.py to increase coverage from 14% to 80%+."""
import pytest
import numpy as np
from lyopronto import opt_Pch
from tests.conftest import assert_physically_reasonable_output


class TestOptPchOnly:
    """Test pressure-only optimizer (fixed shelf temperature)."""
    
    @pytest.fixture
    def opt_pch_setup(self, standard_vial, standard_ht):
        """Setup for Pch-only optimization."""
        product = {
            'cSolid': 0.05,
            'R0': 1.4,
            'A1': 16.0,
            'A2': 0.0,
            'T_pr_crit': -30.0
        }
        
        # Fixed shelf temperature schedule
        Tshelf = {
            'init': -40.0,
            'setpt': [-20.0, -10.0],
            'dt_setpt': [120.0, 120.0],  # 2 hours each in minutes
            'ramp_rate': 1.0  # Ramp rate in degC/min
        }
        
        # Pressure bounds (will be optimized)
        Pchamber = {
            'min': 0.040,
            'max': 0.200
        }
        
        dt = 0.01  # Time step in hours
        
        # Equipment capability
        eq_cap = {'a': 5.0, 'b': 10.0}
        nVial = 398
        
        return {
            'vial': standard_vial,
            'product': product,
            'ht': standard_ht,
            'Pchamber': Pchamber,
            'Tshelf': Tshelf,
            'dt': dt,
            'eq_cap': eq_cap,
            'nVial': nVial
        }
    
    def test_opt_pch_completes(self, opt_pch_setup):
        """Test that optimizer runs to completion."""
        output = opt_Pch.dry(
            opt_pch_setup['vial'],
            opt_pch_setup['product'],
            opt_pch_setup['ht'],
            opt_pch_setup['Pchamber'],
            opt_pch_setup['Tshelf'],
            opt_pch_setup['dt'],
            opt_pch_setup['eq_cap'],
            opt_pch_setup['nVial']
        )
        
        # Should return an array
        assert isinstance(output, np.ndarray)
        assert output.shape[0] > 0
        assert output.shape[1] == 7  # Standard output columns
    
    def test_opt_pch_output_shape(self, opt_pch_setup):
        """Test output has correct format."""
        output = opt_Pch.dry(
            opt_pch_setup['vial'],
            opt_pch_setup['product'],
            opt_pch_setup['ht'],
            opt_pch_setup['Pchamber'],
            opt_pch_setup['Tshelf'],
            opt_pch_setup['dt'],
            opt_pch_setup['eq_cap'],
            opt_pch_setup['nVial']
        )
        
        # Check shape
        assert output.shape[1] == 7, "Output should have 7 columns"
        
        # Check all values are finite
        assert np.all(np.isfinite(output)), "Output contains non-finite values"
    
    def test_opt_pch_respects_temp_constraint(self, opt_pch_setup):
        """Test critical temperature is not exceeded."""
        output = opt_Pch.dry(
            opt_pch_setup['vial'],
            opt_pch_setup['product'],
            opt_pch_setup['ht'],
            opt_pch_setup['Pchamber'],
            opt_pch_setup['Tshelf'],
            opt_pch_setup['dt'],
            opt_pch_setup['eq_cap'],
            opt_pch_setup['nVial']
        )
        
        Tbot = output[:, 2]  # Vial bottom temperature
        T_crit = opt_pch_setup['product']['T_pr_crit']
        
        # Allow 0.5°C tolerance for numerical optimization
        max_violation = np.max(Tbot - T_crit)
        assert max_violation <= 0.5, \
            f"Temperature exceeded critical by {max_violation:.2f}°C"
    
    def test_opt_pch_pressure_within_bounds(self, opt_pch_setup):
        """Test optimized pressure stays within bounds."""
        output = opt_Pch.dry(
            opt_pch_setup['vial'],
            opt_pch_setup['product'],
            opt_pch_setup['ht'],
            opt_pch_setup['Pchamber'],
            opt_pch_setup['Tshelf'],
            opt_pch_setup['dt'],
            opt_pch_setup['eq_cap'],
            opt_pch_setup['nVial']
        )
        
        Pch = output[:, 4] / 1000  # Convert mTorr to Torr
        P_min = opt_pch_setup['Pchamber']['min']
        P_max = opt_pch_setup['Pchamber']['max']
        
        assert np.all(Pch >= P_min * 0.95), \
            f"Pressure {np.min(Pch):.3f} below minimum {P_min}"
        assert np.all(Pch <= P_max * 1.05), \
            f"Pressure {np.max(Pch):.3f} above maximum {P_max}"
    
    def test_opt_pch_respects_equipment(self, opt_pch_setup):
        """Test equipment capability constraint is satisfied."""
        output = opt_Pch.dry(
            opt_pch_setup['vial'],
            opt_pch_setup['product'],
            opt_pch_setup['ht'],
            opt_pch_setup['Pchamber'],
            opt_pch_setup['Tshelf'],
            opt_pch_setup['dt'],
            opt_pch_setup['eq_cap'],
            opt_pch_setup['nVial']
        )
        
        flux = output[:, 5]  # Sublimation flux in kg/hr/m²
        Ap_m2 = opt_pch_setup['vial']['Ap'] / 100**2  # Convert cm² to m²
        
        # Total sublimation rate per vial
        dmdt = flux * Ap_m2  # kg/hr per vial
        
        # Equipment capability at different pressures
        Pch = output[:, 4] / 1000  # Torr
        eq_cap_max = (opt_pch_setup['eq_cap']['a'] + 
                      opt_pch_setup['eq_cap']['b'] * Pch) / opt_pch_setup['nVial']
        
        # Should not exceed equipment capability (with small tolerance)
        violations = dmdt - eq_cap_max
        max_violation = np.max(violations)
        assert max_violation <= 0.01, \
            f"Equipment capability exceeded by {max_violation:.4f} kg/hr"
    
    def test_opt_pch_physically_reasonable(self, opt_pch_setup):
        """Test output is physically reasonable."""
        output = opt_Pch.dry(
            opt_pch_setup['vial'],
            opt_pch_setup['product'],
            opt_pch_setup['ht'],
            opt_pch_setup['Pchamber'],
            opt_pch_setup['Tshelf'],
            opt_pch_setup['dt'],
            opt_pch_setup['eq_cap'],
            opt_pch_setup['nVial']
        )
        
        assert_physically_reasonable_output(output)
    
    def test_opt_pch_reaches_completion(self, opt_pch_setup):
        """Test that drying reaches completion."""
        output = opt_Pch.dry(
            opt_pch_setup['vial'],
            opt_pch_setup['product'],
            opt_pch_setup['ht'],
            opt_pch_setup['Pchamber'],
            opt_pch_setup['Tshelf'],
            opt_pch_setup['dt'],
            opt_pch_setup['eq_cap'],
            opt_pch_setup['nVial']
        )
        
        final_fraction = output[-1, 6]
        assert final_fraction >= 0.99, \
            f"Should reach 99% dried, got {final_fraction*100:.1f}%"
    
    def test_opt_pch_convergence(self, opt_pch_setup):
        """Test optimization converges to a solution."""
        output = opt_Pch.dry(
            opt_pch_setup['vial'],
            opt_pch_setup['product'],
            opt_pch_setup['ht'],
            opt_pch_setup['Pchamber'],
            opt_pch_setup['Tshelf'],
            opt_pch_setup['dt'],
            opt_pch_setup['eq_cap'],
            opt_pch_setup['nVial']
        )
        
        # If optimization converged, should have reasonable drying time
        total_time = output[-1, 0]
        assert 1.0 <= total_time <= 50.0, \
            f"Drying time {total_time:.1f} hr seems unreasonable"
    
    def test_opt_pch_pressure_optimization(self, opt_pch_setup):
        """Test that pressure is actively optimized (not just at bounds)."""
        output = opt_Pch.dry(
            opt_pch_setup['vial'],
            opt_pch_setup['product'],
            opt_pch_setup['ht'],
            opt_pch_setup['Pchamber'],
            opt_pch_setup['Tshelf'],
            opt_pch_setup['dt'],
            opt_pch_setup['eq_cap'],
            opt_pch_setup['nVial']
        )
        
        Pch = output[:, 4] / 1000  # Torr
        
        # Pressure should vary during optimization
        P_range = np.max(Pch) - np.min(Pch)
        assert P_range > 0.001, \
            "Pressure should vary during optimization"


class TestOptPchEdgeCases:
    """Test edge cases for Pch-only optimizer."""
    
    @pytest.fixture
    def conservative_setup(self, standard_vial, standard_ht):
        """Setup with very conservative critical temperature."""
        product = {
            'cSolid': 0.05,
            'R0': 1.4,
            'A1': 16.0,
            'A2': 0.0,
            'T_pr_crit': -40.0  # Very conservative
        }
        
        Tshelf = {
            'init': -45.0,
            'setpt': [-35.0],
            'dt_setpt': [120.0],
            'ramp_rate': 1.0
        }
        
        Pchamber = {
            'min': 0.040,
            'max': 0.100
        }
        
        dt = 0.01
        eq_cap = {'a': 5.0, 'b': 10.0}
        nVial = 398
        
        return {
            'vial': standard_vial,
            'product': product,
            'ht': standard_ht,
            'Pchamber': Pchamber,
            'Tshelf': Tshelf,
            'dt': dt,
            'eq_cap': eq_cap,
            'nVial': nVial
        }
    
    def test_conservative_critical_temp(self, conservative_setup):
        """Test with very conservative critical temperature."""
        output = opt_Pch.dry(
            conservative_setup['vial'],
            conservative_setup['product'],
            conservative_setup['ht'],
            conservative_setup['Pchamber'],
            conservative_setup['Tshelf'],
            conservative_setup['dt'],
            conservative_setup['eq_cap'],
            conservative_setup['nVial']
        )
        
        Tbot = output[:, 2]
        T_crit = conservative_setup['product']['T_pr_crit']
        
        # Should respect conservative constraint
        assert np.max(Tbot) <= T_crit + 0.5
    
    def test_high_product_resistance(self, conservative_setup):
        """Test with high product resistance."""
        conservative_setup['product']['R0'] = 3.0
        conservative_setup['product']['A1'] = 30.0
        
        output = opt_Pch.dry(
            conservative_setup['vial'],
            conservative_setup['product'],
            conservative_setup['ht'],
            conservative_setup['Pchamber'],
            conservative_setup['Tshelf'],
            conservative_setup['dt'],
            conservative_setup['eq_cap'],
            conservative_setup['nVial']
        )
        
        assert output.shape[0] > 0
        assert_physically_reasonable_output(output)
    
    def test_narrow_pressure_range(self, conservative_setup):
        """Test with narrow pressure optimization range."""
        conservative_setup['Pchamber']['min'] = 0.070
        conservative_setup['Pchamber']['max'] = 0.090
        
        output = opt_Pch.dry(
            conservative_setup['vial'],
            conservative_setup['product'],
            conservative_setup['ht'],
            conservative_setup['Pchamber'],
            conservative_setup['Tshelf'],
            conservative_setup['dt'],
            conservative_setup['eq_cap'],
            conservative_setup['nVial']
        )
        
        Pch = output[:, 4] / 1000
        assert np.all((Pch >= 0.065) & (Pch <= 0.095))
    
    def test_tight_equipment_constraint(self, conservative_setup):
        """Test with tight equipment capability constraint."""
        # Reduce equipment capability
        conservative_setup['eq_cap']['a'] = 2.0
        conservative_setup['eq_cap']['b'] = 5.0
        
        output = opt_Pch.dry(
            conservative_setup['vial'],
            conservative_setup['product'],
            conservative_setup['ht'],
            conservative_setup['Pchamber'],
            conservative_setup['Tshelf'],
            conservative_setup['dt'],
            conservative_setup['eq_cap'],
            conservative_setup['nVial']
        )
        
        # Should complete even with tight constraint
        assert output[-1, 6] >= 0.95
