# Input YAML Specification

LyoPRONTO reads simulation inputs from a YAML file via `read_inputs(filename)` and writes them back via `save_inputs(inputs, timestamp)`. The YAML uses `ruamel.yaml` (YAML 1.1, block style). Large arrays (`time_data`, `temp_data`) are stripped before writing; if your input references a temperature data file, the `product_temp_filename` key is preserved as a reminder, and you must load the data separately into `time_data` / `temp_data` before calling `execute_simulation()`.

When read into Python, this YAML becomes a dictionary of dictionaries: you can construct that dictionary-of-dictionaries structure yourself in a script and pass it to simulations.

## Top-Level Structure

```yaml
# always required:
sim:           # simulation configuration (dict) — required
vial:          # vial geometry (dict) — required
product:       # product properties (dict) — required
ht:            # heat transfer parameters (dict) — conditional
Pchamber:      # chamber pressure profile (dict) — conditional shape
Tshelf:        # shelf temperature profile (dict) — conditional shape
# sometimes required:
dt: 0.01       # time step (hr) — required
eq_cap:        # equipment capability (dict) — design space / optimizer
nVial: 398     # number of vials — design space / optimizer
h_freezing:    # freezing heat transfer coefficient — freezing only
t_dry_exp:     # experimental drying time — Kv unknown only
Kv_range:      # Kv search bounds — Kv unknown only
time_data:     # experimental time array — Rp unknown only
temp_data:     # experimental temperature array — Rp unknown only
product_temp_filename:  # path to temperature file — Rp unknown only
```

---

## 1. `sim` — Simulation Configuration

| Key | Type | Description |
|---|---|---|
| `tool` | `str` | One of: `"Freezing Calculator"`, `"Primary Drying Calculator"`, `"Design Space Generator"`, `"Optimizer"` |
| `Kv_known` | `bool` | Whether the vial heat transfer coefficient is known (Drying calculator only)|
| `Rp_known` | `bool` | Whether product resistance is known (Drying calculator only)|
| `Variable_Pch` | `bool` | Chamber pressure is an optimization variable (Optimizer only) |
| `Variable_Tsh` | `bool` | Shelf temperature is an optimization variable (Optimizer only) |

**Constraints**:
- For `"Optimizer"`, at least one of `Variable_Pch` or `Variable_Tsh` must be `true`.
- For `"Primary Drying Calculator"`, `Kv_known` and `Rp_known` cannot both be `false`.

---

## 2. `vial` — Vial Geometry

| Key | Type | Unit | Description |
|---|---|---|---|
| `Av` | `float` | cm² | Vial cross-sectional area |
| `Ap` | `float` | cm² | Product surface area |
| `Vfill` | `float` | mL | Fill volume |

**Example**:
```yaml
vial:
  Av: 3.8
  Ap: 3.14
  Vfill: 2.0
```

---

## 3. `product` — Product Properties

| Key | Type | Unit | Required When |
|---|---|---|---|
| `cSolid` | `float` | g/mL | Always |
| `Tpr0` | `float` | °C | `Freezing Calculator` |
| `Tf` | `float` | °C |  `Freezing Calculator` |
| `Tn` | `float` | °C |  `Freezing Calculator` |
| `R0` | `float` | cm²·hr·Torr/g | Always, unless `Rp_known` is `false` |
| `A1` | `float` | cm·hr·Torr/g | Always, unless `Rp_known` is `false`  |
| `A2` | `float` | 1/cm | Always, unless `Rp_known` is `false` |
| `T_pr_crit` | `float` | °C | `Design Space Generator`, `Optimizer`, optional for `Primary Drying Calculator` |

**Notes**:

- `T_pr_crit` should be set 2–3 °C below the collapse or glass transition temperature, to allow a safety margin.
- For `"Primary Drying Calculator"` with `Rp_known == false`, only `cSolid` and `T_pr_crit` are needed.

**Examples**:

*Freezing*:
```yaml
product:
  cSolid: 0.0
  Tpr0: 15.8
  Tf: -1.54
  Tn: -5.84
```

*Drying (Rp known)*:
```yaml
product:
  cSolid: 0.05
  R0: 1.4
  A1: 16.0
  A2: 0.0
  T_pr_crit: -5
```

---

