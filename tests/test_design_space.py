"""
Tests for Design Space Generator

Tests the design space generation functionality for primary drying optimization.
"""

import pytest
import numpy as np
import lyopronto.design_space as design_space

@pytest.fixture
def physical_props():
    """Standard inputs for design space tests."""
    vial = {'Av': 3.8, 'Ap': 3.14, 'Vfill': 2.0}
    product = {
        'T_pr_crit': -5.0,
        'cSolid': 0.05,
        'R0': 1.4,
        'A1': 16.0,
        'A2': 0.0
    }
    ht = {'KC': 0.000275, 'KP': 0.000893, 'KD': 0.46}
    eq_cap = {'a': -0.182, 'b': 11.7}
    nVial = 398
    dt = 0.01
    return vial, product, ht, eq_cap, nVial, dt

@pytest.fixture
def design_space_1T1P(physical_props):
    """Design space inputs for 1 Tshelf and 1 Pchamber."""
    vial, product, ht, eq_cap, nVial, dt = physical_props
    Tshelf = {
        'init': -35.0,
        'setpt': np.array([0.0]),
        'ramp_rate': 1.0
    }
    Pchamber = {
        'setpt': np.array([0.15]),
        'ramp_rate': 0.5
    }
    return vial, product, ht, Pchamber, Tshelf, eq_cap, nVial, dt

