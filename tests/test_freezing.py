"""Tests for LyoPRONTO freezing functionality."""

import pytest
import numpy as np
from lyopronto.freezing import freeze
from lyopronto.functions import (
    crystallization_time_FUN,
    lumped_cap_Tpr_ice,
    lumped_cap_Tpr_sol,
)
from lyopronto import constant


def calc_shelfT_time(Tshelf):
    max_time = Tshelf["dt_setpt"].sum() / constant.hr_To_min  # Convert minutes to hours
    setpt_changes = np.diff(np.concatenate(([Tshelf["init"]], Tshelf["setpt"])))
    max_time += np.sum(np.abs(setpt_changes)) / Tshelf["ramp_rate"] / constant.hr_To_min
    return max_time


@pytest.fixture
def freezing_params():
    vial = {"Av": 3.8, "Ap": 3.14, "Vfill": 2.0}
    product = {"Tpr0": 15.8, "Tf": -1.52, "Tn": -5.84, "cSolid": 0.05}
    h_freezing = 38.0  # W/m²/K
    Tshelf = {
        "init": 10.0,
        "setpt": np.array([-40.0]),
        "dt_setpt": np.array([1800]),
        "ramp_rate": 1.0,
    }
    dt = 0.01
    return vial, product, h_freezing, Tshelf, dt


class TestFreezingFuncs:
    def test_crystallization_time(self, freezing_params):
        vial, product, h_freezing, Tshelf, dt = freezing_params

        def Tshelf_t(t):
            return Tshelf["setpt"][0]

        t_cryst = crystallization_time_FUN(
            vial["Vfill"],
            h_freezing,
            vial["Av"],
            product["Tf"],
            product["Tn"],
            Tshelf_t,
            0.0,
        )
        assert t_cryst > 0
        assert t_cryst < 10

    def test_lumped_cap(self, freezing_params):
        vial, product, h_freezing, Tshelf, dt = freezing_params
        Tpr0 = product["Tpr0"]
        Tsh0 = Tshelf["init"]
        Tsh = Tsh0 - dt * Tshelf["ramp_rate"] * constant.hr_To_min
        newT1 = lumped_cap_Tpr_sol(
            dt,
            Tpr0,
            vial["Vfill"],
            h_freezing,
            vial["Av"],
            Tsh,
            Tsh0,
            Tshelf["ramp_rate"],
        )
        newT2 = lumped_cap_Tpr_ice(
            dt,
            Tpr0,
            vial["Vfill"],
            h_freezing,
            vial["Av"],
            Tsh,
            Tsh0,
            Tshelf["ramp_rate"],
        )
        assert Tpr0 > newT1
        assert Tpr0 > newT2
        assert newT1 > Tsh
        assert newT2 > Tsh


class TestFreezing:
    """Test freezing functionality."""

    def test_freezing_basics(self, freezing_params):
        """Test that freezing
        - runs to completion
        - returns non-empty output
        - has correct output shape
        - has correct initial conditions
        """
        vial, product, h_freezing, Tshelf, dt = freezing_params
        results = freeze(*freezing_params)
        assert results is not None
        assert len(results) > 0

        assert results.shape[1] == 3
        assert np.all(np.isfinite(results))

        assert results[0, 0] == 0.0
        assert results[0, 1] == pytest.approx(Tshelf["init"])
        assert results[0, 2] == pytest.approx(product["Tpr0"])

        max_time = calc_shelfT_time(Tshelf)

        assert results[-1, 0] == pytest.approx(max_time, abs=dt)
        assert results[-1, 1] == pytest.approx(Tshelf["setpt"][-1])
        # Since default setup has long hold, product should approach shelf
        assert results[-1, 2] == pytest.approx(results[-1, 2], abs=0.1)


