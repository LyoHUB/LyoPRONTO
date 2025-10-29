# LyoPRONTO Code Structure

## Overview

This document provides a high-level overview of the LyoPRONTO codebase structure, key modules, and their relationships.

## Directory Structure

```
LyoPRONTO/
├── lyopronto/              # Main package
│   ├── __init__.py         # Package initialization
│   ├── constant.py         # Physical constants and unit conversions
│   ├── functions.py        # Core physics equations
│   ├── freezing.py         # Freezing phase calculations
│   ├── calc_knownRp.py     # Primary drying with known Rp
│   ├── calc_unknownRp.py   # Primary drying with unknown Rp
│   ├── design_space.py     # Design space generation
│   ├── opt_Pch.py          # Optimize chamber pressure
│   ├── opt_Tsh.py          # Optimize shelf temperature
│   └── opt_Pch_Tsh.py      # Optimize both Pch and Tsh
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py         # Shared fixtures
│   ├── test_functions.py   # Unit tests for physics
│   ├── test_calculators.py # Integration tests for simulators
│   └── test_regression.py  # Regression tests
├── docs/                   # Documentation
├── examples/               # Example scripts
│   ├── ex_knownRp_PD.py   # Example with known Rp
│   └── ex_unknownRp_PD.py # Example with unknown Rp
└── .github/                # GitHub configuration
    ├── workflows/          # CI/CD pipelines
    └── copilot-instructions.md  # AI assistant instructions
```

## Module Dependencies

```
constant.py (no dependencies)
    ↓
functions.py (uses constant)
    ↓
    ├── freezing.py (uses functions, constant)
    ├── calc_knownRp.py (uses functions, constant)
    ├── calc_unknownRp.py (uses functions, constant)
    ├── opt_Pch.py (uses functions, constant)
    ├── opt_Tsh.py (uses functions, constant)
    ├── opt_Pch_Tsh.py (uses functions, constant)
    └── design_space.py (uses functions, opt_*)
```

## Core Modules

### `constant.py`
**Purpose**: Define all physical constants and unit conversions.

**Key Contents**:
- Unit conversions (kg_To_g, cm_To_m, hr_To_s, Torr_to_mTorr)
- Physical properties (rho_ice, rho_solute, rho_solution)
- Thermodynamic constants (dHs, dHf, k_ice, Cp_ice)

**Usage**:
```python
from lyopronto import constant
mass_kg = mass_g / constant.kg_To_g
```

### `functions.py`
**Purpose**: Core physics equations for heat and mass transfer.

**Key Functions**:

#### Thermophysical Properties
- `Vapor_pressure(T_sub)` → Vapor pressure (Torr)
- `Lpr0_FUN(Vfill, Ap, cSolid)` → Initial fill height (cm)
- `Rp_FUN(l, R0, A1, A2)` → Product resistance (cm²-hr-Torr/g)
- `Kv_FUN(KC, KP, KD, Pch)` → Heat transfer coefficient (cal/s/K/cm²)

#### Heat and Mass Transfer
- `sub_rate(Ap, Rp, T_sub, Pch)` → Sublimation rate (kg/hr)
- `T_bot_FUN(T_sub, Lpr0, Lck, Pch, Rp)` → Bottom temperature (°C)
- `T_sub_solver_FUN(T_sub_guess, *data)` → Energy balance residual

#### Parameter Estimation
- `Rp_finder(T_sub, Lpr0, Lck, Pch, Tbot)` → Estimate Rp from measurements

#### Utility Functions
- `calc_step(t, Lck, config)` → Calculate all states at time t
- `fill_output(sol, config)` → Format ODE solution into output array

**Physics Flow**:
```
Inputs: Tsh, Pch, Lck, Lpr0, Rp
    ↓
Solve energy balance → Tsub
    ↓
Calculate sublimation → dmdt
    ↓
Calculate temperatures → Tbot
    ↓
Output: [time, Tsub, Tbot, Tsh, Pch, flux, frac_dried]
```

### `calc_knownRp.py`
**Purpose**: Simulate primary drying when product resistance is known.

**Main Function**: `dry(vial, product, ht, Pchamber, Tshelf, dt)`

**Algorithm**:
1. Initialize with initial product length (Lpr0)
2. Set up ODE: dLck/dt = f(sublimation rate, densities)
3. Integrate using scipy.integrate.solve_ivp
4. Terminate when Lck = Lpr0 (fully dried)
5. Format output using functions.fill_output()

**Output**: numpy array (n_points × 7)
- Column 0: time (hours)
- Column 1: Tsub (°C)
- Column 2: Tbot (°C)
- Column 3: Tsh (°C)
- Column 4: Pch (mTorr)
- Column 5: flux (kg/hr/m²)
- Column 6: frac_dried (0-1)

### `calc_unknownRp.py`
**Purpose**: Simulate primary drying and estimate Rp from measurements.

**Main Difference from calc_knownRp**: 
- Uses measured Tbot to back-calculate Rp at each time point
- Fits Rp parameters (R0, A1, A2) to the estimated values

### `opt_Pch_Tsh.py`, `opt_Pch.py`, `opt_Tsh.py`
**Purpose**: Optimize process parameters (Pch and/or Tsh).

**Scipy-based (Current)**:
- Uses scipy.optimize.minimize
- Sequential optimization at each time step
- Constraint: Tbot < Tpr_crit
- Objective: Maximize sublimation driving force

**To be replaced with**: Pyomo-based simultaneous optimization

### `design_space.py`
**Purpose**: Generate design space by systematic parameter exploration.

**Algorithm**:
1. Grid search over Pch and Tsh ranges
2. For each combination, simulate drying
3. Check if Tbot stays below Tpr_crit
4. Collect feasible (Pch, Tsh) combinations

