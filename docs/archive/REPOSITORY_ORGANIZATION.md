# Repository Organization Guide

This document describes the organizational structure of the LyoPRONTO repository after the cleanup and reorganization completed on October 1, 2025.

## Directory Structure

```
LyoPRONTO/
├── .github/                          # GitHub-specific files
│   ├── workflows/                    # CI/CD workflows
│   │   └── tests.yml                # Automated testing pipeline
│   ├── copilot-instructions.md       # Instructions for GitHub Copilot
│   └── copilot-examples.md          # Code examples for AI assistants
│
├── lyopronto/                        # Main package (scipy-based)
│   ├── __init__.py
│   ├── functions.py                  # Core physics equations
│   ├── constant.py                   # Physical constants
│   ├── calc_knownRp.py              # Primary drying (known Rp)
│   ├── calc_unknownRp.py            # Primary drying (unknown Rp)
│   ├── opt_Pch_Tsh.py               # Optimize both Pch and Tsh
│   ├── opt_Pch.py                   # Optimize Pch only
│   ├── opt_Tsh.py                   # Optimize Tsh only
│   ├── design_space.py              # Design space generator
│   ├── freezing.py                   # Freezing phase
│   └── pyomo_models/                 # Future: Pyomo optimization
│
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                   # Shared fixtures
│   ├── test_functions.py             # Unit tests (44 tests)
│   ├── test_calculators.py           # Integration tests (14 tests)
│   ├── test_regression.py            # Regression tests (9 tests)
│   └── test_web_interface.py         # Web interface validation (8 tests)
│
├── test_data/                        # Reference data for tests
│   ├── README.md                     # Documentation of test data
│   ├── temperature.txt               # Temperature profile input
│   └── lyopronto_primary_drying_Oct_01_2025_18_48_08.csv  # Reference output
│
├── examples/                         # Example scripts
│   ├── README.md                     # Documentation of examples
│   ├── example_web_interface.py      # Web interface replication
│   └── outputs/                      # Generated output files
│       ├── README.md                 # Documentation of outputs
│       ├── *.csv                     # Generated CSV files
│       └── *.png                     # Generated plots
│
├── docs/                             # Documentation
│   ├── index.md                      # Main documentation index
│   ├── explanation.md
│   ├── how-to-guides.md
│   ├── reference.md
│   └── tutorials.md
│
├── htmlcov/                          # Coverage reports (generated, gitignored)
│
├── Documentation Files (Root)
│   ├── README.md                     # Main project README
│   ├── GETTING_STARTED.md           # Quick start guide
│   ├── README_TESTING.md            # Testing guide
│   ├── ARCHITECTURE.md              # System architecture
│   ├── COEXISTENCE_PHILOSOPHY.md   # Scipy/Pyomo coexistence
│   ├── PYOMO_ROADMAP.md            # Pyomo integration plan
│   ├── PHYSICS_REFERENCE.md         # Physics background
│   ├── CODE_STRUCTURE.md            # Code organization
│   ├── CONTRIBUTING.md              # Contribution guidelines
│   ├── TESTING_SUMMARY.md           # Test analysis
│   ├── TEST_FIXES_SUMMARY.md        # Debugging history
│   └── TESTING_AND_EXAMPLES_SUMMARY.md  # Complete testing status
│
├── Configuration Files (Root)
│   ├── .gitignore                    # Git ignore patterns
│   ├── pytest.ini                    # Pytest configuration
│   ├── mkdocs.yml                    # MkDocs configuration
│   ├── requirements.txt              # Production dependencies
│   ├── requirements-dev.txt          # Development dependencies
│   └── LICENSE.txt                   # GPL v3 license
│
└── Legacy Examples (Root)            # To be migrated
    ├── ex_knownRp_PD.py
    ├── ex_unknownRp_PD.py
    └── main.py
```

## File Organization Rules

### 1. Source Code (`lyopronto/`)
**What goes here**: All production Python code
- Core physics functions
- Simulators and optimizers
- Future: Pyomo models in `pyomo_models/` subdirectory

**What doesn't**: Tests, examples, documentation, data files

### 2. Tests (`tests/`)
**What goes here**: All test code
- Unit tests for individual functions
- Integration tests for workflows
- Regression tests for validation
- Fixtures and test utilities

**What doesn't**: Test data (goes in `test_data/`), examples

### 3. Test Data (`test_data/`)
**What goes here**: Reference data files used by tests
- Input files (temperature profiles, etc.)
- Reference output files for validation
- Small data files (<1 MB each)

**What doesn't**: Generated output, temporary files

### 4. Examples (`examples/`)
**What goes here**: Example scripts demonstrating usage
- Standalone runnable scripts
- Well-documented with docstrings
- Realistic use cases

**Output subdirectory** (`examples/outputs/`):
- CSV files generated by examples
- Plot images (PNG)
- Both tracked in git as reference outputs

### 5. Documentation (Root)
**What goes here**: Markdown documentation files
- Project overview (README.md)
- Architecture and design docs
- Testing and development guides
- Physics reference

**What doesn't**: Generated HTML documentation (use `docs/` for that)

### 6. Configuration (Root)
**What goes here**: Project configuration files
- Python dependencies (requirements*.txt)
- Testing configuration (pytest.ini)
- Git configuration (.gitignore)
- Documentation build (mkdocs.yml)

---

## .gitignore Strategy

### Always Ignored (Never Commit)
```
# Python compiled files
__pycache__/
*.pyc
*.pyo

# Virtual environments
venv/
env/
.venv/

# IDE files
.vscode/
.idea/
*.swp

# Coverage reports
.coverage
htmlcov/

# Generated outputs (temporarily)
lyopronto_primary_drying_*.csv  # In root only
primary_drying_results.png       # In root only
```

