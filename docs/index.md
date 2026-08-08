# LyoPRONTO

LyoPRONTO is an open-source user-friendly tool to simulate and optimize freezing and primary drying in lyophilizers written using Python.

## Installation

Install this code directly from GitHub with `pip`:
```bash
pip install git+https://github.com/LyoHUB/LyoPRONTO
```

## Authors
Original authors: Gayathri Shivkumar, Petr S. Kazarin and Alina A. Alexeenko.
Maintained and updated by Isaac S. Wheeler.

## Interactive Simulation
A web-based GUI is available for this software at https://lyopronto.geddes.rcac.purdue.edu or https://lyopronto2.geddes.rcac.purdue.edu.

## How to Use This Code Directly
Construct a YAML file with all the necessary inputs (see YAML files under `test_data` of this repository for examples), then run a Python script like the following:
```python
import time

import lyopronto as lp

# get time for recording simulation results
current_time = time.strftime("%y%m%d_%H%M", time.localtime())

yaml_fname = "your_dir/cycle_setup.yaml" # Fill in with your filename and appropriate location

# Read in simulation inputs
inputs = lp.read_inputs(yaml_fname)
# Execute the simulation
output = lp.execute_simulation(inputs)

# Record the simulation inputs, outputs, and figures
lp.save_inputs(inputs, current_time)
lp.save_csv(output, inputs, current_time)
lp.generate_visualizations(output, inputs, current_time)
```
This will generate a record of both inputs and outputs each time you execute the file, so you can edit the original YAML and rerun the script without worrying about losing prior values of the inputs.

See also documentation examples online [here](https://lyohub.github.io/LyoPRONTO/dev/examples/knownRp_PD/) and [here](https://lyohub.github.io/LyoPRONTO/dev/examples/unknownRp_PD/)

The original method for running this code, as illustrated in a video tutorial
[on LyoHUB's YouTube channel](https://youtu.be/DI-Gz0pBI0w),
is to download this repository, edit the script `main.py` in its root directory, then run that script from the command line (in the same directory):
```
python main.py
```
Files listing the inputs and outputs will be generated in the current directory, along with some plots of temperature, pressure, and drying progress vs. time.


## Citation
G. Shivkumar, P. S. Kazarin, A. D. Strongrich, & A. A. Alexeenko, "LyoPRONTO: An Open-Source Lyophilization PRocess OptimizatioN TOol",  AAPS PharmSciTech (2019) 20: 328. 

The noted paper is open access, and can be found [here](https://link.springer.com/article/10.1208/s12249-019-1532-7).

## Licensing

Copyright (C) 2019, Gayathri Shivkumar, Petr S. Kazarin, Alina A. Alexeenko, and Isaac S. Wheeler.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see <https://www.gnu.org/licenses/>.

By request, this software may also be distributed under the terms of the GNU Lesser General Public License (LGPL); for permission, contact the authors or maintainer.


