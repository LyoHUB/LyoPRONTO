# LyoPRONTO

[![Tests](https://github.com/SECQUOIA/LyoPRONTO/workflows/Tests/badge.svg?branch=dev-pyomo)](https://github.com/SECQUOIA/LyoPRONTO/actions/workflows/tests.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen.svg)](htmlcov/index.html)

LyoPRONTO is an open-source user-friendly tool to simulate and optimize freezing and primary drying in lyophilizers written using Python.

# Authors
Original authors: Gayathri Shivkumar, Petr S. Kazarin and Alina A. Alexeenko.
Maintained and updated by Isaac S. Wheeler.

# Interactive Simulation
A web-based GUI is available for this software at http://lyopronto.geddes.rcac.purdue.edu.

# How to Use This Code Directly
Download this repository, then in your preferred command line navigate to the containing directory (so that `LyoPronto` is a subdirectory).
Execute:
```
python3 LyoPronto.main -m
```
LyoPRONTO is a vial-scale lyophilization (freeze-drying) process simulator written in Python. It models the freezing and primary drying phases using heat and mass transfer equations.
A video tutorial by the authors illustrating this process can be found [on LyoHUB's YouTube channel](https://youtu.be/DI-Gz0pBI0w).

## Modern Examples

For new users, we recommend using the examples in the `examples/` directory instead:
```bash
# Primary drying simulation (recommended starting point)
python examples/example_web_interface.py

# Parameter estimation from experimental data
python examples/example_parameter_estimation.py

# Process optimization
python examples/example_optimizer.py

# Freezing simulation
python examples/example_freezing.py

# Design space generation
python examples/example_design_space.py
```

See [`examples/README.md`](examples/README.md) for detailed documentation.

## Legacy Examples

The repository root contains legacy example scripts for backward compatibility:
- `ex_knownRp_PD.py` - Original primary drying example → Use `examples/example_web_interface.py` instead
- `ex_unknownRp_PD.py` - Original parameter estimation example → Use `examples/example_parameter_estimation.py` instead

These legacy scripts are maintained and tested, but new users should use the modern examples in the `examples/` directory.

# Citation
G. Shivkumar, P. S. Kazarin, A. D. Strongrich, & A. A. Alexeenko, "LyoPRONTO: An Open-Source Lyophilization PRocess OptimizatioN TOol",  AAPS PharmSciTech (2019) 20: 328. 

The noted paper is open access, and can be found [here](https://link.springer.com/article/10.1208/s12249-019-1532-7).

# Licensing

Copyright (C) 2019, Gayathri Shivkumar, Petr S. Kazarin and Alina A. Alexeenko.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see <https://www.gnu.org/licenses/>.

By request, this software may also be distributed under the terms of the GNU Lesser General Public License (LGPL); for permission, contact the authors or maintainer.

# Documentation

### Quick Start
- **Getting Started**: [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md) - Developer setup and environment
- **Examples**: [`examples/README.md`](examples/README.md) - Web interface examples (primary drying, optimizer, freezing, design space)
- **Testing**: [`tests/README.md`](tests/README.md) - Test suite (85 tests, 100% passing)

### Technical Documentation
- **Architecture**: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - System design and module structure
- **Physics**: [`docs/PHYSICS_REFERENCE.md`](docs/PHYSICS_REFERENCE.md) - Equations, models, and thermodynamics
- **Pyomo Integration**: [`docs/PYOMO_ROADMAP.md`](docs/PYOMO_ROADMAP.md) - NLP optimization plans
- **Coexistence Philosophy**: [`docs/COEXISTENCE_PHILOSOPHY.md`](docs/COEXISTENCE_PHILOSOPHY.md) - Scipy + Pyomo parallel implementation

### Development
- **Development Log**: [`docs/DEVELOPMENT_LOG.md`](docs/DEVELOPMENT_LOG.md) - Chronological change history
- **Contributing**: [`CONTRIBUTING.md`](CONTRIBUTING.md) - Contribution guidelines
- **Archive**: [`docs/archive/`](docs/archive/) - Historical session summaries

# Notes on contributing & maintenance

There is a GitHub Action on this repo which will automatically build the documentation (which uses Material for MkDocs with `mike` for versioning). This action triggers on push to main (which creates a `dev` section of the docs), on publishing a release (which creates a numbered version of the docs), and on pull request edits (which makes a `pr-###` version of the docs). 
After merging a pull request, it is a good idea to use [mike](https://github.com/jimporter/mike) to clear out the PR version of the docs. Locally, do something like the following
```
git fetch 
mike delete pr-### # replace with correct PR number
git switch gh-pages
git push origin gh-pages
```
This could theoretically be automated but I decided against this for now. In the long run, it may be worth not generating PR versions of the docs if this is burdensome.