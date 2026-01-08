"""Additional tests to reach 100% coverage for functions.py and design_space.py."""
import pytest
import numpy as np
from lyopronto import functions, design_space


class TestFunctionsCoverageGaps:
    """Tests to cover missing lines in functions.py (95% -> 100%)."""
    
    def test_ineq_constraints_all_branches(self):
        """Test Ineq_Constraints function with various inputs.
        
        Missing coverage: lines 167-172 in functions.py
        """
        # Test case 1: Normal case
        Pch = 0.080
        dmdt = 0.05
        Tpr_crit = -30.0
        Tbot = -32.0
        eq_cap_a = 5.0
        eq_cap_b = 10.0
        nVial = 398
        
        result = functions.Ineq_Constraints(
            Pch, dmdt, Tpr_crit, Tbot, eq_cap_a, eq_cap_b, nVial
        )
        
        # Should return two inequality constraints
        assert len(result) == 2
        assert isinstance(result[0], (int, float))
        assert isinstance(result[1], (int, float))
        
        # Test case 2: Equipment capability constraint active
        dmdt_high = 0.5  # High sublimation rate
        result2 = functions.Ineq_Constraints(
            Pch, dmdt_high, Tpr_crit, Tbot, eq_cap_a, eq_cap_b, nVial
        )
        assert len(result2) == 2
        
        # Test case 3: Temperature constraint active
        Tbot_high = -25.0  # Higher than critical
        result3 = functions.Ineq_Constraints(
            Pch, dmdt, Tpr_crit, Tbot_high, eq_cap_a, eq_cap_b, nVial
        )
        assert len(result3) == 2
        
        # Test case 4: Both constraints active
        result4 = functions.Ineq_Constraints(
            Pch, dmdt_high, Tpr_crit, Tbot_high, eq_cap_a, eq_cap_b, nVial
        )
        assert len(result4) == 2
    
    def test_ineq_constraints_boundary_cases(self):
        """Test Ineq_Constraints at boundary conditions."""
        # At critical temperature
        result = functions.Ineq_Constraints(
            0.080, 0.05, -30.0, -30.0, 5.0, 10.0, 398
        )
        assert result[1] >= -1e-6  # Should be at or near boundary
        
        # At equipment capability limit
        Pch = 0.080
        eq_cap_max = (5.0 + 10.0 * Pch) / 398
        result2 = functions.Ineq_Constraints(
            Pch, eq_cap_max, -30.0, -32.0, 5.0, 10.0, 398
        )
        assert abs(result2[0]) < 1e-6  # Should be at boundary
    
    def test_ineq_constraints_negative_values(self):
        """Test Ineq_Constraints with negative sublimation rate."""
        # Should handle edge cases gracefully
        result = functions.Ineq_Constraints(
            0.080, -0.01, -30.0, -35.0, 5.0, 10.0, 398
        )
        assert len(result) == 2
        assert isinstance(result[0], (int, float))
        assert isinstance(result[1], (int, float))


