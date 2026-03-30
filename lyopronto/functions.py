"""File with a bunch of functions in it."""
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
from scipy.optimize import fsolve, brentq
from scipy.integrate import quad
from scipy.interpolate import PchipInterpolator
import numpy as np
from . import constant

####################### Functions #######################

##

def Vapor_pressure(T_sub):
    """
    Calculates the vapor pressure [Torr]. Input is sublimation front
    temperature [degC]
    """

    p = 2.698e10*np.exp(-6144.96/(273.15+T_sub))   # Vapor pressure at the sublimation temperature [Torr]

    return p

##
def Lpr0_FUN(Vfill,Ap,cSolid):
    """Calculates the intial fill height of the frozen product [cm].

    Args:
        Vfill (float): fill volume [mL]
        Ap (float): product area [cm^2]
        cSolid (float): concentration of the solute in solution [g/mL]

    Returns:
        (float): initial fill height of the frozen product [cm].
    """

    dens_fac = (constant.rho_solution-cSolid*(constant.rho_solution-constant.rho_ice)/constant.rho_solute)
    return Vfill/(Ap*constant.rho_ice)*dens_fac  # Fill height [cm]

##
def Rp_FUN(L,R0,A1,A2):
    """Calculates product resistance [cm^2-hr-Torr/g].

    Args:
        L (float): cake length [cm]
        R0 (float): base product resistance [cm^2-hr-Torr/g]
        A1 (float): product resistance parameter [cm-hr-Torr/g]
        A2 (float): product resistance parameter [1/cm]

    Returns:
        (float): product resistance [cm^2-hr-Torr/g]
    """

    return R0 + A1*L/(1+A2*L) # Product resistance [cm^2-hr-Torr/g]

##
def Kv_FUN(KC,KP,KD,Pch):
    """Calculates the vial heat transfer coefficient.

    Args:
        KC (float): Vial heat transfer parameter [cal/s/K/cm^2].
        KP (float): Vial heat transfer parameter [cal/s/K/cm^2/Torr].
        KD (float): Vial heat transfer parameter [1/Torr].
        Pch (float): Chamber pressure [Torr].

    Returns:
        (float): Vial heat transfer coefficient [cal/s/K/cm^2].
    """

    return KC + KP*Pch/(1.0+KD*Pch) # Kv [cal/s/K/cm^2]

##

def T_sub_solver_FUN(T_sub_guess, *data):
    """Tsub is found from solving for T_unknown.
    Determines the function to calculate the sublimation temperature
    represented as T_unknown. Other inputs are chamber pressure [Torr], vial
    area [cm^2], product area [cm^2], vial heat transfer coefficient
    [cal/s/K/cm^2], initial product length [cm], cake length [cm], product
    resistance [cm^2-Torr-hr/g], and shelf temperature [degC]

    Args:
        T_sub_guess (float): Initial guess for the sublimation temperature [degC].
        data (tuple): Pch, Av, Ap, Kv, Lpr0, Lck, Rp, Tsh

    Returns:
        (float): residual for the pseudosteady heat balance
    """
    
    Pch, Av, Ap, Kv, Lpr0, Lck, Rp, Tsh = data

    P_sub = Vapor_pressure(T_sub_guess)   # Vapor pressure at the sublimation temperature [Torr]
    Qsub = constant.dHs*(P_sub-Pch)*Ap/Rp /constant.hr_To_s # Sublimation heat
    T_b = T_sub_guess + Qsub/Ap/constant.k_ice*(Lpr0-Lck) # Corresponding bottom temperature
    Qsh = Kv*Av*(Tsh - T_b) # Heat transfer from shelf
    return Qsub-Qsh

##
def sub_rate(Ap,Rp,T_sub,Pch):
    """
    Calculates the sublimation rate from each vial [kg/hr]. Inputs are
    product area [cm^2], product resistance [cm^2-Torr-hr/g], sublimation
    front temperature [degC], and chamber pressure [Torr]
    """

    P_sub = Vapor_pressure(T_sub)   # Vapor pressure at the sublimation temperature [Torr]

    dm_dt = Ap/Rp/constant.kg_To_g*(P_sub-Pch)  # Sublimation rate [kg/hr]

    return dm_dt


##
def T_bot_FUN(T_sub,Lpr0,Lck,Pch,Rp):
    """
    Calculates the temperature at the bottom of the vial [degC]. Inputs are
    sublimation front temperature [degC], initial product length [cm], cake
    length [cm], chamber pressure [Torr], and product resistance
    [cm^2-Torr-hr/g]
    """

    P_sub = Vapor_pressure(T_sub)   # Vapor pressure at the sublimation temperature [Torr]

    Tbot = T_sub + (Lpr0-Lck)*(P_sub-Pch)*constant.dHs/Rp/constant.hr_To_s/constant.k_ice # Vial bottom temperature [degC]

    return Tbot
	
