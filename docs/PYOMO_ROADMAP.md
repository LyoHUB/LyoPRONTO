# LyoPRONTO Pyomo Integration Roadmap

## Vision
Add Pyomo-based simultaneous optimization as an alternative to LyoPRONTO's existing scipy-based sequential optimization. Both approaches will coexist in the codebase, with Pyomo enabling better convergence, parameter estimation, and multi-vial optimization for advanced use cases, while scipy remains available for simpler, well-tested workflows.

## Why Pyomo?

### Current Limitations (scipy.optimize)
1. **Sequential optimization**: Optimizes one time step at a time
2. **No look-ahead**: Cannot anticipate future process states
3. **Limited solver options**: Stuck with scipy's algorithms
4. **No sensitivity analysis**: Difficult to perform parameter studies
5. **Scalability issues**: Hard to extend to batch-level optimization

### Pyomo Benefits
1. **Simultaneous optimization**: Optimize entire process trajectory at once
2. **Modern NLP solvers**: Access to IPOPT, SNOPT, KNITRO
3. **Sensitivity analysis**: Built-in tools for parameter estimation
4. **Scalability**: Easy to extend to multiple vials/batches
5. **Flexibility**: Can add complex constraints and objectives

## Current State Assessment

### What Works Well (Keep)
✅ Physics functions (all unit tests pass)
✅ Heat and mass transfer models
✅ Vapor pressure calculations
✅ Product resistance formulations
✅ Energy balance equations

### What We'll Add (Not Replace)
➕ Pyomo simultaneous optimization (new module: lyopronto/pyomo_models/)
➕ Time-discretized formulations (alternative to solve_ivp)
➕ Algebraic constraints (alternative to fsolve)

**Important**: Existing scipy-based modules (`calc_knownRp.py`, `opt_*.py`, etc.) will remain unchanged and fully functional. Pyomo models will be in a separate module tree.

### What's Challenging
⚠️ ODE integration (solve_ivp) → Need discretization strategy
⚠️ Conditional logic (if dmdt < 0) → Need smooth approximations
⚠️ Implicit equations → Become equality constraints

## Phase 1: Single Time-Step Prototype (Week 1-2)

### Goal
Replicate `opt_Pch_Tsh.py` functionality with a Pyomo model

### Tasks
1. **Create Pyomo model structure**
   ```python
   # lyopronto/pyomo_models/single_step.py
   def create_single_step_model(vial, product, ht, Lpr0, Lck, target_Pch=None, target_Tsh=None):
       model = pyo.ConcreteModel()
       
       # Variables
       model.Pch = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0.05, 0.5))
       model.Tsh = pyo.Var(domain=pyo.Reals, bounds=(-50, 50))
       model.Tsub = pyo.Var(domain=pyo.Reals, bounds=(-60, 0))
       model.Tbot = pyo.Var(domain=pyo.Reals, bounds=(-60, 50))
       model.Psub = pyo.Var(domain=pyo.NonNegativeReals)
       model.dmdt = pyo.Var(domain=pyo.NonNegativeReals)
       
       # Constraints
       # ... (heat balance, mass balance, etc.)
       
       # Objective
       model.obj = pyo.Objective(expr=model.Psub - model.Pch, sense=pyo.maximize)
       
       return model
   ```

2. **Implement constraint functions**
   - Vapor pressure (exponential)
   - Heat transfer (linear)
   - Mass transfer (nonlinear)
   - Energy balance (equality constraint)

3. **Add comparison tests**
   ```python
   def test_pyomo_single_step_matches_scipy():
       # Run scipy version
       scipy_result = opt_Pch_Tsh.optimize(...)
       
       # Run Pyomo version
       pyomo_result = pyomo_single_step.optimize(...)
       
       # Compare
       assert np.isclose(scipy_result, pyomo_result, rtol=1e-3)
   ```

4. **Benchmark performance**
   - Time comparison scipy vs. Pyomo
   - Solution quality comparison

### Success Criteria
- ✅ Pyomo model solves successfully
- ✅ Results match scipy within 0.1%
- ✅ All tests pass
- ✅ Performance is acceptable (< 10x slower)