### `freezing.py`
**Purpose**: Calculate freezing phase dynamics.

**Key Functions**:
- Nucleation time calculation
- Crystallization time calculation
- Temperature profile during freezing

## Data Flow

### Typical Simulation Workflow

```
User Input
    ↓
Vial geometry (Av, Ap, Vfill)
Product properties (cSolid, R0, A1, A2)
Heat transfer (KC, KP, KD)
Process conditions (Pch, Tsh profile)
    ↓
calc_knownRp.dry()
    ↓
    ├→ functions.Lpr0_FUN() → Lpr0
    ├→ Set up ODE system
    │   └→ functions.calc_step() at each time
    │       ├→ functions.Kv_FUN()
    │       ├→ functions.Rp_FUN()
    │       ├→ fsolve(functions.T_sub_solver_FUN()) → Tsub
    │       ├→ functions.sub_rate() → dmdt
    │       └→ functions.T_bot_FUN() → Tbot
    └→ solve_ivp() integrates dLck/dt
    ↓
functions.fill_output()
    ↓
Output array (time series of all states)
```

### Optimization Workflow

```
User Input + Constraints
    ↓
opt_Pch_Tsh.optimize()
    ↓
For each time step:
    ├→ scipy.optimize.minimize
    │   ├→ Variables: Pch, Tsh (or subset)
    │   ├→ Objective: max(Psub - Pch)
    │   └→ Constraints: 
    │       ├→ Energy balance (equality)
    │       └→ Tbot < Tpr_crit (inequality)
    └→ Solve for optimal Pch, Tsh
    ↓
Time series of optimal (Pch, Tsh)
```

## Key Interfaces

### Standard Input Format

```python
# Vial geometry
vial = {
    'Av': float,    # Vial area (cm²)
    'Ap': float,    # Product area (cm²)
    'Vfill': float  # Fill volume (mL)
}

# Product properties
product = {
    'cSolid': float,  # Solid concentration (fraction)
    'R0': float,      # Base resistance (cm²-hr-Torr/g)
    'A1': float,      # Resistance parameter (cm-hr-Torr/g)
    'A2': float       # Resistance parameter (1/cm)
}

# Heat transfer parameters
ht = {
    'KC': float,  # cal/s/K/cm²
    'KP': float,  # cal/s/K/cm²/Torr
    'KD': float   # 1/Torr
}

# Process conditions
Pchamber = {
    'setpt': [float],      # Pressure setpoints (Torr)
    'dt_setpt': [float],   # Hold times (min)
    'ramp_rate': float     # Ramp rate (Torr/min)
}

Tshelf = {
    'init': float,         # Initial temp (°C)
    'setpt': [float],      # Temp setpoints (°C)
    'dt_setpt': [float],   # Hold times (min)
    'ramp_rate': float     # Ramp rate (°C/min)
}
```

### Standard Output Format

```python
output = calc_knownRp.dry(...)  # Returns numpy array

# Access data
times = output[:, 0]       # hours
Tsub = output[:, 1]        # °C
Tbot = output[:, 2]        # °C
Tsh = output[:, 3]         # °C
Pch_mTorr = output[:, 4]   # mTorr (NOT Torr!)
flux = output[:, 5]        # kg/hr/m²
frac_dried = output[:, 6]  # 0-1 (NOT percentage!)
```

## Testing Structure

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures and utilities
│   ├── standard_vial()
│   ├── standard_product()
│   ├── standard_setup()
│   └── assert_physically_reasonable_output()
│
├── test_functions.py        # Unit tests (44 tests)
│   ├── TestVaporPressure
│   ├── TestLpr0Function
│   ├── TestRpFunction
│   ├── TestKvFunction
│   ├── TestSubRate
│   └── ...
│
├── test_calculators.py      # Integration tests (14 tests)
│   ├── TestCalcKnownRp
│   ├── TestEdgeCases
│   └── TestMassBalance
│
└── test_regression.py       # Regression tests (9 tests)
    ├── TestRegressionStandardCase
    ├── TestRegressionParametricCases
    └── TestRegressionConsistency
```

## Future Structure (Pyomo)

Planned additions:

```
lyopronto/
├── pyomo_models/           # NEW
│   ├── __init__.py
│   ├── single_step.py      # Single time-step optimization
│   ├── multi_period.py     # Full trajectory optimization
│   ├── parameter_est.py    # Parameter estimation
│   └── utils.py            # Pyomo helper functions
└── ...

tests/
├── test_pyomo_single.py    # NEW
├── test_pyomo_multi.py     # NEW
└── test_pyomo_comparison.py # NEW (Pyomo vs scipy)
```

## Performance Considerations

### Bottlenecks (Current)
1. **fsolve calls** in T_sub_solver_FUN (at every time step)
2. **solve_ivp** with tight tolerances
3. **Sequential optimization** (one time step at a time)

### Optimization Targets (Pyomo)
1. **Simultaneous optimization** → Reduces solve_ivp calls
2. **Better initialization** → Faster convergence
3. **Sparse Jacobian** → Scales better with time discretization

## Extension Points

### Adding New Functionality

1. **New physics function**:
   - Add to `functions.py`
   - Write unit tests in `test_functions.py`
   - Update this documentation

2. **New simulator**:
   - Create new file in `lyopronto/`
   - Use `calc_knownRp.py` as template
   - Add integration tests
   - Update examples

3. **New optimization mode**:
   - Start with existing `opt_*.py` as template
   - Implement Pyomo version in `pyomo_models/`
   - Add comparison tests
   - Benchmark performance

## References

- Main package: `lyopronto/`
- Tests: `tests/`
- Documentation: See `*.md` files in root
- Examples: `ex_*.py` files
- Pyomo roadmap: `PYOMO_ROADMAP.md`
