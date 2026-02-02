"""Unit tests for core physics functions in lyopronto.functions."""

import pytest
import numpy as np
from lyopronto import functions, constant


class TestVaporPressure:
    """Tests for the Vapor_pressure function."""

    def test_vapor_pressure_at_freezing_point(self):
        """Test vapor pressure at 0°C (should be ~4.58 Torr)."""
        P = functions.Vapor_pressure(0.0)
        # Antoine equation at 0°C
        expected = 2.698e10 * np.exp(-6144.96 / 273.15)
        assert np.isclose(P, expected, rtol=1e-6)
        assert np.isclose(P, 4.58, rtol=0.01)  # Literature value

    def test_vapor_pressure_at_minus_20C(self):
        """Test vapor pressure at -20°C (should be ~0.776 Torr)."""
        P = functions.Vapor_pressure(-20.0)
        assert np.isclose(P, 0.776, rtol=0.01)

    def test_vapor_pressure_at_minus_40C(self):
        """Test vapor pressure at -40°C (should be ~0.096 Torr)."""
        P = functions.Vapor_pressure(-40.0)
        assert np.isclose(P, 0.096, rtol=0.01)

    def test_vapor_pressure_monotonic(self):
        """Vapor pressure should increase monotonically with temperature."""
        temps = np.linspace(-80, 0, 20)
        pressures = functions.Vapor_pressure(temps)
        assert all(np.diff(pressures) > 0)

    def test_vapor_pressure_positive(self):
        """Vapor pressure should always be positive."""
        temps = np.linspace(-80, 0, 20)
        pressures = functions.Vapor_pressure(temps)
        assert all(pressures > 0)


class TestLpr0Function:
    """Tests for the Lpr0_FUN (initial fill height) function."""

    def test_lpr0_standard_case(self):
        """Test initial fill height for standard 2 mL fill."""
        Vfill = 2.0  # mL
        Ap = 3.14  # cm^2
        cSolid = 0.05

        Lpr0 = functions.Lpr0_FUN(Vfill, Ap, cSolid)

        # Should be positive and reasonable (few cm)
        assert Lpr0 > 0
        assert 0.1 < Lpr0 < 10  # Reasonable range for vial height

    def test_lpr0_increases_with_volume(self):
        """Fill height should increase with fill volume."""
        Ap = 3.14
        cSolid = 0.05
        volumes = np.array([1.0, 2.0, 3.0, 4.0])
        heights = functions.Lpr0_FUN(volumes, Ap, cSolid)
        assert all(np.diff(heights) > 0)

    def test_lpr0_decreases_with_area(self):
        """Fill height should decrease with product area."""
        Vfill = 2.0
        cSolid = 0.05
        areas = np.array([2.0, 3.0, 4.0, 5.0])
        heights = functions.Lpr0_FUN(Vfill, areas, cSolid)
        assert all(np.diff(heights) < 0)

    def test_lpr0_pure_water(self):
        """Test with pure water (cSolid=0)."""
        Vfill = 2.0
        Ap = 3.14
        cSolid = 0.0

        Lpr0 = functions.Lpr0_FUN(Vfill, Ap, cSolid)

        # Should equal Vfill / (Ap * rho_ice)
        expected = Vfill / (Ap * constant.rho_ice)
        assert np.isclose(Lpr0, expected, rtol=1e-6)