## Phase 2: Multi-Period Model (Week 3-4)

### Goal
Create a time-discretized optimization over the entire drying process

### Approach: Collocation on Finite Elements
```python
model.TIME = pyo.Set(initialize=np.linspace(0, t_final, n_points))

# Time-indexed variables
model.Lck = pyo.Var(model.TIME, domain=pyo.NonNegativeReals)
model.Tsub = pyo.Var(model.TIME, domain=pyo.Reals)
model.Tbot = pyo.Var(model.TIME, domain=pyo.Reals)
# ...

# ODE discretization
def dLck_dt_rule(model, t):
    if t == 0:
        return pyo.Constraint.Skip
    dt = model.TIME.ord(t) - model.TIME.ord(t-1)
    dLck_dt = (model.Lck[t] - model.Lck[t-1]) / dt
    # ... (sublimation rate calculation)
    return dLck_dt == sublimation_rate

model.ode_constraint = pyo.Constraint(model.TIME, rule=dLck_dt_rule)
```

### Tasks
1. **Choose discretization method**
   - Option A: Backward Euler (simple, stable)
   - Option B: Trapezoidal rule (more accurate)
   - Option C: Orthogonal collocation (most accurate, complex)

2. **Implement time-discretized constraints**
   - ODE for cake length growth
   - Heat/mass transfer at each time point
   - Ramp constraints for Tsh and Pch

3. **Handle variable setpoints**
   - Piecewise-linear shelf temperature ramp
   - Piecewise-constant chamber pressure

4. **Add process constraints**
   - Product temperature < critical temperature
   - Minimum/maximum sublimation rate
   - Equipment capability limits

### Success Criteria
- ✅ Multi-period model solves successfully
- ✅ Drying trajectory is physically reasonable
- ✅ Final cake length matches target
- ✅ All constraints are satisfied

## Phase 3: Optimization Modes (Week 5-6)

### Goal
Replicate all three optimization modes with Pyomo

### Modes to Implement

#### 3A: Variable Pch (Fixed Tsh)
```python
# Fix shelf temperature, optimize chamber pressure
model.Tsh.fix(Tsh_setpoint)
model.Pch.unfix()

# Objective: Maximize sublimation rate
model.obj = pyo.Objective(
    expr=sum(model.dmdt[t] for t in model.TIME),
    sense=pyo.maximize
)
```

#### 3B: Variable Tsh (Fixed Pch)
```python
# Fix chamber pressure, optimize shelf temperature
model.Pch.fix(Pch_setpoint)
model.Tsh.unfix()

# Objective: Minimize drying time subject to Tpr < Tpr_crit
model.Tbot <= Tpr_crit  # Add constraint
```

#### 3C: Variable Pch and Tsh
```python
# Optimize both
model.Pch.unfix()
model.Tsh.unfix()

# Multi-objective or weighted objective
```

### Tasks
1. Implement all three modes
2. Add mode-specific constraints
3. Create tests for each mode
4. Compare with scipy versions

### Success Criteria
- ✅ All three modes solve successfully
- ✅ Results match scipy versions
- ✅ Optimal trajectories are smooth and physical

## Phase 4: Advanced Features (Week 7-8)

### 4A: Parameter Estimation
Enable estimation of unknown parameters (R0, A1, A2, Kv parameters)

```python
# Add parameter variables
model.R0 = pyo.Var(domain=pyo.PositiveReals)
model.A1 = pyo.Var(domain=pyo.PositiveReals)

# Least squares objective
model.obj = pyo.Objective(
    expr=sum((model.Tbot[t] - measured_Tbot[t])**2 for t in model.TIME)
)
```

### 4B: Design Space Generation
Systematic exploration of Pch-Tsh parameter space

```python
for Pch in np.linspace(0.06, 0.30, 20):
    for Tsh in np.linspace(-40, 40, 20):
        model.Pch.fix(Pch)
        model.Tsh.fix(Tsh)
        solver.solve(model)
        # Check if Tbot < Tpr_crit
        if feasible:
            design_space.append((Pch, Tsh))
```

