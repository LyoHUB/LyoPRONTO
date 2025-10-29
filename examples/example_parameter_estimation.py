"""
Product Resistance Parameter Estimation Example

This example demonstrates how to estimate product resistance parameters (R0, A1, A2)
from experimental temperature data using the calc_unknownRp module.

The script:
1. Loads experimental temperature data from test_data/temperature.txt
2. Runs parameter estimation to fit Rp model to data
3. Prints estimated parameters (R0, A1, A2)
4. Saves results to CSV
5. Generates comparison plots

This example uses the calc_unknownRp.dry() function which performs inverse
modeling to estimate product resistance parameters from measured product
temperatures during primary drying.

Usage:
    python examples/example_parameter_estimation.py

Output:
    - Console: Estimated R0, A1, A2 parameters
    - CSV: examples/outputs/lyopronto_parameter_estimation_<timestamp>.csv
    - PNG: examples/outputs/parameter_estimation_results.png
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import time
import csv

# Import LyoPRONTO modules
from lyopronto import calc_unknownRp


def main():
    """Run parameter estimation example."""
    
    # ==================== SETUP ====================
    
    # Create output directory
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    # Timestamp for output files
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    
    print("=" * 80)
    print("LyoPRONTO Parameter Estimation Example")
    print("=" * 80)
    print()
    
    # ==================== VIAL PROPERTIES ====================
    
    vial = {
        'Av': 3.80,   # Vial area (cm²)
        'Ap': 3.14,   # Product area (cm²)
        'Vfill': 2.0  # Fill volume (mL)
    }
    
    print("Vial Properties:")
    print(f"  Vial Area (Av):      {vial['Av']:.2f} cm²")
    print(f"  Product Area (Ap):   {vial['Ap']:.2f} cm²")
    print(f"  Fill Volume (Vfill): {vial['Vfill']:.2f} mL")
    print()
    
    # ==================== PRODUCT PROPERTIES ====================
    
    product = {
        'cSolid': 0.05,        # Fractional solute concentration [g/mL]
        'T_pr_crit': -5.0      # Critical product temperature [degC]
    }
    
    print("Product Properties:")
    print(f"  Solute Concentration: {product['cSolid']:.3f} g/mL")
    print(f"  Critical Temperature: {product['T_pr_crit']:.1f}°C")
    print()
    print("  Note: R0, A1, A2 will be estimated from experimental data")
    print()
    
    # ==================== HEAT TRANSFER COEFFICIENTS ====================
    
    # Kv = KC + KP*Pch/(1+KD*Pch)
    ht = {
        'KC': 2.75e-4,  # [cal/s/K/cm**2]
        'KP': 8.93e-4,  # [cal/s/K/cm**2/Torr]
        'KD': 0.46      # [1/Torr]
    }
    
    print("Heat Transfer Coefficients:")
    print(f"  KC: {ht['KC']:.6f} cal/s/K/cm²")
    print(f"  KP: {ht['KP']:.6f} cal/s/K/cm²/Torr")
    print(f"  KD: {ht['KD']:.2f} 1/Torr")
    print()
    
    # ==================== PROCESS CONDITIONS ====================
    
    # Chamber pressure
    Pchamber = {
        'setpt': [0.15],        # [Torr]
        'dt_setpt': [1800.0],   # [min]
        'ramp_rate': 0.5        # [Torr/min]
    }
    
    # Shelf temperature
    Tshelf = {
        'init': -35.0,          # [degC]
        'setpt': [20.0],        # [degC]
        'dt_setpt': [1800.0],   # [min]
        'ramp_rate': 1.0        # [degC/min]
    }
    
    print("Process Conditions:")
    print(f"  Chamber Pressure:       {Pchamber['setpt'][0]:.3f} Torr")
    print(f"  Initial Shelf Temp:     {Tshelf['init']:.1f}°C")
    print(f"  Final Shelf Temp:       {Tshelf['setpt'][0]:.1f}°C")
    print(f"  Temp Ramp Rate:         {Tshelf['ramp_rate']:.1f}°C/min")
    print()
    
    # ==================== LOAD EXPERIMENTAL DATA ====================
    
    # Load temperature data
    data_path = Path(__file__).parent.parent / "test_data" / "temperature.txt"
    
    if not data_path.exists():
        print(f"ERROR: Experimental data file not found: {data_path}")
        print("Please ensure test_data/temperature.txt exists")
        return
    
    print(f"Loading experimental data from: {data_path.name}")
    
    # Load data: format depends on number of columns
    data = np.loadtxt(data_path)
    
    # Handle different file formats
    if data.ndim == 1:
        # Single row case
        time_exp = np.array([data[0]])
        Tbot_exp = np.array([data[1]])
    elif data.shape[1] == 2:
        # Two column format: time [hr], temperature [degC]
        time_exp = data[:, 0]
        Tbot_exp = data[:, 1]
    else:
        # Three column format: vial_number, time [hr], temperature [degC]
        time_exp = data[:, 1]
        Tbot_exp = data[:, 2]
    
    print(f"  Data points: {len(time_exp)}")
    print(f"  Time range: {time_exp[0]:.3f} to {time_exp[-1]:.3f} hr")
    print(f"  Temperature range: {np.min(Tbot_exp):.2f} to {np.max(Tbot_exp):.2f}°C")
    print()
    
    # ==================== RUN PARAMETER ESTIMATION ====================
    
    print("Running parameter estimation...")
    print("(This may take a minute...)")
    print()
    
    try:
        # Run calc_unknownRp.dry() to estimate parameters
        output, product_res = calc_unknownRp.dry(
            vial, product, ht, Pchamber, Tshelf, time_exp, Tbot_exp
        )
        
        # Extract estimated parameters
        # product_res contains [time, Lck (cake length), Rp (resistance)]
        # Fit Rp model: Rp = R0 + A1*Lck/(1 + A2*Lck)
        
        import scipy.optimize as sp
        
        # Curve fit to extract R0, A1, A2
        params, params_covariance = sp.curve_fit(
            lambda h, r, a1, a2: r + h*a1/(1 + h*a2),
            product_res[:, 1],  # Lck (cake length)
            product_res[:, 2],  # Rp (resistance)
            p0=[1.0, 0.0, 0.0]  # Initial guess
        )
        
        R0_est = params[0]
        A1_est = params[1]
        A2_est = params[2]
        
        print("=" * 80)
        print("PARAMETER ESTIMATION RESULTS")
        print("=" * 80)
        print()
        print("Estimated Product Resistance Parameters:")
        print(f"  R0: {R0_est:.6f} cm²·hr·Torr/g")
        print(f"  A1: {A1_est:.6f} cm·hr·Torr/g")
        print(f"  A2: {A2_est:.6f} 1/cm")
        print()
        
        # Calculate standard errors
        perr = np.sqrt(np.diag(params_covariance))
        print("Standard Errors:")
        print(f"  σ(R0): ±{perr[0]:.6f}")
        print(f"  σ(A1): ±{perr[1]:.6f}")
        print(f"  σ(A2): ±{perr[2]:.6f}")
        print()
        
        # ==================== SAVE RESULTS ====================
        
        # Save simulation output
        csv_path = output_dir / f"lyopronto_parameter_estimation_{timestamp}.csv"
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['LyoPRONTO Parameter Estimation Results'])
            writer.writerow([f'Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}'])
            writer.writerow([])
            
            # Estimated parameters
            writer.writerow(['Estimated Parameters'])
            writer.writerow(['R0 [cm²·hr·Torr/g]', R0_est])
            writer.writerow(['A1 [cm·hr·Torr/g]', A1_est])
            writer.writerow(['A2 [1/cm]', A2_est])
            writer.writerow([])
            
            # Standard errors
            writer.writerow(['Standard Errors'])
            writer.writerow(['σ(R0)', perr[0]])
            writer.writerow(['σ(A1)', perr[1]])
            writer.writerow(['σ(A2)', perr[2]])
            writer.writerow([])
            
            # Simulation data
            writer.writerow(['Time [hr]', 'Sublimation Temp [°C]', 'Vial Bottom Temp [°C]',
                           'Shelf Temp [°C]', 'Chamber Pressure [mTorr]',
                           'Sublimation Flux [kg/hr/m²]', 'Fraction Dried'])
            
            for row in output:
                writer.writerow(row)
        
        print(f"Results saved to: {csv_path.name}")
        print()
        
        # ==================== GENERATE PLOTS ====================
        
        print("Generating plots...")
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Parameter Estimation Results', fontsize=16, fontweight='bold')
        
        # Plot 1: Temperature comparison
        ax1 = axes[0, 0]
        ax1.plot(time_exp, Tbot_exp, 'ko', label='Experimental Data', markersize=4)
        ax1.plot(output[:, 0], output[:, 2], 'r-', label='Model Fit', linewidth=2)
        ax1.set_xlabel('Time [hr]', fontweight='bold')
        ax1.set_ylabel('Product Temperature [°C]', fontweight='bold')
        ax1.set_title('Temperature Match', fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Product resistance vs cake length
        ax2 = axes[0, 1]
        ax2.plot(product_res[:, 1], product_res[:, 2], 'b-', linewidth=2)
        ax2.set_xlabel('Cake Length [cm]', fontweight='bold')
        ax2.set_ylabel('Product Resistance [cm²·hr·Torr/g]', fontweight='bold')
        ax2.set_title('Estimated Resistance Profile', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Sublimation flux
        ax3 = axes[1, 0]
        ax3.plot(output[:, 0], output[:, 5], 'g-', linewidth=2)
        ax3.set_xlabel('Time [hr]', fontweight='bold')
        ax3.set_ylabel('Sublimation Flux [kg/hr/m²]', fontweight='bold')
        ax3.set_title('Sublimation Flux', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Fraction dried
        ax4 = axes[1, 1]
        ax4.plot(output[:, 0], output[:, 6], 'purple', linewidth=2)
        ax4.set_xlabel('Time [hr]', fontweight='bold')
        ax4.set_ylabel('Fraction Dried', fontweight='bold')
        ax4.set_title('Drying Progress', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        ax4.set_ylim([0, 1.05])
        
        plt.tight_layout()
        
        # Save figure
        png_path = output_dir / "parameter_estimation_results.png"
        plt.savefig(png_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {png_path.name}")
        plt.close()
        
        print()
        print("=" * 80)
        print("Example completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"ERROR: Parameter estimation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
