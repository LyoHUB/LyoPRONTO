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

    T_max = np.zeros([np.size(Tshelf['setpt']),np.size(Pchamber['setpt'])])
    drying_time = np.zeros([np.size(Tshelf['setpt']),np.size(Pchamber['setpt'])])
    sub_flux_avg = np.zeros([np.size(Tshelf['setpt']),np.size(Pchamber['setpt'])])
    sub_flux_max = np.zeros([np.size(Tshelf['setpt']),np.size(Pchamber['setpt'])])
    sub_flux_end = np.zeros([np.size(Tshelf['setpt']),np.size(Pchamber['setpt'])])
    
    # Initial fill height
    Lpr0 = functions.Lpr0_FUN(vial['Vfill'],vial['Ap'],product['cSolid'])   # cm

    ############  Shelf temperature isotherms ##########

    for i_Tsh,Tsh_setpt in enumerate(Tshelf['setpt']):

        for i_Pch,Pch in enumerate(Pchamber['setpt']):

            ##################  Initialization ################

            # Initialization of time
            iStep = 0      # Time iteration number
            t = 0.0    # Time in hr

            # Initialization of cake length
            Lck = 0.0    # Cake length in cm

            # Initial shelf temperature
            Tsh = Tshelf['init']        # degC
            # Time at which shelf temperature reaches set point in hr
            t_setpt = abs(Tsh_setpt-Tshelf['init'])/Tshelf['ramp_rate']/constant.hr_To_min
       
            # Intial product temperature
            T0=Tsh   # degC

            # Vial heat transfer coefficient in cal/s/K/cm^2
            Kv = functions.Kv_FUN(ht['KC'],ht['KP'],ht['KD'],Pch) 

            ######################################################

            ################ Primary drying ######################

            while(Lck<=Lpr0): # Dry the entire frozen product
    
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
                # Note: iStep==0 check handles first timestep initialization
                # Single timestep completion can occur with aggressive conditions (high shelf temp, low pressure)
                # This is a valid physical scenario where drying completes within dt, not an error
                if (iStep==0):
                    output_saved = np.array([[t, float(Tbot), dmdt/(vial['Ap']*constant.cm_To_m**2)]])
                else:
                    output_saved = np.append(output_saved, [[t, float(Tbot), dmdt/(vial['Ap']*constant.cm_To_m**2)]],axis=0)
    
                # Advance counters
                Lck_prev = Lck # Previous cake length in cm
                Lck = Lck + dL # Cake length in cm
                if (Lck_prev < Lpr0) and (Lck > Lpr0):
                    Lck = Lpr0    # Final cake length in cm
                    dL = Lck - Lck_prev   # Cake length dried in cm
                    t = iStep*dt + dL/((dmdt*constant.kg_To_g)/(1-product['cSolid']*constant.rho_solution/constant.rho_solute)/(vial['Ap']*constant.rho_ice)*(1-product['cSolid']*(constant.rho_solution-constant.rho_ice)/constant.rho_solute)) # hr
                else:
                    t = (iStep+1) * dt # Time in hr

                # Shelf temperature
                if t<t_setpt:
                    # Ramp till set point is reached
                    if Tshelf['init'] < Tsh_setpt:
                        Tsh = Tsh + Tshelf['ramp_rate']*constant.hr_To_min*dt
                    else:
                        Tsh = Tsh - Tshelf['ramp_rate']*constant.hr_To_min*dt
                else:
                    Tsh = Tsh_setpt    # Maintain at set point
      
                    iStep = iStep + 1 # Time iteration number

            ######################################################

            T_max[i_Tsh,i_Pch] = np.max(output_saved[:,1]) if len(output_saved) > 0 else 0.0    # Maximum product temperature in C
            drying_time[i_Tsh,i_Pch] = t    # Total drying time in hr
            del_t = output_saved[1:,0]-output_saved[:-1,0]
            if len(del_t) > 0:
                del_t = np.append(del_t,del_t[-1])
                sub_flux_avg[i_Tsh,i_Pch] = np.sum(output_saved[:,2]*del_t)/np.sum(del_t)    # Average sublimation flux in kg/hr/m^2
                sub_flux_max[i_Tsh,i_Pch] = np.max(output_saved[:,2])    # Maximum sublimation flux in kg/hr/m^2
                sub_flux_end[i_Tsh,i_Pch] = output_saved[-1,2]    # Sublimation flux at the end of primary drying in kg/hr/m^2
            else:
                sub_flux_avg[i_Tsh,i_Pch] = 0.0
                sub_flux_max[i_Tsh,i_Pch] = 0.0
                sub_flux_end[i_Tsh,i_Pch] = 0.0

    ###########################################################################

    drying_time_pr = np.zeros([2])
    sub_flux_avg_pr = np.zeros([2])
    sub_flux_min_pr = np.zeros([2])
    sub_flux_end_pr = np.zeros([2])
    
    ############  Product temperature isotherms ##########

    for j,Pch in enumerate([Pchamber['setpt'][0],Pchamber['setpt'][-1]]):

        ##################  Initialization ################

        # Initialization of time
        iStep = 0      # Time iteration number
        t = 0.0    # Time in hr

        # Initialization of cake length
        Lck = 0.0    # Cake length in cm

        # Vial heat transfer coefficient in cal/s/K/cm^2
        Kv = functions.Kv_FUN(ht['KC'],ht['KP'],ht['KD'],Pch) 

        ######################################################        

        ################ Primary drying ######################

        while(Lck<=Lpr0): # Dry the entire frozen product
    
            Rp = functions.Rp_FUN(Lck,product['R0'],product['A1'],product['A2'])  # Product resistance in cm^2-hr-Torr/g
    
            Tsub = sp.fsolve(functions.T_sub_fromTpr, product['T_pr_crit'], args = (product['T_pr_crit'],Lpr0,Lck,Pch,Rp)) # Sublimation front temperature array in degC
            dmdt = functions.sub_rate(vial['Ap'],Rp,Tsub,Pch)   # Total sublimation rate array in kg/hr
                
            # Sublimated ice length
            dL = (dmdt*constant.kg_To_g)*dt/(1-product['cSolid']*constant.rho_solution/constant.rho_solute)/(vial['Ap']*constant.rho_ice)*(1-product['cSolid']*(constant.rho_solution-constant.rho_ice)/constant.rho_solute) # cm

            # Update record as functions of the cycle time
            if (iStep==0):
                output_saved = np.array([[t, dmdt/(vial['Ap']*constant.cm_To_m**2)]])
            else:
                output_saved = np.append(output_saved, [[t, dmdt/(vial['Ap']*constant.cm_To_m**2)]], axis=0)
        
            # Advance counters
            Lck_prev = Lck # Previous cake length in cm
            Lck = Lck + dL # Cake length in cm
            if (Lck_prev < Lpr0) and (Lck > Lpr0):
                Lck = Lpr0    # Final cake length in cm
                dL = Lck - Lck_prev   # Cake length dried in cm
                t = iStep*dt + dL/((dmdt*constant.kg_To_g)/(1-product['cSolid']*constant.rho_solution/constant.rho_solute)/(vial['Ap']*constant.rho_ice)*(1-product['cSolid']*(constant.rho_solution-constant.rho_ice)/constant.rho_solute)) # hr
            else:
                t = (iStep+1) * dt # Time in hr

                iStep = iStep + 1 # Time iteration number

        ######################################################

        drying_time_pr[j] = t    # Total drying time in hr
        del_t = output_saved[1:,0]-output_saved[:-1,0]
        if len(del_t) > 0:
            del_t = np.append(del_t,del_t[-1])
            sub_flux_avg_pr[j] = np.sum(output_saved[:,1]*del_t)/np.sum(del_t)    # Average sublimation flux in kg/hr/m^2
            sub_flux_min_pr[j] = np.min(output_saved[:,1])    # Minimum sublimation flux in kg/hr/m^2
            sub_flux_end_pr[j] = output_saved[-1,1]    # Sublimation flux at the end of primary drying in kg/hr/m^2
        else:
            sub_flux_avg_pr[j] = 0.0
            sub_flux_min_pr[j] = 0.0
            sub_flux_end_pr[j] = 0.0

    ###########################################################################

    T_max_eq_cap = np.zeros([np.size(Pchamber['setpt'])])

    ############  Equipment Capability ##########

    dmdt_eq_cap = eq_cap['a'] + eq_cap['b']*np.array(Pchamber['setpt'])    # Sublimation rate in kg/hr
    sub_flux_eq_cap = dmdt_eq_cap/nVial/(vial['Ap']*constant.cm_To_m**2)    # Sublimation flux in kg/hr/m^2
    
    drying_time_eq_cap = Lpr0/((dmdt_eq_cap/nVial*constant.kg_To_g)/(1-product['cSolid']*constant.rho_solution/constant.rho_solute)/(vial['Ap']*constant.rho_ice)*(1-product['cSolid']*(constant.rho_solution-constant.rho_ice)/constant.rho_solute))    # Drying time in hr

    Lck = np.linspace(0,Lpr0,100)    # Cake length in cm
    Rp = functions.Rp_FUN(Lck,product['R0'],product['A1'],product['A2'])    # Product resistance in cm^2-hr-Torr/g
    for k,Pch in enumerate(Pchamber['setpt']):
        T_max_eq_cap[k] = functions.Tbot_max_eq_cap(Pch,dmdt_eq_cap[k],Lpr0,Lck,Rp,vial['Ap'])        # Maximum product temperature in degC

    #####################################################

    return np.array([T_max,drying_time,sub_flux_avg,sub_flux_max,sub_flux_end]), np.array([np.array([product['T_pr_crit'],product['T_pr_crit']]),drying_time_pr,sub_flux_avg_pr,sub_flux_min_pr,sub_flux_end_pr]), np.array([T_max_eq_cap,drying_time_eq_cap,sub_flux_eq_cap])