### 4C: Multi-Vial Optimization
Optimize for batch heterogeneity

```python
model.VIALS = pyo.Set(initialize=range(n_vials))

# Variables indexed by vial and time
model.Tsub = pyo.Var(model.VIALS, model.TIME)

# Equipment constraint (total sublimation capacity)
def equipment_capacity_rule(model, t):
    total_sublimation = sum(model.dmdt[v,t] for v in model.VIALS)
    return total_sublimation <= equipment_capability(model.Pch[t])

model.equipment_constraint = pyo.Constraint(model.TIME, rule=equipment_capacity_rule)
```

### Success Criteria
- ✅ Parameter estimation works on synthetic data
- ✅ Design space matches existing implementation
- ✅ Multi-vial optimization converges

## Phase 5: Integration and Documentation (Week 9-10)

### Tasks
1. **API Design**
   ```python
   # High-level API
   result = lyopronto.optimize(
       vial=vial_config,
       product=product_config,
       process={'Pch': 'variable', 'Tsh': 20.0},
       solver='ipopt',
       backend='pyomo'  # or 'scipy' for legacy
   )
   ```

2. **Documentation**
   - User guide for Pyomo models
   - Migration guide from scipy
   - Examples and tutorials
   - API reference

3. **Performance Tuning**
   - Solver options optimization
   - Scaling and initialization strategies
   - Warmstart techniques

4. **CI/CD Integration**
   - Add Pyomo tests to GitHub Actions
   - Performance regression tests
   - Automated benchmarking

### Success Criteria
- ✅ Clean API that hides complexity
- ✅ Complete documentation
- ✅ All tests pass in CI
- ✅ Performance is acceptable

## Technical Challenges and Solutions

### Challenge 1: Exponential Vapor Pressure
**Problem**: `P = 2.698e10 * exp(-6144.96/(T+273.15))` has numerical issues

**Solution**: Use log-transform
```python
model.log_Psub = pyo.Var()
model.log_Psub_constraint = pyo.Constraint(
    expr=model.log_Psub == log(2.698e10) - 6144.96/(model.Tsub + 273.15)
)
model.Psub = pyo.Expression(expr=pyo.exp(model.log_Psub))
```

### Challenge 2: Conditional (if dmdt < 0)
**Problem**: Discrete logic breaks NLP solvers

**Solution**: Use complementarity or smooth approximation
```python
# Option A: Smooth max
model.dmdt = pyo.Expression(
    expr=pyo.sqrt(dmdt_raw**2 + epsilon**2) / 2 + dmdt_raw / 2
)

# Option B: Complementarity constraint (with MPEC solver)
model.dmdt_geq_0 = pyo.Constraint(expr=model.dmdt >= 0)
model.complementarity = pyo.Complementarity(...)
```

### Challenge 3: Nested Equations (fsolve)
**Problem**: `Tsub = fsolve(energy_balance, guess)`

**Solution**: Make it an equality constraint
```python
# Instead of solving for Tsub, make it a variable with constraint
model.Tsub = pyo.Var()
model.energy_balance = pyo.Constraint(
    expr=heat_from_shelf(model.Tsh, model.Tbot) == 
         heat_for_sublimation(model.Tsub, model.Pch)
)
```

### Challenge 4: Initialization
**Problem**: Poor initial guess causes solver failure

**Solution**: Use scipy solution for warmstart
```python
# Run scipy first for initial guess
scipy_solution = calc_knownRp.dry(...)

# Initialize Pyomo variables
for t_idx, t in enumerate(model.TIME):
    model.Tsub[t].set_value(scipy_solution[t_idx, 1])
    model.Tbot[t].set_value(scipy_solution[t_idx, 2])
    # ...
```

## Development Workflow

### Step-by-Step Process
1. **Write test first** (TDD approach)
2. **Implement Pyomo model**
3. **Compare with scipy**
4. **Debug and iterate**
5. **Document and commit**

