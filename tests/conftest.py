"""Pytest configuration and shared fixtures for LyoPRONTO tests."""
import pytest
import numpy as np


@pytest.fixture
def standard_vial():
    """Standard vial configuration."""
    return {'Av': 3.80, 'Ap': 3.14, 'Vfill': 2.0}


@pytest.fixture
def small_vial():
    """Small vial configuration."""
    return {'Av': 2.0, 'Ap': 1.5, 'Vfill': 1.0}


@pytest.fixture
def large_vial():
    """Large vial configuration."""
    return {'Av': 5.0, 'Ap': 4.0, 'Vfill': 3.0}


@pytest.fixture
def standard_product():
    """Standard product configuration (5% solids)."""
    return {'cSolid': 0.05, 'R0': 1.4, 'A1': 16.0, 'A2': 0.0, 'T_pr_crit': -25.0}


@pytest.fixture
def dilute_product():
    """Dilute product configuration (1% solids)."""
    return {'cSolid': 0.01, 'R0': 1.0, 'A1': 10.0, 'A2': 0.0, 'T_pr_crit': -25.0}


@pytest.fixture
def concentrated_product():
    """Concentrated product configuration (10% solids)."""
    return {'cSolid': 0.10, 'R0': 2.0, 'A1': 20.0, 'A2': 0.1, 'T_pr_crit': -25.0}


@pytest.fixture
def standard_ht():
    """Standard heat transfer parameters."""
    return {'KC': 2.75e-4, 'KP': 8.93e-4, 'KD': 0.46}


@pytest.fixture
def standard_pchamber():
    """Standard chamber pressure configuration."""
    return {'setpt': [0.15], 'dt_setpt': [1800.0], 'ramp_rate': 0.5}


@pytest.fixture
def standard_tshelf():
    """Standard shelf temperature configuration."""
    return {'init': -35.0, 'setpt': [20.0], 'dt_setpt': [1800.0], 'ramp_rate': 1.0}


@pytest.fixture
def standard_setup(standard_vial, standard_product, standard_ht, 
                   standard_pchamber, standard_tshelf):
    """Complete standard setup for primary drying simulations."""
    return {
        'vial': standard_vial,
        'product': standard_product,
        'ht': standard_ht,
        'Pchamber': standard_pchamber,
        'Tshelf': standard_tshelf,
        'dt': 0.01
    }


def assert_physically_reasonable_output(output):
    """
    Assert that simulation output is physically reasonable.
    
    Args:
        output: numpy array with columns [time, Tsub, Tbot, Tsh, Pch_mTorr, flux, frac_dried]
        
    Column descriptions:
        [0] time (hours)
        [1] Tsub - sublimation temperature [degC]
        [2] Tbot - vial bottom temperature [degC]
        [3] Tsh - shelf temperature [degC]
        [4] Pch - chamber pressure (mTorr, NOT Torr!)
        [5] flux - sublimation flux (kg/hr/m²)
        [6] frac_dried - fraction dried (0-1, NOT percentage!)
    """
    assert output.shape[1] == 7, "Output should have 7 columns"
    
    # Time should be non-negative and monotonically increasing
    assert np.all(output[:, 0] >= 0), "Time should be non-negative"
    assert np.all(np.diff(output[:, 0]) >= 0), "Time should be monotonically increasing"
    
    # Sublimation temperature should be below freezing
    assert np.all(output[:, 1] < 0), "Sublimation temperature should be below 0°C"
    
    # Bottom temperature should be >= sublimation temperature (with small tolerance for numerical errors)
    assert np.all(output[:, 2] >= output[:, 1] - 0.5), \
        "Bottom temp should be >= sublimation temp (within 0.5°C tolerance)"
    
    # Shelf temperature should be reasonable
    assert np.all(output[:, 3] >= -50) and np.all(output[:, 3] <= 50), \
        "Shelf temperature should be between -50 and 50°C"
    
    # Chamber pressure should be positive (in mTorr, so typically 50-500)
    assert np.all(output[:, 4] > 0), "Chamber pressure should be positive"
    assert np.all(output[:, 4] < 1000), "Chamber pressure seems unreasonably high (check units)"
    
    # Sublimation flux should be non-negative
    assert np.all(output[:, 5] >= 0), "Sublimation flux should be non-negative"
    
    # Fraction dried should be between 0 and 1
    assert np.all(output[:, 6] >= 0) and np.all(output[:, 6] <= 1.01), \
        "Fraction dried should be between 0 and 1 (allowing small numerical overshoot)"
    
    # Fraction dried should be monotonically increasing
    assert np.all(np.diff(output[:, 6]) >= -1e-6), \
        "Fraction dried should be monotonically increasing (allowing small numerical errors)"
