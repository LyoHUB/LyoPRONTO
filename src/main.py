#!/usr/bin/env python

import sys
import scipy.optimize as sp
import numpy as np
import math
import csv
import constant
import freezing
import calc_knownRp
import calc_unknownRp
import design_space
import opt_Pch_Tsh
import opt_Pch
import opt_Tsh
import functions
import pylab as plt
from matplotlib import rc as matplotlibrc
from pdb import set_trace as keyboard
import time

current_time = time.strftime("%y%m%d_%H%M",time.localtime())

################################################################

######################## Inputs ########################

# Simulation type
# 4 Tools available: 'Freezing Calculator', 'Primary Drying Calculator', 'Design-Space-Generator', 'Optimizer'
# For 'Freezing Calculator': h_freezeing, Tpr0, Tf and Tn must be provided
#                 No Variable Tsh - set point must be specified
# For 'Primary Drying Calculator': If Kv and Rp are known, drying time can be determined
#            If drying time and Rp are known, Kv can be determined
#            If Kv and product temperature are known, Rp can be determined
#            No Variable Pch and Tsh - set points must be specified
# For 'Design-Space-Generator': Kv and Rp must be known, Tpr_crit must be provided
#                No Variable Pch and Tsh - set points must be specified
# For 'Optimizer': Kv and Rp must be known, Tpr_crit must be provided
#           Can use variable Pch and/or Tsh
sim = dict([('tool','Primary Drying Calculator'),('Kv_known','Y'),('Rp_known','Y'),('Variable_Pch','N'),('Variable_Tsh','N')])

# Vial and fill properties
# Av = Vial area in cm^2
# Ap = Product Area in cm^2
# Vfill = Fill volume in mL
vial = dict([('Av',3.80),('Ap',3.14),('Vfill',2.0)])

#Product properties
# cSolid = Fractional concentration of solute in the frozen solution
# Tpr0 = Initial product temperature for freezing in degC
# Tf = Freezing temperature in degC
# Tn = Nucleation temperature in degC
# Product Resistance Parameters
# R0 in cm^2-hr-Torr/g, A1 in cm-hr-Torr/g, A2 in 1/cm
if sim['tool'] == 'Freezing Calculator':
    product = dict([('cSolid',0.0),('Tpr0',15.8),('Tf',-1.54),('Tn',-5.84)])
elif not(sim['tool'] == 'Primary Drying Calculator' and sim['Rp_known'] == 'N'):
    product = dict([('cSolid',0.05),('R0',1.4),('A1',16.0),('A2',0.0)])
else:
    product = dict([('cSolid',0.05)])
    # Experimental product temperature measurements: format - t(hr), Tp(C)
    product_temp_filename = './temperature.dat'
# Critical product temperature
# At least 2 to 3 deg C below collapse or glass transition temperature
if not(sim['tool'] == 'Freezing Calculator' and sim['tool'] == 'Primary Drying Calculator'):
    product['T_pr_crit'] = -5        # in degC

# Vial Heat Transfer Parameters
if sim['tool'] == 'Freezing Calculator':
    # Heat transfer coefficient between product and surroundings
    h_freezing = 38.0        #  in W/m^2/K
elif sim['Kv_known'] == 'Y':
    # Kv = KC + KP*Pch/(1+KD*Pch) 
    # KC in cal/s/K/cm^2, KP in cal/s/K/cm^2/Torr, KD in 1/Torr
    ht = dict([('KC',2.75e-4),('KP',8.93e-4),('KD',0.46)])
elif sim['Kv_known'] == 'N':
    Kv_range = np.arange(10.6,10.8,0.01)*1e-4;    # cal/s/K/cm^2
    # Primary drying time
    t_dry_exp = 12.62    # in hr
else:
    print("Kv_known: Input not recognized")
    sys.exit(1)

# Chamber Pressure
if sim['tool'] == 'Freezing Calculator':
    0
elif sim['tool'] == 'Design-Space-Generator':
    # Array of chamber pressure set points in Torr
    Pchamber = dict([('setpt',[0.1,0.4,0.7,1.5])])
elif not(sim['tool'] == 'Optimizer' and sim['Variable_Pch'] == 'Y'):
    # setpt = Chamber pressure set points in Torr
    # dt_setpt = Time for which chamber pressure set points are held in min
    # ramp_rate = Chamber pressure ramping rate in Torr/min
    Pchamber = dict([('setpt',[0.15]),('dt_setpt',[1800.0]),('ramp_rate',0.5)])
else:
    # Chamber pressure limits in Torr
    Pchamber = dict([('min',0.05),('max',1000)])