class TestRpFunction:
    """Tests for the Rp_FUN (product resistance) function."""

    def test_rp_at_zero_length(self):
        """Product resistance at zero cake length should equal R0."""
        R0, A1, A2 = 1.4, 16.0, 0.0
        Rp = functions.Rp_FUN(0.0, R0, A1, A2)
        assert Rp == R0

    def test_rp_increases_with_length(self):
        """Product resistance should increase with cake length."""
        R0, A1, A2 = 1.4, 16.0, 0.1
        lengths = np.linspace(0, 1.0, 10)
        resistances = [functions.Rp_FUN(L, R0, A1, A2) for L in lengths]
        assert all(np.diff(resistances) > 0)

    def test_rp_with_zero_A1(self):
        """With A1=0, resistance should be constant."""
        R0, A1, A2 = 1.4, 0.0, 0.0
        lengths = np.linspace(0, 1.0, 10)
        resistances = functions.Rp_FUN(lengths, R0, A1, A2)
        assert all(resistances == R0)

    def test_rp_linear_case(self):
        """With A2=0, resistance should be linear in length."""
        R0, A1, A2 = 1.4, 16.0, 0.0
        lengths = np.linspace(0, 1.0, 10)
        Rp = functions.Rp_FUN(lengths, R0, A1, A2)
        expected = R0 + A1 * lengths
        assert np.all(np.isclose(Rp, expected, rtol=1e-6))
        assert np.allclose(np.diff(Rp), np.diff(Rp)[0], rtol=1e-6)

    def test_rp_positive(self):
        """Product resistance should always be positive."""
        R0, A1, A2 = 1.4, 16.0, 0.1
        lengths = np.linspace(0, 2.0, 20)
        resistances = functions.Rp_FUN(lengths, R0, A1, A2)
        assert all(resistances > 0)


class TestKvFunction:
    """Tests for the Kv_FUN (vial heat transfer coefficient) function."""

    def test_kv_at_zero_pressure(self):
        """Heat transfer coefficient at zero pressure should equal KC."""
        KC, KP, KD = 2.75e-4, 8.93e-4, 0.46
        Kv = functions.Kv_FUN(KC, KP, KD, 0.0)
        assert np.isclose(Kv, KC, rtol=1e-6)

    def test_kv_increases_with_pressure(self):
        """Heat transfer coefficient should increase with pressure."""
        KC, KP, KD = 2.75e-4, 8.93e-4, 0.46
        pressures = np.linspace(0.01, 1.0, 10)
        kvs = functions.Kv_FUN(KC, KP, KD, pressures)
        assert all(np.diff(kvs) > 0)

    def test_kv_asymptotic_behavior(self):
        """At high pressure, Kv should approach KC + KP/KD."""
        KC, KP, KD = 2.75e-4, 8.93e-4, 0.46
        Kv_high = functions.Kv_FUN(KC, KP, KD, 1000.0)
        expected_limit = KC + KP / KD
        assert np.isclose(Kv_high, expected_limit, rtol=0.01)

    def test_kv_positive(self):
        """Heat transfer coefficient should always be positive."""
        KC, KP, KD = 2.75e-4, 8.93e-4, 0.46
        pressures = np.linspace(0.0, 10.0, 20)
        kvs = functions.Kv_FUN(KC, KP, KD, pressures)
        assert all(kvs > 0)


class TestSubRate:
    """Tests for the sub_rate (sublimation rate) function."""

    def test_sub_rate_positive_driving_force(self):
        """Sublimation rate should be positive when Psub > Pch."""
        Ap = 3.14  # cm^2
        Rp = 1.4  # cm^2-hr-Torr/g
        T_sub = -20.0  # degC
        Pch = 0.1  # Torr

        dmdt = functions.sub_rate(Ap, Rp, T_sub, Pch)

        # Should be positive since Psub(-20°C) ~ 0.776 Torr > 0.1 Torr
        assert dmdt > 0

    def test_sub_rate_zero_driving_force(self):
        """Sublimation rate should be zero when Psub = Pch."""
        Ap = 3.14
        Rp = 1.4
        T_sub = -20.0

        Psub = functions.Vapor_pressure(T_sub)
        dmdt = functions.sub_rate(Ap, Rp, T_sub, Psub)

        assert np.isclose(dmdt, 0.0, atol=1e-10)

    def test_sub_rate_increases_with_temperature(self):
        """Sublimation rate should increase with temperature (fixed Pch)."""
        Ap = 3.14
        Rp = 1.4
        Pch = 0.1
        temps = np.linspace(-40, -10, 10)
        rates = np.array([functions.sub_rate(Ap, Rp, T, Pch) for T in temps])
        assert all(np.diff(rates) > 0)

    def test_sub_rate_proportional_to_area(self):
        """Sublimation rate should be proportional to product area."""
        Rp = 1.4
        T_sub = -20.0
        Pch = 0.1

        dmdt1 = functions.sub_rate(3.14, Rp, T_sub, Pch)
        dmdt2 = functions.sub_rate(6.28, Rp, T_sub, Pch)

        assert np.isclose(dmdt2 / dmdt1, 2.0, rtol=1e-6)

    def test_sub_rate_inversely_proportional_to_rp(self):
        """Sublimation rate should be inversely proportional to Rp."""
        Ap = 3.14
        T_sub = -20.0
        Pch = 0.1

        dmdt1 = functions.sub_rate(Ap, 1.4, T_sub, Pch)
        dmdt2 = functions.sub_rate(Ap, 2.8, T_sub, Pch)

        assert np.isclose(dmdt2 / dmdt1, 0.5, rtol=1e-6)


