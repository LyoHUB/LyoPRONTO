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

import scipy.optimize as sp
import numpy as np
import math
import csv
from . import constant
from . import functions
from pdb import set_trace as keyboard


################# Primary drying at fixed set points ###############

def dry(vial,product,ht,Pchamber,Tshelf,dt):

    ##################  Initialization ################

    # Initial fill height
    Lpr0 = functions.Lpr0_FUN(vial['Vfill'],vial['Ap'],product['cSolid'])   # cm

    # Initialization of time
    iStep = 0      # Time iteration number
    t = 0.0    # Time in hr

    # Initialization of cake length
    Lck = 0.0    # Cake length in cm
    percent_dried = Lck/Lpr0*100.0        # Percent dried

    # Initial shelf temperature
    Tsh = Tshelf['init']        # degC
    Tshelf['setpt'] = np.insert(Tshelf['setpt'],0,Tshelf['init'])        # Include initial shelf temperature in set point array
    # Shelf temperature control time
    Tshelf['t_setpt'] = np.array([[0]])
    for dt_i in Tshelf['dt_setpt']:
        Tshelf['t_setpt'] = np.append(Tshelf['t_setpt'],Tshelf['t_setpt'][-1]+dt_i/constant.hr_To_min)

    # Initial chamber pressure
    Pch = Pchamber['setpt'][0]        # Torr
    Pchamber['setpt'] = np.insert(Pchamber['setpt'],0,Pchamber['setpt'][0])        # Include initial chamber pressure in set point array
    # Chamber pressure control time
    Pchamber['t_setpt'] = np.array([[0]])
    for dt_j in Pchamber['dt_setpt']:
        Pchamber['t_setpt'] = np.append(Pchamber['t_setpt'],Pchamber['t_setpt'][-1]+dt_j/constant.hr_To_min) 
       
    # Initial product temperature
    T0=Tsh   # degC

    ######################################################

    ################ Primary drying ######################

    while(Lck<=Lpr0): # Dry the entire frozen product
    
        Kv = functions.Kv_FUN(ht['KC'],ht['KP'],ht['KD'],Pch)  # Vial heat transfer coefficient in cal/s/K/cm^2
        Rp = functions.Rp_FUN(Lck,product['R0'],product['A1'],product['A2'])  # Product resistance in cm^2-hr-Torr/g

        Tsub = sp.fsolve(functions.T_sub_solver_FUN, T0, args = (Pch,vial['Av'],vial['Ap'],Kv,Lpr0,Lck,Rp,Tsh)) # Sublimation front temperature array in degC
        dmdt = functions.sub_rate(vial['Ap'],Rp,Tsub,Pch)   # Total sublimation rate array in kg/hr
        if dmdt<0:
            print("Shelf temperature is too low for sublimation.")
            dmdt = 0.0
        Tbot = functions.T_bot_FUN(Tsub,Lpr0,Lck,Pch,Rp)    # Vial bottom temperature array in degC

        # Sublimated ice length
        dL = (dmdt*constant.kg_To_g)*dt/(1-product['cSolid']*constant.rho_solution/constant.rho_solute)/(vial['Ap']*constant.rho_ice)*(1-product['cSolid']*(constant.rho_solution-constant.rho_ice)/constant.rho_solute) # cm

        # Update record as functions of the cycle time
        if (iStep==0):
            output_saved = np.array([[t, float(Tsub), float(Tbot), Tsh, Pch*constant.Torr_to_mTorr, dmdt/(vial['Ap']*constant.cm_To_m**2), percent_dried]])
        else:
            output_saved = np.append(output_saved, [[t, float(Tsub), float(Tbot), Tsh, Pch*constant.Torr_to_mTorr, dmdt/(vial['Ap']*constant.cm_To_m**2), percent_dried]],axis=0)

        # Advance counters
        Lck_prev = Lck # Previous cake length in cm
        Lck = Lck + dL # Cake length in cm
        if (Lck_prev < Lpr0) and (Lck > Lpr0):
            Lck = Lpr0    # Final cake length in cm
            dL = Lck - Lck_prev   # Cake length dried in cm
            t = iStep*dt + dL/((dmdt*constant.kg_To_g)/(1-product['cSolid']*constant.rho_solution/constant.rho_solute)/(vial['Ap']*constant.rho_ice)*(1-product['cSolid']*(constant.rho_solution-constant.rho_ice)/constant.rho_solute)) # hr
        else:
            t = (iStep+1) * dt # Time in hr

            percent_dried = Lck/Lpr0*100   # Percent dried

        if len(np.where(Tshelf['t_setpt']>t)[0])==0:
            print("Total time exceeded. Drying incomplete")    # Shelf temperature set point time exceeded, drying not done
            break
        else:
            i = np.where(Tshelf['t_setpt']>t)[0][0]
            # Ramp shelf temperature till next set point is reached and then maintain at set point
            if Tshelf['setpt'][i] >= Tshelf['setpt'][i-1]:
                Tsh = min(Tshelf['setpt'][i-1] + Tshelf['ramp_rate']*constant.hr_To_min*(t-Tshelf['t_setpt'][i-1]),Tshelf['setpt'][i])
            else:
                Tsh = max(Tshelf['setpt'][i-1] - Tshelf['ramp_rate']*constant.hr_To_min*(t-Tshelf['t_setpt'][i-1]),Tshelf['setpt'][i])

            if len(np.where(Pchamber['t_setpt']>t)[0])==0:
                print("Total time exceeded. Drying incomplete")    # Shelf tempertaure set point time exceeded, drying not done
                break
            else:
                j = np.where(Pchamber['t_setpt']>t)[0][0]
                # Ramp shelf temperature till next set point is reached and then maintain at set point
                if Pchamber['setpt'][j] >= Pchamber['setpt'][j-1]:
                    Pch = min(Pchamber['setpt'][j-1] + Pchamber['ramp_rate']*constant.hr_To_min*(t-Pchamber['t_setpt'][j-1]),Pchamber['setpt'][j])
                else:
                    Pch = max(Pchamber['setpt'][j-1] - Pchamber['ramp_rate']*constant.hr_To_min*(t-Pchamber['t_setpt'][j-1]),Pchamber['setpt'][j])
            
            iStep = iStep + 1 # Time iteration number

    ######################################################
    
    Tshelf['setpt'] = Tshelf['setpt'][1:]
    return output_saved    
    
############################################################################
