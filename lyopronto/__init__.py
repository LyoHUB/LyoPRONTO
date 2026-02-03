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

# ----------------------
# Import submodules

from . import constant
from . import freezing
from . import calc_knownRp
from . import calc_unknownRp
from . import design_space
from . import opt_Pch_Tsh
from . import opt_Pch
from . import opt_Tsh
from . import functions
from . import plot_styling

# ----------------------
# Provide functionality for running LyoPRONTO as a module
from warnings import warn
import numpy as np
import csv
import matplotlib.pyplot as plt
from matplotlib import rc as matplotlibrc
from scipy.optimize import curve_fit, brentq
from ruamel.yaml import YAML

yaml = YAML()


def execute_simulation(inputs):
    """
    Run the selected simulation tool with the provided inputs.
    Returns output data based on the chosen simulation mode.
    """
    sim_type = inputs["sim"]["tool"]
    output_data = None

    if sim_type == "Freezing Calculator":
        output_data = freezing.freeze(
            inputs["vial"],
            inputs["product"],
            inputs["h_freezing"],
            inputs["Tshelf"],
            inputs["dt"],
        )

    elif sim_type == "Primary Drying Calculator":
        if inputs["sim"]["Kv_known"] and inputs["sim"]["Rp_known"]:
            output_data = calc_knownRp.dry(
                inputs["vial"],
                inputs["product"],
                inputs["ht"],
                inputs["Pchamber"],
                inputs["Tshelf"],
                inputs["dt"],
            )
        elif not inputs["sim"]["Kv_known"] and inputs["sim"]["Rp_known"]:
            output_data = _optimize_kv_parameter(inputs)
        elif inputs["sim"]["Kv_known"] and not inputs["sim"]["Rp_known"]:
            output_data = _optimize_rp_parameter(inputs)
        else:
            raise ValueError(
                "With the current implementation, either Kv or Rp must be specified."
            )

    elif sim_type == "Design-Space-Generator":
        output_data = design_space.dry(
            inputs["vial"],
            inputs["product"],
            inputs["ht"],
            inputs["Pchamber"],
            inputs["Tshelf"],
            inputs["dt"],
            inputs["eq_cap"],
            inputs["nVial"],
        )

    elif sim_type == "Optimizer":
        output_data = _run_optimizer(inputs)

    return output_data


def _optimize_kv_parameter(inputs):
    """Helper to determine Kv based on experimental drying time."""
    Kv_range = inputs.get("Kv_range", (1e-6, 1e-2))

    def obj(Kc):
        output = calc_knownRp.dry(
            inputs["vial"],
            inputs["product"],
            {"KC": Kc, "KP": 0.0, "KD": 0.0},
            inputs["Pchamber"],
            inputs["Tshelf"],
            inputs["dt"],
        )
        simulated_time = output[-1, 0]
        return simulated_time - inputs["t_dry_exp"]

    if obj(Kv_range[0]) * obj(Kv_range[-1]) > 0:
        warn(
            "Given Kv bounds do not bracket the most likely value. Choosing either min or max."
        )
        if abs(obj(Kv_range[0])) < abs(obj(Kv_range[-1])):
            best_Kv = Kv_range[0]
        else:
            best_Kv = Kv_range[-1]
    else:
        best_Kv = brentq(obj, Kv_range[0], Kv_range[-1])

    deviation = obj(best_Kv)
    output = calc_knownRp.dry(
        inputs["vial"],
        inputs["product"],
        {"KC": best_Kv, "KP": 0.0, "KD": 0.0},
        inputs["Pchamber"],
        inputs["Tshelf"],
        inputs["dt"],
    )

    print(f"Optimal Kv: {best_Kv}, Deviation: {deviation}%")
    return output


def _optimize_rp_parameter(inputs):
    """Helper to determine Rp from experimental product temperature."""

    output, product_res = calc_unknownRp.dry(
        inputs["vial"],
        inputs["product"],
        inputs["ht"],
        inputs["Pchamber"],
        inputs["Tshelf"],
        inputs["time_data"],
        inputs["temp_data"],
    )

    params, _ = curve_fit(
        functions.Rp_FUN, product_res[:, 1], product_res[:, 2], p0=[1.0, 0.0, 0.0]
    )

    print(f"R0: {params[0]}, A1: {params[1]}, A2: {params[2]}")
    return output


