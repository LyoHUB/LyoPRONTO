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
import numpy as np
import math
from . import constant

####################### Functions #######################

##

"""
Calculates the vapor pressure in Torr. Input is sublimation front
temperature in degC
"""
def Vapor_pressure(T_sub):

    F = 2.698e10*math.exp(-6144.96/(273.15+T_sub))   # Vapor pressure at the sublimation temperature in Torr

    return F

##
"""
Calculates the intial fill height of the frozen product in cm. Inputs are fill
volume in mL, product area in cm^2, and fractional concentration of the
solute in the solution
"""
def Lpr0_FUN(Vfill,Ap,cSolid):

    dens_fac = (constant.rho_solution-cSolid*(constant.rho_solution-constant.rho_ice)/constant.rho_solute)
    return Vfill/(Ap*constant.rho_ice)*dens_fac  # Fill height in cm

##
"""
Calculates product resistance in cm^2-hr-Torr/g. Inputs are cake length 
in cm and product resistance parameters R0 in cm^2-hr-Torr/g, 
A1 in cm-hr-Torr/g, A2 in 1/cm
"""
def Rp_FUN(l,R0,A1,A2):

    return R0 + A1*l/(1+A2*l) # Product resistance in cm^2-hr-Torr/g

##
"""
Kv_FUN(KC,KP,KD,Pch)

Calculates the vial heat transfer coefficeint in cal/s/K/cm^2.
Inputs are vial heat transfer parameters KC in cal/s/K/cm^2, KP
in cal/s/K/cm^2/Torr, KD in 1/Torr, and chamber pressure in Torr
"""
def Kv_FUN(KC,KP,KD,Pch):

    return KC + KP*Pch/(1.0+KD*Pch) # Kv in cal/s/K/cm^2

##

"""
Tsub is found from solving for T_unknown.
Determines the function to calculate the sublimation temperature
represented as T_unknown. Other inputs are chamber pressure in Torr, vial
area in cm^2, product area in cm^2, vial heat transfer coefficient in
cal/s/K/cm^2, initial product length in cm, cake length in cm, product
resistance in cm^2-Torr-hr/g, and shelf temperature in degC

"""
def T_sub_solver_FUN(T_sub_guess, *data):
    # Tsub is found from solving for T_unknown.
    # Determines the function to calculate the sublimation temperature
    # represented as T_unknown. Other inputs are chamber pressure in Torr, vial
    # area in cm^2, product area in cm^2, vial heat transfer coefficient in
    # cal/s/K/cm^2, initial product length in cm, cake length in cm, product
    # resistance in cm^2-Torr-hr/g, and shelf temperature in degC
    
    Pch, Av, Ap, Kv, Lpr0, Lck, Rp, Tsh = data

    P_sub = Vapor_pressure(T_sub_guess)   # Vapor pressure at the sublimation temperature in Torr
    Qsub = constant.dHs*(P_sub-Pch)*Ap/Rp /constant.hr_To_s # Sublimation heat
    T_b = T_sub_guess + Qsub/Ap/constant.k_ice*(Lpr0-Lck) # Corresponding bottom temperature
    Qsh = Kv*Av*(Tsh - T_b) # Heat transfer from shelf
    return Qsub-Qsh




##

##
"""
Calculates the sublimation rate from each vial in kg/hr. Inputs are
product area in cm^2, product resistance in cm^2-Torr-hr/g, sublimation
front temperature in degC, and chamber pressure in Torr
"""
def sub_rate(Ap,Rp,T_sub,Pch):

    P_sub = Vapor_pressure(T_sub)   # Vapor pressure at the sublimation temperature in Torr

    dm_dt = Ap/Rp/constant.kg_To_g*(P_sub-Pch)  # Sublimation rate in kg/hr

    return dm_dt


##
"""
Calculates the temperature at the bottom of the vial in degC. Inputs are
sublimation front temperature in degC, initial product length in cm, cake
length in cm, chamber pressure in Torr, and product resistance in
cm^2-Torr-hr/g
"""
def T_bot_FUN(T_sub,Lpr0,Lck,Pch,Rp):

    P_sub = Vapor_pressure(T_sub)   # Vapor pressure at the sublimation temperature in Torr

    Tbot = T_sub + (Lpr0-Lck)*(P_sub-Pch)*constant.dHs/Rp/constant.hr_To_s/constant.k_ice # Vial bottom temperature in degC

    return Tbot
	
