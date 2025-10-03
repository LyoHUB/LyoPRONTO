"""Tests for LyoPRONTO freezing functionality."""

import pytest
import numpy as np
import pandas as pd
from lyopronto import freezing


class TestFreezingWebInterface:
    """Test freezing functionality matching web interface examples."""
    
    @pytest.fixture
    def freezing_params(self):
        vial = {'Av': 3.8, 'Ap': 3.14, 'Vfill': 2.0}
        product = {'Tpr0': 15.8, 'Tf': -1.52, 'Tn': -5.84, 'cSolid': 0.05}
        h_freezing = 38.0 / 4.184 / 10000
        Tshelf = {
            'init': -35.0,
            'setpt': np.array([20.0]),
            'dt_setpt': np.array([1800]),
            'ramp_rate': 1.0
        }
        dt = 0.01
        return vial, product, h_freezing, Tshelf, dt
    
    def test_freezing_completes(self, freezing_params):
        """Test that freezing simulation runs to completion."""
        vial, product, h_freezing, Tshelf, dt = freezing_params
        results = freezing.freeze(vial, product, h_freezing, Tshelf, dt)
        assert results is not None
        assert len(results) > 0
    
    def test_freezing_output_shape(self, freezing_params):
        """Test that freezing output has correct shape."""
        vial, product, h_freezing, Tshelf, dt = freezing_params
        results = freezing.freeze(vial, product, h_freezing, Tshelf, dt)
        assert results.shape[1] == 3
        assert np.all(np.isfinite(results))
    
    def test_freezing_initial_conditions(self, freezing_params):
        """Test that freezing starts with correct initial conditions."""
        vial, product, h_freezing, Tshelf, dt = freezing_params
        results = freezing.freeze(vial, product, h_freezing, Tshelf, dt)
        assert results[0, 0] == 0.0
        assert abs(results[0, 1] - Tshelf['init']) < 0.1
        assert abs(results[0, 2] - product['Tpr0']) < 0.1
