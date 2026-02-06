from . import freezing, calc_knownRp, calc_unknownRp, design_space, opt_Pch_Tsh, opt_Pch, opt_Tsh
from . import functions, constant, plot_styling

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

    elif sim_type == "Design Space Generator":
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
        elif sim["tool"] == "Design Space Generator":
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

        if sim["tool"] == "Design Space Generator":
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
    copied = inputs.copy()
    # If the inputs include large arrays of data, strip those out
    copied.pop("time_data", None)
    copied.pop("temp_data", None)
    # Then save
    try:
        yamlfile = open("lyopronto_input_" + timestamp + ".yaml", "w")
        yaml.dump(copied, yamlfile)
    finally:
        yamlfile.close()


def read_inputs(filename):
    "Read inputs from a YAML file."
    try:
        yamlfile = open(filename, "r")
        inputs = yaml.load(yamlfile)
        if "product_temp_filename" in inputs:
            print("Note: input specifies a product temperature data file."
                  + "This data should be loaded separately and added to the inputs dictionary"
                  + "as `time_data` and `temp_data`.")
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
    elif sim["tool"] == "Design Space Generator":
        _write_design_space_csv(output_data, inputs, filename)
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


def _write_design_space_csv(data, inputs, filename):
    ds_shelf, ds_pr, ds_eq_cap = data
    Tshelf = inputs["Tshelf"]
    Pchamber = inputs["Pchamber"]

    try:
        csvfile = open(filename, "w", newline="")
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
                        *ds_shelf[:, i, j],
                    ]
                )
            writer.writerow(
                ["Product Temperature = ", str(inputs["product"]["T_pr_crit"])]
            )
            writer.writerow(
                [Pchamber["setpt"][0] * constant.Torr_to_mTorr, *ds_pr[:, 0]]
            )
            writer.writerow(
                [Pchamber["setpt"][-1] * constant.Torr_to_mTorr, *ds_pr[:, 1]]
            )
            writer.writerow(["Equipment Capability"])
        for k in range(np.size(Pchamber["setpt"])):
            writer.writerow(
                [
                    Pchamber["setpt"][k] * constant.Torr_to_mTorr,
                    *ds_eq_cap[:, k],
                    ds_eq_cap[-1, k],
                    ds_eq_cap[-1, k],
                ]
            )
    finally:
        csvfile.close()


# TODO: implement this after redesigning design space output API
# def _write_design_space_yaml(data, inputs, filename):
#     ds_shelf, ds_pr, ds_eq_cap = data
#     # ds_shelf: 5 x nTsh x nPch
#     # ds_pr: 5 x 2
#     # ds_eq_cap: 3 x nPch