def _run_optimizer(inputs):
    """Helper to run optimization with variable parameters."""
    args = (
        inputs["vial"],
        inputs["product"],
        inputs["ht"],
        inputs["Pchamber"],
        inputs["Tshelf"],
        inputs["dt"],
        inputs["eq_cap"],
        inputs["nVial"],
    )
    if inputs["sim"]["Variable_Pch"] and inputs["sim"]["Variable_Tsh"]:
        return opt_Pch_Tsh.dry(*args)
    elif inputs["sim"]["Variable_Pch"]:
        return opt_Pch.dry(*args)
    elif inputs["sim"]["Variable_Tsh"]:
        return opt_Tsh.dry(*args)


def save_inputs_legacy(inputs, timestamp):
    """
    Save inputs to a CSV file with timestamped filename.
    """
    filename = f"lyopronto_input_{timestamp}.csv"
    sim = inputs["sim"]
    vial = inputs["vial"]
    product = inputs["product"]

    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(["Simulation Tool", sim["tool"]])
        writer.writerow(["Kv Known", sim["Kv_known"]])
        writer.writerow(["Rp Known", sim["Rp_known"]])
        writer.writerow(["Variable Chamber Pressure", sim["Variable_Pch"]])
        writer.writerow(["Variable Shelf Temperature", sim["Variable_Tsh"]])
        writer.writerow([])

        writer.writerow(["Vial Cross-Section [cm²]", vial["Av"]])
        writer.writerow(["Product Area [cm²]", vial["Ap"]])
        writer.writerow(["Fill Volume [mL]", vial["Vfill"]])
        writer.writerow([])

        writer.writerow(["Fractional solute concentration:", product["cSolid"]])
        if sim["tool"] == "Freezing Calculator":
            writer.writerow(["Intial product temperature [C]:", product["Tpr0"]])
            writer.writerow(["Freezing temperature [C]:", product["Tf"]])
            writer.writerow(["Nucleation temperature [C]:", product["Tn"]])
        elif not (
            sim["tool"] == "Primary Drying Calculator" and sim["Rp_known"] == "N"
        ):
            writer.writerow(["R0 [cm^2-hr-Torr/g]:", product["R0"]])
            writer.writerow(["A1 [cm-hr-Torr/g]:", product["A1"]])
            writer.writerow(["A2 [1/cm]:", product["A2"]])
        if not (
            sim["tool"] == "Freezing Calculator"
            and sim["tool"] == "Primary Drying Calculator"
        ):
            writer.writerow(["Critical product temperature [C]:", product["T_pr_crit"]])

        if sim["tool"] == "Freezing Calculator":
            writer.writerow(["h_freezing [W/m^2/K]:", inputs["h_freezing"]])
        elif sim["Kv_known"]:
            writer.writerow(["KC [cal/s/K/cm^2]:", inputs["ht"]["KC"]])
            writer.writerow(["KP [cal/s/K/cm^2/Torr]:", inputs["ht"]["KP"]])
            writer.writerow(["KD [1/Torr]:", inputs["ht"]["KD"]])
        elif not sim["Kv_known"]:
            writer.writerow(["Kv range [cal/s/K/cm^2]:", inputs["Kv_range"][:]])
            writer.writerow(["Experimental drying time [hr]:", inputs["t_dry_exp"]])

        if sim["tool"] == "Freezing Calculator":
            0
        elif sim["tool"] == "Design-Space-Generator":
            writer.writerow(
                ["Chamber pressure set points [Torr]:", inputs["Pchamber"]["setpt"][:]]
            )
        elif not (sim["tool"] == "Optimizer" and sim["Variable_Pch"] == "Y"):
            for i in range(len(inputs["Pchamber"]["setpt"])):
                writer.writerow(
                    [
                        "Chamber pressure setpoint [Torr]:",
                        inputs["Pchamber"]["setpt"][i],
                        "Duration [min]:",
                        inputs["Pchamber"]["dt_setpt"][i],
                    ]
                )
            writer.writerow(
                [
                    "Chamber pressure ramping rate [Torr/min]:",
                    inputs["Pchamber"]["ramp_rate"],
                ]
            )
        else:
            writer.writerow(
                ["Minimum chamber pressure [Torr]:", inputs["Pchamber"]["min"]]
            )
            writer.writerow(
                ["Maximum chamber pressure [Torr]:", inputs["Pchamber"]["max"]]
            )
        writer.writerow([""])

        if sim["tool"] == "Design-Space-Generator":
            writer.writerow(["Intial shelf temperature [C]:", inputs["Tshelf"]["init"]])
            writer.writerow(
                ["Shelf temperature set points [C]:", inputs["Tshelf"]["setpt"][:]]
            )
            writer.writerow(
                [
                    "Shelf temperature ramping rate [C/min]:",
                    inputs["Tshelf"]["ramp_rate"],
                ]
            )
        elif not (sim["tool"] == "Optimizer" and sim["Variable_Tsh"] == "Y"):
            for i in range(len(inputs["Tshelf"]["setpt"])):
                writer.writerow(
                    [
                        "Shelf temperature setpoint [C]:",
                        inputs["Tshelf"]["setpt"][i],
                        "Duration [min]:",
                        inputs["Tshelf"]["dt_setpt"][i],
                    ]
                )
            writer.writerow(
                [
                    "Shelf temperature ramping rate [C/min]:",
                    inputs["Tshelf"]["ramp_rate"],
                ]
            )
        else:
            writer.writerow(["Minimum shelf temperature [C]:", inputs["Tshelf"]["min"]])
            writer.writerow(["Maximum shelf temperature [C]:", inputs["Tshelf"]["max"]])

        writer.writerow(["Time Step [hr]", inputs["dt"]])
        writer.writerow(["Equipment Parameter a [kg/hr]", inputs["eq_cap"]["a"]])
        writer.writerow(["Equipment Parameter b [kg/hr/Torr]", inputs["eq_cap"]["b"]])
        writer.writerow(["Number of Vials", inputs["nVial"]])


