"""
Example demonstrating the freezing functionality of LyoPRONTO.

This example replicates the web interface freezing calculator with:
- Initial product temperature: 15.8°C
- Initial shelf temperature: -35°C
- Shelf temperature ramp rate: 1°C/min
- Target shelf temperature: -20°C with 1800 min hold
- Freezing temperature: -1.52°C
- Nucleation temperature: -5.84°C
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
from datetime import datetime
from lyopronto import freezing

def run_freezing_example():
    """
    Run freezing example matching web interface parameters.
    
    Web Interface Input:
    - Vial Area: 3.8 cm²
    - Fill Volume: 2 mL
    - Product Area: 3.14 cm²
    - Critical Product Temperature: -5°C
    - Freezing Temperature: -1.52°C
    - Nucleation Temperature: -5.84°C
    - Solid Content: 0.05 g/mL
    - Initial Product Temperature: 15.8°C
    - Initial Shelf Temperature: -35°C
    - Shelf Temperature Ramp Rate: 1°C/min
    - Heat Transfer Coefficient: 38 W/m²·K
    - Number of Vials: 398
    - Time Step: 0.01 hr
    - Shelf Temperature: -2°C with 1800 min hold
    
    Expected Output:
    - Cooling phase: Product cools from 15.8°C to nucleation (-5.84°C)
    - Nucleation: Instantaneous drop to freezing point (-1.52°C)
    - Crystallization: Product at freezing point during phase change
    - Solidification: Product cools to final shelf temperature (-2°C)
    - Total time: ~6.09 hr
    """
    
    # Vial geometry
    vial = {
        'Av': 3.8,     # Vial area [cm**2]
        'Ap': 3.14,    # Product area [cm**2]
        'Vfill': 2.0   # Fill volume [mL]
    }
    
    # Product properties
    product = {
        'Tpr0': 15.8,      # Initial product temperature [degC]
        'Tf': -1.52,       # Freezing temperature [degC]
        'Tn': -5.84,       # Nucleation temperature [degC]
        'cSolid': 0.05     # Solid content in g/mL
    }
    
    # Heat transfer coefficient
    # Convert from W/m²·K to cal/s/K/cm²
    # 38 W/m²·K = 38 J/s/m²/K = 38/4.184 cal/s/m²/K = 38/4.184/10000 cal/s/cm²/K
    h_freezing = 38.0 / 4.184 / 10000  # cal/s/K/cm²
    
    # Shelf temperature settings
    # Initial: -35°C, ramp at 1°C/min to 20°C setpoint
    # Simulation completes when product fully frozen (holds at ~30 hr)
    Tshelf = {
        'init': -35.0,                   # Initial shelf temperature [degC]
        'setpt': np.array([20.0]),       # Target shelf temperature [degC]
        'dt_setpt': np.array([1800]),    # Hold time at setpoint [min] (30 hours)
        'ramp_rate': 1.0                 # Ramp rate [degC]/min
    }
    
    # Time step
    dt = 0.01   # Time step in hr
    
    print("Running freezing example...")
    print(f"Vial area: {vial['Av']} cm², Product area: {vial['Ap']} cm²")
    print(f"Fill volume: {vial['Vfill']} mL")
    print(f"Initial product temperature: {product['Tpr0']} °C")
    print(f"Initial shelf temperature: {Tshelf['init']} °C")
    print(f"Freezing temperature: {product['Tf']} °C")
    print(f"Nucleation temperature: {product['Tn']} °C")
    print(f"Target shelf temperature: {Tshelf['setpt'][0]} °C")
    print(f"Ramp rate: {Tshelf['ramp_rate']} °C/min")
    
    # Run the freezing simulation
    results = freezing.freeze(vial, product, h_freezing, Tshelf, dt)
    
    # Extract results
    time_hr = results[:, 0]
    T_shelf = results[:, 1]
    T_product = results[:, 2]
    
    # Find key events
    # Nucleation: first occurrence of Tn
    nucleation_idx = np.where(np.abs(T_product - product['Tn']) < 0.1)[0]
    if nucleation_idx.size > 0:
        t_nucleation = time_hr[nucleation_idx[0]]
        print(f"\nNucleation occurs at t = {t_nucleation:.3f} hr")
    
    # Crystallization phase: product at freezing temperature
    crystallization_idx = np.where(np.abs(T_product - product['Tf']) < 0.01)[0]
    if crystallization_idx.size > 1:
        t_crystallization_start = time_hr[crystallization_idx[0]]
        t_crystallization_end = time_hr[crystallization_idx[-1]]
        crystallization_time = t_crystallization_end - t_crystallization_start
        print(f"Crystallization from t = {t_crystallization_start:.3f} to {t_crystallization_end:.3f} hr")
        print(f"Crystallization duration: {crystallization_time:.3f} hr")
    
    # Final state
    print(f"\nTotal freezing time: {time_hr[-1]:.2f} hr")
    print(f"Final shelf temperature: {T_shelf[-1]:.2f} °C")
    print(f"Final product temperature: {T_product[-1]:.2f} °C")
    
    # Save results to CSV
    timestamp = datetime.now().strftime("%b_%d_%Y_%H_%M_%S")
    output_file = f'examples/outputs/lyopronto_freezing_{timestamp}.csv'
    
    df = pd.DataFrame({
        'Time [hr]': time_hr,
        'Shelf Temperature [C]': T_shelf,
        'Product Temperature [C]': T_product
    })
    
    df.to_csv(output_file, index=False, sep=';')
    print(f"\nResults saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    results = run_freezing_example()
