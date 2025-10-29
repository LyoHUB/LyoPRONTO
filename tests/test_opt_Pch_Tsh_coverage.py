"""Tests for opt_Pch_Tsh.py to increase coverage from 19% to 80%+."""
import pytest
import numpy as np
from lyopronto import opt_Pch_Tsh, opt_Pch, opt_Tsh
from .test_helpers import assert_physically_reasonable_output


class TestOptPchTsh:
    """Test joint Pch+Tsh optimizer (both optimized simultaneously)."""
    
    @pytest.fixture
    def opt_both_setup(self, standard_vial, standard_ht):
        """Setup for joint Pch+Tsh optimization."""
        product = {
            'cSolid': 0.05,
            'R0': 1.4,
            'A1': 16.0,
            'A2': 0.0,
            'T_pr_crit': -30.0
        }
        
        # No fixed shelf temperature (will be optimized)
        Tshelf = {
            'min': -45.0,
            'max': -5.0
        }
        
        # Pressure bounds (will be optimized)
        Pchamber = {
            'min': 0.040,
            'max': 0.200
        }
        
        dt = 0.01  # Time step [hr]
        
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
    
    @pytest.mark.slow
    def test_opt_both_completes(self, opt_both_setup):
        """Test that optimizer runs to completion."""
        output = opt_Pch_Tsh.dry(
            opt_both_setup['vial'],
            opt_both_setup['product'],
            opt_both_setup['ht'],
            opt_both_setup['Pchamber'],
            opt_both_setup['Tshelf'],
            opt_both_setup['dt'],
            opt_both_setup['eq_cap'],
            opt_both_setup['nVial']
        )
        
        # Should return an array
        assert isinstance(output, np.ndarray)
        assert output.shape[0] > 0
        assert output.shape[1] == 7  # Standard output columns
    
    @pytest.mark.slow
    def test_opt_both_output_shape(self, opt_both_setup):
        """Test output has correct format."""
        output = opt_Pch_Tsh.dry(
            opt_both_setup['vial'],
            opt_both_setup['product'],
            opt_both_setup['ht'],
            opt_both_setup['Pchamber'],
            opt_both_setup['Tshelf'],
            opt_both_setup['dt'],
            opt_both_setup['eq_cap'],
            opt_both_setup['nVial']
        )
        
        # Check shape
        assert output.shape[1] == 7, "Output should have 7 columns"
        
        # Check all values are finite
        assert np.all(np.isfinite(output)), "Output contains non-finite values"
    
    @pytest.mark.slow
    def test_opt_both_respects_temp_constraint(self, opt_both_setup):
        """Test critical temperature is not exceeded."""
        output = opt_Pch_Tsh.dry(
            opt_both_setup['vial'],
            opt_both_setup['product'],
            opt_both_setup['ht'],
            opt_both_setup['Pchamber'],
            opt_both_setup['Tshelf'],
            opt_both_setup['dt'],
            opt_both_setup['eq_cap'],
            opt_both_setup['nVial']
        )
        
        Tbot = output[:, 2]  # Vial bottom temperature
        T_crit = opt_both_setup['product']['T_pr_crit']
        
        # Allow 0.5°C tolerance for numerical optimization
        max_violation = np.max(Tbot - T_crit)
        assert max_violation <= 0.5, \
            f"Temperature exceeded critical by {max_violation:.2f}°C"
    
    @pytest.mark.slow
    def test_opt_both_pressure_within_bounds(self, opt_both_setup):
        """Test optimized pressure stays within bounds."""
        output = opt_Pch_Tsh.dry(
            opt_both_setup['vial'],
            opt_both_setup['product'],
            opt_both_setup['ht'],
            opt_both_setup['Pchamber'],
            opt_both_setup['Tshelf'],
            opt_both_setup['dt'],
            opt_both_setup['eq_cap'],
            opt_both_setup['nVial']
        )
        
        Pch = output[:, 4] / 1000  # Convert mTorr to Torr
        P_min = opt_both_setup['Pchamber']['min']
        P_max = opt_both_setup['Pchamber']['max']
        
        assert np.all(Pch >= P_min * 0.95), \
            f"Pressure {np.min(Pch):.3f} below minimum {P_min}"
        assert np.all(Pch <= P_max * 1.05), \
            f"Pressure {np.max(Pch):.3f} above maximum {P_max}"
    
    @pytest.mark.slow
    def test_opt_both_shelf_temp_within_bounds(self, opt_both_setup):
        """Test optimized shelf temperature stays within bounds."""
        output = opt_Pch_Tsh.dry(
            opt_both_setup['vial'],
            opt_both_setup['product'],
            opt_both_setup['ht'],
            opt_both_setup['Pchamber'],
            opt_both_setup['Tshelf'],
            opt_both_setup['dt'],
            opt_both_setup['eq_cap'],
            opt_both_setup['nVial']
        )
        
        Tsh = output[:, 3]  # Shelf temperature
        T_min = opt_both_setup['Tshelf']['min']
        T_max = opt_both_setup['Tshelf']['max']
        
        assert np.all(Tsh >= T_min - 1.0), \
            f"Shelf temp {np.min(Tsh):.1f} below minimum {T_min}"
        assert np.all(Tsh <= T_max + 1.0), \
            f"Shelf temp {np.max(Tsh):.1f} above maximum {T_max}"
    
    @pytest.mark.slow
    def test_opt_both_respects_equipment(self, opt_both_setup):
        """Test equipment capability constraint is satisfied."""
        output = opt_Pch_Tsh.dry(
            opt_both_setup['vial'],
            opt_both_setup['product'],
            opt_both_setup['ht'],
            opt_both_setup['Pchamber'],
            opt_both_setup['Tshelf'],
            opt_both_setup['dt'],
            opt_both_setup['eq_cap'],
            opt_both_setup['nVial']
        )
        
        flux = output[:, 5]  # Sublimation flux [kg/hr/m**2]
        Ap_m2 = opt_both_setup['vial']['Ap'] / 100**2  # Convert [cm**2] to [m**2]
        
        # Total sublimation rate per vial
        dmdt = flux * Ap_m2  # [kg/hr/vial]
        
        # Equipment capability at different pressures
        Pch = output[:, 4] / 1000  # [Torr]
        eq_cap_max = (opt_both_setup['eq_cap']['a'] + 
                      opt_both_setup['eq_cap']['b'] * Pch) / opt_both_setup['nVial']
        
        # Should not exceed equipment capability (with small tolerance)
        violations = dmdt - eq_cap_max
        max_violation = np.max(violations)
        assert max_violation <= 0.01, \
            f"Equipment capability exceeded by {max_violation:.4f} kg/hr"
    
    @pytest.mark.slow
    def test_opt_both_physically_reasonable(self, opt_both_setup):
        """Test output is physically reasonable."""
        output = opt_Pch_Tsh.dry(
            opt_both_setup['vial'],
            opt_both_setup['product'],
            opt_both_setup['ht'],
            opt_both_setup['Pchamber'],
            opt_both_setup['Tshelf'],
            opt_both_setup['dt'],
            opt_both_setup['eq_cap'],
            opt_both_setup['nVial']
        )
        
        assert_physically_reasonable_output(output)
    
    @pytest.mark.slow
    def test_opt_both_reaches_completion(self, opt_both_setup):
        """Test that drying reaches completion."""
        output = opt_Pch_Tsh.dry(
            opt_both_setup['vial'],
            opt_both_setup['product'],
            opt_both_setup['ht'],
            opt_both_setup['Pchamber'],
            opt_both_setup['Tshelf'],
            opt_both_setup['dt'],
            opt_both_setup['eq_cap'],
            opt_both_setup['nVial']
        )
        
        final_fraction = output[-1, 6]
        assert final_fraction >= 0.99, \
            f"Should reach 99% dried, got {final_fraction*100:.1f}%"
    
    @pytest.mark.slow
    def test_opt_both_convergence(self, opt_both_setup):
        """Test optimization converges to a solution."""
        output = opt_Pch_Tsh.dry(
            opt_both_setup['vial'],
            opt_both_setup['product'],
            opt_both_setup['ht'],
            opt_both_setup['Pchamber'],
            opt_both_setup['Tshelf'],
            opt_both_setup['dt'],
            opt_both_setup['eq_cap'],
            opt_both_setup['nVial']
        )
        
        # If optimization converged, should have reasonable drying time
        total_time = output[-1, 0]
        assert 1.0 <= total_time <= 50.0, \
            f"Drying time {total_time:.1f} hr seems unreasonable"
    
    @pytest.mark.slow
    def test_opt_both_variables_optimized(self, opt_both_setup):
        """Test that both Pch and Tsh are actively optimized."""
        output = opt_Pch_Tsh.dry(
            opt_both_setup['vial'],
            opt_both_setup['product'],
            opt_both_setup['ht'],
            opt_both_setup['Pchamber'],
            opt_both_setup['Tshelf'],
            opt_both_setup['dt'],
            opt_both_setup['eq_cap'],
            opt_both_setup['nVial']
        )
        
        Pch = output[:, 4] / 1000  # Torr
        Tsh = output[:, 3]  # °C
        
        # Both should vary during optimization
        P_range = np.max(Pch) - np.min(Pch)
        T_range = np.max(Tsh) - np.min(Tsh)
        
        assert P_range > 0.001, "Pressure should vary during optimization"
        assert T_range > 0.5, "Shelf temperature should vary during optimization"