def save_inputs(inputs, timestamp):
    "Save inputs to a YAML file with timestamped filename."
    try:
        yamlfile = open("lyopronto_input_" + timestamp + ".yaml", "w")
        yaml.dump(inputs, yamlfile)
    finally:
        yamlfile.close()


def read_inputs(filename):
    "Read inputs from a YAML file."
    try:
        yamlfile = open(filename, "r")
        inputs = yaml.load(yamlfile)
        return inputs
    finally:
        yamlfile.close()


def save_csv(output_data, inputs, timestamp):
    """
    Export simulation results to CSV file with appropriate formatting.
    """
    filename = f"lyopronto_output_{timestamp}.csv"

    sim = inputs["sim"]

    if sim["tool"] == "Freezing Calculator":
        assert output_data.shape[1] == 3
        header = "Time [hr], Shelf Temp [°C], Product Temp [°C]"
        np.savetxt(filename, output_data, delimiter=", ", header=header)
    elif sim["tool"] == "Design-Space-Generator":
        assert output_data.shape[1] == 6
        header = "Chamber Pressure [mTorr], Max Product Temperature [°C], Drying Time [hr], Avg Sublimation Flux [kg/hr/m²], Max/Min Sublimation Flux [kg/hr/m²], Final Sublimation Flux [kg/hr/m²]"
        ds_shelf, ds_pr, ds_eq_cap = output_data
        Tshelf = inputs["Tshelf"]
        Pchamber = inputs["Pchamber"]

        # TODO: This CSV has a weird format. Consider revising, or at least redoing as a few tables.
        try:
            csvfile = open(filename, "w")
            writer = csv.writer(csvfile)
            writer.writerow(
                [
                    "Chamber Pressure [mTorr]",
                    "Maximum Product Temperature [C]",
                    "Drying Time [hr]",
                    "Average Sublimation Flux [kg/hr/m^2]",
                    "Maximum/Minimum Sublimation Flux [kg/hr/m^2]",
                    "Final Sublimation Flux [kg/hr/m^2]",
                ]
            )
            for i in range(np.size(Tshelf["setpt"])):
                writer.writerow(["Shelf Temperature = ", str(Tshelf["setpt"][i])])
                for j in range(np.size(Pchamber["setpt"])):
                    writer.writerow(
                        [
                            Pchamber["setpt"][j] * constant.Torr_to_mTorr,
                            ds_shelf[0, i, j],
                            ds_shelf[1, i, j],
                            ds_shelf[2, i, j],
                            ds_shelf[3, i, j],
                            ds_shelf[4, i, j],
                        ]
                    )
                writer.writerow(
                    ["Product Temperature = ", str(inputs["product"]["T_pr_crit"])]
                )
                writer.writerow(
                    [
                        Pchamber["setpt"][0] * constant.Torr_to_mTorr,
                        ds_pr[0, 0],
                        ds_pr[1, 0],
                        ds_pr[2, 0],
                        ds_pr[3, 0],
                        ds_pr[4, 0],
                    ]
                )
                writer.writerow(
                    [
                        Pchamber["setpt"][-1] * constant.Torr_to_mTorr,
                        ds_pr[0, 1],
                        ds_pr[1, 1],
                        ds_pr[2, 1],
                        ds_pr[3, 1],
                        ds_pr[4, 1],
                    ]
                )
                writer.writerow(["Equipment Capability"])
            for k in range(np.size(Pchamber["setpt"])):
                writer.writerow(
                    [
                        Pchamber["setpt"][k] * constant.Torr_to_mTorr,
                        ds_eq_cap[0, k],
                        ds_eq_cap[1, k],
                        ds_eq_cap[2, k],
                        ds_eq_cap[2, k],
                        ds_eq_cap[2, k],
                    ]
                )
        finally:
            csvfile.close()

    else:
        header = ",".join(
            [
                "Time [hr]",
                "Sublimation Front Temp [°C]",
                "Vial Bottom Temperature [°C]",
                "Shelf Temp [°C]",
                "Chamber Pressure [mTorr]",
                "Sublimation Flux [kg/hr/m²]",
                "Percent Dried",
            ]
        )
        np.savetxt(filename, output_data, delimiter=", ", header=header)


