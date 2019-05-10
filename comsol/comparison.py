import pybamm
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# C_rates dict
C_rates = {"01": 0.1, "05": 0.5, "1": 1, "2": 2, "3": 3}

# load model and geometry
model = pybamm.lithium_ion.DFN()
geometry = model.default_geometry

# load parameters and process model and geometry
param = model.default_parameter_values
param.process_model(model)
param.process_geometry(geometry)

# create mesh
var = pybamm.standard_spatial_vars
var_pts = {var.x_n: 11, var.x_s: 5, var.x_p: 11, var.r_n: 11, var.r_p: 11}
mesh = pybamm.Mesh(geometry, model.default_submesh_types, var_pts)

# discretise model
disc = pybamm.Discretisation(mesh, model.default_spatial_methods)
disc.process_model(model)

# loop over C_rates dict to create plot
plt.figure(figsize=(15, 8))
ax = plt.gca()

for key, C_rate in C_rates.items():

    # load the comsol voltage data
    comsol = pd.read_csv("comsol/Voltage{}.csv".format(key), sep=",", header=None)
    comsol_time = comsol[0].values
    comsol_voltage = comsol[1].values

    # update current density
    param["Typical current density"] = 24 * C_rate
    param.update_model(model, disc)

    # solve model
    solver = model.default_solver
    t = np.linspace(0, 1, 500)
    solver.solve(model, t)

    # extract the voltage
    voltage = pybamm.ProcessedVariable(
        model.variables["Terminal voltage [V]"], solver.t, solver.y, mesh=mesh
    )
    voltage_sol = voltage(solver.t)

    # convert solver time discharge Capacity
    tau = pybamm.standard_parameters_lithium_ion.tau_discharge
    tau_eval = param.process_symbol(tau).evaluate(0, 0)
    discharge_capacity = solver.t * tau_eval * param["Typical current density"] / 3600
    comsol_discharge_capacity = comsol_time * param["Typical current density"] / 3600

    # plot discharge curves
    color = next(ax._get_lines.prop_cycler)["color"]
    plt.plot(comsol_discharge_capacity, comsol_voltage, color=color, linestyle=":")
    plt.plot(
        discharge_capacity,
        voltage_sol,
        color=color,
        linestyle="-",
        label="{} C".format(C_rate),
    )

# add labels etc.
plt.ylim([3.2, 3.9])
plt.legend(loc="best")
plt.xlabel(r"Discharge Capacity (Ah/m$^2$)")
plt.ylabel("Voltage Loss (V)")
plt.title(r"Comsol $\cdots$ PyBaMM $-$")
plt.tight_layout()
plt.savefig("DischargeCurve.eps", format="eps", dpi=1000)
plt.show()