## 4. `ht` — Heat Transfer Parameters

Required for all tools except `Freezing Calculator` or `Primary Drying Calculator` with `Kv_known == false`.
!!! info "Single value of Kv"
    If you only have a single value of $K_v$ and you are simulating at the matching chamber pressure, you can put that value in as `KC` and set `KP`, `KD` both to zero.


| Key | Type | Unit | Description |
|---|---|---|---|
| `KC` | `float` | cal/(s·K·cm²) | Conductive/radiative coefficient |
| `KP` | `float` | cal/(s·K·cm²·Torr) | Pressure-dependent coefficient |
| `KD` | `float` | 1/Torr | Pressure-dependent denominator |

The effective vial coefficient is: `Kv = KC + KP × Pch / (1 + KD × Pch)`

**Example**:
```yaml
ht:
  KC: 0.000275
  KP: 0.000893
  KD: 0.46
```

---

## 5. `Pchamber` — Chamber Pressure Profile

The structure depends on the simulation mode:

**Fixed setpoint** (Primary Drying Calculator, non-variable Optimizer):

| Key | Type | Unit | Description |
|---|---|---|---|
| `setpt` | `list[float]` | Torr | Pressure set points |
| `dt_setpt` | `list[float]` | min | Duration per set point (same length as `setpt`) |
| `ramp_rate` | `float` | Torr/min | Ramp rate between set points |

```yaml
Pchamber:
  setpt: [0.15]
  dt_setpt: [1800.0]
  ramp_rate: 0.5
```

**Sweep array** (Design Space Generator):

```yaml
Pchamber:
  setpt: [0.02, 0.05, 0.1, 0.15]
```

**Bounds** (Optimizer with `Variable_Pch == true`):

```yaml
Pchamber:
  min: 0.05
  max: 1000
```

Not required for `Freezing Calculator`.

---

## 6. `Tshelf` — Shelf Temperature Profile

**Fixed setpoint** (Primary Drying Calculator, non-variable Optimizer):

| Key | Type | Unit | Description |
|---|---|---|---|
| `init` | `float` | °C | Initial shelf temperature |
| `setpt` | `list[float]` | °C | Temperature set points |
| `dt_setpt` | `list[float]` | min | Duration per set point (same length as `setpt`) |
| `ramp_rate` | `float` | °C/min | Ramp rate between set points |

```yaml
Tshelf:
  init: -35.0
  setpt: [20.0]
  dt_setpt: [1800.0]
  ramp_rate: 1.0
```

**Sweep array** (Design Space Generator):

```yaml
Tshelf:
  init: -5.0
  setpt: [-15, 0, 30, 90]
  ramp_rate: 1.0
```

**Bounds** (Optimizer with `Variable_Tsh == true`):

```yaml
Tshelf:
  min: -45
  max: 120
```

---

## 7. Equipment and Scalar Keys

| Key | Type | Unit | Required When | Description |
|---|---|---|---|---|
| `dt` | `float` | hr | Always | Simulation time step |
| `eq_cap.a` | `float` | kg/hr | Design Space & Optimizer | Equipment capability intercept |
| `eq_cap.b` | `float` | kg/hr/Torr | Design Space & Optimizer | Equipment capability slope |
| `nVial` | `int` | — | Design Space & Optimizer | Number of vials in batch |

Equipment capability models choked flow to the condenser: `dm/dt [kg/hr] = a + b × Pch [Torr]`

---

## 8. Other Top-level Keys by Mode

| Key | Type | Required When | Description |
|---|---|---|---|
| `h_freezing` | `float` (W/m²/K) | `Freezing Calculator` | Heat transfer coefficient during freezing |
| `t_dry_exp` | `float` (hr) | `Primary Drying Calculator` +  `Kv_known == false` | Experimental drying time for Kv optimization |
| `Kv_range` | `list[float, float]` (cal/s/K/cm²) | `Primary Drying Calculator` + `Kv_known == false` | Lower and upper bounds for Kv root-finding |
| `time_data` | `list[float]` (hr) | `Rp_known == false` | Experimental time measurements |
| `temp_data` | `list[float]` (°C) | `Rp_known == false` | Experimental product temperature measurements |
| `product_temp_filename` | `str` | `Rp_known == false` | Path to temperature data file (informational only) |
