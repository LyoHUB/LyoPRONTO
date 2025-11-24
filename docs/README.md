# LyoPRONTO Documentation

This directory contains all technical documentation for the LyoPRONTO lyophilization simulator.

## Core Documentation
## Testing & Continuous Integration

LyoPRONTO uses a modern, robust CI/CD pipeline and a comprehensive test suite. The test suite is divided into fast and slow tests, with all code and documentation changes automatically validated via GitHub Actions.

- **Fast/Slow Test Separation:**
    - Fast tests run on every PR and push (under 60 seconds).
    - Slow tests (marked with `@pytest.mark.slow`) run nightly and on demand.
- **Centralized Python Version Management:**
    - All workflows use the Python version(s) specified in `.github/ci-config/ci-versions.yml`.
- **CI Workflows:**
    - PRs and pushes: Fast tests (`pr-tests.yml`)
    - Main branch: Full suite (`tests.yml`)
    - Nightly/manual: Slow tests (`slow-tests.yml`)
    - Docs: Build and link check (`docs.yml`)
- **Coverage & Linting:**
    - Coverage is reported for all test runs.
    - Linting and formatting are enforced in CI.

See [`../tests/README.md`](../tests/README.md) for full details on running, writing, and debugging tests, as well as CI workflow explanations.

### For Developers
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Setup, installation, and first steps
- **[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)** - Chronological change history and milestones
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and module design

### For Users
- **[PHYSICS_REFERENCE.md](PHYSICS_REFERENCE.md)** - Physics equations, models, and thermodynamics
- **Web Documentation** (`*.md` files) - Material for MkDocs documentation site

### For Future Development
- **[PYOMO_ROADMAP.md](PYOMO_ROADMAP.md)** - Pyomo NLP optimization integration plan
- **[COEXISTENCE_PHILOSOPHY.md](COEXISTENCE_PHILOSOPHY.md)** - Strategy for scipy + Pyomo parallel implementation

## Additional Resources

- **Examples**: See [`../examples/README.md`](../examples/README.md) for runnable examples
- **Tests**: See [`../tests/README.md`](../tests/README.md) for test suite documentation
- **Contributing**: See [`../CONTRIBUTING.md`](../CONTRIBUTING.md) for contribution guidelines
- **Archive**: See [`archive/README.md`](archive/README.md) for historical session summaries

## Documentation Organization

```
docs/
├── README.md                      # This file
├── GETTING_STARTED.md             # Developer onboarding
├── DEVELOPMENT_LOG.md             # Change history
├── ARCHITECTURE.md                # System design
├── PHYSICS_REFERENCE.md           # Physics documentation
├── COEXISTENCE_PHILOSOPHY.md      # Scipy/Pyomo strategy
├── PYOMO_ROADMAP.md               # Pyomo integration plan
├── index.md                       # MkDocs homepage
├── explanation.md                 # MkDocs explanations
├── how-to-guides.md               # MkDocs guides
├── reference.md                   # MkDocs API reference
├── tutorials.md                   # MkDocs tutorials
└── archive/                       # Historical documentation
    ├── README.md
    └── *.md                       # Session summaries (13 files)
```

## Building Documentation Site

LyoPRONTO uses Material for MkDocs with `mike` for versioning:

```bash
# Install dependencies
pip install mkdocs-material mike

# Serve documentation locally
mkdocs serve

# Build documentation
mike deploy --push --update-aliases VERSION latest

# Set default version
mike set-default latest
```

See the GitHub Actions workflow for automated documentation building on push, release, and pull requests.

## Contributing to Documentation

When adding new features:
1. Update relevant documentation files
2. Add examples to `examples/README.md`
3. Update `DEVELOPMENT_LOG.md` with major changes
4. Consider updating MkDocs files if user-facing

For questions:
- Check existing documentation first
- See `archive/` for detailed historical context
- Open an issue for clarifications

---

**Last Updated**: October 2, 2025  
**Documentation Files**: 8 core + 13 archived = 21 total