### Example Workflow
```bash
# 1. Create feature branch
git checkout -b feature/pyomo-single-step

# 2. Write test
# tests/test_pyomo_single_step.py

# 3. Run test (should fail)
pytest tests/test_pyomo_single_step.py -v

# 4. Implement feature
# lyopronto/pyomo_models/single_step.py

# 5. Run test (should pass)
pytest tests/test_pyomo_single_step.py -v

# 6. Run all tests
pytest tests/ -v

# 7. Commit and push
git add .
git commit -m "Add Pyomo single-step optimization"
git push origin feature/pyomo-single-step

# 8. Create pull request
gh pr create
```

## Required Dependencies

### New Packages
```txt
# requirements-pyomo.txt
pyomo>=6.6.0
ipopt  # or install via conda
pandas>=2.0.0  # for results analysis
matplotlib>=3.5.0  # for visualization
```

### Installation
```bash
# Install Pyomo
pip install pyomo

# Install IPOPT solver (Linux)
conda install -c conda-forge ipopt

# Or compile from source
# https://coin-or.github.io/Ipopt/INSTALL.html
```

## Expected Outcomes

### Quantitative Goals
- **Performance**: Within 2-3x of scipy for single-step
- **Accuracy**: Match scipy results within 0.1%
- **Coverage**: 100% test coverage for Pyomo modules
- **Documentation**: Complete API docs and user guide

### Qualitative Goals
- **Usability**: Easy to use, well-documented API
- **Maintainability**: Clean, modular code
- **Extensibility**: Easy to add new features
- **Reliability**: Robust error handling and validation

## Risk Mitigation

### Risk 1: Solver Convergence Issues
**Mitigation**: 
- Implement multiple solver options (IPOPT, SNOPT)
- Develop robust initialization strategies
- Add scaling to improve conditioning

### Risk 2: Performance Degradation
**Mitigation**:
- Benchmark early and often
- Optimize discretization (fewer time points)
- Use sparse Jacobian structures

### Risk 3: Complexity Creep
**Mitigation**:
- Keep API simple
- Maintain scipy backend as fallback
- Incremental feature addition

## Success Metrics

### Technical
- [ ] All Pyomo models converge successfully
- [ ] Results match scipy within tolerance
- [ ] Performance is acceptable
- [ ] All tests pass

### Scientific
- [ ] Can perform parameter estimation
- [ ] Can generate design spaces
- [ ] Can optimize multi-vial systems
- [ ] Provides sensitivity analysis

### Practical
- [ ] Users can easily switch to Pyomo
- [ ] Documentation is complete
- [ ] Examples cover common use cases
- [ ] Community adoption (if open-source)

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | 2 weeks | Single time-step Pyomo model |
| Phase 2 | 2 weeks | Multi-period optimization |
| Phase 3 | 2 weeks | All optimization modes |
| Phase 4 | 2 weeks | Advanced features |
| Phase 5 | 2 weeks | Integration & docs |
| **Total** | **10 weeks** | **Production-ready Pyomo implementation** |

## Next Immediate Steps

1. ✅ Testing infrastructure (DONE)
2. ⬜ Fix test assertion issues
3. ⬜ Start Phase 1: Create first Pyomo model
4. ⬜ Set up Pyomo development environment
5. ⬜ Write first comparison test

## Conclusion

This roadmap provides a structured path to **add** Pyomo-based simultaneous optimization to LyoPRONTO **alongside** the existing scipy-based sequential optimization. With the testing infrastructure now in place, we have the confidence to proceed with this integration, knowing that we can validate every step against the proven scipy implementation.

**Key Principle**: **Coexistence, Not Replacement**
- ✅ Scipy modules (`calc_*.py`, `opt_*.py`) remain unchanged
- ✅ Pyomo modules added in separate directory (`lyopronto/pyomo_models/`)
- ✅ Users can choose the approach that fits their needs
- ✅ Both are tested and maintained

The phased approach allows for:
- **Incremental progress** with clear milestones
- **Continuous validation** against scipy baseline
- **Risk mitigation** through parallel development
- **Flexibility** to adjust based on lessons learned
- **User choice** between scipy (simple, proven) and Pyomo (advanced, flexible)

**Recommended Next Action**: Begin Phase 1 by creating a simple single time-step Pyomo model and comparing it with the scipy version.
