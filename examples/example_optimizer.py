#!/usr/bin/env python
"""
Example: Optimizer for Primary Drying

This example demonstrates using the LyoPRONTO optimizers to find
optimal chamber pressure and shelf temperature trajectories.
"""

import numpy as np
from lyopronto import opt_Pch_Tsh


def run_optimizer_example():
    """Run a simple optimizer example.
    
    Returns:
        np.ndarray: Optimization results (time, Tsub, Tbot, Tsh, Pch, flux, frac_dried)
    """
    # Standard vial configuration
    vial = {
        'Av': 3.8,      # Vial area [cm**2]
        'Ap': 3.14,     # Product area [cm**2]
        'Vfill': 2.0,   # Fill volume [mL]
    }
    
    # Standard product configuration
    product = {
        'cSolid': 0.05,      # Solid content [g/mL]
        'R0': 1.4,           # Base resistance [cm**2*hr*Torr/g]
        'A1': 16.0,          # Resistance parameter A1
        'A2': 0.0,           # Resistance parameter A2
        'T_pr_crit': -25.0   # Critical product temperature [degC]
    }
    
    # Heat transfer parameters
    ht = {
        'KC': 2.75e-4,   # Contact coefficient [cal/s/K/cm**2]
        'KP': 8.93e-4,   # Gas conductance coefficient
        'KD': 0.46,      # Frozen layer thickness coefficient
    }
    
    # Optimization bounds
    Pchamber = {
        'min': 0.040,    # Minimum chamber pressure [Torr]
        'max': 0.200,    # Maximum chamber pressure [Torr]
    }
    
    Tshelf = {
        'min': -45.0,    # Minimum shelf temperature [degC]
        'max': -5.0,     # Maximum shelf temperature [degC]
    }
    
    # Simulation parameters
    dt = 0.01  # Time step [hr]
    eq_cap = {'a': 5.0, 'b': 10.0}  # Equipment capability
    nVial = 398  # Number of vials
    
    # Run joint optimization
    output = opt_Pch_Tsh.dry(
        vial, product, ht,
        Pchamber, Tshelf,
        dt, eq_cap, nVial
    )
    
    return output


if __name__ == '__main__':
    results = run_optimizer_example()
    print(f"Optimization complete!")
    print(f"Final time: {results[-1, 0]:.2f} hours")
    print(f"Final fraction dried: {results[-1, 6]:.4f}")
