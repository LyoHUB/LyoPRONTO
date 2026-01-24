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