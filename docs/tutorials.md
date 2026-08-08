# Tutorials

## Original approach

Edit `main.py` in the root folder of the repo, then execute it with `python main.py`.
See also the video tutorial at https://www.youtube.com/watch?v=DI-Gz0pBI0w.

## Newer approach: YAML Input Format

LyoPRONTO accepts inputs as a YAML file, loaded via `read_inputs(filename)` and executed with `execute_simulation(inputs)`. 
The expected keys, values, etc. are fully specified with all units and constraints in the [full reference](reference.md#input-yaml-specification). The keys are also exemplified in the example notebooks, with a set of dictionaries that are put together into a `sim_setup` dictionary for each example.

With a YAML file for your inputs, the high-level workflow is as simple as this:

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