class TestDesignSpaceCoverageGaps:
    """Tests to cover missing lines in design_space.py (90% -> 100%)."""
    
    @pytest.fixture
    def design_space_setup(self, standard_vial, standard_product, standard_ht):
        """Setup for design space calculations."""
        # Multiple pressure and temperature setpoints for full design space
        Pchamber = {'setpt': [0.060, 0.080, 0.100]}
        Tshelf = {
            'init': -40.0,
            'setpt': [-30.0, -20.0, -10.0],
            'ramp_rate': 1.0  # Fast ramp to test different branches
        }
        dt = 0.02  # Larger timestep for faster completion
        eq_cap = {'a': 5.0, 'b': 10.0}
        nVial = 398
        
        return {
            'vial': standard_vial,
            'product': standard_product,
            'ht': standard_ht,
            'Pchamber': Pchamber,
            'Tshelf': Tshelf,
            'dt': dt,
            'eq_cap': eq_cap,
            'nVial': nVial
        }
    
    def test_design_space_negative_sublimation(self, design_space_setup):
        """Test design space with conditions that could lead to negative sublimation.
        
        Missing coverage: lines 74-75 (dmdt < 0 check and print)
        """
        # Set very low shelf temperature to potentially trigger dmdt < 0
        design_space_setup['Tshelf']['init'] = -60.0
        design_space_setup['Tshelf']['setpt'] = [-55.0]
        
        output = design_space.dry(
            design_space_setup['vial'],
            design_space_setup['product'],
            design_space_setup['ht'],
            design_space_setup['Pchamber'],
            design_space_setup['Tshelf'],
            design_space_setup['dt'],
            design_space_setup['eq_cap'],
            design_space_setup['nVial']
        )
        
        # Should complete without crashing
        assert len(output) == 3
        assert output[0].shape[0] == 5  # [T_max, drying_time, sub_flux_avg, sub_flux_max, sub_flux_end]
    
    # @pytest.mark.skip(reason="Ramp-down scenarios cause temperatures too low for sublimation, leading to numerical overflow. The ramp-down code path (lines 103-105) is tested implicitly but cannot complete physically.")
    def test_design_space_shelf_temp_ramp_down(self, design_space_setup):
        """Test design space with shelf temperature ramping down.
        
        Missing coverage: lines 103-105 (Tshelf['init'] > Tsh_setpt branch)
        
        SKIPPED: Ramping temperature DOWN creates temperatures too low for
        sublimation, causing OverflowError in Vapor_pressure calculation.
        This is physically correct behavior - lyophilization requires warming,
        not cooling. The ramp-down code path exists for completeness but
        cannot be fully tested with realistic physics.
        """
        # Start warm, ramp down
        design_space_setup['Tshelf']['init'] = 0.0
        design_space_setup['Tshelf']['setpt'] = [-10.0]
        design_space_setup['Tshelf']['ramp_rate'] = 1.0
        
        output = design_space.dry(
            design_space_setup['vial'],
            design_space_setup['product'],
            design_space_setup['ht'],
            design_space_setup['Pchamber'],
            design_space_setup['Tshelf'],
            design_space_setup['dt'],
            design_space_setup['eq_cap'],
            design_space_setup['nVial']
        )
        
        assert len(output) == 3
    
    def test_design_space_fast_completion(self, design_space_setup):
        """Test design space with conditions leading to very fast drying.
        
        Missing coverage: lines 85, 115-117 (single timestep edge case in product temp section)
        """
        # Use high temperature and large timestep for fast drying
        design_space_setup['Tshelf']['init'] = -15.0
        design_space_setup['Tshelf']['setpt'] = [-10.0]
        design_space_setup['dt'] = 0.5  # Very large timestep
        design_space_setup['product']['cSolid'] = 0.01  # Very dilute for faster drying
        
        output = design_space.dry(
            design_space_setup['vial'],
            design_space_setup['product'],
            design_space_setup['ht'],
            design_space_setup['Pchamber'],
            design_space_setup['Tshelf'],
            design_space_setup['dt'],
            design_space_setup['eq_cap'],
            design_space_setup['nVial']
        )
        
        # Should handle edge case where drying completes in one timestep
        assert len(output) == 3
        assert output[1].shape[0] == 5  # Product temp isotherms
    
    def test_design_space_equipment_capability_section(self, design_space_setup):
        """Test design space equipment capability calculations.
        
        Missing coverage: line 189 (loop over Pchamber setpoints for eq_cap)
        """
        # Use full range of pressures
        design_space_setup['Pchamber']['setpt'] = [0.050, 0.075, 0.100, 0.125, 0.150]
        
        output = design_space.dry(
            design_space_setup['vial'],
            design_space_setup['product'],
            design_space_setup['ht'],
            design_space_setup['Pchamber'],
            design_space_setup['Tshelf'],
            design_space_setup['dt'],
            design_space_setup['eq_cap'],
            design_space_setup['nVial']
        )
        
        # Equipment capability data is in output[2]
        eq_cap_data = output[2]
        assert eq_cap_data.shape[0] == 3  # [T_max_eq_cap, drying_time_eq_cap, sub_flux_eq_cap]
        assert eq_cap_data[0].shape[0] == 5  # Should match number of pressure setpoints
    
    def test_design_space_product_temp_isotherms(self, design_space_setup):
        """Test product temperature isotherm section thoroughly.
        
        Missing coverage: lines 106-107 in product temp section
        """
        # Use minimal setup to focus on product temp isotherms
        design_space_setup['Pchamber']['setpt'] = [0.060, 0.100]  # Just two pressures
        design_space_setup['Tshelf']['setpt'] = [-25.0]
        
        output = design_space.dry(
            design_space_setup['vial'],
            design_space_setup['product'],
            design_space_setup['ht'],
            design_space_setup['Pchamber'],
            design_space_setup['Tshelf'],
            design_space_setup['dt'],
            design_space_setup['eq_cap'],
            design_space_setup['nVial']
        )
        
        # Check product temperature isotherms output
        product_temp_data = output[1]
        assert product_temp_data.shape[0] == 5
        assert product_temp_data[1].shape[0] == 2  # drying_time_pr for 2 pressures
    
    def test_design_space_single_timestep_both_sections(self, design_space_setup):
        """Test both shelf temp and product temp sections with single timestep completion.
        
        This should cover lines 113-117 (shelf temp section) and 181-187 (product temp section)
        """
        # Extreme conditions for very fast drying
        design_space_setup['vial']['Vfill'] = 0.5  # Very small fill volume
        design_space_setup['product']['cSolid'] = 0.005  # Very dilute
        design_space_setup['Tshelf']['init'] = -10.0
        design_space_setup['Tshelf']['setpt'] = [-5.0]
        design_space_setup['Pchamber']['setpt'] = [0.150]  # High pressure
        design_space_setup['dt'] = 1.0  # Large timestep
        
        output = design_space.dry(
            design_space_setup['vial'],
            design_space_setup['product'],
            design_space_setup['ht'],
            design_space_setup['Pchamber'],
            design_space_setup['Tshelf'],
            design_space_setup['dt'],
            design_space_setup['eq_cap'],
            design_space_setup['nVial']
        )
        
        # Should handle single-timestep completion in both sections
        assert len(output) == 3
        # All output arrays should be properly formed even with edge case
        assert np.all(np.isfinite(output[0]))
        assert np.all(np.isfinite(output[1]))
        assert np.all(np.isfinite(output[2]))
