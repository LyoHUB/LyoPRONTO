# Testing Infrastructure for LyoPRONTO

This document describes the testing infrastructure for LyoPRONTO, implemented to support the transition to Pyomo-based optimization.

## Overview

The test suite provides comprehensive coverage of:
- **Unit tests**: Individual physics functions
- **Integration tests**: Complete simulation workflows
- **Regression tests**: Verification against known results
- **Property-based tests**: Mathematical properties and invariants

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/test_functions.py

# Integration tests only
pytest tests/test_calculators.py

# Regression tests only
pytest tests/test_regression.py
```

### Run with Coverage Report

```bash
pytest --cov=lyopronto --cov-report=html
```

Then open `htmlcov/index.html` in your browser.

### Run Tests in Parallel

```bash
pytest -n auto
```

## Test Structure

### `tests/conftest.py`
Shared fixtures and utilities:
- Standard configurations for vials, products, and process parameters
- Physical reasonableness assertions
- Reusable test data

### `tests/test_functions.py`
Unit tests for core physics functions:
- `Vapor_pressure`: Vapor pressure calculations
- `Lpr0_FUN`: Initial fill height
- `Rp_FUN`: Product resistance
- `Kv_FUN`: Vial heat transfer coefficient
- `sub_rate`: Sublimation rate
- `T_bot_FUN`: Vial bottom temperature
- Energy balance consistency tests

### `tests/test_calculators.py`
Integration tests for simulation workflows:
- Complete drying simulations
- Parameter sensitivity tests
- Edge cases and error handling
- Mass balance verification

### `tests/test_regression.py`
Regression tests against validated results:
- Standard reference cases
- Parametric studies
- Output format consistency
- Numerical stability checks

## Test Fixtures

Common fixtures available in all tests:

```python
def test_example(standard_vial, standard_product, standard_ht):
    # Use pre-configured test data
    vial = standard_vial  # {'Av': 3.80, 'Ap': 3.14, 'Vfill': 2.0}
    product = standard_product  # {'cSolid': 0.05, 'R0': 1.4, ...}
    ...
```

Available fixtures:
- `standard_vial`, `small_vial`, `large_vial`
- `standard_product`, `dilute_product`, `concentrated_product`
- `standard_ht` (heat transfer parameters)
- `standard_pchamber` (chamber pressure)
- `standard_tshelf` (shelf temperature)
- `standard_setup` (complete configuration)

## Writing New Tests

### Unit Test Example

```python
def test_my_function():
    """Test description."""
    result = my_function(input_value)
    assert result > 0
    assert np.isclose(result, expected_value, rtol=0.01)
```

### Integration Test Example

```python
def test_simulation_workflow(standard_setup):
    """Test complete workflow."""
    output = calc_knownRp.dry(
        standard_setup['vial'],
        standard_setup['product'],
        # ...
    )
    
    assert_physically_reasonable_output(output)
    assert output[-1, 6] >= 99.0  # Check completion
```

### Parametric Test Example

```python
@pytest.mark.parametrize("pressure,expected_time", [
    (0.06, 20.0),
    (0.15, 15.0),
    (0.30, 12.0),
])
def test_pressure_effect(pressure, expected_time):
    """Test effect of pressure on drying time."""
    # Test implementation
```

## Continuous Integration

Tests are automatically run on:
- Every push to `main` and `dev-pyomo` branches
- Every pull request
- Multiple OS (Linux, Windows, macOS)
- Multiple Python versions (3.8, 3.9, 3.10, 3.11)

See `.github/workflows/tests.yml` for CI configuration.

## Coverage Goals

Target coverage levels:
- **Overall**: >80%
- **Core functions** (`functions.py`): >95%
- **Calculators**: >85%

Check current coverage:
```bash
pytest --cov=lyopronto --cov-report=term-missing
```

## Test Markers

Organize tests with markers:

```python
@pytest.mark.slow
def test_long_simulation():
    """This test takes a long time."""
    pass

@pytest.mark.parametric
def test_parameter_sweep():
    """Parametric study test."""
    pass
```

Run specific markers:
```bash
pytest -m "not slow"  # Skip slow tests
pytest -m "unit"      # Run only unit tests
```

## Debugging Failed Tests

### Run a Single Test
```bash
pytest tests/test_functions.py::TestVaporPressure::test_vapor_pressure_at_freezing_point -v
```

### Show Print Statements
```bash
pytest -s tests/test_functions.py
```

### Drop into Debugger on Failure
```bash
pytest --pdb tests/test_functions.py
```

### Show Local Variables on Failure
```bash
pytest -l tests/test_functions.py
```

## Next Steps

1. **Update Regression Tests**: Once validated reference results are available, update expected values in `test_regression.py`

2. **Add Property-Based Tests**: Use Hypothesis for property-based testing:
   ```python
   from hypothesis import given, strategies as st
   
   @given(st.floats(min_value=-50, max_value=0))
   def test_vapor_pressure_property(temp):
       """Vapor pressure should always be positive."""
       assert functions.Vapor_pressure(temp) > 0
   ```

3. **Performance Benchmarks**: Add tests to track performance:
   ```python
   def test_simulation_performance(benchmark, standard_setup):
       """Benchmark simulation time."""
       benchmark(calc_knownRp.dry, **standard_setup)
   ```

4. **Integration with Pyomo**: As Pyomo models are developed, add comparison tests to verify they match the scipy-based results.

## Contact

For questions about the test infrastructure, contact the development team or open an issue on GitHub.