# Shelf Temperature
if sim['tool'] == 'Design-Space-Generator':
    # Array of shelf temperature set points in C
    # ramp_rate = Shelf temperature ramping rate in C/min
    Tshelf = dict([('init',-5.0),('setpt',[-5,0,2,5]),('ramp_rate',1.0)])
elif not(sim['tool'] == 'Optimizer' and sim['Variable_Tsh'] == 'Y'):
    # init = Intial shelf temperature in C
    # setpt = Shelf temperature set points in C
    # dt_setpt = Time for which shelf temperature set points are held in min
    # ramp_rate = Shelf temperature ramping rate in C/min
    Tshelf = dict([('init',-35.0),('setpt',[20.0]),('dt_setpt',[1800.0]),('ramp_rate',1.0)])
else:
    # Shelf temperature limits in C
    Tshelf = dict([('min',-45),('max',120)])

# Time step
dt = 0.001    # hr

# Lyophilizer equipment capability
# Form: dm/dt [kg/hr] = a + b * Pch [Torr]
# a in kg/hr, b in kg/hr/Torr 
if not(sim['tool'] == 'Freezing Calculator' and sim['tool'] == 'Primary Drying Calculator'):
    eq_cap = dict([('a',-0.182),('b',0.0117e3)])

# Equipment load
if not(sim['tool'] == 'Freezing Calculator' and sim['tool'] == 'Primary Drying Calculator'):
    nVial = 398    # Number of vials

########################################################

#################### Input file saved ##################

# Write data to files
#save input_saved.csv

csvfile = open('input_saved_'+current_time+'.csv', 'w')

try:
    writer = csv.writer(csvfile)
    writer.writerow(['Tool:',sim['tool']])
    writer.writerow(['Kv known?:',sim['Kv_known']])
    writer.writerow(['Rp known?:',sim['Rp_known']])
    writer.writerow(['Variable Pch?:',sim['Variable_Pch']])
    writer.writerow(['Variable Tsh?:',sim['Variable_Tsh']])
    writer.writerow([''])
    
    writer.writerow(['Vial area [cm^2]',vial['Av']])
    writer.writerow(['Product area [cm^2]',vial['Ap']])
    writer.writerow(['Vial fill volume [mL]',vial['Vfill']])
    writer.writerow([''])
    
    writer.writerow(['Fractional solute concentration:',product['cSolid']])
    if sim['tool'] == 'Freezing Calculator':
        writer.writerow(['Intial product temperature [C]:',product['Tpr0']])
        writer.writerow(['Freezing temperature [C]:',product['Tf']])
        writer.writerow(['Nucleation temperature [C]:',product['Tn']])
    elif not(sim['tool'] == 'Primary Drying Calculator' and sim['Rp_known'] == 'N'):
        writer.writerow(['R0 [cm^2-hr-Torr/g]:',product['R0']])
        writer.writerow(['A1 [cm-hr-Torr/g]:',product['A1']])
        writer.writerow(['A2 [1/cm]:',product['A2']])
    if not(sim['tool'] == 'Freezing Calculator' and sim['tool'] == 'Primary Drying Calculator'):
        writer.writerow(['Critical product temperature [C]:', product['T_pr_crit']])
    writer.writerow([''])
    
    if sim['tool'] == 'Freezing Calculator':
        writer.writerow(['h_freezing [W/m^2/K]:',h_freezing])
    elif sim['Kv_known'] == 'Y':
        writer.writerow(['KC [cal/s/K/cm^2]:',ht['KC']])
        writer.writerow(['KP [cal/s/K/cm^2/Torr]:',ht['KP']])
        writer.writerow(['KD [1/Torr]:',ht['KD']])
    elif sim['Kv_known'] == 'N':
        writer.writerow(['Kv range [cal/s/K/cm^2]:',Kv_range[:]])
        writer.writerow(['Experimental drying time [hr]:',t_dry_exp])
    writer.writerow([''])
    
    if sim['tool'] == 'Freezing Calculator':
        0
    elif sim['tool'] == 'Design-Space-Generator':
        writer.writerow(['Chamber pressure set points [Torr]:',Pchamber['setpt'][:]])
    elif not(sim['tool'] == 'Optimizer' and sim['Variable_Pch'] == 'Y'):
        for i in range(len(Pchamber['setpt'])):
            writer.writerow(['Chamber pressure setpoint [Torr]:',Pchamber['setpt'][i],'Duration [min]:',Pchamber['dt_setpt'][i]])
        writer.writerow(['Chamber pressure ramping rate [Torr/min]:',Pchamber['ramp_rate']])
    else:
        writer.writerow(['Minimum chamber pressure [Torr]:',Pchamber['min']])
        writer.writerow(['Maximum chamber pressure [Torr]:',Pchamber['max']])
    writer.writerow([''])
    
    if sim['tool'] == 'Design-Space-Generator':
        writer.writerow(['Intial shelf temperature [C]:',Tshelf['init']])
        writer.writerow(['Shelf temperature set points [C]:',Tshelf['setpt'][:]])
        writer.writerow(['Shelf temperature ramping rate [C/min]:',Tshelf['ramp_rate']])
    elif not(sim['tool'] == 'Optimizer' and sim['Variable_Tsh'] == 'Y'):
        for i in range(len(Tshelf['setpt'])):
            writer.writerow(['Shelf temperature setpoint [C]:',Tshelf['setpt'][i],'Duration [min]:',Tshelf['dt_setpt'][i]])
        writer.writerow(['Shelf temperature ramping rate [C/min]:',Tshelf['ramp_rate']])
    else:
        writer.writerow(['Minimum shelf temperature [C]:',Tshelf['min']])
        writer.writerow(['Maximum shelf temperature [C]:',Tshelf['max']])
    writer.writerow([''])
    
    writer.writerow(['Time step [hr]:',dt])
    writer.writerow([''])
    
    if not (sim['tool'] == 'Freezing Calculator' and sim['tool'] == 'Primary Drying Calculator'):
        writer.writerow(['Equipment capability parameters:','a [kg/hr]:',eq_cap['a'],'b [kg/hr/Torr]:',eq_cap['b']])
        writer.writerow(['Number of vials:',nVial])    

