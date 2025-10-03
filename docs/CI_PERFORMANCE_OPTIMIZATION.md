# CI Performance Optimization

## Problem

The original CI configuration was taking **~11 minutes** to run 128 tests, which is excessive for a test suite that completes in **1-2 minutes locally**.

## Root Causes

1. **Coverage overhead**: Running coverage analysis adds ~2x overhead (1 minute → 2 minutes)
2. **Limited CPU cores**: GitHub free tier runners have only 2 cores (vs 36+ locally)
3. **Dependency installation**: Installing packages can take 2-3 minutes without effective caching
4. **Running coverage on every PR**: Unnecessary for development feedback loop

## Solution: Dual Workflow Strategy

### For Pull Requests: Fast Feedback (`.github/workflows/pr-tests.yml`)
- **No coverage** - tests only
- **Target time**: 3-5 minutes
- **Purpose**: Quick feedback for developers during PR review
- **Runs on**: Pull requests only

### For Main Branch: Full Quality (`.github/workflows/tests.yml`)
- **With coverage** - full analysis
- **Target time**: 5-7 minutes  
- **Purpose**: Complete quality metrics for merged code
- **Runs on**: Pushes to `main` and `dev-pyomo` branches

## Performance Comparison

| Scenario | Before | After | Improvement |
|----------|--------|-------|-------------|
| **PR Tests** | ~11 min | ~3-5 min | **55-73% faster** |
| **Main Branch** | ~11 min | ~5-7 min | **36-55% faster** |
| **Local (no coverage)** | 5.3 min | 1.0 min | **81% faster** (with `-n auto`) |
| **Local (with coverage)** | - | 2.0 min | (reference) |

## Optimizations Applied

### 1. **Split PR and Main Workflows**
```yaml
# pr-tests.yml - Fast feedback for PRs
pytest tests/ -n auto -v  # No coverage

# tests.yml - Full analysis for main
pytest tests/ -n auto -v --cov=lyopronto  # With coverage
```

### 2. **Improved Pip Caching**
```yaml
- uses: actions/setup-python@v5
  with:
    cache: 'pip'
    cache-dependency-path: |
      requirements.txt
      requirements-dev.txt
```

### 3. **Parallel Test Execution**
Already enabled with `-n auto` (uses all available cores)

### 4. **Optimized Dependency Installation**
```bash
# Combined installation (faster)
pip install -r requirements.txt -r requirements-dev.txt

# vs separate installs (slower)
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Is 11 Minutes Acceptable?

**No.** For a project with:
- 128 tests
- ~1 minute execution time locally (parallel, no coverage)
- ~2 minutes with coverage locally

**Acceptable CI times:**
- ✅ **3-5 minutes** for PR tests (no coverage) - **GOOD**
- ✅ **5-7 minutes** for main branch (with coverage) - **ACCEPTABLE**
- ⚠️ **8-10 minutes** - **BORDERLINE** (consider further optimization)
- ❌ **11+ minutes** - **TOO SLOW** (poor developer experience)

## Industry Benchmarks

| Project Size | Tests | Target CI Time | Our Project |
|-------------|-------|----------------|-------------|
| **Small** | <50 | <2 min | - |
| **Medium** | 50-200 | 3-7 min | ✅ 128 tests |
| **Large** | 200-1000 | 7-15 min | - |
| **Very Large** | 1000+ | 15-30 min | - |

## Expected Results

After these optimizations, typical CI runs should be:

```
Pull Request CI:
├── Checkout & Setup: ~30s
├── Install deps (cached): ~1-2m
├── Run tests (no coverage): ~1-2m
└── Total: ~3-5 minutes ✅

Main Branch CI:
├── Checkout & Setup: ~30s
├── Install deps (cached): ~1-2m
├── Run tests (with coverage): ~2-3m
├── Upload coverage: ~30s
└── Total: ~5-7 minutes ✅
```

## Further Optimization Options (If Needed)

If CI times are still too slow, consider:

1. **Test sharding** - Split tests across multiple jobs
   ```yaml
   strategy:
     matrix:
       shard: [1, 2, 3, 4]
   ```

2. **Conditional test execution** - Skip tests for doc-only changes
   ```yaml
   paths-ignore:
     - 'docs/**'
     - '*.md'
   ```

3. **Caching test results** - Skip unchanged tests
   ```yaml
   pytest --lf --ff  # Last failed, then failed first
   ```

4. **Upgrade to GitHub Team** - Get 4 cores instead of 2

## Monitoring

Track CI performance over time:
1. Check workflow run times in GitHub Actions
2. Compare PR tests vs main branch tests
3. Alert if times exceed 10 minutes consistently
4. Review and optimize slow tests quarterly

## References

- [GitHub Actions: Caching dependencies](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)
- [pytest-xdist: Parallel execution](https://pytest-xdist.readthedocs.io/)
- [pytest-cov: Coverage overhead](https://pytest-cov.readthedocs.io/)