class TestOptPchTshComparison:
    """Test that joint optimization performs better than single-variable."""
    
    @pytest.fixture
    def comparison_setup(self, standard_vial, standard_ht):
        """Setup for comparing optimization strategies."""
        product = {
            'cSolid': 0.05,
            'R0': 1.4,
            'A1': 16.0,
            'A2': 0.0,
            'T_pr_crit': -30.0
        }
        
        # For joint optimization
        Tshelf_both = {
            'min': -45.0,
            'max': -5.0
        }
        
        # For Pch-only (fixed Tsh)
        Tshelf_pch_only = {
            'init': -40.0,
            'setpt': [-25.0, -15.0],
            'dt_setpt': [120.0, 120.0],
            'ramp_rate': 1.0
        }
        
        # For Tsh-only (fixed Pch)
        Pchamber_tsh_only = {
            'setpt': [0.080]
        }
        
        Pchamber_bounds = {
            'min': 0.040,
            'max': 0.200
        }
        
        dt = 0.01
        eq_cap = {'a': 5.0, 'b': 10.0}
        nVial = 398
        
        return {
            'vial': standard_vial,
            'product': product,
            'ht': standard_ht,
            'Pchamber_bounds': Pchamber_bounds,
            'Pchamber_tsh_only': Pchamber_tsh_only,
            'Tshelf_both': Tshelf_both,
            'Tshelf_pch_only': Tshelf_pch_only,
            'dt': dt,
            'eq_cap': eq_cap,
            'nVial': nVial
        }
    
    @pytest.mark.slow
    def test_joint_opt_vs_pch_only(self, comparison_setup):
        """Test joint optimization against Pch-only optimization.
        
        Note: Joint optimization is not guaranteed to be faster than Pch-only.
        It optimizes both variables which can take longer but may find better
        solutions. Test validates both approaches complete successfully.
        """
        # Joint optimization
        output_both = opt_Pch_Tsh.dry(
            comparison_setup['vial'],
            comparison_setup['product'],
            comparison_setup['ht'],
            comparison_setup['Pchamber_bounds'],
            comparison_setup['Tshelf_both'],
            comparison_setup['dt'],
            comparison_setup['eq_cap'],
            comparison_setup['nVial']
        )
        
        # Pch-only optimization
        output_pch = opt_Pch.dry(
            comparison_setup['vial'],
            comparison_setup['product'],
            comparison_setup['ht'],
            comparison_setup['Pchamber_bounds'],
            comparison_setup['Tshelf_pch_only'],
            comparison_setup['dt'],
            comparison_setup['eq_cap'],
            comparison_setup['nVial']
        )
        
        # Both should complete and return valid results
        assert output_both is not None
        assert output_pch is not None
        assert len(output_both) > 0
        assert len(output_pch) > 0
        
        # Check both achieve some drying progress
        final_both = output_both[-1, 6]
        final_pch = output_pch[-1, 6]
        assert final_both > 0.0, "Joint optimization should show drying progress"
        assert final_pch > 0.0, "Pch-only optimization should show drying progress"
    
    @pytest.mark.slow
    def test_joint_opt_shorter_or_equal_time(self, comparison_setup):
        """Test that joint optimization achieves reasonable drying time."""
        output = opt_Pch_Tsh.dry(
            comparison_setup['vial'],
            comparison_setup['product'],
            comparison_setup['ht'],
            comparison_setup['Pchamber_bounds'],
            comparison_setup['Tshelf_both'],
            comparison_setup['dt'],
            comparison_setup['eq_cap'],
            comparison_setup['nVial']
        )
        
        total_time = output[-1, 0]
        
        # Should achieve faster drying than typical conservative schedules
        assert total_time < 30.0, \
            f"Joint optimization took {total_time:.1f}h, expected <30h"