finally:
    csvfile.close()
    
########################################################

################### Execute  ##########################

#################

###### Freezing Calculator
if sim['tool'] == 'Freezing Calculator':
    freezing_output_saved = freezing.freeze(vial,product,h_freezing,Tshelf,dt)

#################

###### Primary Drying Calculator Tool
if sim['tool'] == 'Primary Drying Calculator':

    #### Known Kv and Rp
    if (sim['Kv_known'] == 'Y' and sim['Rp_known'] == 'Y'):
        output_saved = calc_knownRp.dry(vial,product,ht,Pchamber,Tshelf,dt)
    
    #### Determine Kv based on drying time    
    elif (sim['Kv_known'] == 'N' and sim['Rp_known'] == 'Y'):
        Kv_best = Kv_range[0]
        Time_dev_min = 1000000.0
        ht = dict([('KC',0.0),('KP',0.0),('KD',0.0)])
        for ht['KC'] in Kv_range:
            output_saved_new = calc_knownRp.dry(vial,product,ht,Pchamber,Tshelf,dt)
            time = output_saved_new[-1,0]    # Total simulated drying time in hr
            Time_dev = abs(t_dry_exp-time)/t_dry_exp*100;    # Percentage deviation of simulated drying time from experimental
            if Time_dev < Time_dev_min:
                Time_dev_min = Time_dev
                Kv_best = ht['KC']
                output_saved = output_saved_new
        print("Best Kv = "+str(Kv_best)+"\n")
        print("Drying time deviation = "+str(Time_dev_min)+"%\n")

    #### Determine Rp based on product temperature
    elif (sim['Kv_known'] == 'Y' and sim['Rp_known'] == 'N'):
        time = []
        Tbot_exp = []
        with open(product_temp_filename) as fi:
            for line in fi:
                line_string = np.fromstring(line,sep=' ')
                time = np.append(time,line_string[0])
                Tbot_exp = np.append(Tbot_exp,line_string[1])
        fi.close()
        output_saved, product_res = calc_unknownRp.dry(vial,product,ht,Pchamber,Tshelf,time,Tbot_exp)
        params,params_covariance = sp.curve_fit(functions.Rp_FUN,product_res[:,1],product_res[:,2],p0=[1.0,0.0,0.0])
        print("R0 = "+str(params[0])+"\n")
        print("A1 = "+str(params[1])+"\n")
        print("A2 = "+str(params[2])+"\n")

    else:
        print("Error: Either Kv or Rp must be specified")
        sys.exit(1)

#################

###### Design Space Generator Tool
if sim['tool'] == 'Design-Space-Generator':
    DS_shelf, DS_pr, DS_eq_cap = design_space.dry(vial,product,ht,Pchamber,Tshelf,dt,eq_cap,nVial)

#################