# TODO: add more kwargs, proper documentation, possibly refactor to make
# each subfunction part of the API
def generate_visualizations(output_data, inputs, timestamp):
    """
    Create and save publication-quality plots based on simulation results.
    """
    # TODO: move these to kwargs for the function
    figure_props = {
        "figwidth": 30,
        "figheight": 20,
        "linewidth": 5,
        "marker_size": 20,
    }
    matplotlibrc("text.latex", preamble=r"\usepackage{color}")
    matplotlibrc("text", usetex=False)
    plt.rcParams["font.family"] = "Arial"

    if inputs["sim"]["tool"] == "Freezing Calculator":
        _plot_freezing_results(output_data, figure_props, timestamp)
    elif inputs["sim"]["tool"] in ["Primary Drying Calculator", "Optimizer"]:
        _plot_drying_results(output_data, figure_props, timestamp)
    elif inputs["sim"]["tool"] == "Design-Space-Generator":
        _plot_design_space(output_data, inputs, figure_props, timestamp)


def _plot_freezing_results(data, props, timestamp):
    """Generate freezing process visualization."""
    fig, ax = plt.subplots(figsize=(props["figwidth"], props["figheight"]))
    ax.plot(
        data[:, 0],
        data[:, 1],
        "-k",
        linewidth=props["linewidth"],
        label="Shelf Temperature",
    )
    ax.plot(
        data[:, 0],
        data[:, 2],
        "-b",
        linewidth=props["linewidth"],
        label="Product Temperature",
    )
    ax.set_xlabel("Time [hr]", fontsize=props["axis_fontsize"], fontweight="bold")
    ax.set_ylabel(
        "Temperature [°C]", fontsize=props["axis_fontsize"], fontweight="bold"
    )
    ax.legend(prop={"size": 40})
    plt.tight_layout()
    plt.savefig(f"Temperatures_{timestamp}.pdf")
    plt.close()


