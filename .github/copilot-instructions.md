# GitHub Copilot Instructions for LyoPRONTO

## Project Context

LyoPRONTO is a vial-scale lyophilization (freeze-drying) process simulator written in Python. It models the freezing and primary drying phases using heat and mass transfer equations.

### Current State
- **Status**: Ready for Pyomo integration (scipy baseline complete)
- **Branch**: `dev-pyomo` for Pyomo development
- **Test Coverage**: 85 tests, 100% passing, 32% code coverage
- **Python Version**: 3.8+
- **Key Principle**: Coexistence, not replacement - both scipy and Pyomo will be available

## Code Style and Conventions

### General Guidelines
- Follow PEP 8 style guide
- Use type hints for function signatures
- Write comprehensive docstrings (NumPy style)
- Keep functions focused and testable
- Prefer explicit over implicit

### Naming Conventions
- Functions: `snake_case` (e.g., `calc_knownRp`, `Vapor_pressure`)
- Classes: `PascalCase` (e.g., `TestVaporPressure`)
- Variables: `snake_case` (e.g., `Pch`, `Tsub`, `dmdt`)
- Constants: `UPPER_CASE` in `constant.py`

### Physics Variables (Use These Names)
```python
# Temperatures (°C)
Tsub  # Sublimation front temperature
Tbot  # Vial bottom temperature
Tsh   # Shelf temperature
Tpr   # Product temperature

# Pressures (Torr unless specified)
Pch   # Chamber pressure
Psub  # Vapor pressure at sublimation front

# Lengths (cm)
Lpr0  # Initial product length
Lck   # Dried cake length

# Product properties
Rp    # Product resistance (cm²-hr-Torr/g)
R0    # Base product resistance
A1, A2  # Product resistance parameters

# Heat transfer
Kv    # Vial heat transfer coefficient (cal/s/K/cm²)
KC, KP, KD  # Vial heat transfer parameters

# Vial geometry
Av    # Vial area (cm²)
Ap    # Product area (cm²)
Vfill # Fill volume (mL)

# Rates
dmdt  # Sublimation rate (kg/hr)
```

## Key Files and Their Purposes

### Core Physics
- `lyopronto/functions.py` - All physics equations (vapor pressure, heat transfer, mass transfer)
- `lyopronto/constant.py` - Physical constants and unit conversions

### Simulators
- `lyopronto/calc_knownRp.py` - Primary drying with known product resistance
- `lyopronto/calc_unknownRp.py` - Primary drying with unknown resistance
- `lyopronto/freezing.py` - Freezing phase calculations

### Optimizers (scipy-based, will remain alongside Pyomo)
- `lyopronto/opt_Pch_Tsh.py` - Optimize both pressure and temperature
- `lyopronto/opt_Pch.py` - Optimize pressure only
- `lyopronto/opt_Tsh.py` - Optimize temperature only

### Pyomo Models (planned, to be added)
- `lyopronto/pyomo_models/single_step.py` - Single time-step optimization
- `lyopronto/pyomo_models/multi_period.py` - Full trajectory optimization

### Testing
- `tests/test_functions.py` - Unit tests for physics functions
- `tests/test_calculators.py` - Integration tests for simulators
- `tests/test_regression.py` - Regression tests
- `tests/conftest.py` - Shared fixtures

## Output Format (IMPORTANT!)

When working with simulation output, remember:

```python
output = calc_knownRp.dry(...)  # Returns numpy array with 7 columns

# Column indices and units:
output[:, 0]  # time (hours)
output[:, 1]  # Tsub - sublimation temperature (°C)
output[:, 2]  # Tbot - vial bottom temperature (°C)
output[:, 3]  # Tsh - shelf temperature (°C)
output[:, 4]  # Pch - chamber pressure (mTorr, NOT Torr!)
output[:, 5]  # flux - sublimation flux (kg/hr/m²)
output[:, 6]  # frac_dried - fraction dried (0-1, NOT percentage!)
```

## Common Pitfalls to Avoid

1. **Unit Confusion**
   - ❌ Don't assume Pch is in Torr (it's in mTorr in output)
   - ❌ Don't assume dried is percentage (it's a fraction 0-1)
   - ❌ Don't forget flux is normalized by area (kg/hr/m²)

2. **Physics Behavior**
   - ❌ Don't assume flux monotonically decreases (it's non-monotonic)
   - ✅ Flux increases early (shelf temp rising) then decreases (resistance dominant)

3. **Numerical Tolerance**
   - ✅ Mass balance within 2% is acceptable (numerical integration error)
   - ✅ Allow 0.5°C tolerance for temperature constraints

4. **Test Writing**
   - ✅ Use fixtures from `conftest.py`
   - ✅ Check physical reasonableness with `assert_physically_reasonable_output()`
   - ✅ Write descriptive test names and docstrings

## Pyomo Development Guidelines

### When Creating Pyomo Models

1. **Variable Bounds** (use these ranges)
   ```python
   Pch: (0.05, 0.5)      # Torr
   Tsh: (-50, 50)        # °C
   Tsub: (-60, 0)        # °C
   Tbot: (-60, 50)       # °C
   dmdt: (0, None)       # kg/hr (non-negative)
   ```

