# Physics Reference for LyoPRONTO

This document provides detailed physics context for AI assistants working with LyoPRONTO. It explains why the code behaves the way it does from a fundamental physics perspective.

## Table of Contents
1. [Lyophilization Overview](#lyophilization-overview)
2. [Heat Transfer Physics](#heat-transfer-physics)
3. [Mass Transfer Physics](#mass-transfer-physics)
4. [Coupling and Non-Monotonic Behavior](#coupling-and-non-monotonic-behavior)
5. [Valid Parameter Ranges](#valid-parameter-ranges)
6. [Edge Cases and Their Physics](#edge-cases-and-their-physics)
7. [Numerical Considerations](#numerical-considerations)

---

## Lyophilization Overview

### What is Lyophilization?

**Lyophilization** (freeze-drying) is a process to preserve pharmaceuticals and biologics by removing water through sublimation. It consists of three phases:

1. **Freezing**: Cool liquid formulation below freezing point → solid ice forms
2. **Primary Drying**: Apply vacuum + heat → ice sublimates directly to vapor (↓ 90-95% of drying time)
3. **Secondary Drying**: Increase temperature → bound water desorbs (↓ 5-10% of time)

LyoPRONTO focuses on **primary drying**, which is the longest and most critical phase.

### Why Sublimation Instead of Melting?

- **Structural preservation**: Ice scaffolding maintains product structure
- **Low temperature**: Protects heat-sensitive biologics
- **Molecular stability**: Prevents degradation reactions that occur in liquid phase
- **Long shelf life**: Removes almost all water (< 1% residual moisture)

### Process Variables

**Control Variables** (what we can set):
- `Pch`: Chamber pressure (Torr) - controlled by vacuum pump
- `Tsh`: Shelf temperature (°C) - controlled by heating/cooling fluid

**State Variables** (what we observe/predict):
- `Tsub`: Temperature at sublimation front (°C)
- `Tbot`: Temperature at vial bottom (°C)
- `dmdt`: Sublimation rate (kg/hr)
- `Lck`: Dried cake thickness (cm)

**Product Properties** (inherent to formulation):
- `Rp`: Product resistance to vapor flow (cm²-hr-Torr/g)
- `Kv`: Vial heat transfer coefficient (cal/s/K/cm²)

### Physical Picture

```
          Vacuum Chamber (Pch)
                 ↑
                 │ vapor flow (dmdt)
        ┌────────┴────────┐
        │  Dried Cake     │  Lck (increasing)
        │  (porous solid) │
        ├─────────────────┤ ← Sublimation front (Tsub)
        │  Frozen Product │  L (decreasing)
        │  (solid ice)    │
        └─────────────────┘
        │   Vial Bottom   │  (Tbot)
        └─────────────────┘
              ↑ Q_in
         Heated Shelf (Tsh)
```

**Key Insight**: The sublimation front moves downward as drying proceeds. Behind it is porous dried cake; ahead of it is solid ice.

---

## Heat Transfer Physics

### Energy Balance

At steady state (quasi-static assumption):
```
Heat IN = Heat OUT
Q_shelf = Q_sublimation
```

**Heat IN** (from shelf):
```python
Q_shelf = Kv * Av * (Tsh - Tbot)  # cal/s
```
- Conducted/radiated from heated shelf through vial bottom
- Proportional to temperature difference
- Limited by vial heat transfer coefficient Kv

**Heat OUT** (for sublimation):
```python
Q_sublimation = dmdt * dHs  # cal/s
```
- Consumed to convert ice → vapor
- Proportional to sublimation rate
- `dHs = 678 cal/g` is latent heat of sublimation for ice

### Vial Heat Transfer Coefficient

Empirical correlation:
```python
Kv = KC + KP * Pch + KD * Lck
```

**Physical interpretation**:
- `KC`: Base conduction (glass-metal contact, radiation)
- `KP * Pch`: Gas conduction through gap (increases with pressure)
- `KD * Lck`: Dried cake thermal resistance (increases with thickness)

**Typical values**:
- `KC ≈ 2.5e-4` cal/s/K/cm²
- `KP ≈ 1e-6` cal/s/K/cm²/Torr
- `KD ≈ -5e-5` cal/s/K/cm²/cm (negative: cake adds resistance)

**Why does Kv matter?**
- High Kv → more heat → faster drying but higher Tsub
- Low Kv → less heat → slower drying but lower Tsub
- Optimization trades off speed vs. temperature control

### Temperature Profile

```
Tsh (shelf)  >  Tbot (vial bottom)  >  Tsub (sublimation front)
 +10°C           -5°C                    -20°C
```

**Why Tbot > Tsub?**
- Heat must flow from hot (shelf) to cold (sublimation)
- Temperature gradient drives heat flux
- Larger gradient → faster heat transfer → faster drying

**Why is Tsub coldest?**
- Sublimation absorbs heat (endothermic: ΔH = +678 cal/g)
- Cools the sublimation front
- Like evaporative cooling (but from solid)

---

## Mass Transfer Physics

### Driving Force for Sublimation

Mass transfer is driven by **vapor pressure difference**:
```python
dmdt ∝ (Psub - Pch)
```

**Psub** (vapor pressure at sublimation front):
- Depends on Tsub via Antoine equation
- Higher Tsub → higher Psub → faster sublimation
```python
Psub = 2.698e10 * exp(-6144.96 / (Tsub + 273.15))  # Torr
```

**Pch** (chamber pressure):
- Controlled by vacuum system
- Lower Pch → larger driving force → faster sublimation

**Physical analogy**: Water flows downhill due to pressure difference. Vapor "flows" from high pressure (Psub) to low pressure (Pch).

### Product Resistance

The dried cake acts as a **porous barrier** to vapor flow:
```python
dmdt = (Ap / Rp) * (Psub - Pch)
```

**Resistance model**:
```python
Rp = R0 + A1 * Lck / (1 + A2 * Lck)
```

**Physical interpretation**:
- `R0`: Base resistance (initial nucleation layer)
- `A1 * Lck`: Linear term (cake thickness effect)
- `A2 * Lck`: Saturation term (resistance doesn't grow indefinitely)

**Why does resistance increase?**
- As Lck grows, vapor has longer path through porous cake
- Pores may collapse or tortuosity increases
- Like blowing through a straw: longer straw = harder to blow

**Typical values**:
- `R0 ≈ 1-5` cm²-hr-Torr/g
- `A1 ≈ 10-50` cm²-hr-Torr/g/cm
- `A2 ≈ 0.1-1` cm⁻¹

**Why does A2 matter?**
- Without A2: Rp grows without bound (unphysical)
- With A2: Rp asymptotes to `R0 + A1/A2` (physically realistic)
- Represents structural stabilization of dried cake

### Sublimation Rate

Combining heat and mass transfer:
```python
# From mass transfer
dmdt = (Ap / Rp) * (Psub - Pch)

# From energy balance
dmdt = Kv * Av * (Tsh - Tbot) / dHs

# These must be equal (implicit in Tsub)
```

**Key insight**: Sublimation rate is **doubly constrained**:
1. Mass transfer: Limited by product resistance
2. Heat transfer: Limited by heat input

**Analogy**: Like a funnel - flow limited by narrower opening (bottleneck).

---

## Coupling and Non-Monotonic Behavior

### Why Flux is Non-Monotonic

**Observation**: Sublimation flux does NOT decrease monotonically. It often **increases early** then decreases.

**Physical explanation**:

**Early Stage** (t < 20% of drying):
- Shelf temperature ramping up (Tsh increasing)
- Heat input increasing (Q_shelf ∝ Tsh - Tbot)
- Tsub rising → Psub rising → dmdt increasing
- **Heat transfer is bottleneck**

**Mid Stage** (20% < t < 80%):
- Tsh reaches setpoint (constant)
- Resistance starting to increase (Lck growing)
- But heat input still strong
- **Transition region**

**Late Stage** (t > 80%):
- Resistance very high (Lck large)
- Vapor pressure difference (Psub - Pch) decreasing
- dmdt decreasing
- **Mass transfer is bottleneck**

**Mathematical view**:
```python
dmdt = (Ap / Rp) * (Psub - Pch)
      = (Ap / Rp(Lck)) * (Psub(Tsub) - Pch)
```
- Rp(Lck) increases with time (bad for dmdt)
- Psub(Tsub) can increase if Tsh is ramping (good for dmdt)
- Net effect: **non-monotonic**, depends on ramp rate

**Implications for AI assistants**:
- ❌ Don't write `assert flux[i+1] < flux[i]` (will fail!)
- ✅ Do write `assert flux eventually decreases` (check late stage)
- ✅ Do expect peak flux at 10-30% dried

### Temperature Coupling

Tsub is **implicitly defined** by energy balance:
```python
Kv * Av * (Tsh - Tbot) = (Ap / Rp) * (Psub(Tsub) - Pch) * dHs
```

This is a **nonlinear equation** in Tsub:
- Psub(Tsub) is exponential (Antoine equation)
- Must solve numerically (fsolve)

**Physical picture**:
- If Tsub too high → Psub high → dmdt high → needs more heat (inconsistent)
- If Tsub too low → Psub low → dmdt low → needs less heat (inconsistent)
- Unique Tsub where heat supply = heat demand (equilibrium)

**Why this matters for Pyomo**:
- Cannot use explicit formula for Tsub
- Must formulate as constraint: `f(Tsub, Tsh, Pch, ...) = 0`
- Requires reformulation (log transform, auxiliary variables)

---

## Valid Parameter Ranges

### Physical Bounds

| Variable | Min | Max | Why |
|----------|-----|-----|-----|
| Pch | 0.05 Torr | 0.5 Torr | Below: choked flow; Above: condensation risk |
| Tsh | -50°C | +50°C | Equipment limits |
| Tsub | -60°C | 0°C | Below: no data; Above: melting |
| Tbot | -60°C | +50°C | Between Tsh and Tsub |
| dmdt | 0 | ∞ | Physically non-negative |

### Practical Constraints

**Temperature limits**:
- **Collapse temperature** (Tc): Product structure collapses if Tsub > Tc
  - Typical Tc: -10°C to -40°C (formulation-dependent)
  - Must ensure `Tsub ≤ Tc - margin` (e.g., Tc - 5°C)
  
**Pressure limits**:
- **Choked flow**: Below ~0.03 Torr, vapor velocity reaches sonic limit
  - Further pressure reduction doesn't increase flow
  - Minimum practical Pch ≈ 0.05 Torr
  
- **Condensation**: Above ~0.5 Torr, vapor may condense on shelf
  - Re-condensed ice interferes with heat transfer
  - Maximum practical Pch ≈ 0.3-0.5 Torr

**Resistance limits**:
- `R0` > 0 (must have some base resistance)
- `A1` ≥ 0 (resistance increases or stays constant with thickness)
- `A2` ≥ 0 (saturation parameter, non-negative)

**Heat transfer limits**:
- `Kv` > 0 (heat must flow from hot to cold)
- Typical range: `1e-5` to `1e-2` cal/s/K/cm²

---

## Edge Cases and Their Physics

### Very Low Shelf Temperature (Tsh < -40°C)

**Observation**: Sometimes Tbot < Tsub (temperature inversion)

**Physical explanation**:
- Very slow sublimation (low heat input)
- Numerical artifact: solver struggles with small fluxes
- Energy balance approximately satisfied, but T_bot prediction unstable

**How to handle**:
- Accept artifact if dmdt is negligible (< 1e-6 kg/hr)
- Or verify energy balance holds: `abs(Q_in - Q_out) / Q_out < 0.01`
- Physically: process is so slow that temperatures are ill-defined

### Very High Pressure (Pch > 0.3 Torr)

**Observation**: Drying time decreases less than expected

**Physical explanation**:
- Higher Pch reduces driving force (Psub - Pch)
- Partially offset by higher Kv (gas conduction)
- Diminishing returns: at high Pch, benefit of more heat < cost of less ΔP

### Very Low Resistance (R0 < 0.5)

**Observation**: Drying very fast but hard to control temperature

**Physical explanation**:
- Mass transfer not limiting → heat transfer is bottleneck
- Small changes in Tsh → large changes in Tsub
- Sensitive process, needs careful control

### Very High Resistance (A1 > 50)

**Observation**: Drying very slow, Tsub approaches Tbot

**Physical explanation**:
- Mass transfer severely limiting
- Heat input cannot be utilized (vapor can't escape fast enough)
- Sublimation rate limited by resistance, not heat
- Temperature gradient small (little heat flux needed)

### End of Drying (L → 0)

**Observation**: Flux drops rapidly, Tsub → Tbot

**Physical explanation**:
- Sublimation ceases (no more ice)
- No latent heat consumption
- Vial bottom heats up toward shelf temperature
- Termination criterion: `L ≤ 0` or `frac_dried ≥ 0.99`

---

## Numerical Considerations

### Mass Balance Error (~2%)

**Observation**: Integrated mass ≠ initial mass by ~1-2%

**Physical reality**: Mass balance IS conserved (law of thermodynamics)

**Numerical explanation**:
- `solve_ivp` uses adaptive time stepping
- Trapezoidal integration of non-uniform flux
- Typical with `Tstep=100` time points
- Would be < 0.1% with `Tstep=1000`, but slower

**How to handle**:
- Accept 2% error as numerical tolerance
- Use `rtol=0.02` in mass balance tests
- Increase Tstep if higher precision needed (at cost of speed)

### Stiff Differential Equations

**Why use BDF method?**
- Temperature dynamics are **stiff** (multiple time scales)
- Fast: Energy balance equilibrates in seconds
- Slow: Ice layer shrinks over hours
- Ratio: ~10⁴ to 10⁵

**BDF (Backward Differentiation Formula)**:
- Implicit method, handles stiffness well
- Allows larger time steps than explicit methods
- Standard for lyophilization simulation

### Implicit Temperature Solver

**Why use fsolve?**
- Energy balance is implicit in Tsub
- Could iterate manually, but fsolve is robust
- Convergence typically 3-5 iterations

**How to reformulate for Pyomo?**
- Cannot call fsolve in constraint
- Must express as algebraic constraint:
  ```python
  Q_shelf - Q_sublimation = 0
  ```
- Pyomo solver handles implicitness

### Exponential Vapor Pressure

**Why log transform?**
- `exp(-6144.96 / (Tsub + 273.15))` is exponential
- In Pyomo, can cause overflow/underflow
- Numerically unstable for optimization

**Solution**:
```python
# Instead of: Psub = A * exp(B / Tsub)
# Use: log(Psub) = log(A) + B / Tsub
log_Psub = pyo.Var()
model.con = pyo.Constraint(expr=log_Psub == log(2.698e10) - 6144.96/(Tsub+273.15))
# Then: Psub = exp(log_Psub) where needed
```

**Benefits**:
- No overflow (log maps exp to linear)
- Better conditioned Jacobian
- Standard technique in chemical engineering optimization

### Initialization for Convergence

**Why warmstart?**
- NLP solvers need good initial guess
- Far from optimum → may not converge
- Close to optimum → converges in 10-50 iterations

**Strategy**:
1. Solve with scipy (fast, robust)
2. Use scipy solution to initialize Pyomo variables
3. Pyomo refines solution (exploits problem structure)

**Example**:
```python
# Get scipy solution
scipy_sol = opt_Pch_Tsh.optimize_scipy(...)

# Initialize Pyomo model
model.Pch.set_value(scipy_sol['Pch'])
model.Tsh.set_value(scipy_sol['Tsh'])
model.Tsub.set_value(scipy_sol['Tsub'])

# Solve (will converge much faster)
opt.solve(model)
```

---

## Common Misconceptions (for AI assistants)

### ❌ "Higher pressure always means faster drying"

**Reality**: Higher Pch has competing effects:
- ✅ Increases Kv (more heat transfer)
- ❌ Decreases driving force (Psub - Pch)
- Net effect: optimal Pch exists (typically 0.1-0.2 Torr)

### ❌ "Flux should decrease monotonically"

**Reality**: Flux is non-monotonic due to shelf temperature ramp
- Early: Tsh rising → flux increasing
- Late: Rp rising → flux decreasing
- Expect peak at 10-30% dried

### ❌ "Pch in output is in Torr"

**Reality**: `output[:, 4]` is in **mTorr** (multiplied by 1000)
- Internal calculations use Torr
- Output converted for historical reasons
- Always check units!

### ❌ "dried column is percentage 0-100"

**Reality**: `output[:, 6]` is **fraction 0-1**
- 0.5 means 50% dried
- 0.99 means 99% dried
- NOT 99 (which would be 9900%!)

### ❌ "Mass balance must be exact"

**Reality**: 1-2% error is normal for numerical integration
- Not a code bug
- Reduce with more time points (slower)
- Or accept tolerance in tests

### ❌ "Tbot is always > Tsub"

**Reality**: Can have Tbot < Tsub at extreme conditions
- Artifact of very slow sublimation
- Not physically meaningful
- Check if dmdt is negligible (< 1e-6)

---

## Quick Reference for Common Checks

### Is this output physically reasonable?

```python
def check_physics(output):
    """Quick physical sanity checks."""
    time = output[:, 0]
    Tsub = output[:, 1]
    Tbot = output[:, 2]
    Tsh = output[:, 3]
    Pch = output[:, 4]  # mTorr!
    flux = output[:, 5]
    dried = output[:, 6]
    
    # Time should be positive and increasing
    assert np.all(time >= 0)
    assert np.all(np.diff(time) > 0)
    
    # Temperatures should be in reasonable range
    assert np.all(Tsub >= -60) and np.all(Tsub <= 0)
    assert np.all(Tbot >= -60) and np.all(Tbot <= 50)
    
    # Pressure should be in mTorr range
    assert np.all(Pch >= 0) and np.all(Pch <= 1000)  # 0-1 Torr in mTorr
    
    # Flux should be non-negative
    assert np.all(flux >= 0)
    
    # Dried fraction should be 0-1 and increasing
    assert np.all(dried >= 0) and np.all(dried <= 1)
    assert np.all(np.diff(dried) >= 0)  # monotonic increase
    
    # Final dried should be close to 1
    assert dried[-1] >= 0.99
    
    print("✅ Output is physically reasonable")
```

---

## References for Deep Dives

### Foundational Papers
- Pikal, M.J. (1985) "Use of laboratory data in freeze drying process design"
- Tang, X. & Pikal, M.J. (2004) "Design of freeze-drying processes for pharmaceuticals"

### Textbooks
- Franks, F. (1998) "Freeze-Drying of Pharmaceuticals and Biopharmaceuticals"
- Oetjen, G.W. & Haseley, P. (2004) "Freeze-Drying"

### Online Resources
- FDA Guidance for Industry: PAT for Freeze-Drying
- Lyophilization Technology Roadmap (PQRI)

---

## Questions?

When debugging physics:
1. **Check units first** - Torr vs mTorr, fraction vs percentage
2. **Verify energy balance** - Q_in ≈ Q_out (within 1%)
3. **Check mass balance** - Integrated flux ≈ initial mass (within 2%)
4. **Plot temperature profile** - Should have Tsh > Tbot ≥ Tsub (usually)
5. **Expect non-monotonic flux** - Peak in early-mid stage is normal
6. **Check edge cases** - Very slow processes may have artifacts

When writing tests:
- Use physical intuition (what should happen?)
- Allow numerical tolerance (2% for integration)
- Test edge cases separately (very low T, very high Rp)
- Document physical reasoning in test docstrings
