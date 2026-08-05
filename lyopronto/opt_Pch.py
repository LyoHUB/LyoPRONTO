
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
import warnings
from . import constant
from . import functions


################# Primary drying at fixed set points ###############

def dry(vial,product,ht,Pchamber,Tshelf,dt,eq_cap,nVial):

    ##################  Initialization ################

    # Initial fill height
    Lpr0 = functions.Lpr0_FUN(vial['Vfill'],vial['Ap'],product['cSolid'])   # [cm]

    # Initialization of time
    iStep = 0      # Time iteration number
    t = 0.0    # Time [hr]

    # Initialization of cake length
    Lck = 0.0    # Cake length [cm]
    percent_dried = Lck/Lpr0*100.0        # Percent dried

    # Initial chamber pressure: middle of range, or 2*min if only min given
    P0 = (Pchamber['min'] + Pchamber.get('max', Pchamber['min']*3))/2.0    

    # Initial shelf temperature
    Tsh = Tshelf['init']        # [degC]
    Tshelf = Tshelf.copy()
    Tshelf['setpt'] = np.insert(Tshelf['setpt'],0,Tshelf['init'])        # Include initial shelf temperature in set point array
    # Shelf temperature control time
    Tshelf['t_setpt'] = np.array([[0]])
    for dt_i in Tshelf['dt_setpt']:
        Tshelf['t_setpt'] = np.append(Tshelf['t_setpt'],Tshelf['t_setpt'][-1]+dt_i/constant.hr_To_min)
       
    # Initial product and shelf temperatures
    Tb0 = product['T_pr_crit'] -0.1   # [degC]
    Ts0 = Tb0 - 0.1   # [degC]
    Tsh0 = Tb0 +0.1   # [degC]

    ######################################################

    ################ Primary drying ######################
    # Objective function to be minimized to maximize sublimation rate
    def objfun(x):
        return (x[0]-x[4])
    # Exact gradient of the linear objective, so SLSQP does not
    # finite-difference it at every point.
    def objfun_jac(x):
        return np.array([1.0,0.0,0.0,0.0,-1.0,0.0,0.0])
    # Quantities solved for: x = [Pch,dmdt,Tbot,Tsh,Psub,Tsub,Kv]
    x0 = np.array([P0,0.0,Tb0,Tsh0,P0*1.1,Ts0,3.0e-4])    # Initial values
    failures = 0

    while(Lck<=Lpr0): # Dry the entire frozen product

        Rp = functions.Rp_FUN(Lck,product['R0'],product['A1'],product['A2'])  # Product resistance [cm^2-hr-Torr/g]

        # Stack the equality constraints into one vector-valued constraint so
        # SLSQP evaluates and differentiates the whole system once per point
        # rather than once per component: sublimation front pressure [Torr],
        # sublimation rate [kg/hr], vial heat transfer balance, shelf
        # temperature [degC], vial heat transfer coefficient [cal/s/K/cm^2], and fixed shelf temperature [degC]
        def eq_sys(x, Tsh=Tsh):
            return np.array(functions.Eq_Constraints(x[0],x[1],x[2],x[3],x[4],x[5],x[6],Lpr0,Lck,vial['Av'],vial['Ap'],Rp)
                            + (x[6]-functions.Kv_FUN(ht['KC'],ht['KP'],ht['KD'],x[0]), x[3]-Tsh))
        # Inequality constraints: equipment capability and maximum product temperature
        def ineq_sys(x):
            return np.array(functions.Ineq_Constraints(x[0],x[1],product['T_pr_crit'],x[2],eq_cap['a'],eq_cap['b'],nVial))
        cons = ({'type':'eq','fun':eq_sys},
            {'type':'ineq','fun':ineq_sys})
        # Bounds for the unknowns
        bnds = ((Pchamber['min'],Pchamber.get('max', None)),(0,None),(None,None),(None,None),(0,None),(None,None),(0,None))
        # Minimize the objective function i.e. maximize the sublimation rate
        res = sp.minimize(objfun,x0,jac = objfun_jac,bounds = bnds, constraints = cons)
        [Pch,dmdt,Tbot,Tsh,Psub,Tsub,Kv] = res['x']    # Results [Torr], [kg/hr], [degC], [degC], [Torr], [degC], [cal/s/K/cm^2]
        # # Use the results as a guess for the next iteration
        # TODO: decide on appropriate error handling for unsuccessful iterations
        # Should check some simple conditions probably and see if inputs have any feasible solutions
        if not res['success']:
            warnings.warn(f"Optimization failed at {t} hr, {percent_dried:.1f}% dried.\n"+\
                          f"Message: {res['message']}\n"+\
                          f"Pch={Pch:.1f}, dmdt={dmdt:.2e}, Tbot={Tbot:.1f}, Tsh={Tsh:.1f}, Psub={Psub:.1f}, Tsub={Tsub:.1f}, Kv={Kv:.2e}")
            failures += 1
            if failures >= 10:
                # warnings.warn(f"Maximum consecutive optimization failures ({failures}) reached. Terminating drying simulation.")
                break
            else:
                continue

        # Sublimated ice length
        dL = (dmdt*constant.kg_To_g)*dt/(1-product['cSolid']*constant.rho_solution/constant.rho_solute)/(vial['Ap']*constant.rho_ice)*(1-product['cSolid']*(constant.rho_solution-constant.rho_ice)/constant.rho_solute) # [cm]

        # Update record as functions of the cycle time
        if (iStep==0):
            output_saved = np.array([[t, float(Tsub), float(Tbot), Tsh, Pch*constant.Torr_to_mTorr, dmdt/(vial['Ap']*constant.cm_To_m**2), percent_dried]])
        else:
            output_saved = np.append(output_saved, [[t, float(Tsub), float(Tbot), Tsh, Pch*constant.Torr_to_mTorr, dmdt/(vial['Ap']*constant.cm_To_m**2), percent_dried]],axis=0)
    
        # Advance counters
        Lck_prev = Lck # Previous cake length [cm]
        Lck = Lck + dL # Cake length [cm]
        if (Lck_prev < Lpr0) and (Lck > Lpr0):
            Lck = Lpr0    # Final cake length [cm]
            dL = Lck - Lck_prev   # Cake length dried [cm]
            t = iStep*dt + dL/((dmdt*constant.kg_To_g)/(1-product['cSolid']*constant.rho_solution/constant.rho_solute)/(vial['Ap']*constant.rho_ice)*(1-product['cSolid']*(constant.rho_solution-constant.rho_ice)/constant.rho_solute)) # [hr]
        else:
            t = (iStep+1) * dt # Time [hr]

        percent_dried = Lck/Lpr0*100   # Percent dried

        if len(np.where(Tshelf['t_setpt']>t)[0])==0:
            warnings.warn("Total time exceeded. Drying incomplete")    # Shelf temperature set point time exceeded, drying not done
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
