"""Unit tests for core physics functions in lyopronto.functions."""
import pytest
import numpy as np
import math
from lyopronto import functions, constant


# Test constants for validation thresholds
RELATIVE_VARIATION_THRESHOLD = 0.1  # Maximum relative variation (10%) for consistency checks


class TestVaporPressure:
    """Tests for the Vapor_pressure function."""
    
    def test_vapor_pressure_at_freezing_point(self):
        """Test vapor pressure at 0°C (should be ~4.58 Torr)."""
        P = functions.Vapor_pressure(0.0)
        # Antoine equation at 0°C
        expected = 2.698e10 * np.exp(-6144.96 / 273.15)
        assert np.isclose(P, expected, rtol=1e-6)
        assert np.isclose(P, 4.58, rtol=0.01)  # Literature value
    
    def test_vapor_pressure_monotonic(self):
        """Vapor pressure should increase monotonically with temperature."""
        temps = np.linspace(-40, 20, 10)
        pressures = [functions.Vapor_pressure(T) for T in temps]
        assert all(p1 < p2 for p1, p2 in zip(pressures[:-1], pressures[1:]))
    
    def test_vapor_pressure_positive(self):
        """Vapor pressure should always be positive."""
        temps = np.linspace(-50, 30, 20)
        pressures = [functions.Vapor_pressure(T) for T in temps]
        assert all(p > 0 for p in pressures)
    
    def test_vapor_pressure_at_minus_20C(self):
        """Test vapor pressure at -20°C (should be ~0.776 Torr)."""
        P = functions.Vapor_pressure(-20.0)
        assert np.isclose(P, 0.776, rtol=0.01)
    
    def test_vapor_pressure_at_minus_40C(self):
        """Test vapor pressure at -40°C (should be ~0.096 Torr)."""
        P = functions.Vapor_pressure(-40.0)
        assert np.isclose(P, 0.096, rtol=0.01)


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
        volumes = [1.0, 2.0, 3.0, 4.0]
        heights = [functions.Lpr0_FUN(V, Ap, cSolid) for V in volumes]
        assert all(h1 < h2 for h1, h2 in zip(heights[:-1], heights[1:]))
    
    def test_lpr0_decreases_with_area(self):
        """Fill height should decrease with product area."""
        Vfill = 2.0
        cSolid = 0.05
        areas = [2.0, 3.0, 4.0, 5.0]
        heights = [functions.Lpr0_FUN(Vfill, A, cSolid) for A in areas]
        assert all(h1 > h2 for h1, h2 in zip(heights[:-1], heights[1:]))
    
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
        assert all(r1 <= r2 for r1, r2 in zip(resistances[:-1], resistances[1:]))
    
    def test_rp_with_zero_A1(self):
        """With A1=0, resistance should be constant."""
        R0, A1, A2 = 1.4, 0.0, 0.0
        lengths = np.linspace(0, 1.0, 10)
        resistances = [functions.Rp_FUN(L, R0, A1, A2) for L in lengths]
        assert all(r == R0 for r in resistances)
    
    def test_rp_linear_case(self):
        """With A2=0, resistance should be linear in length."""
        R0, A1, A2 = 1.4, 16.0, 0.0
        L = 0.5
        Rp = functions.Rp_FUN(L, R0, A1, A2)
        expected = R0 + A1 * L
        assert np.isclose(Rp, expected, rtol=1e-6)
    
    def test_rp_positive(self):
        """Product resistance should always be positive."""
        R0, A1, A2 = 1.4, 16.0, 0.1
        lengths = np.linspace(0, 2.0, 20)
        resistances = [functions.Rp_FUN(L, R0, A1, A2) for L in lengths]
        assert all(r > 0 for r in resistances)


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
        kvs = [functions.Kv_FUN(KC, KP, KD, P) for P in pressures]
        assert all(k1 <= k2 for k1, k2 in zip(kvs[:-1], kvs[1:]))
    
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
        kvs = [functions.Kv_FUN(KC, KP, KD, P) for P in pressures]
        assert all(k > 0 for k in kvs)


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
        rates = [functions.sub_rate(Ap, Rp, T, Pch) for T in temps]
        assert all(r1 < r2 for r1, r2 in zip(rates[:-1], rates[1:]))
    
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
    
    def test_pressure_temperature_relationship(self):
        """Test that vapor pressure increases exponentially with temperature."""
        temps = [-40, -30, -20, -10, 0]
        pressures = [functions.Vapor_pressure(T) for T in temps]
        
        # Check that pressure increases by roughly same factor each 10°C
        ratios = [p2/p1 for p1, p2 in zip(pressures[:-1], pressures[1:])]
        
        # Ratios should be consistent (exponential relationship)
        assert np.std(ratios) / np.mean(ratios) < RELATIVE_VARIATION_THRESHOLD, \
            f"Relative variation should be < {RELATIVE_VARIATION_THRESHOLD}"
