# LyoPRONTO Examples

This directory contains example scripts demonstrating how to use LyoPRONTO.

## Available Examples

### `example_web_interface.py` ⭐ **Recommended Starting Point**

**Purpose**: Replicate the LyoPRONTO web interface calculation

**Features**:
- Loads temperature profile from `test_data/temperature.txt`
- Runs primary drying simulation with known product resistance
- Saves results in web interface CSV format
- Creates publication-quality plots
- Compares results with web interface reference output

**Usage**:
```bash
python examples/example_web_interface.py
```

**Output**:
- Console: Formatted report with all parameters and results
- CSV: `examples/outputs/lyopronto_primary_drying_<timestamp>.csv`
- PNG: `examples/outputs/primary_drying_results.png`

**Input Parameters** (from web interface):
- Vial: 3.8 cm² area, 3.14 cm² product area, 2 mL fill
- Product: R₀=1.4, A₁=16, A₂=0, 0.05 g/mL solid content
- Process: 0.15 Torr, -35°C → 20°C shelf ramp
- Heat transfer: Kc=0.000275, Kp=0.000893, Kd=0.46

**Expected Results**:
- Drying time: 6.66 hours
- Max temperature: -14.77°C
- Final dried: 99.89-100%

---

### `example_optimizer.py` 🔧 **Optimization Example**

**Purpose**: Demonstrate optimizer functionality with fixed chamber pressure and shelf temperature optimization

**Features**:
- Optimizes shelf temperature profile to maximize drying rate
- Maintains product temperature at critical limit
- Fixed chamber pressure operation
- Compares results with web interface optimizer output

**Usage**:
```bash
python examples/example_optimizer.py
```

**Output**:
- Console: Formatted report with optimization results
- CSV: `examples/outputs/lyopronto_optimizer_<timestamp>.csv`

**Input Parameters** (from web interface optimizer):
- Vial: 3.8 cm² area, 3.14 cm² product area, 2 mL fill
- Product: R₀=1.4, A₁=16, A₂=0, 0.05 g/mL solid content
- Critical Product Temperature: -5°C
- Fixed Chamber Pressure: 0.15 Torr (150 mTorr)
- Shelf Temperature Range: -45 to 120°C
- Initial Shelf Temperature: -35°C
- Temperature Ramp Rate: 1°C/min
- Equipment Capability: a=-0.182 kg/hr, b=11.7 kg/hr·Torr
- Number of Vials: 398

**Expected Results**:
- Drying Time: ~2.123 hr
- Optimal shelf temperature profile maintains product at -5°C
- Significantly faster than non-optimized cycles

---

### `example_freezing.py` ❄️ **Freezing Simulation**

**Purpose**: Simulate the freezing phase of lyophilization

**Features**:
- Models cooling, nucleation, crystallization, and solidification phases
- Tracks product and shelf temperatures over time
- Simulates supercooling and latent heat release
- Saves freezing profile for analysis

**Usage**:
```bash
python examples/example_freezing.py
```

**Output**:
- Console: Formatted report with freezing phase timing
- CSV: `examples/outputs/lyopronto_freezing_<timestamp>.csv`

**Input Parameters** (from web interface freezing calculator):
- Vial: 3.8 cm² area, 3.14 cm² product area, 2 mL fill
- Product: 0.05 g/mL solid content
- Initial Product Temperature: 15.8°C
- Freezing Temperature: -1.52°C
- Nucleation Temperature: -5.84°C
- Initial Shelf Temperature: -35°C
- Target Shelf Temperature: 20°C
- Temperature Ramp Rate: 1°C/min
- Heat Transfer Coefficient: 38 W/m²·K

**Expected Results**:
- Cooling phase: Product cools to nucleation temperature
- Nucleation: Rapid transition to freezing point
- Crystallization: Product at freezing temp during phase change
- Solidification: Product cools to final temperature

---

### `example_design_space.py` 📊 **Design Space Analysis**

**Purpose**: Generate design space for primary drying optimization

**Features**:
- Evaluates three design space modes:
  1. Shelf Temperature isotherms (fixed Tshelf, varying Pch)
  2. Product Temperature isotherms (fixed Tproduct at critical, varying Pch)
  3. Equipment Capability (maximum sublimation rate)
- Saves results in web interface CSV format
- Compares with web interface reference output

**Usage**:
```bash
python examples/example_design_space.py
```

**Output**:
- Console: Formatted report with all parameters and results
- CSV: `examples/outputs/lyopronto_design_space_<timestamp>.csv`

**Input Parameters** (from web interface):
- Vial: 3.8 cm² area, 3.14 cm² product area, 2 mL fill
- Product: R₀=1.4, A₁=16, A₂=0, 0.05 g/mL solid, T_crit=-5°C
- Process: 150 mTorr, -35°C initial, 20°C setpoint
- Heat transfer: Kc=0.000275, Kp=0.000893, Kd=0.46
- Equipment: a=-0.182 kg/hr, b=11.7 kg/hr/Torr, 398 vials

**Expected Results**:
1. **Shelf Temperature = 20°C**:
   - Max temperature: 1.32°C
   - Drying time: 0.01 hr (very fast, limited by initial conditions)
   
2. **Product Temperature = -5°C** (at critical limit):
   - Drying time: 1.98 hr
   - Average flux: 3.11 kg/hr/m²
   - Minimum flux: 2.29 kg/hr/m²
   
3. **Equipment Capability** (maximum equipment rate):
   - Max temperature: 4.12°C
   - Drying time: 0.49 hr (fastest feasible)
   - Constant flux: 12.59 kg/hr/m²

**Note**: The shelf temperature mode with high Tshelf (20°C) completes very quickly (0.01 hr), which represents the edge case where the initial conditions allow rapid drying. The product temperature and equipment capability modes provide more realistic operating scenarios.