# def _read_design_space_yaml(filename):
#     """Read design space data from a YAML file."""


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
    elif inputs["sim"]["tool"] == "Design Space Generator":
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
    plot_styling.axis_style_temperature(ax)
    ax.legend(prop={"size": 40})
    plt.tight_layout()
    plt.savefig(f"lyo_Temperatures_{timestamp}.pdf")
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
    Tshelf = np.array(inputs["Tshelf"]["setpt"])
    Pchamber = np.array(inputs["Pchamber"]["setpt"])
    T_pr_crit = inputs["product"]["T_pr_crit"]
    figwidth = props["figwidth"]
    figheight = props["figheight"]
    lineWidth = props["linewidth"]
    color_list = ["b", "m", "g", "c", "r", "y", "k"]  # Line colors

    assert np.all(np.diff(Pchamber) >= 0), "Plotting assumes Pchamber set points are sorted."
    # Design space: sublimation flux vs pressures

    # Range in pressure space, min to max, Torr
    x = np.linspace(np.min(Pchamber), np.max(Pchamber), 1000)
    # Line 1: equipment capability sub flux, kg/hr/m^2
    # Indices (2,-1) is average sub flux at last Pch setpt,
    #         (2,0) is average sub flux at first Pch setpt
    # Slope: (delta sub flux)/(delta pressure)
    # Intercept: sub flux at first pressure
    y1 = (
        (ds_eq_cap[2, -1] - ds_eq_cap[2, 0])
        / (Pchamber[-1] - Pchamber[0])
    ) * (x - Pchamber[0]) + ds_eq_cap[2, 0]
    # Line 2: product temperature limited sub flux, kg/hr/m^2
    # Indices (3, -1) is minimum sub flux at last setpt,
    #          (3,0) is minimum sub flux at first setpt
    # Slope: (delta sub flux)/(delta pressure)
    # Intercept: sub flux at first pressure
    y2 = (
        (ds_pr[3, -1] - ds_pr[3, 0]) / (Pchamber[-1] - Pchamber[0])
    ) * (x - Pchamber[0]) + ds_pr[3, 0]
    # Convert to mTorr for plotting
    x = x * constant.Torr_to_mTorr
    # Get whichever sub flux is lower at each x value
    y = np.minimum(y1, y2)

    fig = plt.figure(0, figsize=(figwidth, figheight))
    ax = fig.add_subplot(1, 1, 1)
    plt.axes(ax)
    # Plot boundary lines
    # Equipment capability line

    ax.plot(
        # x: pressure in mTorr
        Pchamber * constant.Torr_to_mTorr,
        # y: equipment capability average sub flux, for all Pch
        ds_eq_cap[2, :],
        "-o",
        color="k",
        linewidth=lineWidth,
        label="Equipment Capability",
    )
    # Product temperature isotherm
    # Straight line: endpoints only enough
    ax.plot(
        # x: pressure in mTorr
        Pchamber[[0, -1]] * constant.Torr_to_mTorr,
        # y: product temperature limited minimum sub flux, for all first and last Pch
        ds_pr[3, :],
        "-o",
        color="r",
        linewidth=lineWidth,
        label=("T$_{pr}$ = " + str(inputs["product"]["T_pr_crit"]) + "°C"),
    )
    # Shelf temperature isotherms
    for i in range(Tshelf.size):
        ax.plot(
            # x: pressure in mTorr
            Pchamber * constant.Torr_to_mTorr,
            # y: 3 for maximum sub flux, i shelf temp , for all Pch
            ds_shelf[3, i, :],
            "--",
            color=str(color_list[i]),
            linewidth=lineWidth,
            label=("T$_{sh}$ = " + str(Tshelf[i]) + " C"),
        )
    plot_styling.axis_style_designspace(ax, ylabel="Sublimation Flux [kg/hr/m$^2$]")
    plt.legend(prop={"size": 40})
    ll, ul = ax.get_ylim()
    # Adjust axis limits
    # TODO: this logic seems questionable. What does it achieve?
    # If minimum of eq cap average flux > maximum of pr limited min flux
    if np.min(ds_eq_cap[2, :]) > np.max(ds_pr[3, :]):
        # Adjust upper limit to be 1/3 of first two eq cap average flux values
        ul = (ds_eq_cap[2, 0] + ds_eq_cap[2, 1]) / 3
    # If instead minimum of pr limited min flux > maximum of eq cap average flux
    elif np.min(ds_pr[3, :]) > np.max(ds_eq_cap[2, :]):
        # Adjust upper limit to be 1/4 of first two pr limited min flux values
        ul = (ds_pr[3, 0] + ds_pr[3, 1]) / 4
    ll = max(0, ll)
    # Fill the feasible region
    ax.fill_between(x, y, ll, color=[1.0, 1.0, 0.6])
    # ul = np.max(y) * 1.2 # Consider: focus on feasible region
    ax.set_ylim([ll, ul])
    plt.tight_layout()
    figure_name = f"lyo_DesignSpace_SublimationFlux_{timestamp}.pdf"
    plt.savefig(figure_name)
    plt.close()

    # Drying time vs pressures

    #### First, filled area above constraints
    # TODO: this is wrong: doesn't actually match constraints
    # Pressure range in Torr
    x = np.linspace(np.min(Pchamber), np.max(Pchamber), 1000) 
    # Line 1: drying time limited by equipment capability
    y1 = np.interp(x, Pchamber, ds_eq_cap[1, :])
    # Line 2: drying time limited by product temperature
    y2 = np.interp(x, Pchamber[[0, -1]], ds_pr[1, :])
    # get pointwise maximum of y1 and y2
    y = np.maximum(y1, y2)
    x = x * constant.Torr_to_mTorr  # convert pressure range to mTorr

    fig = plt.figure(0, figsize=(figwidth, figheight))
    ax = fig.add_subplot(1, 1, 1)
    plt.axes(ax)
    # Drying time boundary for eq cap
    ax.plot(
        Pchamber * constant.Torr_to_mTorr,
        ds_eq_cap[1, :],
        "-o",
        color="k",
        linewidth=lineWidth,
        label="Equipment Capability",
    )
    # Drying time boundary for product temperature
    ax.plot(
        Pchamber[[0, -1]] * constant.Torr_to_mTorr,
        ds_pr[1, :],
        "-o",
        color="r",
        linewidth=lineWidth,
        label=("T$_{pr}$ = " + str(inputs["product"]["T_pr_crit"]) + " C"),
    )
    # Shelf temperature isotherms
    for i in range(Tshelf.size):
        ax.plot(
            Pchamber * constant.Torr_to_mTorr,
            ds_shelf[1, i, :],
            "--",
            color=str(color_list[i]),
            linewidth=lineWidth,
            label=("T$_{sh}$ = " + str(Tshelf[i]) + " C"),
        )
    plot_styling.axis_style_designspace(ax, ylabel="Drying Time [hr]")
    plt.legend(prop={"size": 40})
    ll, ul = ax.get_ylim()
    ll = max(0, ll)
    ax.set_ylim([ll, ul])
    ax.fill_between(x, y, ul, color=[1.0, 1.0, 0.6])
    figure_name = f"lyo_DesignSpace_DryingTime_{timestamp}.pdf"
    plt.tight_layout()
    plt.savefig(figure_name)
    plt.close()

    # Product temperature vs pressures

    x = np.linspace(
        np.min(Pchamber), np.max(Pchamber), 1000
    )  # pressure range in Torr
    # Curve 1: equipment capability limited product temperature
    y1 = np.interp(x, Pchamber, ds_eq_cap[0, :])  # equipment capability limiting product temperature in degC
    # Curve 2: horizontal line at product temperature limit
    y2 = np.full_like(y1, T_pr_crit)  # horizontal line at product temperature limit
    y = np.minimum(y1, y2)

    x = x * constant.Torr_to_mTorr  # Convert pressure range to mTorr
    # Pointwise minimum of y1 and y2

    fig = plt.figure(0, figsize=(figwidth, figheight))
    ax = fig.add_subplot(1, 1, 1)
    plt.axes(ax)
    ax.plot(
        Pchamber * constant.Torr_to_mTorr,
        ds_eq_cap[0, :],
        "-o",
        color="k",
        linewidth=lineWidth,
        label="Equipment Capability",
    )
    ax.plot(
        Pchamber[[0, -1]] * constant.Torr_to_mTorr,
        ds_pr[0, :],
        "-o",
        color="r",
        linewidth=lineWidth,
        label=("T$_{pr}$ = " + str(inputs["product"]["T_pr_crit"]) + " C"),
    )
    for i in range(np.size(Tshelf)):
        ax.plot(
            Pchamber * constant.Torr_to_mTorr,
            ds_shelf[0, i, :],
            "--",
            color=str(color_list[i]),
            linewidth=lineWidth,
            label=("T$_{sh}$ = " + str(Tshelf[i]) + " C"),
        )
    plot_styling.axis_style_designspace(ax, ylabel="Product Temperature [°C]")
    plt.legend(prop={"size": 40})
    ll, ul = ax.get_ylim()
    # TODO: Possibly tinker with ll and ul
    ax.set_ylim([ll, ul])
    ax.fill_between(x, y, ll, color=[1.0, 1.0, 0.6])
    figure_name = f"lyo_DesignSpace_ProductTemperature_{timestamp}.pdf"
    plt.tight_layout()
    plt.savefig(figure_name)
    plt.close()