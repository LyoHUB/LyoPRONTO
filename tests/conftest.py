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

@pytest.fixture
def unpack_standard_setup(standard_setup):
    """Unpack standard setup into individual components."""
    return (standard_setup['vial'], standard_setup['product'], 
            standard_setup['ht'], standard_setup['Pchamber'], 
            standard_setup['Tshelf'], standard_setup['dt'])