---

### `example_parameter_estimation.py` 🔍 **Parameter Estimation**

**Purpose**: Estimate product resistance parameters (R₀, A₁, A₂) from experimental temperature data

**Features**:
- Demonstrates `calc_unknownRp` module (inverse modeling)
- Loads experimental temperature measurements
- Fits product resistance model to data
- Prints estimated parameters with uncertainties
- Compares model fit to experimental data
- Generates diagnostic plots

**Usage**:
```bash
python examples/example_parameter_estimation.py
```

**Output**:
- Console: Estimated R₀, A₁, A₂ parameters with standard errors
- CSV: `examples/outputs/lyopronto_parameter_estimation_<timestamp>.csv`
- PNG: `examples/outputs/parameter_estimation_results.png` (4-panel diagnostic plot)

**Input Parameters**:
- Vial: 3.8 cm² area, 3.14 cm² product area, 2 mL fill
- Product: 0.05 g/mL solid content, -5°C critical temperature
- Process: 0.15 Torr, -35°C → 20°C shelf ramp
- Heat transfer: Kc=0.000275, Kp=0.000893, Kd=0.46
- Experimental data: `test_data/temperature.txt` (time vs temperature measurements)

**Expected Results**:
- Estimated parameters (example values):
  - R₀: ~1.4 cm²·hr·Torr/g
  - A₁: ~16 cm·hr·Torr/g
  - A₂: ~0 1/cm
- Good fit between model and experimental temperatures
- Physically reasonable resistance profile

**Use Case**: When you have experimental temperature data from a lyophilization run and want to determine the product resistance parameters for your formulation. These parameters can then be used in predictive simulations with `calc_knownRp`.

---

## Running Examples

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt  # or requirements-dev.txt for development
```

### Run an Example
```bash
# Navigate to repo root
cd /path/to/LyoPRONTO

# Run example
python examples/example_web_interface.py
```

### View Outputs
```bash
# View CSV output
less examples/outputs/lyopronto_primary_drying_*.csv

# View plot (requires image viewer)
xdg-open examples/outputs/primary_drying_results.png  # Linux
open examples/outputs/primary_drying_results.png      # macOS
start examples/outputs/primary_drying_results.png     # Windows
```

---

## Example Structure

Each example script follows this pattern:

```python
#!/usr/bin/env python
"""
Example: Brief Description

Longer description of what the example demonstrates.
"""

# 1. Imports
from lyopronto import calc_knownRp
import numpy as np

# 2. Input Parameters
vial = {'Av': 3.8, 'Ap': 3.14, 'Vfill': 2.0}
product = {'R0': 1.4, 'A1': 16.0, 'A2': 0.0, 'cSolid': 0.05}
# ... more parameters

# 3. Run Simulation
output = calc_knownRp.dry(vial, product, ht, Pchamber, Tshelf, dt)

# 4. Process Results
drying_time = output[-1, 0]
max_temp = output[:, 1].max()
# ... extract metrics

# 5. Save/Display
# Save to CSV, create plots, etc.
```

---

## Creating New Examples

To add a new example:

1. **Create script**: `examples/example_<name>.py`
2. **Follow structure**: Use pattern above
3. **Add docstring**: Explain purpose and usage
4. **Test it**: Ensure it runs successfully
5. **Document here**: Add section to this README
6. **Add tests**: Create tests in `tests/test_examples.py` (if needed)

### Example Template

```python
#!/usr/bin/env python
"""
Example: <Brief Title>

This example demonstrates <what it does>.

Features:
- <Feature 1>
- <Feature 2>

Usage:
    python examples/example_<name>.py

Output:
    - <Output 1>
    - <Output 2>
"""

from lyopronto import calc_knownRp

def main():
    # Your example code here
    pass

if __name__ == "__main__":
    main()
```

---

## Planned Examples

Future examples to add:

### `example_pyomo_optimization.py` (Future)
- Use Pyomo-based simultaneous optimization
- Compare with scipy approach
- Demonstrate coexistence of scipy and Pyomo methods

---

## Legacy Examples

The `legacy/` directory contains the original example scripts from early LyoPRONTO development:

- **`ex_knownRp_PD.py`**: Original primary drying example (known resistance)
- **`ex_unknownRp_PD.py`**: Original parameter estimation example

These scripts are preserved for historical reference and backwards compatibility. For new projects, use the modern examples listed above.

See [`legacy/README.md`](legacy/README.md) for details.

---

## Related Directories

- **`test_data/`**: Reference input files used by examples
- **`examples/outputs/`**: Generated output files from examples
- **`examples/legacy/`**: Original example scripts (pre-refactoring)
- **`tests/`**: Test suite including example validation tests

---

## Troubleshooting

### Import Error: "No module named 'lyopronto'"
**Solution**: Make sure you're running from the repository root:
```bash
cd /path/to/LyoPRONTO
python examples/example_web_interface.py
```

Or install in development mode:
```bash
pip install -e .
```

### File Not Found: "temperature.txt"
**Solution**: The file should be in `test_data/`. Check that it exists:
```bash
ls test_data/temperature.txt
```

### Plot Window Doesn't Appear
**Solution**: Plots are saved to `examples/outputs/` even if the window doesn't show. Check for the PNG file.

---

## Questions?

- 📖 See [GETTING_STARTED.md](../GETTING_STARTED.md) for general usage guide
- 🧪 See [README_TESTING.md](../README_TESTING.md) for testing information
- 🏗️ See [ARCHITECTURE.md](../ARCHITECTURE.md) for code structure
- 💡 See [.github/copilot-examples.md](../.github/copilot-examples.md) for code snippets
