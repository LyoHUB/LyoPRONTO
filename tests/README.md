# LyoPRONTO Test Suite

This document describes the testing strategy, usage, and best practices for the LyoPRONTO project.

## Test Strategy

LyoPRONTO uses a three-tier testing approach to balance rapid feedback and comprehensive validation:

- **Fast tests**: Run on every pull request (PR) for quick feedback. These skip slow optimization tests.
- **Full test suite**: Runs on merge to `main`/`dev-pyomo` branches, including all slow tests.
- **Manual slow tests**: Can be triggered on demand via GitHub Actions for pre-merge or feature branch validation.

## Running Tests Locally

- **Fast tests only** (recommended for development):
  ```bash
  pytest tests/ -m "not slow"
  ```
- **All tests** (including slow optimization tests):
  ```bash
  pytest tests/
  ```
- **Only slow tests**:
  ```bash
  pytest tests/ -m "slow"
  ```

## Marking Slow Tests

- Slow tests are marked with `@pytest.mark.slow` in the code.
- Criteria: Any test that takes >20 seconds or involves heavy optimization (e.g., joint/edge-case optimizers).
- This allows CI and developers to easily include/exclude slow tests as needed.

## CI/CD Integration

- **Python version** for all workflows is set in `.github/ci-config/ci-versions.yml` and read dynamically by all workflows.
- **Workflows**:
  - PRs: Run only fast tests for rapid feedback (~2-5 min on CI).
  - Main/dev-pyomo: Run full suite after merge (~30-40 min on CI).
  - Manual: "Slow Tests (Manual)" workflow available in GitHub Actions for on-demand slow test runs.
- **Coverage**: All test runs report coverage using `pytest-cov` and upload to Codecov.

## Best Practices

- Add `@pytest.mark.slow` to any new test that takes >20s or is optimization-heavy.
- Use `[unit]` format for all unit comments in code (e.g., `[cm]`, `[degC]`).
- Keep test output and error messages clear and physically meaningful.
- Use fixtures and helper functions from `conftest.py` for consistency.
- Check physical reasonableness of simulation results using provided helpers.

## Updating Python Version for CI

- Edit `.github/ci-config/ci-versions.yml` to change the Python version for all CI workflows.
- No need to update each workflow file individually.

## Example Commands

- **Run a specific test file:**
  ```bash
  pytest tests/test_opt_Pch.py -v
  ```
- **Run with coverage:**
  ```bash
  pytest tests/ --cov=lyopronto --cov-report=html
  ```
- **Run with debugging:**
  ```bash
  pytest tests/ -v --pdb
  ```

## Additional Resources

- See `docs/SLOW_TEST_STRATEGY.md` for details on the slow test policy and CI/CD approach.
- See `lyopronto/constant.py` and `lyopronto/functions.py` for physics and unit conventions.
- For questions, check the main project README or ask in the project discussions.
