#!/usr/bin/env python

# LyoPRONTO, a vial-scale lyophilization process simulator
# Copyright (C) 2024, Gayathri Shivkumar, Petr S. Kazarin, Alina A. Alexeenko, Isaac S. Wheeler

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import numpy as np


from lyopronto import *
# from . import constant
# from . import freezing
# from . import calc_knownRp
# from . import calc_unknownRp
# from . import design_space
# from . import opt_Pch_Tsh
# from . import opt_Pch
# from . import opt_Tsh
# from . import functions

import time

current_time = time.strftime("%y%m%d_%H%M", time.localtime())

################################################################

######################## Inputs ########################

# Simulation type
# 4 Tools available: 'Freezing Calculator', 'Primary Drying Calculator', 'Design Space Generator', 'Optimizer'
# For 'Freezing Calculator': h_freezeing, Tpr0, Tf and Tn must be provided
#                 No Variable Tsh - set point must be specified
# For 'Primary Drying Calculator': If Kv and Rp are known, drying time can be determined
#            If drying time and Rp are known, Kv can be determined
#            If Kv and product temperature are known, Rp can be determined
#            No Variable Pch and Tsh - set points must be specified
# For 'Design Space Generator': Kv and Rp must be known, Tpr_crit must be provided
#                No Variable Pch and Tsh - set points must be specified
# For 'Optimizer': Kv and Rp must be known, Tpr_crit must be provided
#           Can use variable Pch and/or Tsh
sim = {
    "tool": "Design Space Generator",
    "Kv_known": True,
    "Rp_known": True,
    "Variable_Pch": False,
    "Variable_Tsh": False,
}

# Vial and fill properties
# Av = Vial area in cm^2
# Ap = Product Area in cm^2
# Vfill = Fill volume in mL
vial = {"Av": 3.80, "Ap": 3.14, "Vfill": 2.0}

# Product properties
# cSolid = Fractional concentration of solute in the frozen solution
# Tpr0 = Initial product temperature for freezing in degC
# Tf = Freezing temperature in degC
# Tn = Nucleation temperature in degC
# Product Resistance Parameters
# R0 in cm^2-hr-Torr/g, A1 in cm-hr-Torr/g, A2 in 1/cm
if sim["tool"] == "Freezing Calculator":
    product = {"cSolid": 0.0, "Tpr0": 15.8, "Tf": -1.54, "Tn": -5.84}
elif not (sim["tool"] == "Primary Drying Calculator" and not sim["Rp_known"]):
    product = {"cSolid": 0.05, "R0": 1.4, "A1": 16.0, "A2": 0.0}
else:
    product = {"cSolid": 0.05}

    product_temp_filename = "./temperature.dat"
    exp_data = np.loadtxt(product_temp_filename)
    # Assumed: time in first column, temperature in second column
    # Change as necessary to match data file, but keep these names
    time_data = exp_data[:, 0]
    temp_data = exp_data[:, 1]
# Critical product temperature
# At least 2 to 3 deg C below collapse or glass transition temperature
product["T_pr_crit"] = -5  # in degC

# Vial Heat Transfer Parameters
if sim["tool"] == "Freezing Calculator":
    # Heat transfer coefficient between product and surroundings
    h_freezing = 38.0  #  in W/m^2/K
elif sim["Kv_known"]:
    # Kv = KC + KP*Pch/(1+KD*Pch)
    # KC in cal/s/K/cm^2, KP in cal/s/K/cm^2/Torr, KD in 1/Torr
    ht = {"KC": 2.75e-4, "KP": 8.93e-4, "KD": 0.46}
elif not sim["Kv_known"]:
    Kv_range = np.array([5.0, 20.0]) * 1e-4  # cal/s/K/cm^2, lower & upper bounds
    # Primary drying time
    t_dry_exp = 12.62  # in hr
else:
    print("Kv_known: Input not recognized")
    sys.exit(1)

# Chamber Pressure
if sim["tool"] == "Freezing Calculator":
    0
elif sim["tool"] == "Design Space Generator":
    # Array of chamber pressure set points in Torr
    Pchamber = {"setpt": [0.1, 0.4, 0.7, 1.5]}
elif not (sim["tool"] == "Optimizer" and sim["Variable_Pch"]):
    # setpt = Chamber pressure set points in Torr
    # dt_setpt = Time for which chamber pressure set points are held in min
    # ramp_rate = Chamber pressure ramping rate in Torr/min
    Pchamber = {"setpt": [0.15], "dt_setpt": [1800.0], "ramp_rate": 0.5}
else:
    # Chamber pressure limits in Torr
    Pchamber = {"min": 0.05, "max": 1000}

# Shelf Temperature
if sim["tool"] == "Design Space Generator":
    # Array of shelf temperature set points in C
    # ramp_rate = Shelf temperature ramping rate in C/min
    Tshelf = {"init": -5.0, "setpt": [-5, 0, 2, 5], "ramp_rate": 1.0}
elif not (sim["tool"] == "Optimizer" and sim["Variable_Tsh"]):
    # init = Intial shelf temperature in C
    # setpt = Shelf temperature set points in C
    # dt_setpt = Time for which shelf temperature set points are held in min
    # ramp_rate = Shelf temperature ramping rate in C/min
    Tshelf = {"init": -35.0, "setpt": [20.0], "dt_setpt": [1800.0], "ramp_rate": 1.0}
else:
    # Shelf temperature limits in C
    Tshelf = {"min": -45, "max": 120}

# Time step
dt = 0.01  # hr

# Lyophilizer equipment capability
# Form: dm/dt [kg/hr] = a + b * Pch [Torr]
# a in kg/hr, b in kg/hr/Torr
eq_cap = {"a": -0.182, "b": 0.0117e3}

# Equipment load
nVial = 398  # Number of vials

##############################################
# Collect parameters into input dictionary

# Get all the inputs that are defined into a input dictionary
inputs = {}
loc = locals()
for key in [
    "sim",
    "vial",
    "product",
    "ht",
    "Pchamber",
    "Tshelf",
    "dt",
    "eq_cap",
    "nVial",
    "h_freezing",
    "t_dry_exp",
    "Kv_range",
    "time_data",
    "temp_data",
]:
    if key in loc:
        inputs[key] = loc[key]

#################### Input file saved ##################

# Write data to files

# Save to a .csv, old style
# save_inputs_legacy(inputs, current_time)

# Save to a .yaml, new style
save_inputs(inputs, current_time)

########################################################

################### Execute  ##########################

output_data = execute_simulation(inputs)

######################################################

####################### Outputs #######################

# Write data to files
save_csv(output_data, inputs, current_time)

# Plot data and save figures

generate_visualizations(output_data, inputs, current_time)