##
def Rp_finder(T_sub,Lpr0,Lck,Pch,Tbot):
    """
    Calculates product resistance [cm^2-hr-Torr/g]. Inputs are sublimation
    temperature [degC], initial product length [cm], cake length [cm],
    chamber pressure [Torr], and vial bottom temperature [degC]
    """

    P_sub = Vapor_pressure(T_sub)   # Vapor pressure at the sublimation temperature [Torr]

    Rp = (Lpr0-Lck)*(P_sub-Pch)*constant.dHs/(Tbot-T_sub)/constant.hr_To_s/constant.k_ice	# Product resistance [cm^2-Torr-hr/g]

    return Rp

##

def T_sub_Rp_finder(T_sub, *data):
    """
    Tsub is found from solving for T_unknown.
    Determines the function to calculate the sublimation temperature
    represented as T_unknown. Other inputs are chamber pressure [Torr], vial
    area [cm^2], product area [cm^2], vial heat transfer coefficient
    [cal/s/K/cm^2], initial product length [cm], cake length [cm], vial bottom
    temperature [degC], and shelf temperature [degC]
    """
    
    Av, Ap, Kv, Lpr0, Lck, Tbot, Tsh = data

    LHS = (Tsh - Tbot)*Av*Kv
    RHS = (Tbot - T_sub)*Ap*constant.k_ice/(Lpr0-Lck)

    return LHS-RHS

##

def T_sub_fromTpr(T_unknown, *data):
    """
    Tsub is found from solving for T_unknown.  # Determines the function to calculate the sublimation temperature
    represented as T_unknown. Other inputs are vial bottom temperature [degC],
    initial product length [cm], cake length [cm], chamber pressure [Torr],
    and product resistance [cm^2-Torr-hr/g]
    """
    
    Tbot, Lpr0, Lck, Pch, Rp = data

    P_sub = Vapor_pressure(T_unknown)   # Vapor pressure at the sublimation temperature [Torr]

    F = T_unknown - Tbot + (P_sub-Pch)*(Lpr0-Lck)*constant.dHs/Rp/constant.hr_To_s/constant.k_ice  # Heat and mass transfer energy balance function - Should be zero

    return F

##

def Tbot_max_eq_cap(Pch,dm_dt,Lpr0,Lck,Rp,Ap):
    """
    Calculates the maximum product temperature (occurs at vial bottom)
    [degC]. Inputs are chamber pressure [Torr], sublimation rate based on
    equipment capability [kg/hr], initial product length [cm], cake length
    [cm], product resistance [cm^2-hr-Torr/g], and product area [cm^2]
    """

    P_sub = dm_dt/Ap*Rp + Pch     # Sublimation front pressure [Torr]
    T_sub = -6144.96/np.log(P_sub/2.698e10) - 273.15    # Sublimation front temperature [degC]
    Tbot = T_sub + (Lpr0-Lck)*(P_sub-Pch)*constant.dHs/Rp/constant.hr_To_s/constant.k_ice	# Vial bottom temperature [degC]
    Tbot_max = np.max(Tbot)   # Maximum vial bottom temperature [degC]

    return Tbot_max

def Ineq_Constraints(Pch,dm_dt,Tcrit,Tbot,a,b,nVial):
    """
    Defines the inequality constraints for lyophilization optimization within
    safe operation region inside the desgin space. Inputs are chamber pressure [Torr],
    sublimation rate [kg/hr], critical product temperature [degC], vial bottom
    temperature [degC], equipment capability parameters a [kg/hr] and b [kg/hr/Torr],
    and number of vials
    """

    C1 = a + b*Pch - nVial*dm_dt	# Equipment capability limit
   
    C2 = Tcrit - Tbot		# Maximum product temperature limit

    return C1,C2

##

def Eq_Constraints(Pch,dmdt,Tbot,Tsh,Psub,Tsub,Kv,Lpr0,Lck,Av,Ap,Rp):
    """
    Defines the equality constraints for lyophilization. Inputs are chamber pressure [Torr],
    sublimation rate [kg/hr], vial bottom temperature [degC], shelf temperature [degC],
    sublimation front pressure [Torr], sublimation front temperature [degC], vial heat
    transfer coefficient [cal/s/cm^2/K], initial product length [cm], cake length [cm],
    vial area [cm^2], product area [cm^2], and product resistance [cm^2-Torr-hr/g]
    """

    C1 = Psub - 2.698e10*np.exp(-6144.96/(273.15+Tsub))   # Vapor pressure at the sublimation temperature [Torr]
    
    C2 = dmdt - Ap/Rp/constant.kg_To_g*(Psub-Pch)  # Sublimation rate [kg/hr]
    
    C3 = (Tsh-Tbot)*Av*Kv*(Lpr0-Lck) - Ap*(Tbot-Tsub)*constant.k_ice  # Vial heat transfer balance

    C4 = Tsh - dmdt*constant.kg_To_g/constant.hr_To_s*constant.dHs/Av/Kv - Tbot  # Shelf temperature [degC]

    return C1,C2,C3,C4

