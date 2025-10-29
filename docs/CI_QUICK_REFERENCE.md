# GitHub Actions CI Quick Reference

## 🚀 Quick Start

### Run Tests Locally (Matching CI)
```bash
./run_local_ci.sh
```

### Manual Test Run
```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ -v --cov=lyopronto --cov-report=xml --cov-report=term-missing
```

## 📋 CI Configuration

### Current Setup
- **Platform**: Ubuntu Latest (Linux)
- **Python**: 3.13
- **Tests**: 128 tests
- **Coverage**: 93%
- **Duration**: ~5-6 minutes

### Triggers
- Push to `main` or `dev-pyomo`
- Pull requests to `main` or `dev-pyomo`

## 📁 Files Created

### Core Files
1. **`.github/workflows/tests.yml`** - GitHub Actions workflow
2. **`requirements.txt`** - Core dependencies
3. **`run_local_ci.sh`** - Local CI simulation script

### Documentation
4. **`docs/CI_SETUP.md`** - Comprehensive CI guide (450+ lines)
5. **`docs/CI_SETUP_COMPLETE.md`** - Implementation summary

### Modified
6. **`README.md`** - Added CI badges

## ✅ Verification

```bash
$ ./run_local_ci.sh
==========================================
LyoPRONTO Local CI Simulation
==========================================

1. Checking Python version...
   Current Python: Python 3.13.7

2. Checking repository structure...
   ✅ Repository structure OK

3. Installing dependencies...
   ✅ Dependencies installed

4. Running test suite...
   ✅ 128 passed in 513.67s

Coverage: 93%

==========================================
✅ All tests passed!
==========================================

This matches the CI environment. You're ready to push!
```

## 🔧 Workflow Overview

```yaml
name: Tests

on: [push, pull_request to main/dev-pyomo]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      1. Checkout code (actions/checkout@v4)
      2. Setup Python 3.13 (actions/setup-python@v5)
      3. Install requirements.txt
      4. Install requirements-dev.txt
      5. Run pytest with coverage
      6. Upload coverage (optional, requires Codecov token)
```

## 📊 Test Results

### Coverage Breakdown
```
Module               Coverage
─────────────────────────────
calc_knownRp.py      100%
calc_unknownRp.py     89%
constant.py          100%
design_space.py       90%
freezing.py           80%
functions.py         100%
opt_Pch.py            98%
opt_Pch_Tsh.py       100%
opt_Tsh.py            94%
__init__.py          100%
─────────────────────────────
TOTAL                 93%
```

### Test Distribution
- Unit tests: ~85 tests
- Integration tests: ~30 tests  
- Regression tests: ~10 tests
- Example tests: 3 tests
- **Total**: 128 tests

## 🎯 Best Practices

### Before Pushing
```bash
# 1. Run local CI
./run_local_ci.sh

# 2. If passes, commit and push
git add .
git commit -m "Your changes"
git push

# 3. Watch CI on GitHub Actions tab
```

### Adding New Tests
```bash
# 1. Write test
# 2. Run locally
pytest tests/test_new_feature.py -v

# 3. Check coverage
pytest tests/ --cov=lyopronto --cov-report=html

# 4. Run CI simulation
./run_local_ci.sh

# 5. Push
```

## 🐛 Troubleshooting

### CI Fails, Local Passes
```bash
# Check Python version
python --version  # Should be 3.13

# Reinstall dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Run exact CI command
pytest tests/ -v --cov=lyopronto --cov-report=xml --cov-report=term-missing
```

### View CI Logs
1. Go to GitHub repository
2. Click **Actions** tab
3. Click on failed workflow run
4. Expand failed step to see logs

## 📖 Documentation

- **Full Guide**: `docs/CI_SETUP.md`
- **Implementation Summary**: `docs/CI_SETUP_COMPLETE.md`
- **Test Strategy**: `docs/TESTING_STRATEGY.md`
- **Test Directory**: `tests/README.md`

## 🔗 Links

- **Workflow File**: `.github/workflows/tests.yml`
- **Local Script**: `run_local_ci.sh`
- **Requirements**: `requirements.txt`, `requirements-dev.txt`

## 🎉 Status

✅ CI configured and tested
✅ Local simulation available
✅ 128 tests passing (100%)
✅ 93% code coverage
✅ Documentation complete
✅ README badges added

**Ready for production use!**
