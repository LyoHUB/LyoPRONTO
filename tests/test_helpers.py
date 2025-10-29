"""Helper functions for test validation."""
import numpy as np


def assert_physically_reasonable_output(output):
    """Assert that simulation output has physically reasonable values.
    
    Args:
        output: Numpy array with shape (n_steps, 7) containing simulation results
                Columns: time, Tsub, Tbot, Tsh, Pch, flux, dried_fraction
    """
    # Column 0: Time should be non-negative and increasing
    assert np.all(output[:, 0] >= 0), "Time should be non-negative"
    assert np.all(np.diff(output[:, 0]) > 0), "Time should be strictly increasing"
    
    # Column 1: Tsub should be below freezing
    assert np.all(output[:, 1] < 0), "Sublimation temperature should be < 0°C"
    assert np.all(output[:, 1] > -80), "Tsub should be > -80°C (reasonable range)"
    
    # Column 2: Tbot should be reasonable
    assert np.all(output[:, 2] > -80), "Tbot should be > -80°C"
    assert np.all(output[:, 2] < 60), "Tbot should be < 60°C"
    
    # Column 3: Tsh (shelf temperature) should be reasonable
    assert np.all(output[:, 3] > -80), "Tsh should be > -80°C"
    assert np.all(output[:, 3] < 60), "Tsh should be < 60°C"
    
    # Column 4: Pch should be positive (in mTorr)
    assert np.all(output[:, 4] > 0), "Chamber pressure should be positive"
    assert np.all(output[:, 4] < 1000), "Pch should be < 1000 mTorr (1.3 Torr)"
    
    # Column 5: Flux should be non-negative
    assert np.all(output[:, 5] >= 0), "Sublimation flux should be non-negative"
    
    # Column 6: Dried fraction should be in [0, 1]
    assert np.all(output[:, 6] >= 0), "Dried fraction should be >= 0"
    assert np.all(output[:, 6] <= 1.0), "Dried fraction should be <= 1"
    
    # Dried fraction should be monotonically increasing
    assert np.all(np.diff(output[:, 6]) >= 0), "Dried fraction should increase over time"