##
"""
Calculates product resistance in cm^2-hr-Torr/g. Inputs are sublimation
temperature in degC, initial product length in cm, cake length in cm,
chamber pressure in Torr, and vial bottom temperature in degC
"""
def Rp_finder(T_sub,Lpr0,Lck,Pch,Tbot):

    P_sub = Vapor_pressure(T_sub)   # Vapor pressure at the sublimation temperature in Torr

    Rp = (Lpr0-Lck)*(P_sub-Pch)*constant.dHs/(Tbot-T_sub)/constant.hr_To_s/constant.k_ice	# Product resistance in cm^2-Torr-hr/g

    return Rp

##

"""
Tsub is found from solving for T_unknown.
Determines the function to calculate the sublimation temperature
represented as T_unknown. Other inputs are chamber pressure in Torr, vial
area in cm^2, product area in cm^2, vial heat transfer coefficient in
cal/s/K/cm^2, initial product length in cm, cake length in cm, vial bottom 
temperature in degC, and shelf temperature in degC
"""
def T_sub_Rp_finder(T_unknown, *data):
    
    Av, Ap, Kv, Lpr0, Lck, Tbot, Tsh = data

    F = (1.0 + Ap/Av/Kv*constant.k_ice/(Lpr0-Lck))*(Tbot-T_unknown) - (Tsh-T_unknown)

    return F

##

"""
Tsub is found from solving for T_unknown.  # Determines the function to calculate the sublimation temperature
represented as T_unknown. Other inputs are vial bottom temperature in degC, 
initial product length in cm, cake length in cm, chamber pressure in Torr,
and product resistance in cm^2-Torr-hr/g
"""
def T_sub_fromTpr(T_unknown, *data):
    
    Tbot, Lpr0, Lck, Pch, Rp = data

    P_sub = Vapor_pressure(T_unknown)   # Vapor pressure at the sublimation temperature in Torr

    F = T_unknown - Tbot + (P_sub-Pch)*(Lpr0-Lck)*constant.dHs/Rp/constant.hr_To_s/constant.k_ice  # Heat and mass transfer energy balance function - Should be zero

    return F

##

"""
Tbot_max_eq_cap(Pch,dm_dt,Lpr0,Lck,Rp,Ap)

Calculates the maximum product temperature (occus at vial bottom) in
degC. Inputs are chamber pressure in Torr, sublimation rate based on
equipment capability in kg/hr, initial product length in cm, cake length
in cm, product resistance in cm^2-Torr-hr/g, and product area in cm^2
"""
def Tbot_max_eq_cap(Pch,dm_dt,Lpr0,Lck,Rp,Ap):

    P_sub = dm_dt/Ap*Rp + Pch     # Sublimation front pressure in Torr
    T_sub = -6144.96/np.log(P_sub/2.698e10) - 273.15    # Sublimation front temperature in degC
    Tbot = T_sub + (Lpr0-Lck)*(P_sub-Pch)*constant.dHs/Rp/constant.hr_To_s/constant.k_ice	#Vial bottom temperature in degC
    Tbot_max = np.max(Tbot)   # Maximum vial bottom temperature in degC

    return Tbot_max

"""
Ineq_Constraints(Pch,dm_dt,Tcrit,Tbot,a,b,nVial)

Defines the inequality constraints for lyophilization optimization within
safe operation region inside the desgin space. Inputs are chamber pressure in Torr,
sublimation rate in kg/hr, critical product temperature in degC, vial bottom
temperature in degC, equipment capability parameters a in kg/hr and b in kg/hr/Torr,
and number of vials
"""
def Ineq_Constraints(Pch,dm_dt,Tcrit,Tbot,a,b,nVial):

    C1 = a + b*Pch - nVial*dm_dt	# Equipment capability limit
   
    C2 = Tcrit - Tbot		# Maximum product temperature limit

    return C1,C2

##

