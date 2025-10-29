# Slow Test Strategy

## Problem
- Full test suite takes **37 minutes** on GitHub CI (2 cores)
- Locally takes only **4 minutes** (18 parallel workers)
- Slow optimization tests dominate runtime (~20 tests taking 20-200+ seconds each)

## Solution: Three-Tier Testing Strategy

### 1. **PR Tests (Fast Feedback)** - `.github/workflows/pr-tests.yml`
**Skips slow tests** for rapid iteration during PR development.

- **Draft PR**: Fast tests only (no coverage)
- **Ready for Review**: Fast tests with coverage
- **Runtime**: ~2-5 minutes on CI
- **Command**: `pytest tests/ -m "not slow"`
- **Tests excluded**: 20 slow optimization tests marked with `@pytest.mark.slow`

### 2. **Main Branch Tests (Complete Validation)** - `.github/workflows/tests.yml`
**Runs ALL tests** including slow ones after merge to main/dev-pyomo.

- **Trigger**: Push to main or dev-pyomo branches (after PR merge)
- **Runtime**: ~30-40 minutes on CI
- **Command**: `pytest tests/` (no exclusions)
- **Purpose**: Comprehensive validation of merged code

### 3. **Manual Slow Tests** - `.github/workflows/slow-tests.yml`
**On-demand testing** for slow tests before merge if needed.

- **Trigger**: Manual workflow dispatch from GitHub Actions UI
- **Options**:
  - Run only slow tests: `pytest tests/ -m "slow"`
  - Run all tests: `pytest tests/`
- **Use cases**:
  - Pre-merge validation of optimization changes
  - Testing on feature branches without merging
  - Debugging slow test failures

## Test Breakdown

### Fast Tests (174 tests) - ~50 seconds local, ~2-5 minutes CI
- Core functionality tests
- Quick validation tests
- Edge case tests with simple scenarios

### Slow Tests (20 tests) - ~3+ minutes local, ~30+ minutes CI
- `test_opt_Pch_Tsh_coverage.py`: 17 slow tests (joint optimization)
  - `test_narrow_optimization_ranges` - 207s
  - `test_high_product_resistance` - 121s
  - `test_tight_equipment_constraint` - 75s
  - And 14 more optimization tests
- `test_opt_Pch.py`: 3 slow tests (pressure-only optimization)
  - `test_high_resistance_product` - 47s
  - `test_low_critical_temperature` - 32s
  - `test_consistent_results` - 24s

## Marking Tests as Slow

Tests are marked with the `@pytest.mark.slow` decorator:

```python
class TestOptPchTshEdgeCases:
    @pytest.mark.slow
    def test_narrow_optimization_ranges(self, conservative_setup):
        """Test with narrow optimization ranges."""
        # ... test code ...
```

Criteria for marking tests as slow:
- Takes > 20 seconds on local machine (8-18 cores)
- Involves complex scipy optimization
- Tests edge cases with difficult convergence

## Usage

### For Developers (Local)
```bash
# Fast tests only (recommended for development)
pytest tests/ -m "not slow"  # ~50s

# All tests including slow
pytest tests/  # ~4 minutes

# Only slow tests
pytest tests/ -m "slow"  # ~3+ minutes
```

### For CI/CD

**Automatic (no action needed):**
- PR commits: Fast tests run automatically
- Merge to main: All tests run automatically

**Manual (when needed):**
1. Go to GitHub Actions tab
2. Select "Slow Tests (Manual)" workflow
3. Click "Run workflow"
4. Choose to run all tests or only slow tests

## Benefits

1. **Fast feedback**: PRs get results in ~2-5 minutes instead of 37 minutes
2. **Complete validation**: Main branch still validates everything
3. **Flexibility**: Manual trigger for slow tests when needed
4. **Clear separation**: Developers know which tests are slow
5. **Better CI utilization**: Don't waste CI minutes on every commit

## References

- Slow test markers already defined in `pytest.ini`
- Tests marked using script: `mark_slow_tests.py`
- PR workflow: `.github/workflows/pr-tests.yml`
- Main workflow: `.github/workflows/tests.yml`
- Manual workflow: `.github/workflows/slow-tests.yml`
