Simulated Data
==============

The output of a simulation should be stored in NWB, but not the settings of the simulation.

You may store the result of simulations in NWB files. NWB allows you to store data as if it were recorded in vivo to
facilitate comparison between simulated results and in vivo results. Core components of the NWB schema and HDF5 backend
have been engineered to handle data from hundreds of thousands of units, and natively support parallel data access via
MPI, so much of the NWB:N format should work for large-scale simulations out-of-the-box.

The neurodata extension “simulation_output” provides a neurodata_type for storing continuous recordings from
multiple cells and multiple compartments per cell. The extension only supports storing the output data of a simulation
and does not support parameters for simulation configuration. This is out-of-scope for NWB, since it does not
facilitate side-by-side comparison between simulated and in vivo results, and is quite difficult to generalize given the
diversity of ways one can parameterize a simulation. That said, if you would benefit from storing such data in your
NWBFile, you might consider creating your own custom extension for that particular model.