2. **Avoid Direct Exponentials**
   ```python
   # ❌ Don't do this (numerical issues):
   model.Psub = pyo.Expression(expr=2.698e10 * pyo.exp(-6144.96/(model.Tsub+273.15)))
   
   # ✅ Do this instead (log transform):
   model.log_Psub = pyo.Var()
   model.log_constraint = pyo.Constraint(
       expr=model.log_Psub == log(2.698e10) - 6144.96/(model.Tsub+273.15)
   )
   ```

3. **Handle Conditionals**
   ```python
   # ❌ Don't use if statements in Pyomo expressions
   if dmdt < 0:
       dmdt = 0
   
   # ✅ Use smooth max or complementarity
   model.dmdt_nonneg = pyo.Constraint(expr=model.dmdt >= 0)
   ```

4. **Initialization Strategy**
   - Always initialize with scipy solution for warmstart
   - Use `model.var.set_value()` to set initial guesses

## Testing Requirements

### For New Code
1. Write tests BEFORE implementation (TDD)
2. Ensure at least one unit test per function
3. Add integration test for workflows
4. Include edge case tests
5. Run full test suite: `pytest tests/ -v`

### For Pyomo Code
1. Add comparison test against scipy baseline
2. Test convergence with different initial guesses
3. Test numerical stability
4. Benchmark performance

## Documentation Standards

### Function Docstrings (NumPy Style)
```python
def my_function(arg1, arg2):
    """Brief description of function.
    
    Longer description if needed. Explain physics, assumptions,
    and any important implementation details.
    
    Args:
        arg1 (float): Description with units (e.g., temperature in °C)
        arg2 (dict): Description of dict contents
            
    Returns:
        (float): Description with units
        
    Notes:
        Any important notes about numerical stability, edge cases, etc.
        
    Examples:
        >>> result = my_function(1.0, {'key': 'value'})
        >>> print(result)
        42.0
    """
```

### Comments in Code
- Explain WHY, not WHAT
- Flag physics assumptions
- Note numerical considerations
- Document units in non-obvious places

## Git Workflow

```bash
# Feature development
git checkout -b feature/descriptive-name

# Make changes, write tests
pytest tests/ -v

# Commit with descriptive message
git commit -m "Add feature: brief description

Detailed explanation of what changed and why.
Fixes issue #123."

# Push and create PR
git push origin feature/descriptive-name
```

## Useful Commands

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=lyopronto --cov-report=html

# Run specific test
pytest tests/test_functions.py::TestVaporPressure::test_vapor_pressure_at_freezing_point -v

# Run with debugging
pytest tests/ -v --pdb

# Format code
black lyopronto/ tests/

# Type checking
mypy lyopronto/
```

## Key Physics Equations

### Vapor Pressure (Antoine Equation)
```python
P_sub = 2.698e10 * exp(-6144.96 / (T_sub + 273.15))  # Torr
```

### Product Resistance
```python
Rp = R0 + A1 * Lck / (1 + A2 * Lck)  # cm²-hr-Torr/g
```

### Sublimation Rate
```python
dmdt = Ap / Rp * (P_sub - Pch)  # kg/hr (before area normalization)
```

### Energy Balance
```python
Q_shelf = Kv * Av * (Tsh - Tbot)  # Heat from shelf
Q_sub = dmdt * dHs  # Heat for sublimation
# At steady state: Q_shelf = Q_sub
```

## References

### Core Documentation
- **Coexistence**: See `docs/COEXISTENCE_PHILOSOPHY.md` for scipy/Pyomo coexistence model
- **Roadmap**: See `docs/PYOMO_ROADMAP.md` for Pyomo integration plan
- **Architecture**: See `docs/ARCHITECTURE.md` for system design
- **Physics**: See `docs/PHYSICS_REFERENCE.md` for equations and models
- **Getting Started**: See `docs/GETTING_STARTED.md` for developer guide

### Examples and Tests
- **Examples**: See `examples/README.md` for web interface examples (4 modes)
- **Testing**: See `tests/README.md` for test suite (85 tests, 100% passing)
- **Development Log**: See `docs/DEVELOPMENT_LOG.md` for change history

### Historical Reference
- **Archive**: See `docs/archive/` for detailed session summaries and historical context

## Questions?

When unsure:
1. Check existing tests in `tests/` for examples
2. Review `lyopronto/functions.py` for physics implementation
3. See `docs/PYOMO_ROADMAP.md` for architecture decisions
4. Run tests with `pytest tests/ -v` to validate changes
5. Check `examples/` for working code examples

## Current Focus

🎯 **Ready for Pyomo Integration**
- All 4 web interface modes complete (primary drying, optimizer, freezing, design space)
- 85 tests passing (100% pass rate)
- Scipy baseline fully validated
- Adding Pyomo as parallel optimization method (scipy remains)
- **Remember**: Coexistence, not replacement - both scipy and Pyomo available
- See `docs/PYOMO_ROADMAP.md` and `docs/COEXISTENCE_PHILOSOPHY.md` for details
