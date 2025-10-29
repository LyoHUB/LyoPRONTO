# Contributing to LyoPRONTO

Thank you for your interest in contributing to LyoPRONTO! This document provides guidelines and instructions for contributing.

## Testing & Continuous Integration (CI)

LyoPRONTO uses a modern, robust CI/CD pipeline and a comprehensive test suite. All contributions must pass automated tests and follow the project's testing strategy:

- **Fast/Slow Test Separation:**
    - Fast tests run on every PR and push (under 60 seconds).
    - Slow tests (marked with `@pytest.mark.slow`) run nightly and on demand.
- **Centralized Python Version Management:**
    - All workflows use the Python version(s) specified in `.github/ci-config/ci-versions.yml`.
- **CI Workflows:**
    - PRs and pushes: Fast tests (`pr-tests.yml`)
    - Main branch: Full suite (`tests.yml`)
    - Nightly/manual: Slow tests (`slow-tests.yml`)
    - Docs: Build and link check (`docs.yml`)
- **Coverage & Linting:**
    - Coverage is reported for all test runs.
    - Linting and formatting are enforced in CI.

**Contributor Checklist:**

- Mark slow tests with `@pytest.mark.slow`.
- Add or update tests for all new features and bugfixes.
- Ensure all tests pass locally before submitting a PR (`pytest tests/ -v`).
- Review [`tests/README.md`](tests/README.md) for full details on running, writing, and debugging tests, as well as CI workflow explanations.

---

