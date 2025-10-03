#!/usr/bin/env python
"""
Investigate warning sources in LyoPRONTO tests.
"""
import warnings
import sys

# Capture all warnings
warnings.simplefilter("always")

# Track warnings
warning_counts = {}

def warning_handler(message, category, filename, lineno, file=None, line=None):
    key = f"{category.__name__}: {filename}:{lineno}"
    warning_counts[key] = warning_counts.get(key, 0) + 1
    
warnings.showwarning = warning_handler

# Run a simple test
print("Testing warning sources...")

# Test 1: Import scipy
print("\n1. Importing scipy.optimize...")
import scipy.optimize
print(f"   Warnings so far: {sum(warning_counts.values())}")

# Test 2: Run an optimization
print("\n2. Running scipy.optimize.minimize...")
from scipy.optimize import minimize

def rosenbrock(x):
    return sum(100.0*(x[1:]-x[:-1]**2.0)**2.0 + (1-x[:-1])**2.0)

x0 = [1.3, 0.7, 0.8, 1.9, 1.2]
res = minimize(rosenbrock, x0, method='nelder-mead', options={'xatol': 1e-8, 'disp': False})
print(f"   Warnings so far: {sum(warning_counts.values())}")

# Test 3: Import lyopronto
print("\n3. Importing lyopronto...")
import lyopronto
print(f"   Warnings so far: {sum(warning_counts.values())}")

# Test 4: Run a simple calculation
print("\n4. Running lyopronto.calc_knownRp...")
from lyopronto import calc_knownRp
import numpy as np

vial = {'Av': 3.8, 'Ap': 3.14, 'Vfill': 2.0}
product = {'cSolid': 0.05, 'R0': 1.4, 'A1': 16.0, 'A2': 0.0}
ht = {'KC': 0.000275, 'KP': 0.000893, 'KD': 0.46}
Pchamber = {'setpt': np.array([0.150]), 'dt_setpt': np.array([1800.0]), 'ramp_rate': 0.5}
Tshelf = {'init': -35.0, 'setpt': np.array([0.0]), 'dt_setpt': np.array([1800.0]), 'ramp_rate': 1.0}
dt = 0.01

output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
print(f"   Warnings so far: {sum(warning_counts.values())}")

# Print summary
print(f"\n{'='*60}")
print(f"TOTAL WARNINGS: {sum(warning_counts.values())}")
print(f"{'='*60}")

if warning_counts:
    print("\nTop 10 warning sources:")
    sorted_warnings = sorted(warning_counts.items(), key=lambda x: x[1], reverse=True)
    for i, (key, count) in enumerate(sorted_warnings[:10], 1):
        print(f"{i}. {count:6d}x - {key}")
else:
    print("\nNo warnings detected!")
