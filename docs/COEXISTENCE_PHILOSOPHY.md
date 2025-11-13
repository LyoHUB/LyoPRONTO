# Scipy and Pyomo Coexistence Philosophy

## Core Principle

**LyoPRONTO maintains BOTH scipy and Pyomo optimization approaches as complementary tools, not competitive replacements.**

## Why Both?

### Scipy: The Reliable Workhorse
- ✅ **Proven**: Battle-tested, 100% test coverage
- ✅ **Simple**: Minimal dependencies, easy to install
- ✅ **Fast for simple cases**: Single-vial, constant setpoints
- ✅ **Stable**: Well-understood numerical behavior
- ✅ **Production-ready**: Use with confidence

**When to use scipy**:
- Quick design space exploration
- Single-vial optimization
- Constant process setpoints (fixed Pch, Tsh)
- Production environments requiring stability
- Educational/teaching purposes

### Pyomo: The Advanced Toolkit
- ✅ **Sophisticated**: State-of-the-art NLP solvers (IPOPT)
- ✅ **Flexible**: Time-varying control, multi-objective
- ✅ **Scalable**: Multi-vial batch optimization
- ✅ **Advanced**: Parameter estimation, robust optimization
- ✅ **Research-enabling**: Supports cutting-edge applications

**When to use Pyomo**:
- Multi-vial batch optimization
- Time-varying control policies (Pch(t), Tsh(t))
- Parameter estimation from experimental data
- Robust optimization under uncertainty
- Research and development of new strategies

## Implementation Strategy

### Directory Structure
```
lyopronto/
├── functions.py              # Shared physics (used by both)
├── constant.py               # Shared constants (used by both)
│
├── calc_knownRp.py           # Scipy simulator
├── calc_unknownRp.py         # Scipy simulator
├── opt_Pch_Tsh.py            # Scipy optimizer
├── opt_Pch.py                # Scipy optimizer
├── opt_Tsh.py                # Scipy optimizer
├── design_space.py           # Scipy-based
│
└── pyomo_models/             # NEW: Pyomo implementations
    ├── __init__.py
    ├── single_step.py        # Pyomo single time-step
    ├── multi_period.py       # Pyomo full trajectory
    └── utils.py              # Pyomo helpers
```

### Code Boundaries

**NEVER modify**:
- `lyopronto/functions.py` - Shared physics functions
- `lyopronto/constant.py` - Shared constants
- `lyopronto/calc_*.py` - Scipy simulators (keep unchanged)
- `lyopronto/opt_*.py` - Scipy optimizers (keep unchanged)

**ADD new code in**:
- `lyopronto/pyomo_models/` - All Pyomo-specific code

**Shared between both**:
- `tests/conftest.py` - Test fixtures used by both
- Input dictionaries (vial, product) - Same format for both

## User Interface

### Option 1: Explicit Choice (Recommended)
```python
# Use scipy (existing)
from lyopronto import opt_Pch_Tsh
result_scipy = opt_Pch_Tsh.optimize(vial, product, constraints)

# Use Pyomo (new)
from lyopronto.pyomo_models import single_step
result_pyomo = single_step.optimize(vial, product, constraints)
```

### Option 2: Unified API (Future Enhancement)
```python
# Unified interface with method selection
from lyopronto import optimize

result = optimize(
    vial, product, constraints,
    method='scipy'  # or method='pyomo'
)
```

## Testing Strategy

### Scipy Tests (Existing)
- `tests/test_functions.py` - Physics functions
- `tests/test_calculators.py` - Scipy simulators
- `tests/test_regression.py` - Scipy baselines

**Keep all existing tests passing!**

### Pyomo Tests (New)
- `tests/test_pyomo_models.py` - Pyomo optimization
- `tests/test_pyomo_vs_scipy.py` - Comparison tests

**Validation approach**:
1. Run scipy optimizer → get result
2. Run Pyomo optimizer → get result
3. Assert results are "close enough" (within 1-5%)
4. Expect Pyomo to find equal-or-better optima

### Example Comparison Test
```python
def test_pyomo_matches_scipy_single_step(standard_setup):
    """Verify Pyomo single-step gives similar results to scipy."""
    vial, product, Pch, Tsh = standard_setup
    
    # Scipy baseline
    scipy_result = opt_Pch_Tsh.optimize_single_step(
        vial, product, Lck=0.5, constraints
    )
    
    # Pyomo alternative
    pyomo_result = single_step.optimize(
        vial, product, Lck=0.5, constraints
    )
    
    # Compare (allow Pyomo to be slightly better)
    assert pyomo_result['objective'] >= scipy_result['objective'] * 0.95
    assert abs(pyomo_result['Pch'] - scipy_result['Pch']) < 0.05
    assert abs(pyomo_result['Tsh'] - scipy_result['Tsh']) < 2.0
```

## Documentation Strategy

### Scipy Documentation (Existing)
- Keep all existing examples
- Maintain all existing docstrings
- Continue to document as primary method

### Pyomo Documentation (New)
- Add separate Pyomo examples
- Document advanced use cases
- Clearly mark as "advanced/optional"

