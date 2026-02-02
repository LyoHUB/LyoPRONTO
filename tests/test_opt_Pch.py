"""
Comprehensive tests for opt_Pch.py - Pressure optimization module.

This module optimizes chamber pressure while fixing shelf temperature.
Tests based on working example_optimizer.py structure.
"""

import pytest
import numpy as np
from lyopronto import opt_Pch, constant, functions
from .utils import (
    assert_physically_reasonable_output,
    assert_complete_drying,
    assert_incomplete_drying,
)


def opt_pch_consistency(output, setup):
    vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = setup

    assert output is not None, "opt_Pch.dry should return output"
    assert isinstance(output, np.ndarray), "Output should be numpy array"

    # Should have 7 columns: time, Tsub, Tbot, Tsh, Pch, flux, percent_dried
    assert output.shape[1] == 7, f"Expected 7 columns, got {output.shape[1]}"

    # Should have multiple time points
    assert output.shape[0] > 1, "Should have multiple time points"

    assert_physically_reasonable_output(output)

    # Shelf temperature (column 3) should start at init
    assert output[0, 3] == pytest.approx(Tshelf["init"]), (
        f"Initial Tsh should be ~{Tshelf['init']}°C"
    )

    # With time, shelf temperature should follow setpoints
    # ramptime
    # if output[-1, 0] > Tshelf[
    # assert 
    Tsh_values = output[:, 3]
    Tsh_check = functions.RampInterpolator(Tshelf)(output[:, 0])
    locs = np.where(~np.isclose(Tsh_values, Tsh_check, atol=0.1, rtol=0))
    print(locs)
    print(functions.RampInterpolator(Tshelf).times)
    print(output[:, 0][locs])
    print(Tsh_values[locs])
    print(Tsh_check[locs])
    np.testing.assert_allclose(Tsh_values, Tsh_check, atol=0.1, rtol=0)

    # Pressure (column 4) should vary
    Pch_values = output[:, 4]
    assert np.std(Pch_values) > 0, "Pressure should vary (be optimized)"

    # Both should respect bounds
    assert np.all(Pch_values >= Pchamber["min"] * constant.Torr_to_mTorr), (
        "Pressure should be >= min bound"
    )
    if hasattr(Pchamber, "max"):
        assert np.all(Pch_values <= Pchamber["max"] * constant.Torr_to_mTorr), (
            "Pressure should be <= max bound"
        )

    # Tbot (column 2) should stay at or below T_pr_crit
    T_crit = product["T_pr_crit"]
    assert np.all(output[:, 2] <= T_crit + 0.01), (
        f"Product temperature should be <= {T_crit}°C (critical)"
    )

    # Should not exceed equipment capability (with small tolerance)
    # Equipment capability at different pressures
    Pch = output[:, 4] / 1000  # [Torr]
    actual_cap = eq_cap["a"] + eq_cap["b"] * Pch  # [kg/hr]
    # Total sublimation rate per vial
    flux = output[:, 5]  # Sublimation flux [kg/hr/m**2]
    Ap_m2 = vial["Ap"] * constant.cm_To_m**2  # Convert [cm**2] to [m**2]
    dmdt = flux * Ap_m2  # [kg/hr/vial]
    violations = dmdt - actual_cap

    assert np.all(violations <= 0), (
        f"Equipment capability exceeded by {np.max(violations):.3e} kg/hr"
    )

@pytest.fixture
def standard_opt_pch_inputs():
    """Standard inputs for opt_Pch testing (pressure optimization)."""
    # Vial geometry
    vial = {
        "Av": 3.8,  # Vial area [cm**2]
        "Ap": 3.14,  # Product area [cm**2]
        "Vfill": 2.0,  # Fill volume [mL]
    }

    # Product properties
    product = {
        "T_pr_crit": -25.0,  # Critical product temperature [degC]
        "cSolid": 0.05,  # Solid content [g/mL]
        "R0": 1.4,  # Product resistance coefficient R0 [cm**2-hr-Torr/g]
        "A1": 16.0,  # Product resistance coefficient A1 [1/cm]
        "A2": 0.0,  # Product resistance coefficient A2 [1/cm**2]
    }

    # Vial heat transfer coefficients
    ht = {
        "KC": 0.000275,  # Kc [cal/s/K/cm**2]
        "KP": 0.000893,  # Kp [cal/s/K/cm**2/Torr]
        "KD": 0.46,  # Kd dimensionless
    }

    # Chamber pressure optimization settings
    Pchamber = {
        "min": 0.05,  # Minimum chamber pressure [Torr]
        "max": 1.0,  # Maximum chamber pressure [Torr]
    }

    # Shelf temperature settings (FIXED for opt_Pch)
    # Multi-step profile: start at -35°C, ramp to -20°C, then 0°C
    Tshelf = {
        "init": -35.0,  # Initial shelf temperature [degC]
        "setpt": np.array([-10.0]),  # Set points [degC]
        "dt_setpt": np.array([3600]),  # Hold times [min]
        "ramp_rate": 1.0,  # Ramp rate [degC/min]
    }

    # Equipment capability
    eq_cap = {
        "a": -0.182,  # Equipment capability coefficient a [kg]/hr
        "b": 11.7,  # Equipment capability coefficient b [kg/hr/Torr]
    }

    # Number of vials
    nVial = 398

    # Time step
    dt = 0.01  # Time step [hr]

    return vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial


