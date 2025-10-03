# Continuous Integration Setup

## Overview

LyoPRONTO uses GitHub Actions for continuous integration (CI) to ensure code quality and test coverage. The CI runs automatically on every push and pull request to the `main` and `dev-pyomo` branches.

## CI Configuration

### Platform and Python Version
- **OS**: Ubuntu Latest (Linux only)
- **Python**: 3.13 (latest stable)
- **Rationale**: Matches the primary development environment

### Workflow File
`.github/workflows/tests.yml`

### What Gets Tested
1. **Full test suite**: All 128 tests in `tests/`
2. **Code coverage**: Measured with pytest-cov
3. **Coverage report**: Uploaded to Codecov (if configured)

### Workflow Triggers
- **Push** to `main` or `dev-pyomo` branches
- **Pull requests** targeting `main` or `dev-pyomo` branches

## Local CI Simulation

To replicate the CI environment locally before pushing:

### Quick Start
```bash
./run_local_ci.sh
```

This script will:
1. Check your Python version (warns if not 3.13)
2. Install all dependencies
3. Run the full test suite with coverage
4. Generate coverage reports

### Manual Replication
If you prefer to run commands manually:

```bash
# 1. Upgrade pip
python -m pip install --upgrade pip

# 2. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. Run tests (exactly as CI does - with parallel execution)
pytest tests/ -n auto -v --cov=lyopronto --cov-report=xml --cov-report=term-missing
```

**Note**: Tests run in parallel (`-n auto`) for 2-4x speedup. For debugging, omit `-n auto`.

## Dependencies

### Core Dependencies (`requirements.txt`)
```
numpy>=1.24.0
scipy>=1.10.0
matplotlib>=3.7.0
pandas>=2.0.0
```

### Development Dependencies (`requirements-dev.txt`)
```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-xdist>=3.3.0
hypothesis>=6.82.0
black>=23.7.0
flake8>=6.1.0
mypy>=1.4.0
```

## Python Version Compatibility

### Current Setup
- **CI**: Python 3.13 only
- **Local Development**: Python 3.8+ supported

### Why Python 3.13 for CI?
- Latest stable release
- Best performance and features
- Matches primary development environment

### Testing Other Python Versions
If you need to test on other Python versions locally:

```bash
# Using conda
conda create -n lyopronto-py38 python=3.8
conda activate lyopronto-py38
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/

# Using pyenv
pyenv install 3.8.18
pyenv virtualenv 3.8.18 lyopronto-py38
pyenv activate lyopronto-py38
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/
```

## CI Workflow Details

### Step-by-Step Process

1. **Checkout Code**: Uses `actions/checkout@v4`
2. **Setup Python**: Uses `actions/setup-python@v5` with Python 3.13
3. **Cache Dependencies**: Pip cache enabled for faster runs
4. **Install Dependencies**: 
   - Core: `requirements.txt`
   - Dev: `requirements-dev.txt`
5. **Run Tests**: `pytest tests/ -n auto -v --cov=lyopronto --cov-report=xml --cov-report=term-missing` (parallel execution)
6. **Upload Coverage**: To Codecov (if token configured)

### Typical Run Time
- **Full test suite** (parallel): ~2-3 minutes on GitHub Actions runners (2-core)
- **Local** (parallel, depends on hardware): 2-4 minutes (4-8 cores)
- **Sequential** (without `-n auto`): ~8-9 minutes (not recommended)

## Coverage Reports

### Viewing Coverage Locally

After running tests with coverage:

```bash
# Generate HTML coverage report
coverage html

# Open in browser (Linux)
xdg-open htmlcov/index.html

# Open in browser (macOS)
open htmlcov/index.html

# Open in browser (Windows)
start htmlcov/index.html
```

### Current Coverage
- **Overall**: 93%
- **Target**: Maintain above 90%

## Codecov Integration (Optional)