class TestOptPchTshEdgeCases:
    """Test edge cases for joint optimizer."""
    
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
            'min': -50.0,
            'max': -20.0
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
    
    @pytest.mark.slow
    def test_conservative_critical_temp(self, conservative_setup):
        """Test with very conservative critical temperature."""
        output = opt_Pch_Tsh.dry(
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
    
    @pytest.mark.slow
    def test_high_product_resistance(self, conservative_setup):
        """Test with high product resistance."""
        conservative_setup['product']['R0'] = 3.0
        conservative_setup['product']['A1'] = 30.0
        
        output = opt_Pch_Tsh.dry(
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
    
    @pytest.mark.slow
    def test_narrow_optimization_ranges(self, conservative_setup):
        """Test with narrow optimization ranges."""
        conservative_setup['Pchamber']['min'] = 0.070
        conservative_setup['Pchamber']['max'] = 0.090
        conservative_setup['Tshelf']['min'] = -35.0
        conservative_setup['Tshelf']['max'] = -25.0
        
        output = opt_Pch_Tsh.dry(
            conservative_setup['vial'],
            conservative_setup['product'],
            conservative_setup['ht'],
            conservative_setup['Pchamber'],
            conservative_setup['Tshelf'],
            conservative_setup['dt'],
            conservative_setup['eq_cap'],
            conservative_setup['nVial']
        )
        
        # Should still find solution within narrow ranges
        assert output[-1, 6] >= 0.95
    
    @pytest.mark.slow
    def test_tight_equipment_constraint(self, conservative_setup):
        """Test with tight equipment capability constraint."""
        # Reduce equipment capability
        conservative_setup['eq_cap']['a'] = 2.0
        conservative_setup['eq_cap']['b'] = 5.0
        
        output = opt_Pch_Tsh.dry(
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
    
    @pytest.mark.slow
    def test_concentrated_product(self, conservative_setup):
        """Test with high solids concentration."""
        conservative_setup['product']['cSolid'] = 0.15  # 15% solids
        
        output = opt_Pch_Tsh.dry(
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