def _plot_drying_results(data, props, timestamp):
    """Generate primary drying process visualizations."""

    figwidth = props["figwidth"]
    figheight = props["figheight"]
    linewidth = props["linewidth"]
    marker_size = props["marker_size"]
    # Pressure and sublimation flux
    fig = plt.figure(0, figsize=(figwidth, figheight))
    ax1 = fig.add_subplot(1, 1, 1)
    ax2 = ax1.twinx()
    ax1.plot(
        data[:, 0],
        data[:, 4],
        "-o",
        color="b",
        markevery=5,
        linewidth=linewidth,
        markersize=marker_size,
        label="Chamber Pressure",
    )
    ax2.plot(
        data[:, 0],
        data[:, 5],
        "-",
        color=[0, 0.7, 0.3],
        linewidth=linewidth,
        label="Sublimation Flux",
    )

    plot_styling.axis_style_pressure(ax1)
    plot_styling.axis_style_subflux(ax2)

    plt.tight_layout()
    plt.savefig(f"lyo_Pressure_SublimationFlux_{timestamp}.pdf")
    plt.close()

    # Drying progress
    fig = plt.figure(0, figsize=(figwidth, figheight))
    ax = fig.add_subplot(1, 1, 1)
    plot_styling.axis_style_percdried(ax)
    ax.plot(data[:, 0], data[:, -1], "-k", linewidth=linewidth, label="Percent Dried")
    plt.tight_layout()
    plt.savefig(f"lyo_DryingProgress_{timestamp}.pdf")
    plt.close()

    # Temperatures
    fig = plt.figure(0, figsize=(figwidth, figheight))
    ax = fig.add_subplot(1, 1, 1)
    plot_styling.axis_style_temperature(ax)
    ax.plot(
        data[:, 0],
        data[:, 1],
        "-b",
        linewidth=linewidth,
        label="Sublimation Front Temperature",
    )
    ax.plot(
        data[:, 0],
        data[:, 2],
        "-r",
        linewidth=linewidth,
        label="Maximum Product Temperature",
    )
    ax.plot(
        data[:, 0],
        data[:, 3],
        "-o",
        color="k",
        markevery=5,
        linewidth=linewidth,
        markersize=marker_size,
        label="Shelf Temperature",
    )
    plt.legend(fontsize=40, loc="best")
    ll, ul = ax.get_ylim()
    ax.set_ylim([ll, ul + 5.0])
    plt.tight_layout()
    plt.savefig(f"lyo_Temperatures_{timestamp}.pdf")
    plt.close()