### Cross-References
- Scipy docs mention: "For advanced features, see Pyomo models"
- Pyomo docs mention: "For simpler cases, use scipy optimizers"

## Development Workflow

### Working on Scipy Code
```bash
# Business as usual
git checkout -b fix/scipy-bug
# Edit lyopronto/*.py files
pytest tests/test_calculators.py -v
git commit -m "Fix: scipy optimizer edge case"
```

### Working on Pyomo Code
```bash
# Separate branch for Pyomo development
git checkout dev-pyomo
git checkout -b feature/pyomo-multi-period
# Edit lyopronto/pyomo_models/*.py files
pytest tests/test_pyomo_models.py -v
git commit -m "Add: multi-period Pyomo optimization"
```

### Integration Points
- Merge Pyomo features to `dev-pyomo` first
- Merge `dev-pyomo` to `main` only when stable
- Scipy code continues to work on `main` throughout

## Performance Expectations

| Use Case | Scipy Time | Pyomo Time | Winner |
|----------|------------|------------|--------|
| Single time-step optimization | 0.1-0.5s | 0.5-2s | Scipy (faster) |
| Full trajectory (100 steps) | 10-60s | 2-10s | Pyomo (faster) |
| Multi-vial (10 vials) | N/A | 5-30s | Pyomo (only option) |
| Time-varying control | N/A | 5-20s | Pyomo (only option) |

**Key insight**: Scipy is faster for simple single-step problems. Pyomo is faster for complex multi-period problems.

## Maintenance Commitment

### Scipy Code
- ✅ **Maintained indefinitely**
- ✅ **Bug fixes prioritized**
- ✅ **Considered "production" code**
- ✅ **Regression tests always passing**

### Pyomo Code
- ✅ **Maintained as advanced feature**
- ✅ **Allowed to be more experimental**
- ✅ **May have stricter dependency requirements**
- ⚠️ **Can evolve more rapidly**

## Migration Path (For Users)

We do **NOT** force users to migrate from scipy to Pyomo. However, users can migrate gradually:

### Phase 1: Exploration (No Risk)
```python
# Keep using scipy in production
result_prod = opt_Pch_Tsh.optimize(vial, product, constraints)

# Experiment with Pyomo in parallel
result_exp = single_step.optimize(vial, product, constraints)

# Compare results, build confidence
print(f"Scipy: {result_prod['time']:.2f} hr")
print(f"Pyomo: {result_exp['time']:.2f} hr")
```

### Phase 2: Selective Adoption
```python
# Use scipy for routine work
if use_case == 'routine':
    result = opt_Pch_Tsh.optimize(vial, product, constraints)

# Use Pyomo for advanced cases
elif use_case == 'multi_vial':
    result = multi_period.optimize(vials, product, constraints)
```

### Phase 3: Full Adoption (Optional)
```python
# Can switch entirely to Pyomo if desired
# But scipy remains available as fallback
result = single_step.optimize(vial, product, constraints)
```

## Communication Guidelines

### In Code Comments
```python
# GOOD: Clear about coexistence
# This scipy optimizer is maintained alongside Pyomo alternatives
# For advanced features, see lyopronto.pyomo_models

# BAD: Implies replacement
# DEPRECATED: Use Pyomo instead
```

### In Documentation
```markdown
# GOOD: Presents both options
LyoPRONTO provides two optimization approaches:
- **scipy**: Simple, proven, recommended for most users
- **Pyomo**: Advanced, flexible, for research and complex cases

# BAD: Implies one is obsolete
Pyomo is the new optimizer (scipy is old)
```

### In Commit Messages
```bash
# GOOD
git commit -m "Add: Pyomo single-step optimizer alongside scipy"

# BAD
git commit -m "Replace scipy with Pyomo"
git commit -m "Deprecate scipy optimizer"
```

## FAQ

### Q: Why not just replace scipy with Pyomo?
**A**: Scipy is simpler, has fewer dependencies, and is faster for simple cases. Many users don't need Pyomo's advanced features.

### Q: Will scipy code be maintained?
**A**: Yes, indefinitely. It's production-ready and many users rely on it.

### Q: Can I use both in the same script?
**A**: Yes! You can use scipy for some calculations and Pyomo for others.

### Q: Which should I use?
**A**: 
- **Start with scipy** if you're new or have simple needs
- **Try Pyomo** if you need time-varying control, multi-vial optimization, or parameter estimation

### Q: Will Pyomo eventually become the only option?
**A**: No. Scipy and Pyomo will coexist indefinitely.

### Q: What if I find a bug in the scipy code?
**A**: Please report it! We will fix bugs in scipy code just as we always have.

### Q: Can I contribute to scipy code?
**A**: Yes! Scipy modules are fully maintained and accept improvements.

## Summary

**Both scipy and Pyomo are first-class citizens in LyoPRONTO.**

- Neither is "deprecated" or "legacy"
- Neither is "better" in all cases
- Both are tested, documented, and maintained
- Users choose based on their needs

This philosophy ensures:
- ✅ Stability for existing users
- ✅ Innovation for advanced users
- ✅ No forced migrations
- ✅ Clear code organization
- ✅ Long-term maintainability