class TestDesignSpaceBasic:
    """Basic functionality tests for design space generation."""
    
    def test_design_space_runs(self, design_space_inputs):
        """Test that design space generation completes without errors."""
        # Use conservative parameters that avoid edge cases
        vial = {'Av': 3.8, 'Ap': 3.14, 'Vfill': 2.0}
        product = {
            'T_pr_crit': -5.0,
            'cSolid': 0.05,
            'R0': 1.4,
            'A1': 16.0,
            'A2': 0.0
        }
        ht = {'KC': 0.000275, 'KP': 0.000893, 'KD': 0.46}
        
        # Use parameters that ensure reasonable drying time
        Tshelf = {
            'init': -35.0,
            'setpt': np.array([0.0]),  # More conservative than 20°C
            'ramp_rate': 1.0
        }
        Pchamber = {
            'setpt': np.array([0.15]),  # 150 mTorr
            'ramp_rate': 0.5
        }
        eq_cap = {'a': -0.182, 'b': 11.7}
        nVial = 398
        dt = 0.01
        
        # Should complete without errors
        shelf_results, product_results, eq_cap_results = design_space.dry(
            vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial
        )
        
        # Basic validation
        assert shelf_results is not None
        assert product_results is not None
        assert eq_cap_results is not None
    
    def test_design_space_output_structure(self):
        """Test that design space output has correct structure."""
        vial = {'Av': 3.8, 'Ap': 3.14, 'Vfill': 2.0}
        product = {
            'T_pr_crit': -5.0,
            'cSolid': 0.05,
            'R0': 1.4,
            'A1': 16.0,
            'A2': 0.0
        }
        ht = {'KC': 0.000275, 'KP': 0.000893, 'KD': 0.46}
        
        Tshelf = {
            'init': -35.0,
            'setpt': np.array([0.0]),
            'ramp_rate': 1.0
        }
        Pchamber = {
            'setpt': np.array([0.15]),
            'ramp_rate': 0.5
        }
        eq_cap = {'a': -0.182, 'b': 11.7}
        nVial = 398
        dt = 0.01
        
        shelf_results, product_results, eq_cap_results = design_space.dry(
            vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial
        )
        
        # Shelf results: [T_max, drying_time, avg_flux, max_flux, end_flux]
        assert len(shelf_results) == 5
        assert shelf_results[0].shape == (1, 1)  # T_max for 1 Tshelf x 1 Pch
        assert shelf_results[1].shape == (1, 1)  # drying_time
        assert shelf_results[2].shape == (1, 1)  # avg_flux
        assert shelf_results[3].shape == (1, 1)  # max_flux
        assert shelf_results[4].shape == (1, 1)  # end_flux
        
        # Product results: [T_product (2 values), drying_time, avg_flux, min_flux, end_flux]
        assert len(product_results) == 5
        assert product_results[0].shape == (2,)  # T_product for first and last Pch
        assert product_results[1].shape == (2,)  # drying_time
        
        # Equipment capability results: [T_max, drying_time, flux]
        assert len(eq_cap_results) == 3
        assert eq_cap_results[0].shape == (1,)  # T_max for 1 Pch
        assert eq_cap_results[1].shape == (1,)  # drying_time
        assert eq_cap_results[2].shape == (1,)  # flux
    
    def test_design_space_physical_constraints(self):
        """Test that design space results satisfy physical constraints."""
        vial = {'Av': 3.8, 'Ap': 3.14, 'Vfill': 2.0}
        product = {
            'T_pr_crit': -5.0,
            'cSolid': 0.05,
            'R0': 1.4,
            'A1': 16.0,
            'A2': 0.0
        }
        ht = {'KC': 0.000275, 'KP': 0.000893, 'KD': 0.46}
        
        Tshelf = {
            'init': -35.0,
            'setpt': np.array([0.0]),
            'ramp_rate': 1.0
        }
        Pchamber = {
            'setpt': np.array([0.15]),
            'ramp_rate': 0.5
        }
        eq_cap = {'a': -0.182, 'b': 11.7}
        nVial = 398
        dt = 0.01
        
        shelf_results, product_results, eq_cap_results = design_space.dry(
            vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial
        )
        
        # Extract values
        T_max_shelf = shelf_results[0][0, 0]
        drying_time_shelf = shelf_results[1][0, 0]
        avg_flux_shelf = shelf_results[2][0, 0]
        
        drying_time_product = product_results[1][0]
        avg_flux_product = product_results[2][0]
        
        T_max_eq = eq_cap_results[0][0]
        drying_time_eq = eq_cap_results[1][0]
        flux_eq = eq_cap_results[2][0]
        
        # Physical constraints
        assert T_max_shelf >= -50.0, "Product temperature too low"
        assert T_max_shelf <= 50.0, "Product temperature too high"
        assert drying_time_shelf > 0, "Drying time must be positive"
        assert drying_time_shelf < 100.0, "Drying time unreasonably long"
        assert avg_flux_shelf >= 0, "Flux must be non-negative"
        
        assert drying_time_product > 0, "Product drying time must be positive"
        assert avg_flux_product > 0, "Product flux must be positive"
        
        assert T_max_eq >= -50.0, "Equipment max temp too low"
        assert T_max_eq <= 50.0, "Equipment max temp too high"
        assert drying_time_eq > 0, "Equipment drying time must be positive"
        assert flux_eq > 0, "Equipment flux must be positive"
    
    def test_product_temperature_constraint(self):
        """Test that product temperature results match critical temperature."""
        vial = {'Av': 3.8, 'Ap': 3.14, 'Vfill': 2.0}
        T_crit = -5.0
        product = {
            'T_pr_crit': T_crit,
            'cSolid': 0.05,
            'R0': 1.4,
            'A1': 16.0,
            'A2': 0.0
        }
        ht = {'KC': 0.000275, 'KP': 0.000893, 'KD': 0.46}
        
        Tshelf = {
            'init': -35.0,
            'setpt': np.array([0.0]),
            'ramp_rate': 1.0
        }
        Pchamber = {
            'setpt': np.array([0.15]),
            'ramp_rate': 0.5
        }
        eq_cap = {'a': -0.182, 'b': 11.7}
        nVial = 398
        dt = 0.01
        
        _, product_results, _ = design_space.dry(
            vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial
        )
        
        # Product temperature should equal critical temperature
        T_product = product_results[0][0]
        assert abs(T_product - T_crit) < 0.01, \
            f"Product temperature {T_product}°C should equal critical {T_crit}°C"
    
    def test_equipment_capability_mass_balance(self):
        """Test that equipment capability respects equipment constraints."""
        vial = {'Av': 3.8, 'Ap': 3.14, 'Vfill': 2.0}
        product = {
            'T_pr_crit': -5.0,
            'cSolid': 0.05,
            'R0': 1.4,
            'A1': 16.0,
            'A2': 0.0
        }
        ht = {'KC': 0.000275, 'KP': 0.000893, 'KD': 0.46}
        
        Tshelf = {
            'init': -35.0,
            'setpt': np.array([0.0]),
            'ramp_rate': 1.0
        }
        Pch = 0.15  # Torr
        Pchamber = {
            'setpt': np.array([Pch]),
            'ramp_rate': 0.5
        }
        eq_cap = {'a': -0.182, 'b': 11.7}
        nVial = 398
        dt = 0.01
        
        _, _, eq_cap_results = design_space.dry(
            vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial
        )
        
        # Equipment sublimation rate
        dmdt_eq = eq_cap['a'] + eq_cap['b'] * Pch  # kg/hr for all vials
        flux_eq_expected = dmdt_eq / nVial / (vial['Ap'] * 1e-4)  # kg/hr/m²
        
        flux_eq_calculated = eq_cap_results[2][0]
        
        # Should match within numerical tolerance
        assert abs(flux_eq_calculated - flux_eq_expected) / flux_eq_expected < 0.01, \
            f"Equipment flux mismatch: {flux_eq_calculated} vs {flux_eq_expected}"


