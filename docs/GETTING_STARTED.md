# Getting Started with LyoPRONTO Development

## Quick Start

### 1. Set Up Development Environment

```bash
# Clone the repository (if not already done)
cd /home/bernalde/repos/LyoPRONTO

# Create virtual environment (if not already done)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Verify installation
python -c "import lyopronto; print('LyoPRONTO installed successfully!')"
```

### 2. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_functions.py -v

# Run with coverage report
pytest tests/ --cov=lyopronto --cov-report=html

# View coverage report
open htmlcov/index.html  # On Linux: xdg-open htmlcov/index.html
```

### 3. Explore the Codebase

```bash
# View project structure
tree -L 2 lyopronto/

# Read core modules
cat lyopronto/functions.py | head -50
cat lyopronto/calc_knownRp.py | head -50
```

## Current Project Status

### What's Done ✅
1. **Testing Infrastructure**
   - 53 tests created (39 passing, 14 with minor issues)
   - Comprehensive unit tests for all physics functions
   - Integration tests for simulation workflows
   - Regression tests for consistency checks
   - CI/CD configuration (GitHub Actions)

2. **Documentation**
   - `README_TESTING.md`: How to use the test suite
   - `TESTING_SUMMARY.md`: Analysis of test results
   - `PYOMO_ROADMAP.md`: Plan for Pyomo transition
   - `README.md`: (existing) General project documentation

3. **Code Quality Tools**
   - pytest configuration (`pytest.ini`)
   - Development dependencies (`requirements-dev.txt`)
   - Test fixtures and helpers (`tests/conftest.py`)

### What's Next ⏭️

#### Immediate (Today)
1. **Fix test assertion issues** (30 min)
   - Update column 6 assertions: `>= 0.99` instead of `>= 99.0`
   - Update column 4 assertions: expect mTorr not Torr
   - Investigate termination conditions

2. **Run example simulations** (15 min)
   - Execute `ex_knownRp_PD.py`
   - Verify outputs look reasonable
   - Understand typical parameter ranges

#### Short Term (This Week)
1. **Start Pyomo Phase 1** (2-3 days)
   - Create `lyopronto/pyomo_models/` directory
   - Implement single time-step optimization
   - Write comparison tests

2. **Set up Pyomo environment** (1 hour)
   ```bash
   pip install pyomo
   conda install -c conda-forge ipopt
   ```

3. **Create first Pyomo model** (1-2 days)
   - Replicate `opt_Pch_Tsh.py` functionality
   - Compare results with scipy version
   - Document any differences

## Key Files to Understand

### Core Physics
- `lyopronto/functions.py` - All physics equations
- `lyopronto/constant.py` - Physical constants and unit conversions

### Simulators
- `lyopronto/calc_knownRp.py` - Primary drying with known Rp
- `lyopronto/calc_unknownRp.py` - Primary drying with unknown Rp

### Optimizers (Current - Scipy-based)
- `lyopronto/opt_Pch_Tsh.py` - Optimize both pressure and temperature
- `lyopronto/opt_Pch.py` - Optimize pressure only
- `lyopronto/opt_Tsh.py` - Optimize temperature only

### Examples
- `ex_knownRp_PD.py` - Example of known product resistance case
- `ex_unknownRp_PD.py` - Example of unknown product resistance case

### Tests
- `tests/test_functions.py` - Unit tests for physics functions
- `tests/test_calculators.py` - Integration tests for simulators
- `tests/test_regression.py` - Regression and consistency tests
- `tests/conftest.py` - Shared fixtures and utilities

## Understanding the Physics

### Key Concepts

1. **Lyophilization Process**
   - Freeze liquid in vials
   - Apply vacuum (low chamber pressure)
   - Heat from shelf causes ice to sublimate
   - Goal: Remove all water while keeping product below critical temperature

2. **Key Variables**
   - `Pch`: Chamber pressure (Torr or mTorr)
   - `Tsh`: Shelf temperature (°C)
   - `Tsub`: Sublimation front temperature (°C)
   - `Tbot`: Vial bottom temperature (°C)
   - `Lck`: Dried cake length (cm)
   - `Lpr0`: Initial product length (cm)
   - `Rp`: Product resistance (cm²-hr-Torr/g)

3. **Key Equations**
   - Vapor pressure: `P = 2.698e10 * exp(-6144.96/(T+273.15))`
   - Sublimation rate: `dm/dt = Ap/Rp * (Psub - Pch)`
   - Heat transfer: `Q = Kv * Av * (Tsh - Tbot)`
   - Energy balance: Heat in = Heat for sublimation

### Process Flow
```
1. Product frozen at low temperature
2. Chamber evacuated to low pressure
3. Shelf temperature gradually increased
4. Ice sublimates from top down
5. Dried cake grows upward (Lck increases)
6. Process continues until Lck = Lpr0 (fully dried)
```

## Common Tasks

### Run a Simulation
```python
from lyopronto import calc_knownRp