class TestTBotFunction:
    """Tests for the T_bot_FUN (vial bottom temperature) function."""

    def test_tbot_greater_than_tsub(self):
        """Bottom temperature should be greater than sublimation temperature."""
        T_sub = -20.0
        Lpr0 = 0.7  # cm
        Lck = 0.3  # cm
        Pch = 0.1  # Torr
        Rp = 1.4  # cm^2-hr-Torr/g

        Tbot = functions.T_bot_FUN(T_sub, Lpr0, Lck, Pch, Rp)

        assert Tbot > T_sub

    def test_tbot_equals_tsub_at_full_drying(self):
        """Bottom temp should equal sublimation temp when fully dried."""
        T_sub = -20.0
        Lpr0 = 0.7
        Lck = Lpr0  # Fully dried
        Pch = 0.1
        Rp = 1.4

        Tbot = functions.T_bot_FUN(T_sub, Lpr0, Lck, Pch, Rp)

        assert np.isclose(Tbot, T_sub, rtol=1e-6)

    def test_tbot_increases_with_frozen_thickness(self):
        """Bottom temp should increase as frozen layer gets thicker."""
        T_sub = -20.0
        Lpr0 = 1.0
        Pch = 0.1
        Rp = 1.4

        # As Lck decreases, frozen layer (Lpr0-Lck) increases
        cake_lengths = np.linspace(0.9, 0.1, 10)
        tbots = [functions.T_bot_FUN(T_sub, Lpr0, Lck, Pch, Rp) for Lck in cake_lengths]

        assert all(t1 <= t2 for t1, t2 in zip(tbots[:-1], tbots[1:]))


class TestRpFinder:
    """Tests for the Rp_finder (product resistance from measurements) function."""

    def test_rp_finder_consistency(self):
        """Rp_finder should be consistent with T_bot_FUN."""
        T_sub = -20.0
        Lpr0 = 0.7
        Lck = 0.3
        Pch = 0.1
        Rp_original = 1.4

        # Calculate Tbot from known Rp
        Tbot = functions.T_bot_FUN(T_sub, Lpr0, Lck, Pch, Rp_original)

        # Calculate Rp from Tbot
        Rp_calculated = functions.Rp_finder(T_sub, Lpr0, Lck, Pch, Tbot)

        assert np.isclose(Rp_calculated, Rp_original, rtol=1e-6)

    def test_rp_finder_positive(self):
        """Product resistance should always be positive."""
        T_sub = -20.0
        Lpr0 = 0.7
        Lck = 0.3
        Pch = 0.1
        Tbot = -15.0  # Should be > T_sub

        Rp = functions.Rp_finder(T_sub, Lpr0, Lck, Pch, Tbot)

        assert Rp > 0


class TestPhysicalConsistency:
    """Integration tests for physical consistency across functions."""

    def test_energy_balance_consistency(self):
        """Test that heat and mass transfer are consistent."""
        # Setup
        T_sub = -20.0
        Pch = 0.1
        Ap = 3.14
        Rp = 1.4
        Lpr0 = 0.7
        Lck = 0.3

        # Calculate sublimation rate
        dmdt = functions.sub_rate(Ap, Rp, T_sub, Pch)

        # Calculate heat required for sublimation (cal/s)
        Q_sublimation = dmdt * constant.kg_To_g / constant.hr_To_s * constant.dHs

        # Calculate temperature difference needed
        Tbot = functions.T_bot_FUN(T_sub, Lpr0, Lck, Pch, Rp)

        # Calculate heat conducted through frozen layer (cal/s)
        Q_conduction = constant.k_ice * Ap * (Tbot - T_sub) / (Lpr0 - Lck)

        # These should be equal (energy balance)
        assert np.isclose(Q_sublimation, Q_conduction, rtol=1e-6)