class TestOptPchBasic:
    """Basic functionality tests for opt_Pch module."""

    def test_pressure_optimization(self, standard_opt_pch_inputs):
        """Test that opt_Pch.dry executes,  output has correct structure, and
        each output column contains valid data. Then, check that
        pressure is optimized (varies over time), shelf temperature follows
        specified profile, and product temperature stays below critical temperature."""
        output = opt_Pch.dry(*standard_opt_pch_inputs)
        opt_pch_consistency(output, standard_opt_pch_inputs)
        assert_complete_drying(output)
        # Drying time should be reasonable (0.5 to 10 hours)
        drying_time = output[-1, 0]
        assert 0.5 < drying_time < 20, (
            f"Drying time {drying_time:.2f} hr should be reasonable (0.5-20 hr)"
        )

    def test_pressure_optimization_nomax(self, standard_opt_pch_inputs):
        """Test that opt_Pch.dry works without a maximum pressure constraint."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        # Remove max pressure constraint
        del Pchamber["max"]
        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        opt_pch_consistency(output, (vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial))
        assert_complete_drying(output)

class TestOptPchEdgeCases:
    """Edge case tests for opt_Pch module."""

    # @pytest.mark.skip(reason="TODO: needs some feasibility checking")
    def test_low_critical_temperature(self, standard_opt_pch_inputs):
        """Test with very low critical temperature (-35°C)."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs

        # Lower critical temperature
        product["T_pr_crit"] = -35.0
        Pchamber["min"] = 0.001  # Lower min pressure to 1 mTorr
        Pchamber["max"] = 2.00  # Raise max pressure to 2.00 Torr
        Tshelf["setpt"] = [-30]  # Lower shelf temperature to make feasible

        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)

        opt_pch_consistency(output, (vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial))
        assert_complete_drying(output)

    def test_insufficient_time(self, standard_opt_pch_inputs):
        """Test with very low critical temperature (-35°C)."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs

        Tshelf["dt_setpt"] = [120]  # Less drying time

        with pytest.warns(UserWarning, match="Drying incomplete"):
            output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
        opt_pch_consistency(output, (vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial))
        assert_incomplete_drying(output)

    def test_high_resistance_product(self, standard_opt_pch_inputs):
        """Test with high resistance product."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs

        # Increase resistance
        product["R0"] = 3.0
        product["A1"] = 30.0
        # Drop shelf temperature to make constraint feasible
        Tshelf["setpt"] = np.array([-20.0])

        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)

        opt_pch_consistency(output, (vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial))

        assert_complete_drying(output)
        # Higher resistance should lead to longer drying time
        # TODO pin this to a value from default run conditions
        assert output[-1, 0] > 1.0, "High resistance should take longer to dry"

    def test_multi_shelf_temperature_setpoints(self, standard_opt_pch_inputs):
        """Test with multiple shelf temperature setpoints."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs

        # Two setpoints
        Tshelf["setpt"] = np.array([-20.0, 0.0, -10.0])
        Tshelf["dt_setpt"] = np.array([120, 120, 1200])

        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)

        opt_pch_consistency(output, (vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial))

        assert_complete_drying(output)

    def test_higher_min_pressure(self, standard_opt_pch_inputs):
        """Test with higher minimum pressure constraint (0.10 Torr)."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs

        # Higher minimum pressure
        Pchamber["min"] = 0.10  # Torr = 100 mTorr
        # Needs a lower shelf temperature to complete drying
        Tshelf["setpt"] = np.array([-20.0])

        output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)

        opt_pch_consistency(output, (vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial))

        assert_complete_drying(output)
        # All pressures should be >= 100 mTorr
        assert np.all(output[:, 4] >= 100), "Pressure should respect higher min bound"

    def test_incomplete_optimization(self, standard_opt_pch_inputs):
        """Test with higher minimum pressure constraint (0.10 Torr)."""
        vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs

        # Higher minimum pressure
        Pchamber["min"] = 0.10  # Torr = 100 mTorr
        # With higher shelf temperature, CANNOT complete drying and adhere to constraints
        Tshelf["setpt"] = [0]

        with pytest.warns(UserWarning, match="Optimization failed"):
            output = opt_Pch.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)

        assert_incomplete_drying(output)
        # All pressures should be >= 100 mTorr
        assert np.all(output[:, 4] >= 100), "Pressure should respect higher min bound"

    def test_narrow_pressure_range(self, standard_opt_pch_inputs):
        """Test with narrow pressure optimization range."""
        vial, product, ht, _, Tshelf, dt, eq_cap, nVial = standard_opt_pch_inputs
        new_Pch = {"min": 0.070, "max": 0.090}
        product["T_pr_crit"] = -30.0  # Lower critical temperature to challenge
        Tshelf["setpt"] = [-20.0]  # Lower shelf temperature to make feasible

        output = opt_Pch.dry(vial, product, ht, new_Pch, Tshelf, dt, eq_cap, nVial)

        opt_pch_consistency(output, (vial, product, ht, new_Pch, Tshelf, dt, eq_cap, nVial))

    def test_tight_equipment_constraint(self, standard_opt_pch_inputs):
        """Test with tighter equipment capability constraint."""
        vial, product, ht, Pchamber, Tshelf, dt, _, nVial = standard_opt_pch_inputs
        # Reduce equipment capability
        tight_eq_cap = {
            "a": -0.3,  # [kg/hr]
            "b": 5.0,  # [kg/hr/Torr]
        }

        output = opt_Pch.dry(
            vial, product, ht, Pchamber, Tshelf, dt, tight_eq_cap, nVial
        )

        # Should run without errors and show some progress despite tighter constraint
        opt_pch_consistency(output, (vial, product, ht, Pchamber, Tshelf, dt, tight_eq_cap, nVial))
        assert_complete_drying(output)

    @pytest.mark.slow
    def test_consistent_results(self, standard_opt_pch_inputs):
        """Test that repeated runs give consistent results."""
        # Run twice
        output1 = opt_Pch.dry(*standard_opt_pch_inputs)
        output2 = opt_Pch.dry(*standard_opt_pch_inputs)

        # Results should be identical (deterministic optimization)
        np.testing.assert_array_almost_equal( output1, output2, decimal=6)