# Define configuration
vial = {'Av': 3.80, 'Ap': 3.14, 'Vfill': 2.0}
product = {'cSolid': 0.05, 'R0': 1.4, 'A1': 16.0, 'A2': 0.0}
ht = {'KC': 2.75e-4, 'KP': 8.93e-4, 'KD': 0.46}
Pchamber = {'setpt': [0.15], 'dt_setpt': [1800.0], 'ramp_rate': 0.5}
Tshelf = {'init': -35.0, 'setpt': [20.0], 'dt_setpt': [1800.0], 'ramp_rate': 1.0}
dt = 0.01

# Run simulation
output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)

# Output columns: [time, Tsub, Tbot, Tsh, Pch, flux, %dried]
print(f"Drying time: {output[-1, 0]:.2f} hours")
print(f"Final % dried: {output[-1, 6]*100:.1f}%")
```

### Add a New Test
```python
# In tests/test_my_feature.py
import pytest
import numpy as np
from lyopronto import my_module

def test_my_new_feature(standard_setup):
    """Test description."""
    result = my_module.my_function(standard_setup)
    
    assert result > 0
    assert np.isclose(result, expected_value, rtol=0.01)
```

### Debug a Failing Test
```bash
# Run specific test with verbose output
pytest tests/test_functions.py::TestVaporPressure::test_vapor_pressure_at_freezing_point -v -s

# Drop into debugger on failure
pytest tests/test_functions.py -v --pdb

# Show local variables on failure
pytest tests/test_functions.py -v -l
```

### Profile Performance
```python
import time
from lyopronto import calc_knownRp

start = time.time()
output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)
elapsed = time.time() - start

print(f"Simulation took {elapsed:.2f} seconds")
```

## Best Practices

### Code Style
- Follow PEP 8
- Use type hints where helpful
- Write docstrings for all public functions
- Keep functions focused and testable

### Testing
- Write tests before implementing features (TDD)
- Test one thing per test function
- Use descriptive test names
- Use fixtures to avoid duplication

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes
# ... edit files ...

# Run tests
pytest tests/ -v

# Commit
git add .
git commit -m "Add my feature"

# Push
git push origin feature/my-feature

# Create pull request on GitHub
```

### Documentation
- Update docstrings when changing functions
- Add examples to documentation
- Keep README files current
- Document any non-obvious design decisions

## Troubleshooting

### Import Errors
```bash
# Make sure package is installed in development mode
pip install -e .

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Test Failures
```bash
# Run tests with verbose output
pytest tests/ -v

# Check if issue is with one specific test
pytest tests/test_functions.py::TestVaporPressure -v

# Update test expectations if code behavior changed intentionally
```

### Simulation Issues
```python
# Check intermediate values
print(f"Lpr0: {Lpr0:.4f} cm")
print(f"Rp: {Rp:.4f} cm²-hr-Torr/g")
print(f"Kv: {Kv:.6f} cal/s/K/cm²")

# Verify physical reasonableness
assert Lpr0 > 0, "Initial product length must be positive"
assert Rp > 0, "Product resistance must be positive"
```

## Resources

### Documentation
- `README_TESTING.md` - Testing guide
- `TESTING_SUMMARY.md` - Current test status
- `PYOMO_ROADMAP.md` - Pyomo transition plan
- `docs/` - MkDocs documentation (if available)

### Papers/References
- Original LyoPRONTO paper (check `README.md` for citation)
- Pyomo documentation: https://www.pyomo.org/
- IPOPT solver: https://coin-or.github.io/Ipopt/

### Tools
- pytest: https://docs.pytest.org/
- GitHub Actions: https://docs.github.com/actions
- MkDocs: https://www.mkdocs.org/

## Getting Help

### Questions?
1. Check existing documentation
2. Search issues on GitHub
3. Ask the development team
4. Open a new issue with details

### Found a Bug?
1. Check if it's already reported
2. Write a minimal test case that reproduces it
3. Open an issue with:
   - Description of the problem
   - Steps to reproduce
   - Expected vs. actual behavior
   - System information

### Want to Contribute?
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

## Summary

You now have:
- ✅ A comprehensive test suite (53 tests)
- ✅ Clear documentation of the codebase
- ✅ A roadmap for Pyomo transition
- ✅ Tools and workflows for development

**Next action**: Fix the minor test assertion issues, then start Phase 1 of the Pyomo implementation!

Good luck with the development! 🚀
