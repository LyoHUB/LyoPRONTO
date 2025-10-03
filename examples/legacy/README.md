# Legacy Example Scripts

This directory contains the original example scripts from the early development of LyoPRONTO. These scripts are preserved for:

1. **Historical reference**: Shows original usage patterns
2. **Testing**: Validated by `tests/test_example_scripts.py`
3. **Backwards compatibility**: Users with existing workflows

## Scripts

### ex_knownRp_PD.py
**Purpose**: Primary drying simulation with **known** product resistance parameters.

**Usage**:
```bash
cd examples/legacy
python ex_knownRp_PD.py
```

**Inputs**:
- Vial geometry (Av, Ap, Vfill)
- Product properties (cSolid, R0, A1, A2)
- Heat transfer coefficients (KC, KP, KD)
- Chamber pressure profile
- Shelf temperature profile

**Outputs**:
- `output_saved_YYMMDD_HHMM.csv` - Time series data
- `Temperatures_YYMMDD_HHMM.pdf` - Temperature profiles
- `Pressure,SublimationFlux_YYMMDD_HHMM.pdf` - Pressure and flux
- `PercentDried_YYMMDD_HHMM.pdf` - Drying progress

### ex_unknownRp_PD.py
**Purpose**: Primary drying simulation with **unknown** product resistance - estimates R0, A1, A2 from experimental temperature data.

**Usage**:
```bash
cd examples/legacy
python ex_unknownRp_PD.py
```

**Inputs**:
- All inputs from `ex_knownRp_PD.py` EXCEPT R0, A1, A2
- Experimental product temperature data (`temperature.dat`)

**Outputs**:
- Same as `ex_knownRp_PD.py` plus:
- Estimated parameters: R0, A1, A2 printed to console

**Test Data**: `temperature.dat` (452 time points)

## Migration to Modern Examples

For new projects, use the modern examples in `examples/`:

| Legacy Script | Modern Equivalent |
|---------------|-------------------|
| `ex_knownRp_PD.py` | `example_web_interface.py` |
| `ex_unknownRp_PD.py` | `example_parameter_estimation.py` |

## Differences: Legacy vs Modern

### Legacy Scripts
- ✅ Original implementation
- ✅ Comprehensive plotting (LaTeX formatting)
- ✅ CSV output with timestamps
- ⚠️ Direct imports from package
- ⚠️ Hardcoded file paths
- ⚠️ Less modular structure

### Modern Examples
- ✅ Cleaner code structure
- ✅ Better error handling
- ✅ Consistent naming conventions
- ✅ Documentation strings
- ✅ More modular/reusable
- ✅ Integration with test suite

## Testing

Legacy scripts are tested in `tests/test_example_scripts.py`:

```python
def test_ex_knownRp_execution():
    """Test that ex_knownRp_PD.py runs successfully."""
    
def test_ex_unknownRp_execution():
    """Test that ex_unknownRp_PD.py runs successfully."""
    
def test_ex_unknownRp_parameter_values():
    """Test that parameter estimation produces reasonable values."""
```

Run tests:
```bash
pytest tests/test_example_scripts.py -v
```

## Notes

1. **File Paths**: Scripts expect to run from `examples/legacy/` directory
2. **Temperature Data**: Uses `temperature.dat` (2-column format: time, temperature)
3. **Output Location**: Generates files in current directory
4. **Dependencies**: Same as main package (see `requirements-dev.txt`)

## See Also

- `examples/README.md` - Modern examples documentation
- `tests/test_example_scripts.py` - Legacy script tests
- `docs/GETTING_STARTED.md` - Developer guide