### Always Tracked (Do Commit)
```
# Source code
lyopronto/**/*.py

# Tests
tests/**/*.py

# Test data
test_data/*.csv
test_data/*.txt

# Example outputs (as reference)
examples/outputs/*.csv
examples/outputs/*.png

# Documentation
*.md
docs/**/*

# Configuration
requirements*.txt
pytest.ini
.gitignore
```

---

## Naming Conventions

### Python Files
- **Modules**: `lowercase_with_underscores.py`
- **Examples**: `example_<description>.py`
- **Tests**: `test_<module_name>.py`

### Data Files
- **Input data**: `<descriptor>.txt` or `<descriptor>.csv`
- **Output data**: `lyopronto_<tool>_<timestamp>.csv`
- **Plots**: `<descriptor>_results.png`

### Documentation Files
- **Guides**: `UPPERCASE_TITLE.md` (in root)
- **Module docs**: `lowercase.md` (in docs/)
- **Directory docs**: `README.md` (in subdirectories)

---

## Cleanup Procedures

### Daily Development Cleanup
Remove temporary generated files from root:
```bash
rm lyopronto_primary_drying_*.csv
rm primary_drying_results.png
rm *.pyc
```

Or use git clean (careful!):
```bash
git clean -Xn  # Dry run - show what would be deleted
git clean -Xf  # Actually delete ignored files
```

### Test Data Cleanup
**DON'T** delete files in `test_data/` - these are reference files needed for tests!

### Example Output Cleanup
Keep reference outputs in `examples/outputs/`, but can remove duplicates:
```bash
cd examples/outputs/
# Keep only the reference file
ls lyopronto_primary_drying_*.csv | grep -v "Oct_01_2025_18_48_08" | xargs rm
```

---

## Adding New Files

### Adding New Example
1. Create `examples/example_<name>.py`
2. Document in `examples/README.md`
3. Add test in `tests/test_examples.py` (if needed)
4. Run and verify output
5. Commit example script (not generated output, unless reference)

### Adding New Test Data
1. Place file in `test_data/`
2. Document in `test_data/README.md`
3. Update tests to use it
4. Commit to repository (small files only)

### Adding New Test
1. Add to appropriate `tests/test_*.py` file
2. Use fixtures from `conftest.py`
3. Run test suite to verify
4. Commit

### Adding New Documentation
1. Create `DESCRIPTIVE_NAME.md` in root (for major docs)
2. Or add to `docs/` (for detailed/generated docs)
3. Update README.md to reference it
4. Commit

---

## Repository Health Checks

### Check for Clutter
```bash
# Files that shouldn't be in root
ls *.csv *.png 2>/dev/null && echo "⚠️ Clean up root!" || echo "✓ Root is clean"

# Large files
find . -type f -size +1M ! -path "./.git/*" ! -path "./htmlcov/*"
```

### Check Organization
```bash
# Test data in right place
ls test_data/*.csv test_data/*.txt

# Examples in right place
ls examples/*.py

# Example outputs in right place
ls examples/outputs/*.csv examples/outputs/*.png

# Tests in right place
ls tests/test_*.py
```

### Verify .gitignore
```bash
# Check what git sees
git status --short

# Check what's ignored
git status --ignored --short
```

---

## Migration Status

### ✅ Completed
- Moved `temperature.txt` → `test_data/`
- Moved reference CSV → `test_data/` (for tests) and `examples/outputs/` (for examples)
- Moved generated CSVs → `examples/outputs/`
- Moved plots → `examples/outputs/`
- Created `test_data/README.md`
- Created `examples/README.md`
- Created `examples/outputs/README.md`
- Updated `.gitignore`
- Updated file paths in code
- Verified tests pass
- Verified examples work

### 📋 Pending (Optional)
- Migrate `ex_knownRp_PD.py` → `examples/example_known_rp.py`
- Migrate `ex_unknownRp_PD.py` → `examples/example_unknown_rp.py`
- Remove or update `main.py`
- Create additional examples (optimization, design space, etc.)

---

## Quick Reference

### Where do I put...?

| Item | Location | Example |
|------|----------|---------|
| New physics function | `lyopronto/` | `lyopronto/new_module.py` |
| New test | `tests/` | `tests/test_new_module.py` |
| Input data for tests | `test_data/` | `test_data/reference.csv` |
| Example script | `examples/` | `examples/example_feature.py` |
| Example output | `examples/outputs/` | `examples/outputs/result.csv` |
| Documentation | Root or `docs/` | `FEATURE_GUIDE.md` |
| Configuration | Root | `pyproject.toml` |

### Where do I find...?

| Need | Location |
|------|----------|
| Temperature input | `test_data/temperature.txt` |
| Reference CSV | `test_data/lyopronto_primary_drying_Oct_01_2025_18_48_08.csv` |
| Example outputs | `examples/outputs/*.csv`, `examples/outputs/*.png` |
| Test fixtures | `tests/conftest.py` |
| Physics constants | `lyopronto/constant.py` |
| Core equations | `lyopronto/functions.py` |

---

## Summary

**Repository is now well-organized with**:
- ✅ Clear separation of concerns
- ✅ Test data in dedicated directory
- ✅ Examples with their outputs
- ✅ Comprehensive documentation
- ✅ Smart .gitignore rules
- ✅ All tests passing
- ✅ All examples working

**Key principle**: Everything has a place, and similar things are together.
