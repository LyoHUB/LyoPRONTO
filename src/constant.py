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

################## Constants #####################

# Unit Conversion
kg_To_g = 1000.0
cm_To_m = 1.0e-2
hr_To_s = 3600.0
hr_To_min = 60.0
min_To_s = 60.0
Torr_to_mTorr = 1000.0
cal_To_J = 4.184

rho_ice = 0.918 # g/mL
rho_solute = 1.5 # g/mL
rho_solution = 1.0  # g/mL

dHs = 678.0 # Heat of sublimation in cal/g
k_ice = 0.0059 # Thermal conductivity of ice in cal/cm/s/K
dHf = 79.7 # Heat of fusion in cal/g

Cp_ice = 2030.0 # Constant pressure specific heat of ice in J/kg/K
Cp_solution = 4000.0 # Constant pressure specific heat of water in J/kg/K

##################################################
