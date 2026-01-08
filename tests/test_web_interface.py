"""
Tests for web interface examples.

This module tests that the example scripts produce results matching
the web interface reference outputs.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from lyopronto import calc_knownRp


class TestWebInterfaceExample:
    """Test that our example replicates web interface results."""
    
    @pytest.fixture
    def web_interface_inputs(self):
        """Standard inputs from web interface screenshot."""
        vial = {
            'Av': 3.8,      # Vial area (cm²)
            'Ap': 3.14,     # Product area (cm²)
            'Vfill': 2.0,   # Fill volume (mL)
        }
        
        product = {
            'R0': 1.4,       # Base resistance
            'A1': 16.0,      # Resistance parameter A1
            'A2': 0.0,       # Resistance parameter A2
            'cSolid': 0.05,  # Solid content
        }
        
        ht = {
            'KC': 0.000275,
            'KP': 0.000893,
            'KD': 0.46,
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
        
        dt = 0.01
        
        return vial, product, ht, Pchamber, Tshelf, dt
    
    def test_web_interface_simulation(self, web_interface_inputs):
        """Test that simulation matches web interface output."""
        vial, product, ht, Pchamber, Tshelf, dt = web_interface_inputs
        
        # Run simulation
        output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
        
        # Check output structure
        assert output.shape[1] == 7, "Output should have 7 columns"
        assert output.size > 0, "Output should not be empty"
        
        # Extract key results
        drying_time = output[-1, 0]
        max_temp = output[:, 1].max()
        final_dried = output[-1, 6]
        
        # Check drying time matches web interface (6.66 hr)
        assert abs(drying_time - 6.66) < 0.1, \
            f"Drying time {drying_time:.2f} hr doesn't match web interface (6.66 hr)"
        
        # Check temperature constraint
        assert max_temp <= -5.0 + 0.5, \
            f"Temperature {max_temp:.2f}°C exceeds critical temp (-5°C)"
        
        # Check drying completion
        assert final_dried >= 0.99, \
            f"Final dried fraction {final_dried:.2f} < 0.99"
    
    def test_compare_with_reference_csv(self, web_interface_inputs):
        """Test that output matches reference CSV from web interface."""
        vial, product, ht, Pchamber, Tshelf, dt = web_interface_inputs
        
        # Run simulation
        output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
        
        # Load reference CSV (if it exists)
        ref_csv = Path('test_data/reference_primary_drying.csv')
        if not ref_csv.exists():
            pytest.skip(f"Reference CSV not found: {ref_csv}")
        
        df_ref = pd.read_csv(ref_csv, sep=';')
        
        # Compare key metrics
        ref_time = df_ref['Time [hr]'].iloc[-1]
        sim_time = output[-1, 0]
        assert abs(ref_time - sim_time) / ref_time < 0.05, \
            f"Drying time differs by >5%: {sim_time:.2f} vs {ref_time:.2f} hr"
        
        ref_max_temp = df_ref['Sublimation Temperature [C]'].max()
        sim_max_temp = output[:, 1].max()
        assert abs(ref_max_temp - sim_max_temp) < 1.0, \
            f"Max temperature differs by >1°C: {sim_max_temp:.2f} vs {ref_max_temp:.2f}°C"
        
        # Compare final drying percentage
        ref_final_dried = df_ref['Percent Dried'].iloc[-1] / 100  # Convert to fraction
        sim_final_dried = output[-1, 6]
        assert abs(ref_final_dried - sim_final_dried) < 0.05, \
            f"Final dried fraction differs: {sim_final_dried:.2f} vs {ref_final_dried:.2f}"
    
    def test_temperature_profile_reasonable(self, web_interface_inputs):
        """Test that temperature profile is physically reasonable."""
        vial, product, ht, Pchamber, Tshelf, dt = web_interface_inputs
        
        output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
        
        Tsub = output[:, 1]
        Tbot = output[:, 2]
        Tsh = output[:, 3]
        
        # Temperature should be within physical bounds
        assert np.all(Tsub >= -60), "Sublimation temp too low"
        assert np.all(Tsub <= 0), "Sublimation temp above freezing"
        
        # Shelf temperature should ramp from -35 to 20°C
        assert Tsh[0] == pytest.approx(-35.0, abs=0.5), "Initial shelf temp incorrect"
        assert Tsh[-1] <= 20.0, "Final shelf temp exceeds setpoint"
        
        # Temperature gradient should generally be Tsh > Tbot > Tsub
        # (allowing some tolerance for edge cases)
        violations = np.sum(Tbot < Tsub)
        assert violations < len(output) * 0.1, \
            f"Too many Tbot < Tsub violations: {violations}/{len(output)}"
    
    def test_flux_profile_non_monotonic(self, web_interface_inputs):
        """Test that flux profile shows expected non-monotonic behavior."""
        vial, product, ht, Pchamber, Tshelf, dt = web_interface_inputs
        
        output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
        
        flux = output[:, 5]
        
        # Flux should be non-negative
        assert np.all(flux >= 0), "Negative flux detected"
        
        # Find maximum flux
        max_flux_idx = np.argmax(flux)
        
        # Maximum should not be at the very beginning or end
        assert max_flux_idx > len(flux) * 0.05, \
            "Max flux too early - should increase initially"
        assert max_flux_idx < len(flux) * 0.95, \
            "Max flux too late - should decrease eventually"
        
        # After peak, flux should generally decrease (late stage)
        late_stage = flux[int(len(flux)*0.8):]
        assert np.all(np.diff(late_stage) <= 0.1), \
            "Flux should decrease in late stage"
    
    def test_chamber_pressure_constant(self, web_interface_inputs):
        """Test that chamber pressure remains constant at setpoint."""
        vial, product, ht, Pchamber, Tshelf, dt = web_interface_inputs
        
        output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
        
        Pch_output = output[:, 4]  # In mTorr
        
        # Should be constant at 150 mTorr (0.15 Torr * 1000)
        expected_Pch = 150.0  # mTorr
        assert np.all(Pch_output == pytest.approx(expected_Pch, abs=0.1)), \
            f"Chamber pressure not constant at {expected_Pch} mTorr"
    
    def test_mass_balance(self, web_interface_inputs):
        """Test mass balance between sublimation and product consumption."""
        vial, product, ht, Pchamber, Tshelf, dt = web_interface_inputs
        
        output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
        
        from lyopronto.functions import Lpr0_FUN
        from lyopronto.constant import rho_ice
        
        # Calculate initial ice mass
        Lpr0 = Lpr0_FUN(vial['Vfill'], vial['Ap'], product['cSolid'])
        m_initial = rho_ice * vial['Ap'] * Lpr0  # grams
        
        # Integrate sublimation flux
        time = output[:, 0]
        flux = output[:, 5]  # kg/hr/m²
        
        # Convert flux to total mass sublimed
        # flux is kg/hr/m², Ap is in cm² = Ap*1e-4 m²
        # Integrate gives kg, convert to g
        total_sublimed = np.trapezoid(flux, time) * (vial['Ap'] * 1e-4) * 1000  # g
        
        # Check mass balance (within 3% tolerance for numerical integration with 100 points)
        error = abs(total_sublimed - m_initial) / m_initial
        assert error < 0.03, \
            f"Mass balance error {error*100:.1f}% exceeds 3% tolerance"
    
    def test_output_format_matches_web_csv(self, web_interface_inputs):
        """Test that output format matches web interface CSV structure."""
        vial, product, ht, Pchamber, Tshelf, dt = web_interface_inputs
        
        output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
        
        # Output should have 7 columns
        assert output.shape[1] == 7, "Should have 7 columns"
        
        # Column 0: Time (hr) - should start at 0 and increase
        assert output[0, 0] == 0.0, "Time should start at 0"
        assert np.all(np.diff(output[:, 0]) > 0), "Time should increase"
        
        # Column 4: Pch should be [mTorr] (not Torr)
        assert output[0, 4] == pytest.approx(150.0, abs=1.0), \
            "Pch should be [mTorr] (150, not 0.15)"
        
        # Column 6: Dried should be fraction 0-1 (not percentage)
        assert 0 <= output[0, 6] <= 1.0, "Dried should be fraction 0-1"
        assert output[-1, 6] == pytest.approx(1.0, abs=0.01), \
            "Final dried should be ~1.0"


class TestWebInterfaceComparison:
    """Integration tests comparing with actual web interface output."""
    
    def test_exact_match_with_reference(self):
        """Test for exact match with reference web output."""
        # This test uses the actual reference CSV
        ref_csv = Path('test_data/reference_primary_drying.csv')
        if not ref_csv.exists():
            pytest.skip(f"Reference CSV not found: {ref_csv}")
        
        # Set up exact inputs from web interface
        vial = {'Av': 3.8, 'Ap': 3.14, 'Vfill': 2.0}
        product = {'R0': 1.4, 'A1': 16.0, 'A2': 0.0, 'cSolid': 0.05}
        ht = {'KC': 0.000275, 'KP': 0.000893, 'KD': 0.46}
        Pchamber = {'setpt': [0.15], 'dt_setpt': [1800.0], 'ramp_rate': 0.5}
        Tshelf = {'init': -35.0, 'setpt': [20.0], 'dt_setpt': [1800.0], 'ramp_rate': 1.0}
        dt = 0.01
        
        # Run simulation
        output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
        
        # Load reference
        df_ref = pd.read_csv(ref_csv, sep=';')
        
        # Key comparisons
        assert abs(output[-1, 0] - df_ref['Time [hr]'].iloc[-1]) < 0.1, \
            "Drying time should match within 0.1 hr"
        
        assert abs(output[:, 1].max() - df_ref['Sublimation Temperature [C]'].max()) < 0.5, \
            "Max temperature should match within 0.5°C"
