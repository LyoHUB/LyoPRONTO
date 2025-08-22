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

from scipy.optimize import fsolve
from scipy.integrate import solve_ivp
import numpy as np
from . import constant
from . import functions


################# Primary drying at fixed set points ###############

def dry(vial,product,ht,Pchamber,Tshelf,dt):

    ##################  Initialization ################

    # Initial fill height
    Lpr0 = functions.Lpr0_FUN(vial['Vfill'],vial['Ap'],product['cSolid'])   # cm

    Pch_t = lambda t: Pchamber['setpt'][0] # TODO: allow ramps
    Tsh_t = lambda t: min(Tshelf['setpt'][0], t*60*Tshelf['ramp_rate'] + Tshelf['init'])

    config = (vial, product, ht, Pch_t, Tsh_t, dt, Lpr0)

    Lck0 = [0.0]
    T0 = Tsh_t(0)

    ################ Set up dynamic equation ######################
    def calc_dLdt(t, u):
        Lck = u[0]
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

        dLdt = (dmdt*constant.kg_To_g)/(1-product['cSolid']*constant.rho_solution/constant.rho_solute)/(vial['Ap']*constant.rho_ice)*(1-product['cSolid']*(constant.rho_solution-constant.rho_ice)/constant.rho_solute) # cm
        return [dLdt]

    ### ------ Condition for ending simulation: completed drying
    def finish(t, L):
        return Lpr0 - L[0]
    finish.terminal = True
    

    # ------- Solve the equations
    sol = solve_ivp(calc_dLdt, (0, 24*3600*14), Lck0, events=finish, 
                    vectorized=False, dense_output=True, method="BDF")

    output = functions.fill_output(sol, config)

    return output    
    
############################################################################