class TestOptPchReference:
    @pytest.fixture
    def opt_pch_reference_inputs(self):
        vial = {"Av": 3.8, "Ap": 3.14, "Vfill": 2.0}
        # Product properties
        product = {
            "T_pr_crit": -5.0,  # Critical product temperature [degC]
            "cSolid": 0.05,  # Solid content [g/mL]
            "R0": 1.4,  # Product resistance coefficient R0 [cm**2-hr-Torr/g]
            "A1": 16.0,  # Product resistance coefficient A1 [1/cm]
            "A2": 0.0,  # Product resistance coefficient A2 [1/cm**2]
        }
        # Vial heat transfer coefficients
        ht = {"KC": 0.000275, "KP": 0.000893, "KD": 0.46}
        # Chamber pressure optimization settings
        Pchamber = {
            "min": 0.05,  # Minimum chamber pressure [Torr]
            "max": 1000.0,  # Maximum chamber pressure [Torr]
        }
        # Shelf temperature settings (FIXED for opt_Pch)
        Tshelf = {
            "init": -35.0,  # Initial shelf temperature [degC]
            "setpt": np.array([20.0]),  # Set points [degC]
            "dt_setpt": np.array([1800]),  # Hold times [min]
            "ramp_rate": 1.0,  # Ramp rate [degC/min]
        }
        # Equipment capability
        eq_cap = {
            "a": -0.182,  # Equipment capability coefficient a [kg]/hr
            "b": 11.7,  # Equipment capability coefficient b [kg/hr/Torr]
        }
        nVial = 398
        dt = 0.01  # Time step [hr]
        return vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial

    # This test may need updating since the reference case can be questionable.
    def test_opt_pch_reference(self, repo_root, opt_pch_reference_inputs):
        """Test opt_Pch results against reference data from web interface optimizer."""
        ref_csv = repo_root / "test_data" / "reference_opt_Pch.csv"
        if not ref_csv.exists():
            pytest.skip(f"Reference CSV not found: {ref_csv}")
        output_ref = np.loadtxt(ref_csv, delimiter=",", skiprows=1)
        output = opt_Pch.dry(*opt_pch_reference_inputs)

        # DON'T directly compare: this optimization is very poorly formulated, and checking
        # element-wise equality against reference data is brittle and not meaningful.
        # Instead, check that output is reasonable and matches or exceeds the performance.
        opt_pch_consistency(output, opt_pch_reference_inputs)
        assert_complete_drying(output)
        # Drying time should be equal to or better than reference
        drying_time_ref = output_ref[-1, 0]
        drying_time = output[-1, 0]
        assert drying_time <= drying_time_ref, (
            f"Drying time {drying_time:.2f} hr should be <= reference "
            + f"{drying_time_ref:.2f} hr"
        )
        # array_compare = np.isclose(output, output_ref, atol=1e-3)
        # assert array_compare.all(), (
        #     "opt_Pch output should match reference data, but reference data is known to "
        #     + "be odd, so (with maintainer approval) the reference data may be updated."
        #     + f"Not matching at positions:\n {np.where(~array_compare)}"
        # )