##

def lumped_cap_Tpr_abstract(t,Tpr0,V,h,Av,Tsh,Tsh0,Tsh_ramp,rho,Cpi):
    """
    Calculates the product temperature [degC]. Inputs are time [hr], initial product temperature [degC], product density [g/mL], constant pressure specific heat of the product [J/kg/K], product volume [mL], heat transfer coefficient [W/m^2/K], vial area [cm^2], current shelf temperature [degC], initial shelf temperature [degC], shelf temperature ramping rate [degC/min]
    """

    rr = Tsh_ramp/constant.min_To_s # Ramp rate [K/s]
    rhoV = rho*V  # Mass of solution [g]
    Cp = Cpi/constant.kg_To_g # Specific heat capacity [J/g/K]
    hA = h*Av*constant.cm_To_m**2  # Heat transfer coefficient times area [W/K]
    ts = t*constant.hr_To_s # Time [s]

    tau = rhoV*Cp/hA  # Time constant [s]
    asymp_T = (Tpr0 - Tsh0 + rr*rhoV*Cp/hA) # Prefactor in solution [degC]

    return asymp_T*np.exp(-ts/tau) - rr*tau + Tsh

def lumped_cap_Tpr_ice(*args):
    return lumped_cap_Tpr_abstract(*args, constant.rho_ice,constant.Cp_ice)

def lumped_cap_Tpr_sol(*args):
    return lumped_cap_Tpr_abstract(*args, constant.rho_solution,constant.Cp_solution)

##

class RampInterpolator:
    """Class to handle ramped setpoint interpolation."""

    def __init__(self, rampspec, count_ramp_against_dt=True):
        self.ramp_sep = count_ramp_against_dt
        self.dt_setpt = np.array(rampspec["dt_setpt"])
        self.ramp_rate = rampspec["ramp_rate"]
        if "init" in rampspec:
            self.setpt = np.concatenate(([rampspec["init"]], rampspec["setpt"]))
            self.values = np.concatenate(([self.setpt[0]], np.repeat(self.setpt[1:], 2)))
            times = np.array([0.0])
        else:
            self.setpt = np.array(rampspec["setpt"])
            self.values = np.repeat(self.setpt, 2)
            times = np.array([0.0, self.dt_setpt[0] / constant.hr_To_min])
        # Older logic: setpoint_dt includes the ramp time.
        # Kept for backward compatibility, but add a check if insufficient time allowed for ramp
        if count_ramp_against_dt:
            # If there is no "init" value, dt_setpt[0] was already consumed.
            has_init = "init" in rampspec
            for i in range(1, len(self.setpt)):
                # If fewer dt_setpt than setpt provided, repeat the last dt
                dt_idx = i - 1 if has_init else i
                totaltime = self.dt_setpt[min(len(self.dt_setpt) - 1, dt_idx)] / constant.hr_To_min
                ramptime = abs((self.setpt[i] - self.setpt[i-1]) / self.ramp_rate) / constant.hr_To_min
                holdtime = totaltime - ramptime
                if holdtime < 0:
                    warn(f"Ramp time ({ramptime * constant.hr_To_min:.1f} min) from "
                         f"{self.setpt[i-1]:.2e} to {self.setpt[i]:.2e} exceeds "
                         f"total stage time ({totaltime * constant.hr_To_min:.1f} min). "
                         f"Clamping hold time to 0.")
                    holdtime = 0.0
                times = np.append(times, [ramptime, holdtime])
        else:
        # Newer logic: setpoint_dt applies *after* the ramp is complete.
            for i,v in enumerate(self.setpt[1:], start=1):
                ramptime = abs((v - self.setpt[i-1]) / self.ramp_rate) / constant.hr_To_min
                # If less dt_setpt than setpt provided, repeat the last dt
                holdtime = self.dt_setpt[min(len(self.dt_setpt)-1, i-1)] / constant.hr_To_min
                times = np.append(times, [ramptime, holdtime])
        self.times = np.cumsum(times)
        
    def __call__(self, t):
        return np.interp(t, self.times, self.values)
    
    def max_time(self):
        return self.times[-1]
    
    def max_setpt(self):
        return np.max(self.values)

##

