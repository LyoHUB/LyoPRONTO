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
def axis_tick_styling(
        ax,
        color = 'k',
        gcafontSize = 60,
        majorTickWidth = 5,
        minorTickWidth = 3,
        majorTickLength = 30,
        minorTickLength = 20,
        labelPad = 30,
    ):
    """ Function to set styling for matplotlib axes ticks """
    ax.minorticks_on()
    ax.tick_params(axis='both',direction='in',pad=labelPad,width=majorTickWidth,length=majorTickLength,bottom=1,top=0)
    ax.tick_params(axis='both',which='minor',direction='in',width=minorTickWidth,length=minorTickLength)
    ax.tick_params(axis='both',labelsize=gcafontSize,labelfontfamily='Arial')
    ax.tick_params(axis='y',which='both',color=color, labelcolor=color)
    for tick in [*ax.get_xticklabels(), *ax.get_yticklabels()]:
        tick.set_fontweight('bold')
    ax.xaxis.labelpad = labelPad
    ax.yaxis.labelpad = labelPad

def axis_style_pressure(
        ax,
        gcafontSize = 60,
        labelPad = 30,
        color = 'b',
        majorTickWidth = 5,
        minorTickWidth = 3,
        majorTickLength = 30,
        minorTickLength = 20,
    ):  
    """ Function to set styling for axes, with time on x and pressure on y """

    ax.set_xlabel("Time [hr]",fontsize=gcafontSize,fontweight='bold',fontname="Arial")
    ax.set_ylabel("Chamber Pressure [mTorr]",fontsize=gcafontSize,color=color,fontweight='bold',fontname="Arial")

    axis_tick_styling(
        ax,
        color = color,
        gcafontSize = gcafontSize,
        majorTickWidth = majorTickWidth,
        minorTickWidth = minorTickWidth,
        majorTickLength = majorTickLength,
        minorTickLength = minorTickLength,
        labelPad = labelPad,
    )
    
def axis_style_subflux(
        ax,
        gcafontSize = 60,
        labelPad = 30,
        color = [0, 0.7, 0.3],
        majorTickWidth = 5,
        minorTickWidth = 3,
        majorTickLength = 30,
        minorTickLength = 20,
    ):  
    """ Function to set styling for axes, with time on x and sublimation flux on y """

    ax.set_xlabel("Time [hr]",fontsize=gcafontSize,fontweight='bold',fontname="Arial")
    ax.set_ylabel("Sublimation Flux [kg/hr/m$^2$]",fontsize=gcafontSize,color=color,fontweight='bold',fontname="Arial")

    axis_tick_styling(
        ax,
        color = color,
        gcafontSize = gcafontSize,
        majorTickWidth = majorTickWidth,
        minorTickWidth = minorTickWidth,
        majorTickLength = majorTickLength,
        minorTickLength = minorTickLength,
        labelPad = labelPad,
    )

def axis_style_percdried(
        ax,
        gcafontSize = 60,
        labelPad = 30,
        color = 'k',
        majorTickWidth = 5,
        minorTickWidth = 3,
        majorTickLength = 30,
        minorTickLength = 20,
    ):  
    """ Function to set styling for axes, with time on x and percent dried on y """

    ax.set_xlabel("Time [hr]",fontsize=gcafontSize,fontweight='bold',fontname="Arial")
    ax.set_ylabel("Percent Dried",fontsize=gcafontSize,color=color,fontweight='bold',fontname="Arial")

    axis_tick_styling(
        ax,
        color = color,
        gcafontSize = gcafontSize,
        majorTickWidth = majorTickWidth,
        minorTickWidth = minorTickWidth,
        majorTickLength = majorTickLength,
        minorTickLength = minorTickLength,
        labelPad = labelPad,
    )

def axis_style_temperature(
        ax,
        gcafontSize = 60,
        labelPad = 30,
        color = 'k',
        majorTickWidth = 5,
        minorTickWidth = 3,
        majorTickLength = 30,
        minorTickLength = 20,
    ):  
    """ Function to set styling for axes, with time on x and temperature on y """

    ax.set_xlabel("Time [hr]",fontsize=gcafontSize,fontweight='bold',fontname="Arial")
    ax.set_ylabel("Product Temperature [°C]",fontsize=gcafontSize,color=color,fontweight='bold',fontname="Arial")

    axis_tick_styling(
        ax,
        color = color,
        gcafontSize = gcafontSize,
        majorTickWidth = majorTickWidth,
        minorTickWidth = minorTickWidth,
        majorTickLength = majorTickLength,
        minorTickLength = minorTickLength,
        labelPad = labelPad,
    )
    
def axis_style_rp(
        ax,
        gcafontSize = 60,
        labelPad = 30,
        color = 'k',
        majorTickWidth = 5,
        minorTickWidth = 3,
        majorTickLength = 30,
        minorTickLength = 20,
    ):  
    """ Function to set styling for axes, with dry layer height on x and product resistance on y """

    ax.set_xlabel("Dry Layer Height [cm]",fontsize=gcafontSize,fontweight='bold',fontname="Arial")
    ax.set_ylabel('Product Resistance [cm$^2$ hr Torr/g]',fontsize=gcafontSize,color=color,fontweight='bold',fontname="Arial")

    axis_tick_styling(
        ax,
        color = color,
        gcafontSize = gcafontSize,
        majorTickWidth = majorTickWidth,
        minorTickWidth = minorTickWidth,
        majorTickLength = majorTickLength,
        minorTickLength = minorTickLength,
        labelPad = labelPad,
    )


