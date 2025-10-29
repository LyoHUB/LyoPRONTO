
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


################# Primary drying at fixed set points ###############

def dry(vial,product,ht,Pchamber,Tshelf,dt,eq_cap,nVial):

    ##################  Initialization ################

    # Initial fill height
    Lpr0 = functions.Lpr0_FUN(vial['Vfill'],vial['Ap'],product['cSolid'])   # cm

    # Initialization of time
    iStep = 0      # Time iteration number
    t = 0.0    # Time in hr

    # Initialization of cake length
    Lck = 0.0    # Cake length in cm
    percent_dried = Lck/Lpr0*100.0        # Percent dried

    # Initial chamber pressure
    P0 = 0.1    # Initial guess for chamber pressure in Torr

    # Initial shelf temperature
    Tsh = Tshelf['init']        # degC
    Tshelf = Tshelf.copy()
    Tshelf['setpt'] = np.insert(Tshelf['setpt'],0,Tshelf['init'])        # Include initial shelf temperature in set point array
    # Shelf temperature control time
    Tshelf['t_setpt'] = np.array([[0]])
    for dt_i in Tshelf['dt_setpt']:
        Tshelf['t_setpt'] = np.append(Tshelf['t_setpt'],Tshelf['t_setpt'][-1]+dt_i/constant.hr_To_min)
       
    # Initial product and shelf temperatures
    T0=product['T_pr_crit']   # degC

    ######################################################

    ################ Primary drying ######################

    while(Lck<=Lpr0): # Dry the entire frozen product

        Rp = functions.Rp_FUN(Lck,product['R0'],product['A1'],product['A2'])  # Product resistance in cm^2-hr-Torr/g
    
        # Quantities solved for: x = [Pch,dmdt,Tbot,Tsh,Psub,Tsub,Kv]
        fun = lambda x: (x[0]-x[4])    # Objective function to be minimized to maximize sublimation rate
        x0 = [P0,0.0,T0,T0,P0,T0,3.0e-4]    # Initial values
        # Constraints
        cons = ({'type':'eq','fun':lambda x: functions.Eq_Constraints(x[0],x[1],x[2],x[3],x[4],x[5],x[6],Lpr0,Lck,vial['Av'],vial['Ap'],Rp)[0]},  # sublimation front pressure in Torr
            {'type':'eq','fun':lambda x: functions.Eq_Constraints(x[0],x[1],x[2],x[3],x[4],x[5],x[6],Lpr0,Lck,vial['Av'],vial['Ap'],Rp)[1]},    # sublimation rate in kg/hr
            {'type':'eq','fun':lambda x: functions.Eq_Constraints(x[0],x[1],x[2],x[3],x[4],x[5],x[6],Lpr0,Lck,vial['Av'],vial['Ap'],Rp)[2]},    # vial heat transfer balance
            {'type':'eq','fun':lambda x: functions.Eq_Constraints(x[0],x[1],x[2],x[3],x[4],x[5],x[6],Lpr0,Lck,vial['Av'],vial['Ap'],Rp)[3]},    # shelf temperature in degC
            {'type':'eq','fun':lambda x: x[6]-functions.Kv_FUN(ht['KC'],ht['KP'],ht['KD'],x[0])},    # vial heat transfer coefficient in cal/s/K/cm^2
            {'type':'eq','fun':lambda x: x[3]-Tsh},    # shelf temperature fixed in degC
            {'type':'ineq','fun':lambda x: functions.Ineq_Constraints(x[0],x[1],product['T_pr_crit'],x[2],eq_cap['a'],eq_cap['b'],nVial)[0]},  # equipment capability inequlity
            {'type':'ineq','fun':lambda x: functions.Ineq_Constraints(x[0],x[1],product['T_pr_crit'],x[2],eq_cap['a'],eq_cap['b'],nVial)[1]})  # maximum product temperature inequality
        # Bounds for the unknowns
        bnds = ((Pchamber['min'],None),(None,None),(None,None),(None,None),(None,None),(None,None),(None,None))
        # Minimize the objective function i.e. maximize the sublimation rate
        res = sp.minimize(fun,x0,bounds = bnds, constraints = cons)
        [Pch,dmdt,Tbot,Tsh,Psub,Tsub,Kv] = res['x']    # Results in Torr, kg/hr, degC, degC, Torr, degC, cal/s/K/cm^2

        # Sublimated ice length
        dL = (dmdt*constant.kg_To_g)*dt/(1-product['cSolid']*constant.rho_solution/constant.rho_solute)/(vial['Ap']*constant.rho_ice)*(1-product['cSolid']*(constant.rho_solution-constant.rho_ice)/constant.rho_solute) # cm

        # Update record as functions of the cycle time
        if iStep == 0:
            output_saved = np.array([[t, float(Tsub), float(Tbot), Tsh, Pch*constant.Torr_to_mTorr, dmdt/(vial['Ap']*constant.cm_To_m**2), percent_dried/100.0]])
        else:
            output_saved = np.append(output_saved, [[t, float(Tsub), float(Tbot), Tsh, Pch*constant.Torr_to_mTorr, dmdt/(vial['Ap']*constant.cm_To_m**2), percent_dried/100.0]], axis=0)
    
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
          
            iStep = iStep + 1 # Time iteration number

    ######################################################

    return output_saved    
    
############################################################################
