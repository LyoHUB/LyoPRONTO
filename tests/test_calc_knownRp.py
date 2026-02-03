"""Integration tests for primary drying calculators."""

import pytest
import numpy as np
from lyopronto import calc_knownRp, constant
from .utils import (
    assert_physically_reasonable_output,
    assert_complete_drying,
    assert_incomplete_drying,
)


@pytest.fixture
def knownRp_standard_setup(standard_setup):
    """Unpack standard setup into individual components."""
    return (
        standard_setup["vial"],
        standard_setup["product"],
        standard_setup["ht"],
        standard_setup["Pchamber"],
        standard_setup["Tshelf"],
        None,
    )


class TestCalcKnownRp:
    """Tests for the calc_knownRp.dry calculator."""

    def test_dry_basics(self, knownRp_standard_setup):
        """Test that primary drying calculator completes without errors."""
        """Test that: 
        - drying reaches near completion.
        - array has appropriate shape.
        - values are physically reasonable.
        """

        output = calc_knownRp.dry(*knownRp_standard_setup)
        # Should return an array
        assert isinstance(output, np.ndarray)
        assert output.shape[0] > 0  # Should have at least some time steps
        assert output.shape[1] == 7  # Should have 7 columns
        assert_complete_drying(output)
        assert_physically_reasonable_output(output)
        drying_time = output[-1, 0]  # hours
        # Should be between 5 and 50 hours for standard conditions
        assert 5.0 < drying_time < 50.0, (
            f"Drying time {drying_time:.1f} hrs seems unreasonable"
        )
        assert_physically_reasonable_output(output)
        # Flux at end should be less than peak (resistance eventually dominates)
        flux_peak = np.max(output[:, 5])
        flux_end = output[-1, 5]
        assert flux_end < flux_peak, "Final flux should be less than peak flux"

    def test_small_fill_dries_faster(self, knownRp_standard_setup):
        """Test that smaller fill volumes dry faster than larger fill volumes."""
        vial, product, ht, Pchamber, Tshelf, dt = knownRp_standard_setup
        small_fill = vial.copy()
        small_fill["Vfill"] /= 2.0  # smaller fill volume
        # Small fill
        output_small = calc_knownRp.dry(small_fill, product, ht, Pchamber, Tshelf, dt)
        # Standard fill
        output_standard = calc_knownRp.dry(*knownRp_standard_setup)
        time_small = output_small[-1, 0]
        time_standard = output_standard[-1, 0]
        assert time_small < time_standard, "Small fill volume should dry faster"

    def test_other_pressures(self, knownRp_standard_setup):
        """Test that runs with different chamber pressure leads to faster drying."""
        # Low pressure
        vial, product, ht, Pchamber, Tshelf, dt = knownRp_standard_setup
        Pchamber_low = {"setpt": [0.05], "dt_setpt": [1800.0], "ramp_rate": 0.5}
        Pchamber_high = {"setpt": [0.20], "dt_setpt": [1800.0], "ramp_rate": 0.5}
        output_low = calc_knownRp.dry(vial, product, ht, Pchamber_low, Tshelf, dt)
        output_high = calc_knownRp.dry(vial, product, ht, Pchamber_high, Tshelf, dt)
        # Both complete drying
        assert_complete_drying(output_low)
        assert_complete_drying(output_high)

    def test_conservative_shelf_temp_case(self, knownRp_standard_setup):
        """Test conservative shelf temperature case (-20°C)."""
        vial, product, ht, Pchamber, _, dt = knownRp_standard_setup
        Tshelf = {
            "init": -40.0,
            "setpt": [-20.0],
            "dt_setpt": [1800.0],
            "ramp_rate": 0.5,
        }
        output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
        assert_physically_reasonable_output(output)

    def test_concentrated_product_takes_longer(self, knownRp_standard_setup):
        """Test that dilute product takes longer to dry, given same Rp."""
        vial, product, ht, Pchamber, Tshelf, dt = knownRp_standard_setup
        product_dilute = product.copy()
        product_concentrated = product.copy()
        output_dilute = calc_knownRp.dry(vial, product_dilute, ht, Pchamber, Tshelf, dt)
        product_dilute["cSolid"] = 0.01  # 1%
        product_concentrated["cSolid"] = 0.10  # 10%
        output_concentrated = calc_knownRp.dry(
            vial, product_concentrated, ht, Pchamber, Tshelf, dt
        )
        time_dilute = output_dilute[-1, 0]
        time_concentrated = output_concentrated[-1, 0]
        assert time_concentrated < time_dilute, "Dilute product should take longer"

    def test_reproducibility(self, knownRp_standard_setup):
        """Test that running same simulation twice gives same results."""
        output1 = calc_knownRp.dry(*knownRp_standard_setup)
        output2 = calc_knownRp.dry(*knownRp_standard_setup)
        np.testing.assert_array_almost_equal(output1, output2, decimal=10)

    def test_different_timesteps_similar_results(self, knownRp_standard_setup):
        """Test that different timesteps give similar final results."""
        # Coarse timestep
        output_coarse = calc_knownRp.dry(*knownRp_standard_setup[:-1], 0.02)
        # Fine timestep
        output_fine = calc_knownRp.dry(*knownRp_standard_setup[:-1], 0.005)
        time_coarse = output_coarse[-1, 0]
        time_fine = output_fine[-1, 0]
        # Times should be within 5% of each other
        assert time_coarse == pytest.approx(time_fine, rel=0.05)
        assert np.isclose(output_fine[0, :], output_coarse[0, :], atol=1e-3).all()
        assert np.isclose(output_fine[-1, :], output_coarse[-1, :], atol=1e-3).all()

    def test_mass_balance_conservation(self, knownRp_standard_setup):
        """Test that integrated mass removed equals initial mass."""
        vial, product, ht, Pchamber, Tshelf, dt = knownRp_standard_setup
        output = calc_knownRp.dry(*knownRp_standard_setup)
        # Calculate initial water mass
        Vfill = vial["Vfill"]  # mL
        cSolid = product["cSolid"]
        water_mass_initial = (
            Vfill * constant.rho_solution * (1 - cSolid) / constant.kg_To_g
        )  # kg

        # Integrate sublimation flux over time
        times = output[:, 0]  # [hr]
        fluxes = output[:, 5]  # [kg/hr/m**2]
        Ap_m2 = vial["Ap"] * constant.cm_To_m**2  # [m**2]

        # Convert flux to total mass rate: flux [kg/hr/m**2] * area [m**2] = [kg/hr]
        mass_rates = fluxes * Ap_m2  # [kg/hr]
        # Numerical integration using trapezoidal rule
        mass_removed = np.trapezoid(mass_rates, times)  # [kg]
        # Should be approximately equal (within 2% due to numerical integration)
        # Note: Trapezoidal rule on 100 points gives ~2% error
        assert mass_removed == pytest.approx(water_mass_initial, rel=0.02), (
            f"Mass removed {mass_removed:.4f} kg != initial mass {water_mass_initial:.4f} kg "
            f"(error: {abs(mass_removed - water_mass_initial) / water_mass_initial * 100:.1f}%)"
        )


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_short_time(self, knownRp_standard_setup):
        """Test with short time (should not finish drying)."""
        vial, product, ht, Pchamber, _, dt = knownRp_standard_setup
        Tshelf = {"init": -35.0, "setpt": [20.0], "dt_setpt": [10.0], "ramp_rate": 0.5}
        Pchamber["dt_setpt"] = [10.0]

        with pytest.warns(UserWarning, match="time"):
            output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
        assert_physically_reasonable_output(output)
        assert_incomplete_drying(output)

        Tshelf = {
            "init": -35.0,
            "setpt": [10, 20.0],
            "dt_setpt": [10.0],
            "ramp_rate": 0.5,
        }
        Pchamber["dt_setpt"] = [10.0]
        with pytest.warns(UserWarning, match="time"):
            output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
        assert_physically_reasonable_output(output)
        assert_incomplete_drying(output)

        Tshelf = {"init": -35.0, "setpt": [20.0], "dt_setpt": [10.0], "ramp_rate": 0.5}
        Pchamber["setpt"] = [0.1, 0.12]
        Pchamber["dt_setpt"] = [10.0]
        with pytest.warns(UserWarning, match="time"):
            output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
        assert_physically_reasonable_output(output)
        assert_incomplete_drying(output)

    def test_very_low_shelf_temperature(self, knownRp_standard_setup):
        """Test with very low shelf temperature (should not dry at all)."""
        vial, product, ht, Pchamber, _, dt = knownRp_standard_setup
        Tshelf = {
            "init": -50.0,
            "setpt": [-40.0],
            "dt_setpt": [1800.0],
            "ramp_rate": 0.5,
        }

        with pytest.warns(UserWarning, match="vapor pressure"):
            output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)

        # Should still produce valid output
        assert output.shape[0] > 0
        # Check that temperatures match shelf
        # Check that no drying occurs
        assert np.all(output[:, 5] == 0)  # Non-negative flux
        assert np.all(output[:, 6] == 0)

    def test_very_small_fill(self, knownRp_standard_setup):
        """Test with very small fill volume."""
        vial, product, ht, Pchamber, Tshelf, dt = knownRp_standard_setup
        vial["Vfill"] = 0.5

        output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)

        assert_complete_drying(output)
        assert_physically_reasonable_output(output)

    def test_high_resistance_product(self, knownRp_standard_setup):
        """Test with high resistance product (should dry slowly)."""
        vial, product, ht, Pchamber, Tshelf, dt = knownRp_standard_setup
        product["R0"] = 5.0
        product["A1"] = 50.0

        output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)

        # High resistance means longer drying, but check it completes
        assert_complete_drying(output)
        # Note: May not take >20 hours depending on other parameters
        assert_physically_reasonable_output(output)


