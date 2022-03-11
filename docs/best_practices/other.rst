Unsorted
========

The ‘location’ field should reflect your best estimate of the recorded brain area. The 'location' column of the electrodes table is meant to store the 
brain region that the electrode as in. Different labs have different standards for electrode localization. Some use atlases and coordinate maps to 
precisely place an electrode, and use physiological measures to confirm its placement. Others use histology or imaging processing algorithms to identify 
regions after-the-fact. You fill this column with localization results from your most accurate method. For instance, if you target electrodes using 
physiology, and later use histology to confirm placement, we would recommend that you add a new column to the electrodes table called 'location_target', 
set those values to the original intended target, and alter the values of 'location' to match the histology results.
Use established ontologies for naming areas It is preferable to use established ontologies instead of lab conventions for indicating anatomical region. 
We recommend the Allen Brain Atlas terms for mice, and you may use either the full name or the abbreviation (do not make up your own terms.)
x,y,z is for the anatomical coordinates. For mice, use the Allen Institute Common Coordinate Framework v3, which follows the convention 
(+x = posterior, +y = inferior, +z = right).

For relative position of an electrode on a probe, use rel_x, rel_y[, rel_z]. These positions will be used by spike sorting software to determine 
electrodes that are close enough to share a neuron.
The location column of the electrodes table is required. If you do not know the location of an electrode, use 'unknown'.

Naming of neurodata_types
As a default, name class instances with the same name as the class. Many of the neurodata_types in NWB:N allow you to set their name to something 
other than the default name. This allows multiple objects of the same type to be stored side-by-side and allows data writers to provide human-readable 
information about the contents of the neurodata_type. If appropriate, simply use the name of the neurodata_type as the name of that object. For instance, 
if you are placing an ElectricalSeries object in /acquisition that holds voltage traces for a multichannel recording, consider simply naming that object 
"ElectricalSeries". This is the default_name for that object, and naming it like this will increase your chances that analysis and visualization tools 
will operate seamlessly with you data.There may be cases where you have multiple neurodata instances of the same type in the same Group. In this case the 
instances must have unique names. If they are both equally important data sources, build upon the class name (e.g. "ElectricalSeries_1" and "ElectricalSeries_2"). 
If one of the instances is an extra of less importance, name that one something different (e.g. "ElectricalSeries" and "ElectricalSeries_extra_electrode").
Names are not for storing meta-data. If you need to place other data of the same neurodata_type, you will need to choose another name. Keep in mind that 
meta-data should not be stored solely in the name of objects. It is OK to name an object something like “ElectricalSeries_large_array” however the name alone 
is not sufficient documentation. In this case, the source of the signal will be clear from the device of the rows from the linked electrodes table region, 
and you should also include any important distinguishing information in the description field of the object. Make an effort to make meta-data as explicit as 
possible. Good names help users but do not help applications parse your file.
’/’ is not allowed in names. When creating a custom name, using the forward slash (/) is not allowed, as this can confuse h5py and lead to the creation of an 
additional group. Instead of including a forward slash in the name, please use “Over” like in DfOverF.
Naming of processing modules
Give preference to default processing module names. In NWB:N version [ver], optional ProcessingModules will be added to increase standardization of processing 
module names. These names mirror the extension module names: “ecephys”, “icephys”, “behavior”, “ophys”, “misc”. We encourage the use of these defaults, but 
there may be some cases when deviating from this pattern is appropriate. For instance, if there is a processing step that involves data from multiple modalities, 
or if the user wants to compare two processing pipelines for a single modality (e.g. different spike sorters), you should create ProcessingModules with custom names. 
ProcessingModules are themselves neurodata_types, and the other rules for neurodata_types also apply here.
Unit of measurement
Use SI units where possible. Every TimeSeries instance has a unit as an attribute of the data Dataset, which is meant to indicate the unit of measurement of that data. 
We advise using SI units. Time is always in units of seconds.
Times
All times are in seconds. All session times are in seconds with respect to the timestamps_reference_time if present, otherwise they should be with respect to the 
session_start_time. This includes:
spike_times in the Units table.
start_time, stop_time, and any other custom times in any TimeIntervals object, including trials and epochs.
the starting_time or timestamps of any TimeSeries. The rate of TimeSeries should be in Hz.
World times are in ISO 8601 format. This includes:
session_start_time
timestamps_reference_time
the date_of_birth parameter of Subject
The age parameter of Subject should use the ISO 8601 Duration format. For instance indicating an age of 90 days would be 'P90D'.
Extensions
Extend only when necessary Extensions are an essential mechanism to integrate data with NWB:N that is otherwise not supported. However, we here need to consider that 
there are certain cost associated with extensions, e.g., cost for creating, supporting, documenting, and maintaining new extensions and effort for users to use and learn 
extensions. As such, we should create new extensions only when necessary and use existing neurodata_types as much as possible. DynamicTables used in NWB:N, e.g., to store 
information about time intervals and electrodes, provide the ability to dynamically add columns without the need for extensions and, as such, can help avoid the need for 
custom extensions in many cases.
Use/Reuse existing neurodata_types When possible, use existing types when creating extensions either by creating new neurodata_types that inherit from existing ones, or by 
creating neurodata_types that contain existing ones. Building on existing types facilitates the reuse of existing functionality and interpretation of the data. If a community 
extension already exists that has a similar scope, it is preferable to use that extension rather than creating a new one.
Provide meaningful docs When creating extensions be sure to provide as part of the extension specification, meaningful documentation of all fields (groups, datasets, 
attributes, links etc.) to describe what they store and how they are used.
Write the specification to the file. When using pynwb, you can store the specification (core and extension(s)) within the NWB file by using io.write(filepath, 
cache_spec=True). Caching the specification is preferable, particularly if you are using a custom extension, because this ensures that anybody who receives the data also 
receives the necessary data to interpret it.
Simulated data
The output of a simulation should be stored in NWB, but not the settings of the simulation. You may store the result of simulations in NWB files. NWB:N allows you to store 
data as if it were recorded in vivo to facilitate comparison between simulated results and in vivo results. Core components of the NWB:N schema and HDF5 backend have been 
engineered to handle data from hundreds of thousands of units, and natively support parallel data access via MPI, so much of the NWB:N format should work for large-scale 
simulations out-of-the-box. The neurodata extension “simulation_output” provides a neurodata_type for storing continuous recordings from multiple cells and multiple 
compartments per cell. The extension only supports storing the output data of a simulation and does not support parameters for simulation configuration. This is out-of-scope 
for NWB:N, since it does not facilitate side-by-side comparison between simulated and in vivo results, and is quite difficult to generalize given the diversity of ways one can 
parametrize a simulation. That said, if you would benefit from storing such data in your NWB:N file, you might consider creating your own custom extension.
