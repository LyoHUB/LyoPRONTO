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

from warnings import warn
from scipy.optimize import fsolve
from scipy.integrate import solve_ivp
import numpy as np
from . import constant
from . import functions


################# Primary drying at fixed set points ###############

def dry(vial,product,ht,Pchamber,Tshelf,dt):
    """Simulate the primary drying process for known condiditions and parameters.

    Args:
        vial (dict): see master simulation inputs
        product (dict): see master simulation inputs
        ht (dict): see master simulation inputs
        Pchamber (dict): see master simulation inputs
        Tshelf (dict): see master simulation inputs
        dt (float): Fixed time step for output [hours]

    Returns:
        output_table (ndarray): Simulation output table with columns for:
            0. Time [hr],
            1. Sublimation front temperature [°C],
            2. Vial bottom temperature [°C],
            3. Shelf temperature [°C],
            4. Chamber pressure [mTorr],
            5. Sublimation flux [kg/hr/m²],
            6. Drying percent [%]
    """

    ##################  Initialization ################

    # Initial fill height
    Lpr0 = functions.Lpr0_FUN(vial['Vfill'],vial['Ap'],product['cSolid'])   # cm

    # Time-dependent functions for Pchamber and Tshelf
    # TODO: make a function to use across modules for this functionality
    # Takes time in hours
    def Pch_t(t):
        return Pchamber['setpt'][0] # TODO: allow ramps
    def Tsh_t(t):
        return min(Tshelf['setpt'][0], t*60*Tshelf['ramp_rate'] + Tshelf['init'])

    # Get maximum simulation time based on shelf and chamber setpoints
    # This may not really be necessary, but is part of legacy behavior
    # Could remove in a future release
    max_t_T = 0
    for i, setpt in enumerate(Tshelf['setpt']):
        max_t_T += abs(setpt - (Tshelf['setpt'][i-1] if i>0 else Tshelf['init'])) / Tshelf['ramp_rate'] / constant.hr_To_min
        max_t_T += Tshelf['dt_setpt'][min(i, len(Tshelf['dt_setpt'])-1)] / constant.hr_To_min
    max_t_P = 0
    if len(Pchamber['setpt'])>1:
        for i, setpt in enumerate(Pchamber['setpt']):
            max_t_P += Pchamber['dt_setpt'][min(i, len(Pchamber['dt_setpt'])-1)] / constant.hr_To_min
            max_t_P += abs(setpt - (Pchamber['setpt'][i-1] if i>0 else Pchamber['setpt'][0])) / Pchamber['ramp_rate'] / constant.hr_To_min
    else:
        max_t_P += Pchamber.get('dt_setpt', [0])[0] / constant.hr_To_min
    max_t = max(max_t_T, max_t_P, 1)   # hr, add buffer

    if max(Pchamber['setpt']) > functions.Vapor_pressure(max(Tshelf['setpt'])):
        warn("Chamber pressure setpoint exceeds vapor pressure at shelf temperature setpoint(s). " +\
             "Drying cannot proceed.")
        return np.array([[0.0, Tshelf['init'], Tshelf['init'], Tshelf['init'], Pchamber['setpt'][0], 0.0, 0.0]])

    config = (vial, product, ht, Pch_t, Tsh_t, dt, Lpr0)

    Lck0 = [0.0]
    T0 = Tsh_t(0)

    ################ Set up dynamic equation ######################
    # This function is defined here because it uses local variables, rather than
    # taking them as arguments.
    def calc_dLdt(t, u):
        # Time in hours
        Lck = u[0] # cm
        Tsh = Tsh_t(t)
        Pch = Pch_t(t)
        Kv = functions.Kv_FUN(ht['KC'],ht['KP'],ht['KD'],Pch)  # Vial heat transfer coefficient in cal/s/K/cm^2
        Rp = functions.Rp_FUN(Lck,product['R0'],product['A1'],product['A2'])  # Product resistance in cm^2-hr-Torr/g
        Tsub = fsolve(functions.T_sub_solver_FUN, T0, args = (Pch,vial['Av'],vial['Ap'],Kv,Lpr0,Lck,Rp,Tsh))[0] # Sublimation front temperature array in degC
        dmdt = functions.sub_rate(vial['Ap'],Rp,Tsub,Pch)   # Total sublimation rate array in kg/hr
        if dmdt<0:
            # print("Shelf temperature is too low for sublimation.")
            dmdt = 0.0
            dLdt = 0
            return [dLdt]
        # Tbot = functions.T_bot_FUN(Tsub,Lpr0,Lck,Pch,Rp)    # Vial bottom temperature array in degC

        dLdt = (dmdt*constant.kg_To_g)/(1-product['cSolid']*constant.rho_solution/constant.rho_solute)/(vial['Ap']*constant.rho_ice)*(1-product['cSolid']*(constant.rho_solution-constant.rho_ice)/constant.rho_solute) # cm/hr
        return [dLdt]

    ### ------ Condition for ending simulation: completed drying
    def finish(t, L):
        return Lpr0 - L[0]
    finish.terminal = True
    

    # ------- Solve the equations
    sol = solve_ivp(calc_dLdt, (0, max_t), Lck0, events=finish, 
                    vectorized=False, dense_output=True, method="BDF")
    if sol.t[-1] == max_t:# and Lpr0 > sol.y[0, -1]:
        warn("Maximum simulation time (specified by Pchamber and Tshelf) reached before drying completion.")

    output = functions.fill_output(sol, config)

    return output    
    
############################################################################