class TestIneqConstraints:
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
        result = functions.Ineq_Constraints(0.080, 0.05, -30.0, -30.0, 5.0, 10.0, 398)
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
        result = functions.Ineq_Constraints(0.080, -0.01, -30.0, -35.0, 5.0, 10.0, 398)
        assert len(result) == 2
        assert isinstance(result[0], (int, float))
        assert isinstance(result[1], (int, float))


def calc_max_time(ramp_dict, ramp_sep=False):
    # max_time = Tshelf["dt_setpt"].sum() / constant.hr_To_min  # Convert minutes to hours
    max_time = 0.0
    for i in range(len(ramp_dict["setpt"])):
        max_time += (
            ramp_dict["dt_setpt"][min(len(ramp_dict["dt_setpt"]) - 1, i)]
            / constant.hr_To_min
        )
    if ramp_sep:
        if "init" in ramp_dict:
            setpts = np.concatenate(([ramp_dict["init"]], ramp_dict["setpt"]))
        else:
            setpts = ramp_dict["setpt"]
        setpt_changes = np.abs(np.diff(setpts))
        max_time += np.sum(setpt_changes) / ramp_dict["ramp_rate"] / constant.hr_To_min
    return max_time


class TestRampInterpolatorSeparateDt:
    """Tests for the RampInterpolator class, with dt_setpt counted separately from ramp time."""

    def test_ramp_interpolator_basic(self):
        """Test basic functionality of RampInterpolator."""
        Tshelf = {
            "init": 20.0,
            "setpt": np.array([-10.0, -40.0]),
            "dt_setpt": np.array([60, 600]),
            "ramp_rate": 1.0,
        }
        ramp = functions.RampInterpolator(Tshelf, count_ramp_against_dt=False)

        np.testing.assert_allclose(
            ramp.times, np.array([0.0, 0.5, 1.5, 2, 12])
        )  # in hours
        np.testing.assert_allclose(
            ramp.values, np.array([20.0, -10.0, -10.0, -40.0, -40.0])
        )
        assert len(ramp.times) == 2 * len(Tshelf["setpt"]) + 1

        # Initial condition
        assert ramp(0.0) == 20.0

        assert calc_max_time(Tshelf, ramp_sep=True) == pytest.approx(ramp.times[-1])

    def test_ramp_interpolator_multisetpt(self):
        """Test RampInterpolator with several setpoints."""
        Tshelf = {
            "init": -40.0,
            "setpt": [-20.0, 0, -10.0, 20.0],
            "dt_setpt": np.array([120, 120, 60, 600]),
            "ramp_rate": 1,
        }
        ramp = functions.RampInterpolator(Tshelf, count_ramp_against_dt=False)

        np.testing.assert_allclose(
            ramp.times, np.array([0, 1/3, 2+1/3, 2+2/3, 4+2/3, 4+5/6, 5+5/6, 6+1/3, 16+1/3])
        )  # in hours
        np.testing.assert_allclose(
            ramp.values, np.array([-40, -20.0, -20.0, 0, 0, -10.0, -10.0, 20.0, 20.0])
        )
        assert len(ramp.times) == 2 * len(Tshelf["setpt"]) + 1

        assert calc_max_time(Tshelf, ramp_sep=True) == pytest.approx(ramp.times[-1])

    def test_ramp_interpolator_noinit(self):
        """Test basic functionality of RampInterpolator."""
        Pchamber = {
            "setpt": [0.1],
            "dt_setpt": [60],
            "ramp_rate": 1.0,
        }
        ramp = functions.RampInterpolator(Pchamber, count_ramp_against_dt=False)
        assert len(ramp.times) == 2 * len(Pchamber["setpt"])

        assert ramp(0.0) == Pchamber["setpt"][0]
        assert ramp(-100.0) == Pchamber["setpt"][0]
        assert ramp(100.0) == Pchamber["setpt"][0]
        assert calc_max_time(Pchamber, ramp_sep=True) == pytest.approx(ramp.times[-1])

    def test_ramp_interpolator_samesetpt(self):
        """Test basic functionality of RampInterpolator."""
        Pchamber = {
            "setpt": [0.1, 0.1],
            "dt_setpt": [60],
            "ramp_rate": 1.0,
        }
        ramp = functions.RampInterpolator(Pchamber, count_ramp_against_dt=False)
        assert len(ramp.times) == 2 * len(Pchamber["setpt"])

        # Return constant value for all time
        assert ramp(0.0) == Pchamber["setpt"][0]
        assert ramp(-100.0) == Pchamber["setpt"][0]
        assert ramp(100.0) == Pchamber["setpt"][0]
        assert calc_max_time(Pchamber, ramp_sep=True) == pytest.approx(ramp.times[-1])

    def test_ramp_interpolator_twosetptnoinit(self):
        """Test basic functionality of RampInterpolator."""
        Pchamber = {
            "setpt": [0.1, 0.5],
            "dt_setpt": [60],
            "ramp_rate": 0.4/60,
        }
        ramp = functions.RampInterpolator(Pchamber, count_ramp_against_dt=False)

        assert len(ramp.times) == 2 * len(Pchamber["setpt"])
        print(ramp.times)
        assert np.isclose(np.diff(ramp.times)[0::2], 1.0).all()

        assert ramp(0.0) == Pchamber["setpt"][0]
        assert ramp(1.0) == Pchamber["setpt"][0]
        assert ramp(1.5) == pytest.approx((Pchamber["setpt"][0] + Pchamber["setpt"][1]) / 2)
        assert ramp(2.0) == Pchamber["setpt"][1]
        assert ramp(3.0) == Pchamber["setpt"][1]

        assert ramp(-100.0) == Pchamber["setpt"][0]
        assert ramp(100.0) == Pchamber["setpt"][-1]
        assert calc_max_time(Pchamber, ramp_sep=True) == pytest.approx(ramp.times[-1])

    def test_ramp_interpolator_out_of_bounds(self):
        """Test RampInterpolator behavior outside defined time range."""
        Tshelf = {
            "init": 5.0,
            "setpt": np.array([-5.0, -40.0]),
            "dt_setpt": np.array([60, 600]),
            "ramp_rate": 1.0,
        }
        ramp = functions.RampInterpolator(Tshelf, count_ramp_against_dt=False)

        # Before start
        assert ramp(-10.0) == 5.0

        # After end
        assert ramp(1000) == -40.0