###### Optimizer Tool
if sim['tool'] == 'Optimizer':

    #### Variable Pch and Tsh
    if (sim['Variable_Pch'] == 'Y' and sim['Variable_Tsh'] == 'Y'):
        output_saved = opt_Pch_Tsh.dry(vial,product,ht,Pchamber,Tshelf,dt,eq_cap,nVial)

    #### Variable Pch at specified Tsh
    elif (sim['Variable_Pch'] == 'Y' and sim['Variable_Tsh'] == 'N'):
        output_saved = opt_Pch.dry(vial,product,ht,Pchamber,Tshelf,dt,eq_cap,nVial)

    #### Variable Tsh at specified Pch
    elif (sim['Variable_Pch'] == 'N' and sim['Variable_Tsh'] == 'Y'):
        output_saved = opt_Tsh.dry(vial,product,ht,Pchamber,Tshelf,dt,eq_cap,nVial)

    else:
        print("Error: Either Pch or Tsh must be variable for process optimization")
        sys.exit(1)
        
######################################################
        
####################### Outputs #######################

# LaTeX setup
matplotlibrc('text.latex', preamble=r'\usepackage{color}')
matplotlibrc('text',usetex=False)
matplotlibrc('font',family='sans-serif')

figwidth = 30
figheight = 20
lineWidth = 5
textFontSize = 60
gcafontSize = 60
markerSize = 20
labelPad = 30
majorTickWidth = 5
minorTickWidth = 3
majorTickLength = 30
minorTickLength = 20

Color_list = ['b','m','g','c','r','y','k']    # Line colors

# Write data to files
#save output_saved.csv
# Plot data and save figures
csvfile = open('output_saved_'+current_time+'.csv', 'w')