def crystallization_time_FUN(V,h,Av,Tf,Tn,Tsh_func,t0):
    """
    Calculates the crystallization time [hr]. Inputs are fill volume [mL], heat transfer coefficient [W/m^2/K], vial area [cm^2], freezing temperature [degC], nucleation temperature [degC], shelf temperature [degC]
    """

    # t = constant.rho_solution*V*(constant.dHf*constant.cal_To_J-constant.Cp_solution/constant.kg_To_g*(Tf-Tn))/h/constant.hr_To_s/Av/constant.cm_To_m**2/(Tf-Tsh)
    rhoV = constant.rho_solution*V  # Mass of the solution [g]
    Hf = constant.dHf*constant.cal_To_J # Fusion enthalpy [J/g]
    Cp = constant.Cp_solution/constant.kg_To_g # Specific heat capacity [J/g/K]
    hA = h*constant.hr_To_s * Av*constant.cm_To_m**2 # Heat transfer coefficient [J/K/hr]
    # t = rhoV*(Hf-Cp*(Tf-Tn))/hA/(Tf-Tsh) # time: g*(J/g- J/g/K*K)/(J/m^2/K/hr*m^2*K) = hr
    lhs = rhoV*(Hf-Cp*(Tf-Tn))/hA
    def integrand(dt):
        return Tf - Tsh_func(t0+dt)
    def resid(delta_t):
        integral, _ = quad(integrand, 0, delta_t)
        return integral - lhs
    delta_t = brentq(resid, 0, 100.0)
    return delta_t

##



################################################################
def calc_step(t, Lck, inputs):
    """Calculate the full set of system states at a given time step from ODE solution states.

    Args:
        t (float): The current time in hours.
        Lck (float): The cake thickness [cm].
        inputs (tuple): A tuple containing the inputs parameters.

    Returns:
        (np.ndarray): The full set of system states at the given time step:
            0. Time [hr],
            1. Sublimation front temperature [°C],
            2. Vial bottom temperature [°C],
            3. Shelf temperature [°C],
            4. Chamber pressure [mTorr],
            5. Sublimation flux [kg/hr/m²],
            6. Drying percent [%]
    """
    vial, product, ht, Pch_t, Tsh_t, dt, Lpr0 = inputs
    Tsh = Tsh_t(t)
    Pch = Pch_t(t)
    Kv = Kv_FUN(ht['KC'],ht['KP'],ht['KD'],Pch)  # Vial heat transfer coefficient [cal/s/K/cm^2]
    Rp = Rp_FUN(Lck,product['R0'],product['A1'],product['A2'])  # Product resistance [cm^2-hr-Torr/g]
    Tsub = fsolve(T_sub_solver_FUN, 250, args = (Pch,vial['Av'],vial['Ap'],Kv,Lpr0,Lck,Rp,Tsh))[0] # Sublimation front temperature [degC]
    dmdt = sub_rate(vial['Ap'],Rp,Tsub,Pch)   # Total sublimation rate [kg/hr]
    if dmdt<0:
        dmdt = 0.0
        Tsub = Tsh  # No sublimation, Tsub equals shelf temp
        Tbot = Tsh
    else:
        Tbot = T_bot_FUN(Tsub,Lpr0,Lck,Pch,Rp)    # Vial bottom temperature [degC]
    dry_percent = (Lck/Lpr0)*100

    col = np.array([t, Tsub, Tbot, Tsh, Pch*constant.Torr_to_mTorr, dmdt/(vial['Ap']*constant.cm_To_m**2), dry_percent])
    return col

def fill_output(sol, inputs):
    """Fill the output array with the results from the ODE solver.

    Args:
        sol (ODESolution): The solution object returned by the ODE solver.
        inputs (tuple): A tuple containing the input parameters.

    Returns:
        (np.ndarray): The output array filled with the results from the ODE solver.

    Each call to calc_step requires a nonlinear solve for Tsub, so doing this for thousands 
    of points is impractical. Instead, we calculate at the the ODE solver points, and 
    interpolate elsewhere.
    """
    dt = inputs[5]

    Pch_t, Tsh_t = inputs[3], inputs[4]

    interp_points = np.zeros((len(sol.t), 7))
    for i,(t, y) in enumerate(zip(sol.t, sol.y[0])):
        interp_points[i,:] = calc_step(t, y, inputs)
    # out_t = np.arange(0, sol.t[-1], dt)   
    if dt is None:
        return interp_points
    else:
        out_t = np.arange(0, sol.t[-1], dt)   
    interp_func = PchipInterpolator(sol.t, interp_points, axis=0)
    fullout = np.zeros((len(out_t), 7))
    for i, t in enumerate(out_t):
        if np.any(sol.t == t):
            fullout[i,:] = interp_points[sol.t == t, :]
        else:
            fullout[i,:] = interp_func(t)
        fullout[i, 3] = Tsh_t(t)  # Ensure shelf temp is exact
        fullout[i, 4] = Pch_t(t)*constant.Torr_to_mTorr  # Ensure chamber pressure is exact
    return fullout