### Setup
1. Go to [codecov.io](https://codecov.io/)
2. Sign in with GitHub
3. Enable LyoPRONTO repository
4. Copy the upload token
5. Add to GitHub repository secrets as `CODECOV_TOKEN`

### Without Codecov
The CI will still run successfully without Codecov. Coverage reports are generated but not uploaded.

## Troubleshooting

### CI Fails but Tests Pass Locally

**Common Causes**:
1. **Python version mismatch**: CI uses 3.13, you might use different version
2. **Missing dependencies**: Ensure `requirements.txt` is up to date
3. **Path issues**: CI runs from repository root
4. **Environment differences**: Check for environment-specific code

**Solution**:
```bash
# Run local CI simulation
./run_local_ci.sh

# Or manually with Python 3.13
conda create -n lyopronto-ci python=3.13
conda activate lyopronto-ci
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ -v
```

### Dependency Installation Fails

**Issue**: Missing system dependencies for numpy/scipy

**Solution** (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install -y build-essential gfortran libopenblas-dev liblapack-dev
```

### Tests Timeout

**Issue**: Some tests take too long on CI

**Current Limits**: No timeout set
**Typical Duration**: 5-6 minutes total

If tests consistently exceed 10 minutes, investigate slow tests:
```bash
pytest tests/ -v --durations=10
```

## Best Practices

### Before Pushing

1. **Run local CI simulation**:
   ```bash
   ./run_local_ci.sh
   ```

2. **Check coverage**:
   - Ensure new code has tests
   - Maintain >90% overall coverage
   - Check `htmlcov/index.html` for uncovered lines

3. **Run linters** (optional):
   ```bash
   black lyopronto/ tests/
   flake8 lyopronto/ tests/
   mypy lyopronto/
   ```

### Adding New Tests

1. **Write tests first** (TDD)
2. **Run locally**: `pytest tests/test_new_feature.py -v`
3. **Check coverage**: `pytest tests/ --cov=lyopronto --cov-report=html`
4. **Run CI simulation**: `./run_local_ci.sh`
5. **Push**: CI will run automatically

### Updating Dependencies

When adding new dependencies:

1. **Add to `requirements.txt`** (core dependencies)
   ```bash
   echo "new-package>=1.0.0" >> requirements.txt
   ```

2. **Or `requirements-dev.txt`** (dev/test dependencies)
   ```bash
   echo "new-test-tool>=2.0.0" >> requirements-dev.txt
   ```

3. **Test locally**:
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   pytest tests/
   ```

4. **Update CI** (if needed): Modify `.github/workflows/tests.yml`

## Viewing CI Results

### On GitHub

1. Go to repository on GitHub
2. Click **Actions** tab
3. View workflow runs
4. Click on a run to see details
5. Expand steps to see logs

### Status Badges

Add to `README.md`:
```markdown
![Tests](https://github.com/SECQUOIA/LyoPRONTO/workflows/Tests/badge.svg?branch=dev-pyomo)
[![codecov](https://codecov.io/gh/SECQUOIA/LyoPRONTO/branch/dev-pyomo/graph/badge.svg)](https://codecov.io/gh/SECQUOIA/LyoPRONTO)
```

## Future Enhancements

### Potential Additions

1. **Multi-Python Testing**:
   ```yaml
   python-version: ['3.8', '3.9', '3.10', '3.11', '3.12', '3.13']
   ```

2. **Multi-OS Testing**:
   ```yaml
   os: [ubuntu-latest, windows-latest, macos-latest]
   ```

3. **Code Quality Checks**:
   - Black (formatting)
   - Flake8 (linting)
   - MyPy (type checking)

4. **Performance Benchmarks**:
   - Track test execution time
   - Detect performance regressions

5. **Documentation Builds**:
   - Build MkDocs documentation
   - Check for broken links

### Current Philosophy

**Keep it simple**: 
- Single OS (Linux)
- Single Python version (3.13)
- Focus on test quality over quantity of configurations
- Easy to replicate locally

**Reason**: Faster CI runs, easier maintenance, matches development environment

## Related Documentation

- **Testing Strategy**: `docs/TESTING_STRATEGY.md`
- **Test Directory**: `tests/README.md`
- **Contributing**: `CONTRIBUTING.md`
- **Development Log**: `docs/DEVELOPMENT_LOG.md`

## Questions?

If CI fails unexpectedly:

1. **Check workflow logs**: GitHub Actions → Failed run → View logs
2. **Reproduce locally**: `./run_local_ci.sh`
3. **Compare environments**: Python version, dependencies, OS
4. **Check recent changes**: `git diff main...dev-pyomo`

---

*CI Configuration last updated: October 2, 2025*
*Python Version: 3.13*
*Test Count: 128*
*Coverage Target: >90%*