if sim['tool'] == 'Design-Space-Generator':
    try:
        writer = csv.writer(csvfile)
        writer.writerow(['Chamber Pressure [mTorr]','Maximum Product Temperature [C]','Drying Time [hr]','Average Sublimation Flux [kg/hr/m^2]','Maximum/Minimum Sublimation Flux [kg/hr/m^2]','Final Sublimation Flux [kg/hr/m^2]'])
        for i in range(np.size(Tshelf['setpt'])):
            writer.writerow(['Shelf Temperature = ',str(Tshelf['setpt'][i])])
            for j in range(np.size(Pchamber['setpt'])):
                    writer.writerow([Pchamber['setpt'][j]*constant.Torr_to_mTorr,DS_shelf[0,i,j],DS_shelf[1,i,j],DS_shelf[2,i,j],DS_shelf[3,i,j],DS_shelf[4,i,j]])
            writer.writerow(['Product Temperature = ',str(product['T_pr_crit'])])
            writer.writerow([Pchamber['setpt'][0]*constant.Torr_to_mTorr,DS_pr[0,0],DS_pr[1,0],DS_pr[2,0],DS_pr[3,0],DS_pr[4,0]])
            writer.writerow([Pchamber['setpt'][-1]*constant.Torr_to_mTorr,DS_pr[0,1],DS_pr[1,1],DS_pr[2,1],DS_pr[3,1],DS_pr[4,1]])
            writer.writerow(['Equipment Capability'])
        for k in range(np.size(Pchamber['setpt'])):
            writer.writerow([Pchamber['setpt'][k]*constant.Torr_to_mTorr,DS_eq_cap[0,k],DS_eq_cap[1,k],DS_eq_cap[2,k],DS_eq_cap[2,k],DS_eq_cap[2,k]])
    finally:
            csvfile.close()
            
    x = np.linspace(np.min(Pchamber['setpt']),np.max(Pchamber['setpt']),1000)    # pressure range in Torr
    y1 = ((DS_eq_cap[2,-1]-DS_eq_cap[2,0])/(Pchamber['setpt'][-1]-Pchamber['setpt'][0]))*(x-Pchamber['setpt'][0]) + DS_eq_cap[2,0]        # equipment capability sublimation flux in kg/hr/m^2
    y2 = ((DS_pr[3,-1]-DS_pr[3,0])/(Pchamber['setpt'][-1]-Pchamber['setpt'][0]))*(x-Pchamber['setpt'][0]) + DS_pr[3,0]    # product temperature limited sublimation flux in kg/hr/m^2
    x = x*constant.Torr_to_mTorr        # pressure range in mTorr
    i = np.where(y1>=y2)[0][0]
    y = np.append(y1[:i],y2[i:])
    x1 = np.append(x,x[::-1])
    
    fig = plt.figure(0,figsize=(figwidth,figheight))
    ax = fig.add_subplot(1,1,1)
    plt.axes(ax)
    plt.minorticks_on()
    plt.setp(ax.get_xticklabels(),fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    plt.setp(ax.get_yticklabels(),fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.tick_params(axis='x',direction='in',pad=labelPad,width=majorTickWidth,length=majorTickLength,bottom=1,top=0)
    ax.tick_params(axis='y',direction='in',pad=labelPad,width=majorTickWidth,length=majorTickLength,left=1,right=0)
    ax.tick_params(axis='x',which='minor',direction='in',width=minorTickWidth,length=minorTickLength,bottom=1,top=0)
    ax.tick_params(axis='y',which='minor',direction='in',width=minorTickWidth,length=minorTickLength,left=1,right=0)
    ax.plot([P*constant.Torr_to_mTorr for P in Pchamber['setpt']],DS_eq_cap[2,:],'-o',color='k',linewidth=lineWidth, label = "Equipment Capability")
    ax.plot([Pchamber['setpt'][0]*constant.Torr_to_mTorr,Pchamber['setpt'][-1]*constant.Torr_to_mTorr],DS_pr[3,:],'-o',color='r',linewidth=lineWidth, label = ("T$_{pr}$ = "+str(product['T_pr_crit'])+" C"))
    for i in range(np.size(Tshelf['setpt'])):
        ax.plot([P*constant.Torr_to_mTorr for P in Pchamber['setpt']],DS_shelf[3,i,:],'--',color=str(Color_list[i]),linewidth=lineWidth, label = ("T$_{sh}$ = "+str(Tshelf['setpt'][i])+" C"))
    ax.set_xlabel("Chamber Pressure [mTorr]",fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.set_ylabel("Sublimation Flux [kg/hr/m$^2$]",fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.xaxis.labelpad = labelPad
    ax.yaxis.labelpad = labelPad
    handles, labels = ax.get_legend_handles_labels()
    plt.legend(handles, labels, prop={'size':40},loc='best')
    ll,ul = ax.get_ylim()
    if np.min(DS_eq_cap[2,:])>np.max(DS_pr[3,:]):
        ul = (DS_eq_cap[2,0]+DS_eq_cap[2,1])/3
    elif np.min(DS_pr[3,:])>np.max(DS_eq_cap[2,:]):
        ul = (DS_pr[3,0]+DS_pr[3,1])/4
    ax.set_ylim([ll,ul])
    x2 = np.append(y,ll*x/x)
    ax.fill(x1,x2,color=[1.,1.,0.6])
    figure_name = 'DesignSpace_SublimationFlux_'+current_time+'.pdf'
    plt.tight_layout()
    plt.savefig(figure_name)
    plt.close()    
    
    x = np.linspace(np.min(Pchamber['setpt']),np.max(Pchamber['setpt']),1000)    # pressure range in Torr
    y1 = ((DS_eq_cap[1,-1]-DS_eq_cap[1,0])/(Pchamber['setpt'][-1]-Pchamber['setpt'][0]))*(x-Pchamber['setpt'][0]) + DS_eq_cap[1,0]        # equipment capability drying time in hr
    y2 = ((DS_pr[1,-1]-DS_pr[1,0])/(Pchamber['setpt'][-1]-Pchamber['setpt'][0]))*(x-Pchamber['setpt'][0]) + DS_pr[1,0]    # product temperature limited drying time in hr
    x = x*constant.Torr_to_mTorr        # pressure range in mTorr
    i = np.where(y1<y2)[0][0]
    y = np.append(y1[:i],y2[i:])
    x1 = np.append(x,x[::-1])

    fig = plt.figure(0,figsize=(figwidth,figheight))
    ax = fig.add_subplot(1,1,1)
    plt.axes(ax)
    plt.minorticks_on()
    plt.setp(ax.get_xticklabels(),fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    plt.setp(ax.get_yticklabels(),fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.tick_params(axis='x',direction='in',pad=labelPad,width=majorTickWidth,length=majorTickLength,bottom=1,top=0)
    ax.tick_params(axis='y',direction='in',pad=labelPad,width=majorTickWidth,length=majorTickLength,left=1,right=0)
    ax.tick_params(axis='x',which='minor',direction='in',width=minorTickWidth,length=minorTickLength,bottom=1,top=0)
    ax.tick_params(axis='y',which='minor',direction='in',width=minorTickWidth,length=minorTickLength,left=1,right=0)
    ax.plot([P*constant.Torr_to_mTorr for P in Pchamber['setpt']],DS_eq_cap[1,:],'-o',color='k',linewidth=lineWidth, label = "Equipment Capability")
    ax.plot([Pchamber['setpt'][0]*constant.Torr_to_mTorr,Pchamber['setpt'][-1]*constant.Torr_to_mTorr],DS_pr[1,:],'-o',color='r',linewidth=lineWidth, label = ("T$_{pr}$ = "+str(product['T_pr_crit'])+" C"))
    for i in range(np.size(Tshelf['setpt'])):
        ax.plot([P*constant.Torr_to_mTorr for P in Pchamber['setpt']],DS_shelf[1,i,:],'--',color=str(Color_list[i]),linewidth=lineWidth, label = ("T$_{sh}$ = "+str(Tshelf['setpt'][i])+" C"))
    ax.set_xlabel("Chamber Pressure [mTorr]",fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.set_ylabel("Drying Time [hr]",fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.xaxis.labelpad = labelPad
    ax.yaxis.labelpad = labelPad
    handles, labels = ax.get_legend_handles_labels()
    plt.legend(handles, labels, prop={'size':40},loc='best')
    ll,ul = ax.get_ylim()
    if np.min(DS_eq_cap[2,:])>np.max(DS_pr[3,:]):
        ul = (DS_eq_cap[2,0]+DS_eq_cap[2,1])/3
    elif np.min(DS_pr[3,:])>np.max(DS_eq_cap[2,:]):
        ul = (DS_pr[3,0]+DS_pr[3,1])/4
    ax.set_ylim([ll,ul])
    x2 = np.append(y,ul*x/x)
    ax.fill(x1,x2,color=[1.,1.,0.6])
    figure_name = 'DesignSpace_DryingTime_'+current_time+'.pdf'
    plt.tight_layout()
    plt.savefig(figure_name)
    plt.close()    

    x = np.linspace(np.min(Pchamber['setpt']),np.max(Pchamber['setpt']),1000)    # pressure range in Torr
    y1 = ((DS_eq_cap[0,-1]-DS_eq_cap[0,0])/(Pchamber['setpt'][-1]-Pchamber['setpt'][0]))*(x-Pchamber['setpt'][0]) + DS_eq_cap[0,0]        # equipment capability limiting product temperature in degC
    y2 = ((DS_pr[0,-1]-DS_pr[0,0])/(Pchamber['setpt'][-1]-Pchamber['setpt'][0]))*(x-Pchamber['setpt'][0]) + DS_pr[0,0]    # product temperature limit in deg C
    x = x*constant.Torr_to_mTorr        # pressure range in mTorr
    i = np.where(y1>=y2)[0][0]
    y = np.append(y1[:i],y2[i:])
    x1 = np.append(x,x[::-1])
    
    fig = plt.figure(0,figsize=(figwidth,figheight))
    ax = fig.add_subplot(1,1,1)
    plt.axes(ax)
    plt.minorticks_on()
    plt.setp(ax.get_xticklabels(),fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    plt.setp(ax.get_yticklabels(),fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.tick_params(axis='x',direction='in',pad=labelPad,width=majorTickWidth,length=majorTickLength,bottom=1,top=0)
    ax.tick_params(axis='y',direction='in',pad=labelPad,width=majorTickWidth,length=majorTickLength,left=1,right=0)
    ax.tick_params(axis='x',which='minor',direction='in',width=minorTickWidth,length=minorTickLength,bottom=1,top=0)
    ax.tick_params(axis='y',which='minor',direction='in',width=minorTickWidth,length=minorTickLength,left=1,right=0)
    ax.plot([P*constant.Torr_to_mTorr for P in Pchamber['setpt']],DS_eq_cap[0,:],'-o',color='k',linewidth=lineWidth, label = "Equipment Capability")
    ax.plot([Pchamber['setpt'][0]*constant.Torr_to_mTorr,Pchamber['setpt'][-1]*constant.Torr_to_mTorr],DS_pr[0,:],'-o',color='r',linewidth=lineWidth, label = ("T$_{pr}$ = "+str(product['T_pr_crit'])+" C"))
    for i in range(np.size(Tshelf['setpt'])):
        ax.plot([P*constant.Torr_to_mTorr for P in Pchamber['setpt']],DS_shelf[0,i,:],'--',color=str(Color_list[i]),linewidth=lineWidth, label = ("T$_{sh}$ = "+str(Tshelf['setpt'][i])+" C"))
    ax.set_xlabel("Chamber Pressure [mTorr]",fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.set_ylabel("Product Temperature [C]",fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.xaxis.labelpad = labelPad
    ax.yaxis.labelpad = labelPad
    handles, labels = ax.get_legend_handles_labels()
    plt.legend(handles, labels, prop={'size':40},loc='best')
    ll,ul = ax.get_ylim()
    if np.min(DS_eq_cap[2,:])>np.max(DS_pr[3,:]):
        ul = (DS_eq_cap[2,0]+DS_eq_cap[2,1])/3
    elif np.min(DS_pr[3,:])>np.max(DS_eq_cap[2,:]):
        ul = (DS_pr[3,0]+DS_pr[3,1])/4
    ax.set_ylim([ll,ul])
    x2 = np.append(y,ll*x/x)
    ax.fill(x1,x2,color=[1.,1.,0.6])
    figure_name = 'DesignSpace_ProductTemperature_'+current_time+'.pdf'
    plt.tight_layout()
    plt.savefig(figure_name)
    plt.close()    

elif sim['tool'] == 'Freezing Calculator':
    try:
            writer = csv.writer(csvfile)
            writer.writerow(['Time [hr]','Shelf Temperature [C]','Product Temperature [C]'])
            for i in range(0,len(freezing_output_saved)):
                writer.writerow(freezing_output_saved[i])
    finally:
            csvfile.close()
    
    fig = plt.figure(0,figsize=(figwidth,figheight))
    ax = fig.add_subplot(1,1,1)
    plt.axes(ax)
    plt.minorticks_on()
    plt.setp(ax.get_xticklabels(),fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    plt.setp(ax.get_yticklabels(),fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.tick_params(axis='x',direction='in',pad=labelPad,width=majorTickWidth,length=majorTickLength,bottom=1,top=0)
    ax.tick_params(axis='y',direction='in',pad=labelPad,width=majorTickWidth,length=majorTickLength,left=1,right=0)
    ax.tick_params(axis='x',which='minor',direction='in',width=minorTickWidth,length=minorTickLength,bottom=1,top=0)
    ax.tick_params(axis='y',which='minor',direction='in',width=minorTickWidth,length=minorTickLength,left=1,right=0)
    ax.plot(freezing_output_saved[:,0],freezing_output_saved[:,1],'-k',linewidth=lineWidth, label = "Shelf Temperature")
    ax.plot(freezing_output_saved[:,0],freezing_output_saved[:,2],'-b',linewidth=lineWidth, label = "Product Temperature")
    ax.set_xlabel("Time [hr]",fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.set_ylabel("Temperature [C]",fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.xaxis.labelpad = labelPad
    ax.yaxis.labelpad = labelPad
    handles, labels = ax.get_legend_handles_labels()
    plt.legend(handles, labels, prop={'size':40},loc='best')
    ll,ul = ax.get_ylim()
    ax.set_ylim([ll,ul+5.0])
    figure_name = 'Temperatures_'+current_time+'.pdf'
    plt.tight_layout()
    plt.savefig(figure_name)
    plt.close()    

else:
    try:
            writer = csv.writer(csvfile)
            writer.writerow(['Time [hr]','Sublimation Temperature [C]','Vial Bottom Temperature [C]', 'Shelf Temperature [C]','Chamber Pressure [mTorr]','Sublimation Flux [kg/hr/m^2]','Percent Dried'])
            for i in range(0,len(output_saved)):
                writer.writerow(output_saved[i])
    finally:
            csvfile.close()
    
    fig = plt.figure(0,figsize=(figwidth,figheight))
    ax1 = fig.add_subplot(1,1,1)
    ax2 = ax1.twinx()
    plt.axes(ax1)
    plt.minorticks_on()
    plt.axes(ax2)
    plt.minorticks_on()
    plt.setp(ax1.get_xticklabels(),fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    plt.setp(ax1.get_yticklabels(),fontsize=gcafontSize,color='b',fontweight='bold',fontname="Helvetica")
    plt.setp(ax2.get_yticklabels(),fontsize=gcafontSize,color=[0,0.7,0.3],fontweight='bold',fontname="Helvetica")
    ax1.tick_params(axis='x',direction='in',pad=labelPad,width=majorTickWidth,length=majorTickLength,bottom=1,top=0)
    ax1.tick_params(axis='y',direction='in',pad=labelPad,width=majorTickWidth,length=majorTickLength,color='b')
    ax2.tick_params(axis='y',direction='in',pad=labelPad,width=majorTickWidth,length=majorTickLength,color=[0,0.7,0.3])
    ax1.tick_params(axis='x',which='minor',direction='in',width=minorTickWidth,length=minorTickLength,bottom=1,top=0)
    ax1.tick_params(axis='y',which='minor',direction='in',width=minorTickWidth,length=minorTickLength,color='b')
    ax2.tick_params(axis='y',which='minor',direction='in',width=minorTickWidth,length=minorTickLength,color=[0,0.7,0.3])
    ax1.plot(output_saved[:,0],output_saved[:,4],'-o',color='b',markevery=5,linewidth=lineWidth, markersize=markerSize, label = "Chamber Pressure")
    ax1.set_xlabel("Time [hr]",fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax1.set_ylabel("Chamber Pressure [mTorr]",fontsize=gcafontSize,color='b',fontweight='bold',fontname="Helvetica")
    ax2.plot(output_saved[:,0],output_saved[:,5],'-',color=[0,0.7,0.3],linewidth=lineWidth, label = "Sublimation Flux")
    ax2.set_ylabel("Sublimation Flux [kg/hr/m$^2$]",fontsize=gcafontSize,color=[0,0.7,0.3],fontweight='bold',fontname="Helvetica")
    ax1.xaxis.labelpad = labelPad
    ax1.yaxis.labelpad = labelPad
    ax2.yaxis.labelpad = labelPad
    figure_name = 'Pressure,SublimationFlux_'+current_time+'.pdf'
    plt.tight_layout()
    plt.savefig(figure_name)
    plt.close()
    
    fig = plt.figure(0,figsize=(figwidth,figheight))
    ax = fig.add_subplot(1,1,1)
    plt.axes(ax)
    plt.minorticks_on()
    plt.setp(ax.get_xticklabels(),fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    plt.setp(ax.get_yticklabels(),fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.tick_params(axis='x',direction='in',pad=labelPad,width=majorTickWidth,length=majorTickLength,bottom=1,top=0)
    ax.tick_params(axis='y',direction='in',pad=labelPad,width=majorTickWidth,length=majorTickLength,left=1,right=0)
    ax.tick_params(axis='x',which='minor',direction='in',width=minorTickWidth,length=minorTickLength,bottom=1,top=0)
    ax.tick_params(axis='y',which='minor',direction='in',width=minorTickWidth,length=minorTickLength,left=1,right=0)
    ax.plot(output_saved[:,0],output_saved[:,-1],'-k',linewidth=lineWidth, label = "Percent Dried")
    ax.set_xlabel("Time [hr]",fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.set_ylabel("Percent Dried",fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.xaxis.labelpad = labelPad
    ax.yaxis.labelpad = labelPad
    figure_name = 'PercentDried_'+current_time+'.pdf'
    plt.tight_layout()
    plt.savefig(figure_name)
    plt.close()
    
    fig = plt.figure(0,figsize=(figwidth,figheight))
    ax = fig.add_subplot(1,1,1)
    plt.axes(ax)
    plt.minorticks_on()
    plt.setp(ax.get_xticklabels(),fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    plt.setp(ax.get_yticklabels(),fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.tick_params(axis='x',direction='in',pad=labelPad,width=majorTickWidth,length=majorTickLength,bottom=1,top=0)
    ax.tick_params(axis='y',direction='in',pad=labelPad,width=majorTickWidth,length=majorTickLength,left=1,right=0)
    ax.tick_params(axis='x',which='minor',direction='in',width=minorTickWidth,length=minorTickLength,bottom=1,top=0)
    ax.tick_params(axis='y',which='minor',direction='in',width=minorTickWidth,length=minorTickLength,left=1,right=0)
    ax.plot(output_saved[:,0],output_saved[:,1],'-b',linewidth=lineWidth, label = "Sublimation Front Temperature")
    ax.plot(output_saved[:,0],output_saved[:,2],'-r',linewidth=lineWidth, label = "Maximum Product Temperature")
    ax.plot(output_saved[:,0],output_saved[:,3],'-o',color='k',markevery=5,linewidth=lineWidth, markersize=markerSize, label = "Shelf Temperature")
    ax.set_xlabel("Time [hr]",fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.set_ylabel("Temperature [C]",fontsize=gcafontSize,fontweight='bold',fontname="Helvetica")
    ax.xaxis.labelpad = labelPad
    ax.yaxis.labelpad = labelPad
    handles, labels = ax.get_legend_handles_labels()
    plt.legend(handles, labels, prop={'size':40},loc='best')
    ll,ul = ax.get_ylim()
    ax.set_ylim([ll,ul+5.0])
    figure_name = 'Temperatures_'+current_time+'.pdf'
    plt.tight_layout()
    plt.savefig(figure_name)
    plt.close()

#######################################################
