"""Helper functions for test validation."""
import numpy as np

def assert_physically_reasonable_output(output, Tmax=60):
    """
    Assert that simulation output is physically reasonable.
    
    Args:
        output: numpy array with columns [time, Tsub, Tbot, Tsh, Pch_mTorr, flux, frac_dried]
        
    Column descriptions:
        [0] time [hr]
        [1] Tsub - sublimation temperature [degC]
        [2] Tbot - vial bottom temperature [degC]
        [3] Tsh - shelf temperature [degC]
        [4] Pch - chamber pressure [mTorr]
        [5] flux - sublimation flux [kg/hr/m**2]
        [6] percent_dried - percent dried (0-100%)
    """
    assert output.shape[1] == 7, "Output should have 7 columns"
        
    # Check output columns exist and are numeric
    assert np.all(np.isfinite(output[:, 0])), "Time column has invalid values"
    assert np.all(np.isfinite(output[:, 1])), "Tsub column has invalid values"
    assert np.all(np.isfinite(output[:, 2])), "Tbot column has invalid values"
    assert np.all(np.isfinite(output[:, 3])), "Tsh column has invalid values"
    assert np.all(np.isfinite(output[:, 4])), "Pch column has invalid values"
    assert np.all(np.isfinite(output[:, 5])), "flux column has invalid values"
    assert np.all(np.isfinite(output[:, 6])), "frac_dried column has invalid values"
    
    # Time should be non-negative and monotonically increasing
    assert np.all(output[:, 0] >= 0), "Time should be non-negative"
    assert np.all(np.diff(output[:, 0]) >= 0), "Time should be monotonically increasing"

    # Total time should be reasonable
    assert 0.1 < output[-1, 0] < 200, "Total drying time seems unreasonable"
    
    # Sublimation temperature should be below freezing
    assert np.all(output[:, 1] < 0), "Sublimation temperature should be below 0°C"
    assert np.all(output[:, 1] > -80), "Tsub should be > -80°C (reasonable range)"

    # Sublimation flux should be non-negative
    assert np.all(output[:, 5] >= 0), "Sublimation flux should be non-negative"
    

    # Sublimation temperature should be below shelf temperature 
    assert np.all(output[:, 3] >= output[:, 1]), \
        "Sublimation temp should be <= shelf temp"
    
    # Bottom temperature should be >= sublimation temperature 
    assert np.all(output[:, 2] >= output[:, 1]), \
        "Bottom temp should be >= sublimation temp"
    
    # Shelf temperature should be reasonable
    assert np.all(output[:, 3] >= -80) and np.all(output[:, 3] <= Tmax), \
        f"Shelf temperature should be between -80 and {Tmax}°C"
    
    # Chamber pressure should be positive (in mTorr, so typically 50-500)
    assert np.all(output[:, 4] > 0), "Chamber pressure should be positive"
    assert np.all(output[:, 4] < 2000), "Chamber pressure seems unreasonably high (check units)"
    
    # Percent dried should be between 0 and 100
    assert np.all(output[:, 6] >= 0) and np.all(output[:, 6] <= 101.0), \
        "Percent dried should be between 0 and 100 (allowing small numerical overshoot)"
    
    # Percent dried should be monotonically increasing
    assert np.all(np.diff(output[:, 6]) >= -1e-6), \
        "Percent dried should be monotonically increasing (allowing small numerical errors)"