class TestDesignSpaceComparison:
    """Comparative tests between different design space modes."""
    
    def test_shelf_vs_product_temperature_modes(self):
        """Test that shelf and product temperature modes give different results."""
        vial = {'Av': 3.8, 'Ap': 3.14, 'Vfill': 2.0}
        product = {
            'T_pr_crit': -5.0,
            'cSolid': 0.05,
            'R0': 1.4,
            'A1': 16.0,
            'A2': 0.0
        }
        ht = {'KC': 0.000275, 'KP': 0.000893, 'KD': 0.46}
        
        Tshelf = {
            'init': -35.0,
            'setpt': np.array([0.0]),
            'ramp_rate': 1.0
        }
        Pchamber = {
            'setpt': np.array([0.15]),
            'ramp_rate': 0.5
        }
        eq_cap = {'a': -0.182, 'b': 11.7}
        nVial = 398
        dt = 0.01
        
        shelf_results, product_results, _ = design_space.dry(
            vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial
        )
        
        # Shelf temperature mode (fixed Tshelf)
        drying_time_shelf = shelf_results[1][0, 0]
        
        # Product temperature mode (fixed Tproduct at critical)
        drying_time_product = product_results[1][0]
        
        # Product temperature mode should have different drying time
        # (usually longer since it maintains T at critical limit)
        assert drying_time_shelf != drying_time_product, \
            "Shelf and product modes should give different drying times"
    
    def test_equipment_capability_fastest(self):
        """Test that equipment capability gives fastest drying (if feasible)."""
        vial = {'Av': 3.8, 'Ap': 3.14, 'Vfill': 2.0}
        product = {
            'T_pr_crit': -5.0,
            'cSolid': 0.05,
            'R0': 1.4,
            'A1': 16.0,
            'A2': 0.0
        }
        ht = {'KC': 0.000275, 'KP': 0.000893, 'KD': 0.46}
        
        Tshelf = {
            'init': -35.0,
            'setpt': np.array([0.0]),
            'ramp_rate': 1.0
        }
        Pchamber = {
            'setpt': np.array([0.15]),
            'ramp_rate': 0.5
        }
        eq_cap = {'a': -0.182, 'b': 11.7}
        nVial = 398
        dt = 0.01
        
        shelf_results, product_results, eq_cap_results = design_space.dry(
            vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial
        )
        
        drying_time_eq = eq_cap_results[1][0]
        drying_time_product = product_results[1][0]
        
        # Equipment capability should be faster or similar
        # (it assumes maximum equipment sublimation rate)
        assert drying_time_eq <= drying_time_product * 1.5, \
            "Equipment capability should give reasonably fast drying"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
