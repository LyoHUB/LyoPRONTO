import scipy.optimize as sp
import numpy as np
import math
import csv
from . import constant
from . import functions
from pdb import set_trace as keyboard


################# Freezing ###############

def freeze(vial,product,h_freezing,Tshelf,dt):

    ##################  Initialization ################

    # Initial fill height
    Lpr0 = functions.Lpr0_FUN(vial['Vfill'],vial['Ap'],product['cSolid'])   # cm

    # Frozen product volume
    V_frozen = Lpr0*vial['Ap']    # mL

    # Initialization of time
    iStep = 0      # Time iteration number
    t = 0.0    # Time in hr

    # Initial shelf temperature
    Tsh = Tshelf['init']        # degC
    
    # Shelf temperature and time triggers, ramping rates
    Tsh_tr = np.array([Tshelf['init']])    # degC
    for T in Tshelf['setpt']:
        Tsh_tr = np.append(Tsh_tr,T)    # degC
        Tsh_tr = np.append(Tsh_tr,T)    # degC
    r = np.array([[0.0]])    # degC/min
    for i,T in enumerate(Tsh_tr[:-1]):
        if Tsh_tr[i+1]>T:
            r = np.append(r,Tshelf['ramp_rate'])    # degC/min
        elif Tsh_tr[i-1]<T:
            r = np.append(r,-Tshelf['ramp_rate'])    # degC/min
        else:
            r = np.append(r,0.0)    # degC/min
    t_tr = np.array([[0.0]])    # hr
    j = 0
    for i,T in enumerate(Tsh_tr[:-1]):
        if Tsh_tr[i+1]==T:
            t_tr = np.append(t_tr,t_tr[i-1]+Tshelf['dt_setpt'][j]/constant.hr_To_min)
            j = j+1
        else:
            t_tr = np.append(t_tr,(Tsh_tr[i+1]-T)/r[i+1]/constant.hr_To_min)    # hr
    

    # Initial product temperature
    Tpr = product['Tpr0']    # degC
    Tpr0 = Tpr
    i_prev = 1    
    
    ######################################################

    freezing_output_saved = np.array([[t, Tsh, Tpr]])

    ################ Cooling ######################

    while(Tpr>product['Tn']): # Till the product reaches the nucleation temperature

        iStep = iStep + 1 # Time iteration number
        t = iStep*dt # hr

        if len(np.where(t_tr>t)[0])==0:
            print("Total time exceeded. Freezing incomplete")    # Shelf temperature set point time exceeded, freezing not done
            break
        else:
            i = np.where(t_tr>t)[0][0]
            if not(i == i_prev):
                Tpr0 = Tpr
                i_prev = i
            # Ramp shelf temperature till next set point is reached and then maintain at set point
            Tsh = Tsh + r[i]*constant.hr_To_min*dt    # degC
            # Product temperature
            Tpr = functions.lumped_cap_Tpr(t-t_tr[i-1],Tpr0,constant.rho_solution,constant.Cp_solution,vial['Vfill'],h_freezing,vial['Av'],Tsh,Tsh_tr[i-1],r[i])    # degC

        # Update record as functions of the cycle time
            freezing_output_saved = np.append(freezing_output_saved, [[t, Tsh, Tpr]],axis=0)    

    ######################################################

    ################ Nucleation ######################

    freezing_output_saved = np.append(freezing_output_saved, [[t, Tsh, product['Tn']]],axis=0)

    ######################################################

    ################ Crystallization ######################

    tn = t    # Nucleation onset time in hr
    dt_crystallization = functions.crystallization_time_FUN(vial['Vfill'],h_freezing,vial['Av'],product['Tf'],product['Tn'],Tsh)    # Crystallization time in hr
    ts = tn + dt_crystallization    # Solidification onset time in hr

    while(t<ts):

        if len(np.where(t_tr>t)[0])==0:
            print("Total time exceeded. Freezing incomplete")    # Shelf temperature set point time exceeded, freezing not done
            break
        else:
            i = np.where(t_tr>t)[0][0]
            if not(i == i_prev):
                Tpr0 = Tpr
                i_prev = i
            # Ramp shelf temperature till next set point is reached and then maintain at set point
            Tsh = Tsh + r[i]*constant.hr_To_min*dt    # degC
            # Product temperature stays at freezing temperature
            Tpr = product['Tf']    # degC

        # Update record as functions of the cycle time
            freezing_output_saved = np.append(freezing_output_saved, [[t, Tsh, Tpr]],axis=0)

        iStep = iStep + 1 # Time iteration number
        t = iStep*dt # hr    

    ######################################################

    ################ Solidification ######################

    while(t<t_tr[-1]):

        Tpr = functions.lumped_cap_Tpr(t-ts,product['Tf'],constant.rho_ice,constant.Cp_ice,V_frozen,h_freezing,vial['Av'],Tsh,Tsh,0.0)

        # Update record as functions of the cycle time
        freezing_output_saved = np.append(freezing_output_saved, [[t, Tsh, Tpr]],axis=0)

        iStep = iStep + 1 # Time iteration number
        t = iStep*dt # hr

    ######################################################
    
    return freezing_output_saved    
    
############################################################################