class TestRampInterpolatorCombinedDt:
    """Tests for the RampInterpolator class, with ramp time counted against dt_setpt."""

    def test_ramp_interpolator_basic(self):
        """Test basic functionality of RampInterpolator."""
        Tshelf = {
            "init": 20.0,
            "setpt": np.array([-10.0, -40.0]),
            "dt_setpt": np.array([60, 600]),
            "ramp_rate": 1.0,
        }
        ramp = functions.RampInterpolator(Tshelf, count_ramp_against_dt=True)

        np.testing.assert_allclose(
            ramp.times, np.array([0.0, 0.5, 1.0, 1.5, 11])
        )  # in hours
        np.testing.assert_allclose(
            ramp.values, np.array([20.0, -10.0, -10.0, -40.0, -40.0])
        )
        assert len(ramp.times) == 2 * len(Tshelf["setpt"]) + 1

        # Initial condition
        assert ramp(0.0) == 20.0

        assert calc_max_time(Tshelf) == pytest.approx(ramp.times[-1])

    def test_ramp_interpolator_multisetpt(self):
        """Test RampInterpolator with several setpoints."""
        Tshelf = {
            "init": -40.0,
            "setpt": [-20.0, 0, -10.0, 20.0],
            "dt_setpt": np.array([120, 120, 60, 600]),
            "ramp_rate": 1,
        }
        ramp = functions.RampInterpolator(Tshelf, count_ramp_against_dt=True)

        np.testing.assert_allclose(
            ramp.times, np.array([0, 1/3, 2, 2+1/3, 4, 4+1/6, 5, 5.5, 15])
        )  # in hours
        np.testing.assert_allclose(
            ramp.values, np.array([-40, -20.0, -20.0, 0, 0, -10.0, -10.0, 20.0, 20.0])
        )
        assert len(ramp.times) == 2 * len(Tshelf["setpt"]) + 1

        assert calc_max_time(Tshelf) == pytest.approx(ramp.times[-1])

    def test_ramp_interpolator_noinit(self):
        """Test basic functionality of RampInterpolator."""
        Pchamber = {
            "setpt": [0.1],
            "dt_setpt": [60],
            "ramp_rate": 1.0,
        }
        ramp = functions.RampInterpolator(Pchamber, count_ramp_against_dt=True)
        assert len(ramp.times) == 2 * len(Pchamber["setpt"])

        assert ramp(0.0) == Pchamber["setpt"][0]
        assert ramp(-100.0) == Pchamber["setpt"][0]
        assert ramp(100.0) == Pchamber["setpt"][0]
        assert calc_max_time(Pchamber) == pytest.approx(ramp.times[-1])

    def test_ramp_interpolator_samesetpt(self):
        """Test basic functionality of RampInterpolator."""
        Pchamber = {
            "setpt": [0.1, 0.1],
            "dt_setpt": [60],
            "ramp_rate": 1.0,
        }
        ramp = functions.RampInterpolator(Pchamber, count_ramp_against_dt=True)
        assert len(ramp.times) == 2 * len(Pchamber["setpt"])

        # Return constant value for all time
        assert ramp(0.0) == Pchamber["setpt"][0]
        assert ramp(-100.0) == Pchamber["setpt"][0]
        assert ramp(100.0) == Pchamber["setpt"][0]
        assert calc_max_time(Pchamber) == pytest.approx(ramp.times[-1])

    def test_ramp_interpolator_twosetptnoinit(self):
        """Test basic functionality of RampInterpolator."""
        Pchamber = {
            "setpt": [0.1, 0.5],
            "dt_setpt": [60],
            "ramp_rate": 0.4/30,
        }
        ramp = functions.RampInterpolator(Pchamber, count_ramp_against_dt=True)

        assert len(ramp.times) == 2 * len(Pchamber["setpt"])
        np.testing.assert_allclose(np.diff(ramp.times)[0::2], [1.0, 0.5])

        assert ramp(0.0) == Pchamber["setpt"][0]
        assert ramp(1.0) == Pchamber["setpt"][0]
        assert ramp(1.25) == pytest.approx((Pchamber["setpt"][0] + Pchamber["setpt"][1]) / 2)
        assert ramp(1.5) == Pchamber["setpt"][1]
        assert ramp(2.0) == Pchamber["setpt"][1]

        assert ramp(-100.0) == Pchamber["setpt"][0]
        assert ramp(100.0) == Pchamber["setpt"][-1]
        assert calc_max_time(Pchamber) == pytest.approx(ramp.times[-1])

    def test_ramp_interpolator_insufficient_dt(self):
        """Test RampInterpolator raises error if dt_setpt too small for ramp_rate."""
        Tshelf = {
            "init": 20.0,
            "setpt": np.array([-10.0, -40.0]),
            "dt_setpt": np.array([10, 10]),  # Too small for ramp_rate=1.0
            "ramp_rate": 0.01,
        }
        with pytest.warns(UserWarning, match="Ramp"):
            functions.RampInterpolator(Tshelf, count_ramp_against_dt=True)

    def test_ramp_interpolator_out_of_bounds(self):
        """Test RampInterpolator behavior outside defined time range."""
        Tshelf = {
            "init": 5.0,
            "setpt": np.array([-5.0, -40.0]),
            "dt_setpt": np.array([60, 600]),
            "ramp_rate": 1.0,
        }
        ramp = functions.RampInterpolator(Tshelf)

        # Before start
        assert ramp(-10.0) == 5.0

        # After end
        assert ramp(1000) == -40.0