# TODO: work through this logic and see how much can be refactored out
def _plot_design_space(data, inputs, props, timestamp):
    """Generate design space boundary visualization."""
    # Implementation for design space plotting

    ds_shelf, ds_pr, ds_eq_cap = data
    Tshelf = inputs["Tshelf"]
    Pchamber = inputs["Pchamber"]
    figwidth = props["figwidth"]
    figheight = props["figheight"]
    lineWidth = props["linewidth"]
    color_list = ["b", "m", "g", "c", "r", "y", "k"]  # Line colors

    # Design space: sublimation flux vs pressures

    x = np.linspace(
        np.min(Pchamber["setpt"]), np.max(Pchamber["setpt"]), 1000
    )  # pressure range in Torr
    y1 = (
        (ds_eq_cap[2, -1] - ds_eq_cap[2, 0])
        / (Pchamber["setpt"][-1] - Pchamber["setpt"][0])
    ) * (x - Pchamber["setpt"][0]) + ds_eq_cap[
        2, 0
    ]  # equipment capability sublimation flux in kg/hr/m^2
    y2 = (
        (ds_pr[3, -1] - ds_pr[3, 0]) / (Pchamber["setpt"][-1] - Pchamber["setpt"][0])
    ) * (x - Pchamber["setpt"][0]) + ds_pr[
        3, 0
    ]  # product temperature limited sublimation flux in kg/hr/m^2
    x = x * constant.Torr_to_mTorr  # pressure range in mTorr
    i = np.where(y1 >= y2)[0][0]
    y = np.append(y1[:i], y2[i:])
    x1 = np.append(x, x[::-1])

    fig = plt.figure(0, figsize=(figwidth, figheight))
    ax = fig.add_subplot(1, 1, 1)
    plt.axes(ax)
    ax.plot(
        [P * constant.Torr_to_mTorr for P in Pchamber["setpt"]],
        ds_eq_cap[2, :],
        "-o",
        color="k",
        linewidth=lineWidth,
        label="Equipment Capability",
    )
    ax.plot(
        [
            Pchamber["setpt"][0] * constant.Torr_to_mTorr,
            Pchamber["setpt"][-1] * constant.Torr_to_mTorr,
        ],
        ds_pr[3, :],
        "-o",
        color="r",
        linewidth=lineWidth,
        label=("T$_{pr}$ = " + str(inputs["product"]["T_pr_crit"]) + "°C"),
    )
    for i in range(np.size(Tshelf["setpt"])):
        ax.plot(
            [P * constant.Torr_to_mTorr for P in Pchamber["setpt"]],
            ds_shelf[3, i, :],
            "--",
            color=str(color_list[i]),
            linewidth=lineWidth,
            label=("T$_{sh}$ = " + str(Tshelf["setpt"][i]) + " C"),
        )
    plot_styling.axis_style_designspace(ax)
    plt.legend(prop={"size": 40})
    ll, ul = ax.get_ylim()
    if np.min(ds_eq_cap[2, :]) > np.max(ds_pr[3, :]):
        ul = (ds_eq_cap[2, 0] + ds_eq_cap[2, 1]) / 3
    elif np.min(ds_pr[3, :]) > np.max(ds_eq_cap[2, :]):
        ul = (ds_pr[3, 0] + ds_pr[3, 1]) / 4
    ax.set_ylim([ll, ul])
    x2 = np.append(y, ll * x / x)
    ax.fill(x1, x2, color=[1.0, 1.0, 0.6])
    plt.tight_layout()
    figure_name = f"lyo_DesignSpace_SublimationFlux_{timestamp}.pdf"
    plt.savefig(figure_name)
    plt.close()

    # Drying progress vs pressures

    x = np.linspace(
        np.min(Pchamber["setpt"]), np.max(Pchamber["setpt"]), 1000
    )  # pressure range in Torr
    y1 = (
        (ds_eq_cap[1, -1] - ds_eq_cap[1, 0])
        / (Pchamber["setpt"][-1] - Pchamber["setpt"][0])
    ) * (x - Pchamber["setpt"][0]) + ds_eq_cap[
        1, 0
    ]  # equipment capability drying time in hr
    y2 = (
        (ds_pr[1, -1] - ds_pr[1, 0]) / (Pchamber["setpt"][-1] - Pchamber["setpt"][0])
    ) * (x - Pchamber["setpt"][0]) + ds_pr[
        1, 0
    ]  # product temperature limited drying time in hr
    x = x * constant.Torr_to_mTorr  # pressure range in mTorr
    i = np.where(y1 < y2)[0][0]
    y = np.append(y1[:i], y2[i:])
    x1 = np.append(x, x[::-1])

    fig = plt.figure(0, figsize=(figwidth, figheight))
    ax = fig.add_subplot(1, 1, 1)
    plt.axes(ax)
    ax.plot(
        [P * constant.Torr_to_mTorr for P in Pchamber["setpt"]],
        ds_eq_cap[1, :],
        "-o",
        color="k",
        linewidth=lineWidth,
        label="Equipment Capability",
    )
    ax.plot(
        [
            Pchamber["setpt"][0] * constant.Torr_to_mTorr,
            Pchamber["setpt"][-1] * constant.Torr_to_mTorr,
        ],
        ds_pr[1, :],
        "-o",
        color="r",
        linewidth=lineWidth,
        label=("T$_{pr}$ = " + str(inputs["product"]["T_pr_crit"]) + " C"),
    )
    for i in range(np.size(Tshelf["setpt"])):
        ax.plot(
            [P * constant.Torr_to_mTorr for P in Pchamber["setpt"]],
            ds_shelf[1, i, :],
            "--",
            color=str(color_list[i]),
            linewidth=lineWidth,
            label=("T$_{sh}$ = " + str(Tshelf["setpt"][i]) + " C"),
        )
    plot_styling.axis_style_ds_percdried(ax)
    plt.legend(prop={"size": 40})
    # The following seems incorrect: done for all three y axes, regardless of units
    ll, ul = ax.get_ylim()
    if np.min(ds_eq_cap[2, :]) > np.max(ds_pr[3, :]):
        ul = (ds_eq_cap[2, 0] + ds_eq_cap[2, 1]) / 3
    elif np.min(ds_pr[3, :]) > np.max(ds_eq_cap[2, :]):
        ul = (ds_pr[3, 0] + ds_pr[3, 1]) / 4
    ax.set_ylim([ll, ul])
    x2 = np.append(y, ul * x / x)
    ax.fill(x1, x2, color=[1.0, 1.0, 0.6])
    figure_name = f"lyo_DesignSpace_DryingTime_{timestamp}.pdf"
    plt.tight_layout()
    plt.savefig(figure_name)
    plt.close()

    # Product temperature vs pressures

    x = np.linspace(
        np.min(Pchamber["setpt"]), np.max(Pchamber["setpt"]), 1000
    )  # pressure range in Torr
    y1 = (
        (ds_eq_cap[0, -1] - ds_eq_cap[0, 0])
        / (Pchamber["setpt"][-1] - Pchamber["setpt"][0])
    ) * (x - Pchamber["setpt"][0]) + ds_eq_cap[
        0, 0
    ]  # equipment capability limiting product temperature in degC
    y2 = (
        (ds_pr[0, -1] - ds_pr[0, 0]) / (Pchamber["setpt"][-1] - Pchamber["setpt"][0])
    ) * (x - Pchamber["setpt"][0]) + ds_pr[0, 0]  # product temperature limit in deg C
    x = x * constant.Torr_to_mTorr  # pressure range in mTorr
    i = np.where(y1 >= y2)[0][0]
    y = np.append(y1[:i], y2[i:])
    x1 = np.append(x, x[::-1])

    fig = plt.figure(0, figsize=(figwidth, figheight))
    ax = fig.add_subplot(1, 1, 1)
    plt.axes(ax)
    ax.plot(
        [P * constant.Torr_to_mTorr for P in Pchamber["setpt"]],
        ds_eq_cap[0, :],
        "-o",
        color="k",
        linewidth=lineWidth,
        label="Equipment Capability",
    )
    ax.plot(
        [
            Pchamber["setpt"][0] * constant.Torr_to_mTorr,
            Pchamber["setpt"][-1] * constant.Torr_to_mTorr,
        ],
        ds_pr[0, :],
        "-o",
        color="r",
        linewidth=lineWidth,
        label=("T$_{pr}$ = " + str(inputs["product"]["T_pr_crit"]) + " C"),
    )
    for i in range(np.size(Tshelf["setpt"])):
        ax.plot(
            [P * constant.Torr_to_mTorr for P in Pchamber["setpt"]],
            ds_shelf[0, i, :],
            "--",
            color=str(color_list[i]),
            linewidth=lineWidth,
            label=("T$_{sh}$ = " + str(Tshelf["setpt"][i]) + " C"),
        )
    plot_styling.axis_style_ds_temperature(ax)
    plt.legend(prop={"size": 40})
    # The following seems incorrect: done for all three y axes, regardless of units
    ll, ul = ax.get_ylim()
    if np.min(ds_eq_cap[2, :]) > np.max(ds_pr[3, :]):
        ul = (ds_eq_cap[2, 0] + ds_eq_cap[2, 1]) / 3
    elif np.min(ds_pr[3, :]) > np.max(ds_eq_cap[2, :]):
        ul = (ds_pr[3, 0] + ds_pr[3, 1]) / 4
    ax.set_ylim([ll, ul])
    x2 = np.append(y, ll * x / x)
    ax.fill(x1, x2, color=[1.0, 1.0, 0.6])
    figure_name = f"lyo_DesignSpace_ProductTemperature_{timestamp}.pdf"
    plt.tight_layout()
    plt.savefig(figure_name)
    plt.close()