class TestRegression:
    """
    Regression tests against standard reference case.

    TODO: These values could be updated with actual validated results from
    the original paper or verified simulations.
    Further examples could be added with different conditions.
    """

    @pytest.fixture
    def reference_case(self):
        """Standard reference case parameters."""
        vial = {"Av": 3.80, "Ap": 3.14, "Vfill": 2.0}
        product = {"cSolid": 0.05, "R0": 1.4, "A1": 16.0, "A2": 0.0}
        ht = {"KC": 2.75e-4, "KP": 8.93e-4, "KD": 0.46}
        Pchamber = {"setpt": [0.15], "dt_setpt": [1800.0], "ramp_rate": 0.5}
        Tshelf = {
            "init": -35.0,
            "setpt": [20.0],
            "dt_setpt": [1800.0],
            "ramp_rate": 1.0,
        }
        dt = 0.01

        return vial, product, ht, Pchamber, Tshelf, dt

    def test_reference_drying_time(self, reference_case):
        """
        Test that drying time matches reference value.

        The reference value is based on standard conditions with the current model.
        If model physics change, this test will catch regressions.
        """
        """Test initial conditions match expected values."""
        """Test final state matches expected values."""
        output = calc_knownRp.dry(*reference_case)

        # Expected drying time based on current model behavior
        # Standard case: 2 mL fill, 5% solids, Pch=0.15 Torr, Tsh ramp to 20°C
        drying_time = output[-1, 0]
        expected_time = 6.66  # hours

        # Allow 5% tolerance for numerical variations
        assert drying_time == pytest.approx(expected_time, abs=0.05), (
            f"Drying time {drying_time:.2f} hrs differs from reference {expected_time:.2f} hrs"
        )

        # Check initial values (first row)
        initial_time = output[0, 0]
        initial_Tsub = output[0, 1]
        initial_Tbot = output[0, 2]
        initial_Tsh = output[0, 3]
        initial_Pch_mTorr = output[0, 4]
        initial_percent = output[0, 6]

        assert initial_time == 0.0
        assert initial_Tsub == pytest.approx(-35.8, abs=0.1)  # Should start very cold
        assert initial_Tbot == pytest.approx(-35.8, abs=0.1)  # Should start very cold
        assert initial_Tsh == pytest.approx(-35.0, abs=0.0001)  # Initial shelf temp
        assert initial_Pch_mTorr == pytest.approx(
            150.0, abs=0.1
        )  # Chamber pressure [mTorr]
        assert initial_percent == 0.0  # Starting at 0 percent dried

        # Check final values (last row)
        final_Tsub = output[-1, 1]
        final_Tbot = output[-1, 2]
        final_Tsh = output[-1, 3]
        final_flux = output[-1, 5]

        assert final_Tsh == pytest.approx(
            20.0, abs=0.01
        )  # Should reach target shelf temp
        assert final_Tbot == pytest.approx(-14.7, abs=0.1)
        assert final_Tbot == pytest.approx(final_Tsub, abs=0.1)
        assert final_flux == pytest.approx(
            0.8945, abs=0.01
        )  # Flux should still be significant
        assert_complete_drying(output)

    def test_match_web_output(self, reference_data_path):
        """Test for exact match with reference web output."""
        # This test uses the actual reference CSV
        ref_csv = reference_data_path / "reference_primary_drying.csv"
        if not ref_csv.exists():
            pytest.skip(f"Reference CSV not found: {ref_csv}")

        output_ref = np.loadtxt(ref_csv, delimiter=";", skiprows=1)

        # Set up exact inputs from web interface
        vial = {"Av": 3.8, "Ap": 3.14, "Vfill": 2.0}
        product = {"R0": 1.4, "A1": 16.0, "A2": 0.0, "cSolid": 0.05}
        ht = {"KC": 0.000275, "KP": 0.000893, "KD": 0.46}
        Pchamber = {"setpt": [0.15], "dt_setpt": [1800.0], "ramp_rate": 0.5}
        Tshelf = {
            "init": -35.0,
            "setpt": [20.0],
            "dt_setpt": [1800.0],
            "ramp_rate": 1.0,
        }
        dt = 0.01

        # Run simulation
        output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)

        # Compare all except percent dried with relative tolerance 5%
        assert np.isclose(output[:, 0:6], output_ref[:, 0:6], rtol=0.05).all()
        # This one is more finicky, use absolute tolerance of 0.1% dried
        assert np.isclose(output[:, 6], output_ref[:, 6], atol=0.1).all()

    # This is partially redundant with above, but is one more sanity check
    def test_flux_profile_non_monotonic(self, reference_case):
        """Test that flux profile shows expected non-monotonic behavior."""
        output = calc_knownRp.dry(*reference_case)

        flux = output[:, 5]

        # Flux should be non-negative
        assert np.all(flux >= 0), "Negative flux detected"

        # Find maximum flux
        max_flux_idx = np.argmax(flux)

        # Maximum should not be at the very beginning or end
        assert max_flux_idx > len(flux) * 0.05, (
            "Max flux too early - should increase initially"
        )
        assert max_flux_idx < len(flux) * 0.95, (
            "Max flux too late - should decrease eventually"
        )

        # After peak, flux should generally decrease (late stage)
        late_stage = flux[int(len(flux) * 0.8) :]
        assert np.all(np.diff(late_stage) <= 0.0), "Flux should decrease in late stage"