"""
Eq_Constraints(Pch,dmdt,Tbot,Tsh,Psub,Tsub,Kv,Lpr0,Lck,Av,Ap,Rp)

Defines the equality constraints for lyophilization. Inputs are chamber pressure in Torr,
sublimation rate in kg/hr, vial bottom temperature in degC, shelf temperature in degC,
sublimation front pressure in Torr, sublimation front temperature in degC, vial heat
transfer coefficient in cal/s/cm^2/C, initial product length in cm, cake length in cm,
vial area in cm^2, product area in cm^2, and product resistance in cm^2-Torr-hr/g 
"""
def Eq_Constraints(Pch,dmdt,Tbot,Tsh,Psub,Tsub,Kv,Lpr0,Lck,Av,Ap,Rp):

    C1 = Psub - 2.698e10*math.exp(-6144.96/(273.15+Tsub))   # Vapor pressure at the sublimation temperature in Torr
    
    C2 = dmdt - Ap/Rp/constant.kg_To_g*(Psub-Pch)  # Sublimation rate in kg/hr
    
    C3 = (Tsh-Tbot)*Av*Kv*(Lpr0-Lck) - Ap*(Tbot-Tsub)*constant.k_ice  # Vial heat transfer balance

    C4 = Tsh - dmdt*constant.kg_To_g/constant.hr_To_s*constant.dHs/Av/Kv - Tbot  # Shelf temperature in C

    return C1,C2,C3,C4

##

"""
lumped_cap_Tpr(t,Tpr0,rho,Cp,V,h,Av,Tsh,Tsh0, Tsh_ramp)

Calculates the product temperature in C. Inputs are time in hr, initial product temperature in degC, product density in g/mL, constant pressure specific heat of the product in J/kg/K, product volume in mL, heat transfer coefficient in W/m^2/K, vial area in cm^2, current shelf temperature in degC, initial shelf temperature in degC, shelf temperature ramping rate in degC/min
"""
def lumped_cap_Tpr(t,Tpr0,rho,Cp,V,h,Av,Tsh,Tsh0, Tsh_ramp):

    F = (Tpr0 + Tsh_ramp/constant.min_To_s*rho*Cp/constant.kg_To_g*V/h/Av/constant.cm_To_m**2 - Tsh0)*math.exp(-h*Av*constant.cm_To_m**2*t*constant.hr_To_s/rho/Cp*constant.kg_To_g/V) - Tsh_ramp/constant.min_To_s*rho*Cp/constant.kg_To_g*V/h/Av/constant.cm_To_m**2 + Tsh

    return F

##

##

"""
crystallization_time_FUN(V,h,Av,Tf,Tn,Tsh)

Calculates the crystallization time in hr. Inputs are fill volume in mL, heat transfer coefficient in W/m^2/K, vial area in cm^2, freezing temperature in degC, nucleation temperature in degC, shelf temperature in degC
"""
def crystallization_time_FUN(V,h,Av,Tf,Tn,Tsh):

    F = constant.rho_solution*V*(constant.dHf*constant.cal_To_J-constant.Cp_solution/constant.kg_To_g*(Tf-Tn))/h/constant.hr_To_s/Av/constant.cm_To_m**2/(Tf-Tsh)

    return F

##



################################################################
def calc_step(t, Lck, config):
    vial, product, ht, Pch_t, Tsh_t, dt, Lpr0 = config
    Tsh = Tsh_t(t)
    Pch = Pch_t(t)
    Kv = Kv_FUN(ht['KC'],ht['KP'],ht['KD'],Pch)  # Vial heat transfer coefficient in cal/s/K/cm^2
    Rp = Rp_FUN(Lck,product['R0'],product['A1'],product['A2'])  # Product resistance in cm^2-hr-Torr/g
    Tsub = fsolve(T_sub_solver_FUN, 250, args = (Pch,vial['Av'],vial['Ap'],Kv,Lpr0,Lck,Rp,Tsh))[0] # Sublimation front temperature array in degC
    dmdt = sub_rate(vial['Ap'],Rp,Tsub,Pch)   # Total sublimation rate array in kg/hr
    if dmdt<0:
        # print("Shelf temperature is too low for sublimation.")
        dmdt = 0.0
    Tbot = T_bot_FUN(Tsub,Lpr0,Lck,Pch,Rp)    # Vial bottom temperature array in degC
    dry_frac = Lck/Lpr0

    col = np.array([t, Tsub, Tbot, Tsh, Pch*constant.Torr_to_mTorr, dmdt/(vial['Ap']*constant.cm_To_m**2), dry_frac])
    return col

def fill_output(sol, config):
    vial, product, ht, Pchamber, Tshelf, dt, Lpr0 = config
    # out_t = np.arange(0, sol.t[-1], dt)   
    out_t = np.linspace(0, sol.t[-1], 100)   
    fullout = np.zeros((len(out_t), len(calc_step(0, 0, config))))
    for i,t in enumerate(out_t):
        fullout[i,:] = calc_step(t, sol.sol(t)[0], config)
    return fullout
