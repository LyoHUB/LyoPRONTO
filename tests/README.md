# LyoPRONTO Test Suite

This directory contains comprehensive tests for the LyoPRONTO lyophilization simulator.

## Test Organization

### Test Files (85 tests total)

- **`test_calculators.py`** (26 tests) - Primary drying calculator tests
  - Tests for `calc_knownRp.py` and `calc_unknownRp.py`
  - Validates mass balance, energy balance, physical constraints
  
- **`test_functions.py`** (27 tests) - Physics function tests
  - Vapor pressure, product resistance, heat transfer
  - Sublimation rates, temperature calculations
  
- **`test_web_interface.py`** (8 tests) - Web interface calculator validation
  - Matches web interface output (6.66 hr drying time)
  - Temperature profile, flux profiles, mass balance
  
- **`test_opt_Tsh.py`** (14 tests) - Shelf temperature optimization tests (opt_Tsh module)
  - Validates optimizer results (2.123 hr optimal time)
  - Tests different constraints and edge cases
  
- **`test_freezing.py`** (3 tests) - Freezing simulation tests
  - Basic functionality and output format
  - Initial conditions and phase transitions
  
- **`test_design_space.py`** (7 tests) - Design space generator tests
  - Three evaluation modes (shelf temp, product temp, equipment)
  - Physical constraints and mode comparisons
  
- **`test_regression.py`** (10 tests) - Regression and stability tests
  - Numerical stability across different conditions
  - Output format consistency

### Shared Fixtures (`conftest.py`)

Common test fixtures used across test files:
- Standard vial geometry
- Standard product properties
- Heat transfer coefficients
- Process conditions

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
# Expected: 85 passed in ~43 seconds
```

### Run Specific Test File
```bash
pytest tests/test_design_space.py -v
pytest tests/test_opt_Tsh.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=lyopronto --cov-report=html
# Generates htmlcov/index.html
```

### Run Tests in Parallel
```bash
pytest tests/ -n auto
```

## Test Guidelines

### Writing New Tests

1. **Use descriptive names**: `test_opt_Tsh_maintains_critical_temperature`
2. **Add docstrings**: Explain what the test validates
3. **Use fixtures**: Import from `conftest.py` when possible
4. **Check physical reasonableness**: Not just numerical correctness
5. **Document expected behavior**: Especially for edge cases

### Test Structure
```python
def test_something_specific():
    """Test that [specific behavior] works correctly.
    
    This test validates [what it validates] by [how it validates].
    Expected result: [what should happen]
    """
    # Arrange - Set up inputs
    vial = {'Av': 3.8, 'Ap': 3.14, 'Vfill': 2.0}
    
    # Act - Run the function
    result = function_under_test(vial)
    
    # Assert - Check results
    assert result > 0, "Result should be positive"
    assert result < 100, "Result should be reasonable"
```

### Physical Validation

All tests should validate:
- **Physical constraints**: Temperatures, pressures in valid ranges
- **Mass balance**: Ice sublimated matches expected
- **Energy balance**: Heat in equals heat out
- **Monotonicity**: Time increases, certain quantities monotonic
- **Boundary conditions**: Initial and final states correct

## Test Coverage

Current coverage: ~32% (focused on physics and optimization)

**Well-covered**:
- Core physics functions (vapor pressure, resistance, heat transfer)
- Primary drying calculators
- Optimizer functionality

**Could improve**:
- Edge cases in freezing module
- More design space scenarios
- Error handling paths

## Continuous Integration

Tests are run automatically on:
- Every commit (via GitHub Actions - if configured)
- Pull requests to main branch
- Release tags

**Requirements**:
- All tests must pass
- No new warnings introduced
- Coverage should not decrease

## Test Data

Reference data for validation is stored in `test_data/`:
- `temperature.txt` - Temperature profile input
- `lyopronto_primary_drying_*.csv` - Web interface reference
- `lyopronto_optimizer_*.csv` - Optimizer reference
- `lyopronto_freezing_*.csv` - Freezing reference
- `lyopronto_design_space_*.csv` - Design space reference

## Debugging Failed Tests

### View detailed output
```bash
pytest tests/ -v --tb=long
```

### Run specific test with debugging
```bash
pytest tests/test_file.py::TestClass::test_method -v --pdb
```

### Check for warnings
```bash
pytest tests/ --warning=error
```

## Performance

- **Total tests**: 85
- **Execution time**: ~43 seconds
- **Parallel execution**: Can reduce to ~15 seconds with `-n auto`

## Contributing

When adding new functionality:
1. Write tests first (TDD)
2. Ensure all existing tests pass
3. Add tests for edge cases
4. Update this README if adding new test file
5. Run full test suite before committing

## Questions?

- Check existing tests for examples
- See `conftest.py` for available fixtures
- Review `../docs/COEXISTENCE_PHILOSOPHY.md` for testing scipy vs Pyomo
- See main `README.md` for getting started

---

**Last Updated**: October 2, 2025  
**Test Suite Version**: 1.0  
**Total Tests**: 85 (100% passing)
