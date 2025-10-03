#!/usr/bin/env python
"""
Example: Replicating LyoPRONTO Web Interface Calculation

This example replicates the primary drying calculation from the LyoPRONTO web interface.
It demonstrates how to:
1. Load vial bottom temperature from a file
2. Set up vial and product parameters matching the web interface
3. Run primary drying simulation with known product resistance
4. Save results to CSV format
5. Compare with web interface output

Based on the web interface inputs from the screenshot:
- Vial Area: 3.8 cm²
- Fill Volume: 2 mL
- Product Area: 3.14 cm²
- Critical Product Temperature: -5°C
- Solid Content: 0.05 g/mL
- Known Product Resistance: R₀=1.4, A₁=16, A₂=0
- Known Vial Heat Transfer: Kc=0.000275, Kp=0.000893, Kd=0.46
- Initial Shelf Temperature: -35°C
- Shelf Temperature Ramp Rate: 1°C/min
- Chamber Pressure: 0.15 Torr
- Chamber Pressure Ramp Rate: 0.5 Torr/min
- Number of Vials: 398
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from lyopronto import calc_knownRp

# ============================================================================
# INPUTS (matching web interface screenshot)
# ============================================================================

# Vial and fill properties
vial = {
    'Av': 3.8,      # Vial area (cm²)
    'Ap': 3.14,     # Product area (cm²)
    'Vfill': 2.0,   # Fill volume (mL)
}

# Product properties
product = {
    'R0': 1.4,           # Base resistance (cm²-hr-Torr/g)
    'A1': 16.0,          # Resistance parameter A1 (cm-hr-Torr/g)
    'A2': 0.0,           # Resistance parameter A2 (1/cm)
    'cSolid': 0.05,      # Solid content (g/mL) - note: API uses 'cSolid' not 'rho_solid'
}

# Critical product temperature
T_pr_crit = -5.0  # °C (at least 2-3°C below collapse/Tg)

# Vial heat transfer parameters
ht = {
    'KC': 0.000275,  # Base heat transfer coefficient
    'KP': 0.000893,  # Pressure-dependent term
    'KD': 0.46,      # Distance-dependent term
}

# Process conditions
Pch = 0.15  # Chamber pressure (Torr)
Tsh = 20.0  # Final shelf temperature (°C)

# Initial conditions
T_init = -35.0  # Initial shelf temperature (°C)

# Ramp rates
shelf_ramp_rate = 1.0  # °C/min
pressure_ramp_rate = 0.5  # Torr/min

# Equipment capability
equipment_capability = {
    'a': -0.182,  # kg/hr
    'b': 11.7,    # kg/hr/Torr
}

# Number of vials
n_vials = 398

# Time parameters
dt = 0.01  # Time step (hr)

# ============================================================================
# LOAD VIAL BOTTOM TEMPERATURE PROFILE (if available)
# ============================================================================

def load_temperature_profile(filepath='test_data/temperature.txt'):
    """
    Load vial bottom temperature profile from file.
    
    Expected format: tab-separated values
    Column 1: Time (hr)
    Column 2: Temperature (°C)
    
    Args:
        filepath (str): Path to temperature file (relative to repo root)
        
    Returns:
        np.ndarray: Array with columns [time, temperature]
    """
    try:
        data = np.loadtxt(filepath)
        print(f"✓ Loaded temperature profile from {filepath}")
        print(f"  Time range: {data[0, 0]:.2f} to {data[-1, 0]:.2f} hr")
        print(f"  Temperature range: {data[:, 1].min():.2f} to {data[:, 1].max():.2f} °C")
        return data
    except FileNotFoundError:
        print(f"✗ Temperature file not found: {filepath}")
        print("  Proceeding with standard simulation (no temperature constraint)")
        return None

# ============================================================================
# RUN SIMULATION
# ============================================================================

def run_primary_drying_simulation():
    """
    Run primary drying simulation with parameters from web interface.
    
    Returns:
        np.ndarray: Simulation output array (n_timesteps, 7)
    """
    print("\n" + "="*70)
    print("LyoPRONTO Primary Drying Simulation")
    print("Replicating Web Interface Calculation")
    print("="*70)
    
    # Display input parameters
    print("\n📋 INPUT PARAMETERS:")
    print(f"\nVial Geometry:")
    print(f"  Vial Area (Av):    {vial['Av']:.2f} cm²")
    print(f"  Product Area (Ap): {vial['Ap']:.2f} cm²")
    print(f"  Fill Volume:       {vial['Vfill']:.2f} mL")
    
    print(f"\nProduct Properties:")
    print(f"  R₀:                {product['R0']:.1f} cm²-hr-Torr/g")
    print(f"  A₁:                {product['A1']:.1f} cm-hr-Torr/g")
    print(f"  A₂:                {product['A2']:.1f} 1/cm")
    print(f"  Solid Content:     {product['cSolid']:.2f} g/mL")
    print(f"  Critical Temp:     {T_pr_crit:.1f} °C")
    
    print(f"\nHeat Transfer:")
    print(f"  Kc:                {ht['KC']:.6f} cal/s/K/cm²")
    print(f"  Kp:                {ht['KP']:.6f} cal/s/K/cm²/Torr")
    print(f"  Kd:                {ht['KD']:.2f}")
    
    print(f"\nProcess Conditions:")
    print(f"  Chamber Pressure:  {Pch:.2f} Torr ({Pch*1000:.0f} mTorr)")
    print(f"  Shelf Temperature: {T_init:.1f} → {Tsh:.1f} °C")
    print(f"  Ramp Rate:         {shelf_ramp_rate:.1f} °C/min")
    
    print(f"\nEquipment:")
    print(f"  Number of Vials:   {n_vials}")
    print(f"  Capability:        dm/dt = {equipment_capability['a']:.3f} + {equipment_capability['b']:.1f}*Pch")
    
    # Load temperature profile if available
    temp_profile = load_temperature_profile()
    
    # Prepare Pchamber dictionary
    Pchamber = {
        'setpt': [Pch],
        'dt_setpt': [1800.0],  # 1800 minutes hold time
        'ramp_rate': pressure_ramp_rate
    }
    
    # Prepare Tshelf dictionary
    Tshelf = {
        'init': T_init,
        'setpt': [Tsh],
        'dt_setpt': [1800.0],  # 1800 minutes hold time
        'ramp_rate': shelf_ramp_rate
    }
    
    # Run simulation
    print("\n🔄 Running simulation...")
    print(f"  Time step: {dt} hr")
    
    output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
    
    # Extract final results
    drying_time = output[-1, 0]
    final_temp = output[-1, 1]
    max_temp = output[:, 1].max()
    avg_flux = output[:, 5].mean()
    max_flux = output[:, 5].max()
    
    print(f"✓ Simulation complete!")
    print(f"\n📊 RESULTS:")
    print(f"  Drying Time:       {drying_time:.2f} hr")
    print(f"  Max Product Temp:  {max_temp:.2f} °C")
    print(f"  Final Temp:        {final_temp:.2f} °C")
    print(f"  Avg Flux:          {avg_flux:.4f} kg/hr/m²")
    print(f"  Max Flux:          {max_flux:.4f} kg/hr/m²")
    
    # Check temperature constraint
    if max_temp <= T_pr_crit:
        print(f"  ✓ Temperature constraint satisfied ({max_temp:.2f} ≤ {T_pr_crit:.2f} °C)")
    else:
        print(f"  ✗ Temperature constraint VIOLATED ({max_temp:.2f} > {T_pr_crit:.2f} °C)")
    
    return output

# ============================================================================
# SAVE RESULTS
# ============================================================================

def save_results_to_csv(output, filename=None):
    """
    Save simulation results to CSV file in web interface format.
    
    Args:
        output (np.ndarray): Simulation output array
        filename (str): Output filename (default: auto-generated with timestamp)
    """
    if filename is None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%b_%d_%Y_%H_%M_%S")
        filename = f"lyopronto_primary_drying_{timestamp}.csv"
    
    # Create DataFrame with proper column names (matching web interface)
    df = pd.DataFrame({
        'Time [hr]': output[:, 0],
        'Sublimation Temperature [C]': output[:, 1],
        'Vial Bottom Temperature [C]': output[:, 2],
        'Shelf Temperature [C]': output[:, 3],
        'Chamber Pressure [mTorr]': output[:, 4],  # Already in mTorr
        'Sublimation Flux [kg/hr/m^2]': output[:, 5],
        'Percent Dried': output[:, 6] * 100,  # Convert fraction to percentage
    })
    
    # Save with semicolon delimiter (matching web interface format)
    df.to_csv(filename, sep=';', index=False)
    print(f"\n💾 Results saved to: {filename}")
    print(f"   Format: CSV with semicolon delimiter")
    print(f"   Rows: {len(df)}")

# ============================================================================
# PLOT RESULTS
# ============================================================================

def plot_results(output, save_fig=True):
    """
    Create plots of simulation results.
    
    Args:
        output (np.ndarray): Simulation output array
        save_fig (bool): Whether to save figure to file
    """
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    fig.suptitle('LyoPRONTO Primary Drying Simulation Results', fontsize=14, fontweight='bold')
    
    time = output[:, 0]
    Tsub = output[:, 1]
    Tbot = output[:, 2]
    Tsh = output[:, 3]
    Pch = output[:, 4]
    flux = output[:, 5]
    percent_dried = output[:, 6] * 100  # Convert to percentage
    
    # Temperature profile
    axes[0, 0].plot(time, Tsub, 'b-', label='Sublimation Front', linewidth=2)
    axes[0, 0].plot(time, Tbot, 'r--', label='Vial Bottom', linewidth=2)
    axes[0, 0].axhline(T_pr_crit, color='k', linestyle=':', label='Critical Temp', linewidth=1)
    axes[0, 0].set_xlabel('Time (hr)')
    axes[0, 0].set_ylabel('Temperature (°C)')
    axes[0, 0].set_title('Temperature Profile')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Sublimation flux
    axes[0, 1].plot(time, flux, 'g-', linewidth=2)
    axes[0, 1].set_xlabel('Time (hr)')
    axes[0, 1].set_ylabel('Sublimation Flux (kg/hr/m²)')
    axes[0, 1].set_title('Sublimation Flux (Non-Monotonic)')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Drying progress
    axes[0, 2].plot(time, percent_dried, 'm-', linewidth=2)
    axes[0, 2].set_xlabel('Time (hr)')
    axes[0, 2].set_ylabel('% Dried')
    axes[0, 2].set_title('Drying Progress')
    axes[0, 2].set_ylim([0, 105])
    axes[0, 2].grid(True, alpha=0.3)
    
    # Chamber pressure (convert mTorr to Torr for display)
    axes[1, 0].plot(time, Pch / 1000, 'c-', linewidth=2)
    axes[1, 0].set_xlabel('Time (hr)')
    axes[1, 0].set_ylabel('Chamber Pressure (Torr)')
    axes[1, 0].set_title('Chamber Pressure')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Shelf temperature
    axes[1, 1].plot(time, Tsh, 'orange', linewidth=2)
    axes[1, 1].set_xlabel('Time (hr)')
    axes[1, 1].set_ylabel('Shelf Temperature (°C)')
    axes[1, 1].set_title('Shelf Temperature Ramp')
    axes[1, 1].grid(True, alpha=0.3)
    
    # Temperature difference (driving force for heat transfer)
    temp_diff = Tsh - Tbot
    axes[1, 2].plot(time, temp_diff, 'brown', linewidth=2)
    axes[1, 2].set_xlabel('Time (hr)')
    axes[1, 2].set_ylabel('Temperature Difference (°C)')
    axes[1, 2].set_title('Tsh - Tbot (Heat Transfer Driving Force)')
    axes[1, 2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_fig:
        figname = 'primary_drying_results.png'
        plt.savefig(figname, dpi=300, bbox_inches='tight')
        print(f"📊 Plots saved to: {figname}")
    
    plt.show()

# ============================================================================
# COMPARISON WITH WEB INTERFACE OUTPUT
# ============================================================================

def compare_with_web_output(output, web_csv='test_data/reference_primary_drying.csv'):
    """
    Compare simulation results with web interface output.
    
    Args:
        output (np.ndarray): Current simulation output
        web_csv (str): Path to web interface CSV output
    """
    try:
        # Load web interface output
        df_web = pd.read_csv(web_csv, sep=';')
        
        print("\n" + "="*70)
        print("COMPARISON WITH WEB INTERFACE OUTPUT")
        print("="*70)
        
        # Compare key metrics
        web_time = df_web['Time [hr]'].iloc[-1]
        sim_time = output[-1, 0]
        
        web_final_dried = df_web['Percent Dried'].iloc[-1]
        sim_final_dried = output[-1, 6] * 100
        
        web_max_temp = df_web['Sublimation Temperature [C]'].max()
        sim_max_temp = output[:, 1].max()
        
        print(f"\n📐 Drying Time:")
        print(f"  Web Interface:  {web_time:.2f} hr")
        print(f"  This Simulation: {sim_time:.2f} hr")
        print(f"  Difference:      {abs(web_time - sim_time):.2f} hr ({abs(web_time - sim_time)/web_time*100:.1f}%)")
        
        print(f"\n📐 Final % Dried:")
        print(f"  Web Interface:   {web_final_dried:.2f}%")
        print(f"  This Simulation: {sim_final_dried:.2f}%")
        
        print(f"\n📐 Max Product Temperature:")
        print(f"  Web Interface:   {web_max_temp:.2f} °C")
        print(f"  This Simulation: {sim_max_temp:.2f} °C")
        print(f"  Difference:      {abs(web_max_temp - sim_max_temp):.2f} °C")
        
        # Overall assessment
        time_match = abs(web_time - sim_time) / web_time < 0.05  # Within 5%
        temp_match = abs(web_max_temp - sim_max_temp) < 1.0  # Within 1°C
        
        print(f"\n✅ Assessment:")
        if time_match and temp_match:
            print(f"  ✓ Results match web interface within acceptable tolerance")
        else:
            print(f"  ⚠ Some differences detected - check input parameters")
        
    except FileNotFoundError:
        print(f"\n⚠ Web interface output file not found: {web_csv}")
        print("  Skipping comparison")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Run simulation
    output = run_primary_drying_simulation()
    
    # Save results
    save_results_to_csv(output)
    
    # Create plots
    plot_results(output, save_fig=True)
    
    # Compare with web interface output (if available)
    compare_with_web_output(output)
    
    print("\n" + "="*70)
    print("✓ Example complete!")
    print("="*70)