class TestFreezingEdgeCases:
    """Test freezing edge cases."""

    def test_multiple_setpoints(self, freezing_params):
        vial, product, h_freezing, _, dt = freezing_params
        Tshelf = {
            "init": 5.0,
            "setpt": np.array([-5.0, -7.0, -40.0]),
            "dt_setpt": np.array([60, 60, 600]),
            "ramp_rate": 1.0,
        }

        max_time = calc_shelfT_time(Tshelf)

        results = freeze(vial, product, h_freezing, Tshelf, dt)

        assert results[-1, 0] == pytest.approx(max_time, abs=dt)
        assert results[-1, 1] == pytest.approx(Tshelf["setpt"][-1])
        # Since setup has long hold, product should approach shelf
        assert results[-1, 2] == pytest.approx(Tshelf["setpt"][-1], abs=0.1)

    def test_annealing(self, freezing_params):
        vial, product, h_freezing, _, dt = freezing_params
        Tshelf = {
            "init": 5.0,
            "setpt": np.array([-40.0, -10.0, -40.0]),
            "dt_setpt": np.array([120, 120, 360]),
            "ramp_rate": 1.0,
        }

        max_time = calc_shelfT_time(Tshelf)

        results = freeze(vial, product, h_freezing, Tshelf, dt)

        assert results[-1, 0] == pytest.approx(max_time, abs=dt)
        assert results[-1, 1] == pytest.approx(Tshelf["setpt"][-1])
        # Since setup has long hold, product should approach shelf
        assert results[-1, 2] == pytest.approx(Tshelf["setpt"][-1], abs=0.1)

    def test_no_nucleation(self, freezing_params):
        """Test behavior when nucleation temperature is never reached."""
        vial, product, h_freezing, Tshelf, dt = freezing_params
        product["Tn"] = -50.0  # Set nucleation temp below shelf temp

        with pytest.warns(UserWarning, match="nucleation"):
            results = freeze(vial, product, h_freezing, Tshelf, dt)

        # Should warn and return output ending before nucleation
        assert results[-1, 2] == Tshelf["setpt"][-1]

    def test_incomplete_solidification(self, freezing_params):
        """Test behavior when nucleation temperature is reached, but crystallization is not finished."""
        vial, product, h_freezing, Tshelf, dt = freezing_params
        product["Tn"] = -9.0  # Set nucleation temp near shelf temp
        Tshelf["setpt"] = np.array([-10.0])  # Set shelf temp above nucleation temp
        Tshelf["dt_setpt"] = np.array([60])

        with pytest.warns(UserWarning, match="crystallized"):
            results = freeze(vial, product, h_freezing, Tshelf, dt)

        # Should warn and return output ending before nucleation
        assert results[-1, 2] > product["Tn"]

    def test_freezing_below_nucleation(
        self,
    ):
        """Test [whatever happens if nucleation is immediate]."""
        vial = {"Av": 3.8, "Ap": 3.14, "Vfill": 2.0}
        product = {"Tpr0": -6, "Tf": -1.52, "Tn": -5.84, "cSolid": 0.05}
        h_freezing = 38.0
        Tshelf = {
            "init": -10.0,
            "setpt": np.array([-40.0]),
            "dt_setpt": np.array([1800]),
            "ramp_rate": 1.0,
        }
        dt = 0.01

        freeze(vial, product, h_freezing, Tshelf, dt)


class TestFreezingReference:
    @pytest.fixture
    def freezing_params_ref(self):
        vial = {"Av": 3.8, "Ap": 3.14, "Vfill": 2.0}
        product = {"Tpr0": 15.8, "Tf": -1.54, "Tn": -5.84, "cSolid": 0.05}
        h_freezing = 38.0  # W/m²/K
        Tshelf = {
            "init": 10.0,
            "setpt": np.array([-40.0]),
            "dt_setpt": np.array([180]),
            "ramp_rate": 1.0,
        }
        dt = 0.01
        return vial, product, h_freezing, Tshelf, dt

    def test_freezing_reference(self, repo_root, freezing_params_ref):
        # NOTE: The original version of LyoPRONTO, and therefore the online interface,
        # had several correctness bugs in the freezing implementation. Therefore, reference
        # data was generated directly from this code, unlike other regression tests.
        ref_csv = repo_root / "test_data" / "reference_freezing.csv"
        if not ref_csv.exists():
            pytest.skip(f"Reference CSV not found: {ref_csv}")
        output_ref = np.loadtxt(ref_csv, delimiter=",", skiprows=1)

        output = freeze(*freezing_params_ref)

        array_compare = np.isclose(output, output_ref, rtol=1e-2)
        print(output[~array_compare], output_ref[~array_compare])
        assert array_compare.all(), (
            f"Freezing output does not match reference data, at {np.where(~array_compare)}"
        )
