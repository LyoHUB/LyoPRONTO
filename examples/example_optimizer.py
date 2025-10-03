"""
Example demonstrating the optimizer functionality of LyoPRONTO.

This example replicates the web interface optimizer with:
- Fixed chamber pressure at 0.15 Torr (150 mTorr)
- Shelf temperature optimization in range -45 to 120°C
- Temperature and pressure ramp rates and hold times
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
from datetime import datetime
from lyopronto import opt_Tsh

def run_optimizer_example():
    """
    Run optimizer example matching web interface parameters.
    
    Web Interface Input:
    - Vial Area: 3.8 cm²
    - Fill Volume: 2 mL
    - Product Area: 3.14 cm²
    - Critical Product Temperature: -5°C
    - Solid Content: 0.05 g/mL
    - Vial Heat Transfer: Kc=0.000275, Kp=0.000893, Kd=0.46
    - Product Resistance: R0=1.4, A1=16, A2=0
    - Initial Shelf Temperature: -35°C
    - Shelf Temperature Ramp Rate: 1°C/min
    - Chamber Pressure Ramp Rate: 0.5 Torr/min
    - Equipment Capability: a=-0.182 kg/hr, b=11.7 kg/hr·Torr
    - Number of Vials: 398
    - Time Step: 0.01 hr
    - Optimization: Shelf Temperature Range -45 to 120°C
    - Temperature Hold Time: 1800 min
    - Fixed Chamber Pressure: 0.15 Torr
    - Pressure Hold Time: 1800 min
    
    Expected Output:
    - Drying time: ~2.123 hr
    - Optimal shelf temperature: ~120°C (ramped from -35°C)
    - Product temperature stays at -5°C limit
    """
    
    # Vial geometry
    vial = {
        'Av': 3.8,     # Vial area in cm^2
        'Ap': 3.14,    # Product area in cm^2
        'Vfill': 2.0   # Fill volume in mL
    }
    
    # Product properties
    product = {
        'T_pr_crit': -5.0,   # Critical product temperature in degC
        'cSolid': 0.05,      # Solid content in g/mL
        'R0': 1.4,           # Product resistance coefficient R0 in cm^2-hr-Torr/g
        'A1': 16.0,          # Product resistance coefficient A1 in 1/cm
        'A2': 0.0            # Product resistance coefficient A2 in 1/cm^2
    }
    
    # Vial heat transfer coefficients
    ht = {
        'KC': 0.000275,   # Kc in cal/s/K/cm^2
        'KP': 0.000893,   # Kp in cal/s/K/cm^2/Torr
        'KD': 0.46        # Kd dimensionless
    }
    
    # Chamber pressure settings
    # Fixed pressure: 0.15 Torr throughout the cycle
    # Ramp rate: 0.5 Torr/min, Hold time: 1800 min
    Pchamber = {
        'setpt': np.array([0.15]),      # Set point in Torr
        'dt_setpt': np.array([1800]),   # Hold time in min
        'ramp_rate': 0.5                # Ramp rate in Torr/min
    }
    
    # Shelf temperature optimization settings
    # Optimization range: -45 to 120°C
    # Initial: -35°C, Ramp rate: 1°C/min, Hold time: 1800 min
    Tshelf = {
        'min': -45.0,                   # Minimum shelf temperature in degC
        'max': 120.0,                   # Maximum shelf temperature in degC
        'init': -35.0,                  # Initial shelf temperature in degC
        'setpt': np.array([120.0]),     # Target set point in degC
        'dt_setpt': np.array([1800]),   # Hold time in min
        'ramp_rate': 1.0                # Ramp rate in degC/min
    }
    
    # Equipment capability
    eq_cap = {
        'a': -0.182,   # Equipment capability coefficient a in kg/hr
        'b': 11.7      # Equipment capability coefficient b in kg/hr/Torr
    }
    
    # Number of vials
    nVial = 398
    
    # Time step
    dt = 0.01   # Time step in hr
    
    print("Running optimizer example...")
    print(f"Vial area: {vial['Av']} cm², Product area: {vial['Ap']} cm²")
    print(f"Fill volume: {vial['Vfill']} mL")
    print(f"Critical temperature: {product['T_pr_crit']} °C")
    print(f"Fixed chamber pressure: {Pchamber['setpt'][0]} Torr ({Pchamber['setpt'][0]*1000} mTorr)")
    print(f"Shelf temperature range: {Tshelf['min']} to {Tshelf['max']} °C")
    print(f"Number of vials: {nVial}")
    
    # Run the optimizer
    results = opt_Tsh.dry(vial, product, ht, Pchamber, Tshelf, dt, eq_cap, nVial)
    
    # Extract results
    time_hr = results[:, 0]
    T_sub = results[:, 1]
    T_bot = results[:, 2]
    T_shelf = results[:, 3]
    P_chamber_mTorr = results[:, 4]
    flux = results[:, 5]
    percent_dried = results[:, 6]
    
    # Print summary
    print(f"\nOptimization complete!")
    print(f"Total drying time: {time_hr[-1]:.3f} hr")
    print(f"Final shelf temperature: {T_shelf[-1]:.2f} °C")
    print(f"Maximum product temperature: {T_bot.max():.2f} °C")
    print(f"Final percent dried: {percent_dried[-1]:.1f}%")
    
    # Save results to CSV
    timestamp = datetime.now().strftime("%b_%d_%Y_%H_%M_%S")
    output_file = f'examples/outputs/lyopronto_optimizer_{timestamp}.csv'
    
    df = pd.DataFrame({
        'Time [hr]': time_hr,
        'Sublimation Temperature [C]': T_sub,
        'Vial Bottom Temperature [C]': T_bot,
        'Shelf Temperature [C]': T_shelf,
        'Chamber Pressure [mTorr]': P_chamber_mTorr,
        'Sublimation Flux [kg/hr/m^2]': flux,
        'Percent Dried': percent_dried
    })
    
    df.to_csv(output_file, index=False, sep=';')
    print(f"\nResults saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    results = run_optimizer_example()