## Table of Contents
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Submitting Changes](#submitting-changes)
- [Pyomo Development](#pyomo-development)

## Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- Basic understanding of lyophilization process (helpful but not required)

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/SECQUOIA/LyoPRONTO.git
cd LyoPRONTO

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests to verify setup
pytest tests/ -v
```

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-description
```

### 2. Make Changes

- Write tests first (TDD approach recommended)
- Implement your feature
- Ensure all tests pass
- Update documentation

### 3. Test Your Changes

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=lyopronto --cov-report=html

# Check specific test
pytest tests/test_functions.py -v

# Run with debugging
pytest tests/ -v --pdb
```

### 4. Code Quality Checks

```bash
# Format code
black lyopronto/ tests/

# Check linting
flake8 lyopronto/ tests/

# Type checking (optional but recommended)
mypy lyopronto/
```

### 5. Commit Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Add feature: brief description

Detailed explanation of what changed and why.
- Key change 1
- Key change 2

Closes #issue_number"
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title and description
- Reference to related issues
- Summary of changes
- Test results

## Coding Standards

### Python Style
- Follow PEP 8 style guide
- Use NumPy-style docstrings
- Include type hints for function signatures
- Maximum line length: 100 characters (flexible for readability)

### Physics Variable Naming
Use these standard names for consistency:

```python
# Temperatures [degC]
Tsub  # Sublimation front temperature
Tbot  # Vial bottom temperature
Tsh   # Shelf temperature

# Pressures (Torr)
Pch   # Chamber pressure
Psub  # Vapor pressure at sublimation front

# Lengths (cm)
Lpr0  # Initial product length
Lck   # Dried cake length

# Product properties
Rp    # Product resistance (cm²-hr-Torr/g)
Kv    # Vial heat transfer coefficient [cal/s/K/cm**2])

# Rates
dmdt  # Sublimation rate (kg/hr)
```

### Documentation Requirements

Every function should have a docstring:

```python
def calculate_vapor_pressure(temperature):
    """Calculate vapor pressure using Antoine equation.
    
    The vapor pressure of ice is calculated using the Antoine
    equation with parameters specific to water/ice system.
    
    Args:
        temperature (float): Temperature in degrees Celsius.
        
    Returns:
        (float): Vapor pressure in Torr.
        
    Notes:
        Valid for temperatures between -60°C and 0°C.
        
    Examples:
        >>> P = calculate_vapor_pressure(-20.0)
        >>> print(f"{P:.3f} Torr")
        0.776 Torr
    """
```

## Testing Requirements

### Test Coverage
- All new functions must have unit tests
- Aim for >80% code coverage
- Include edge cases and error conditions
- Test physical reasonableness of results

### Test Structure

```python
class TestMyFeature:
    """Tests for my new feature."""
    
    def test_normal_case(self, standard_setup):
        """Test with typical input values."""
        result = my_function(standard_setup)
        assert result > 0
        assert np.isclose(result, expected, rtol=0.01)
    
    def test_edge_case(self):
        """Test with boundary conditions."""
        result = my_function(edge_case_input)
        assert is_physically_reasonable(result)
    
    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ValueError):
            my_function(invalid_input)
```

### Using Fixtures

Leverage existing fixtures from `tests/conftest.py`:

```python
def test_with_fixtures(self, standard_vial, standard_product):
    """Test using predefined fixtures."""
    result = simulate(standard_vial, standard_product)
    assert result is not None
```

## Submitting Changes

### Pull Request Checklist

Before submitting a PR, ensure:

- [ ] All tests pass (`pytest tests/ -v`)
- [ ] Code is formatted (`black lyopronto/ tests/`)
- [ ] Documentation is updated
- [ ] Docstrings are complete
- [ ] CHANGELOG.md is updated (if applicable)
- [ ] No unnecessary files are included
- [ ] Commit messages are clear and descriptive

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Motivation
Why is this change needed? What problem does it solve?

## Changes
- Key change 1
- Key change 2
- Key change 3

## Testing
- [ ] Added unit tests
- [ ] Added integration tests
- [ ] All existing tests pass
- [ ] Manually tested with example cases

## Documentation
- [ ] Updated docstrings
- [ ] Updated README if needed
- [ ] Updated CHANGELOG

## Related Issues
Closes #123
Relates to #456
```

## Pyomo Development

### Special Considerations for Pyomo Code

When contributing Pyomo-based optimization code:

1. **Create Comparison Tests**
   ```python
   def test_pyomo_matches_scipy():
       """Verify Pyomo results match scipy baseline."""
       scipy_result = scipy_optimize(...)
       pyomo_result = pyomo_optimize(...)
       np.testing.assert_allclose(scipy_result, pyomo_result, rtol=1e-3)
   ```

2. **Use Proper Initialization**
   - Always warmstart with scipy solution
   - Document initialization strategy

3. **Handle Numerical Issues**
   - Use log-transforms for exponentials
   - Add scaling to improve conditioning
   - Document solver options

4. **Benchmark Performance**
   - Compare timing against scipy
   - Aim for <3x scipy performance
   - Profile bottlenecks

### Pyomo Model Structure

Follow this structure for new Pyomo models:

```python
def create_model(params):
    """Create Pyomo model for [description].
    
    Args:
        params: Model parameters
        
    Returns:
        Concrete Pyomo model ready to solve
    """
    model = pyo.ConcreteModel()
    
    # 1. Sets
    # 2. Parameters  
    # 3. Variables with bounds
    # 4. Constraints
    # 5. Objective
    
    return model

def solve_model(model, solver='ipopt'):
    """Solve Pyomo model and extract results."""
    # Solve
    # Check status
    # Extract results
    # Return formatted output
```

## Questions or Issues?

- Check existing documentation in `docs/` and `*.md` files
- Review `PYOMO_ROADMAP.md` for architecture decisions
- Search existing issues on GitHub
- Ask questions by opening a new issue

## Code of Conduct

- Be respectful and constructive
- Focus on the code, not the person
- Welcome newcomers and help them learn
- Give credit where credit is due

## Recognition

Contributors will be acknowledged in:
- `CONTRIBUTORS.md` file
- Release notes
- Academic papers (for significant contributions)

Thank you for contributing to LyoPRONTO! 🚀
