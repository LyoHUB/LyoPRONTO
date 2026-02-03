# LyoPRONTO Test Data

This directory contains reference data and input files used for validation and testing.

## Reference Files (from Web Interface)

These files contain reference outputs from the LyoPRONTO web interface for validation. They use the `reference_` prefix to distinguish them from locally generated outputs.

### `reference_primary_drying.csv`
Reference output from web interface primary drying calculator.

- **Source**: Web interface output (Oct 1, 2025)
- **Original name**: `lyopronto_primary_drying_Oct_01_2025_18_48_08.csv`
- **Format**: Seven columns (time, Tsub, Tbot, Tsh, Pch, flux, frac_dried)
- **Points**: 668 data points
- **Usage**: Validation for `test_web_interface.py`
- **Key Results**: 6.66 hr drying time, -14.77°C max temperature

### `reference_optimizer.csv`
Reference output from web interface optimizer.

- **Source**: Web interface optimizer (Oct 1, 2025)
- **Original name**: `lyopronto_optimizer_Oct_01_2025_20_03_23.csv`
- **Format**: Seven columns (time, Tsub, Tbot, Tsh, Pch, flux, frac_dried)
- **Points**: 216 data points
- **Usage**: Validation for `test_opt_Tsh.py`
- **Key Results**: 2.123 hr optimal drying time, -5.00°C product temperature

### `reference_freezing.csv`
Reference output from web interface freezing calculator.

- **Source**: Web interface freezing calculator (Oct 1, 2025)
- **Original name**: `lyopronto_freezing_Oct_01_2025_20_28_12.csv`
- **Format**: Three columns (time, Tshelf, Tproduct)
- **Points**: 3003 data points
- **Usage**: Validation for `test_freezing.py`
- **Key Results**: ~30 hr total freezing time, all phases simulated

### `reference_design_space.csv`
Reference output from web interface design space generator.

- **Source**: Web interface design space (Oct 2, 2025)
- **Original name**: `lyopronto_design_space_Oct_02_2025_12_13_08.csv`
- **Format**: Semicolon-separated values with sections
- **Sections**: Shelf temperature, Product temperature, Equipment capability
- **Usage**: Validation for `test_design_space.py`

## Input Files

### `temperature.txt`
Temperature profile used as input for the primary drying calculator example.

- **Source**: Web interface input
- **Format**: Two columns (time in hr, shelf temperature in °C)
- **Points**: 453 data points
- **Usage**: Input for `example_web_interface.py`

---

## File Naming Convention

- **Reference data** (from web interface): `reference_<mode>.csv`
- **Generated output** (from local runs): `lyopronto_<mode>_<timestamp>.csv` (in `examples/outputs/`)
- **Input data**: Descriptive names (e.g., `temperature.txt`)

This naming scheme makes it clear which files are ground truth references vs. locally generated outputs.

---

## Adding New Test Data

When adding new test data files:

1. **Place files here**: `test_data/`
2. **Use descriptive names**: Include date or case description
3. **Document in this README**: Add section describing the file
4. **Reference in tests**: Update test files to use the data
5. **Commit to repo**: Test data should be version controlled

## Data Format Guidelines

- **CSV files**: Use semicolon (`;`) delimiter to match web interface
- **Text files**: Use tab-separated or space-separated values
- **Units**: Always specify units in column headers
- **Documentation**: Include source and purpose in README

## Do Not Include

- ❌ Temporary output files
- ❌ Large binary files (>10 MB)
- ❌ Sensitive or proprietary data
- ❌ Generated files that can be reproduced

## Size Limits

Keep test data files small (<1 MB each) to avoid bloating the repository. If larger files are needed, consider:
- Hosting externally and downloading during tests
- Using compressed formats
- Generating synthetic data in test fixtures
