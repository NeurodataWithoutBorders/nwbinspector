Naming
======


Neurodata Types
---------------


As a default, name class instances with the same name as the class.

Many of the Neurodata Types in NWB allow you to set their name to something other than the default name. 

This allows multiple objects of the same type to be stored side-by-side and allows data writers to provide 
human-readable information about the contents of the neurodata_type. If appropriate, simply use the name of the 
Neurodata Type as the name of that object.

For instance, if you are placing an ElectricalSeries object in /acquisition that holds voltage traces for a 
multichannel recording, consider simply naming that object "ElectricalSeries". This is the default_name for that 
object, and naming it like this will increase your chances that analysis and visualization tools will operate 
seamlessly with you data.There may be cases where you have multiple neurodata instances of the same type in the same 
Group. In this case the instances must have unique names. If they are both equally important data sources, build upon 
the class name (e.g. "ElectricalSeries_1" and "ElectricalSeries_2"). If one of the instances is an extra of less 
importance, name that one something different (e.g. "ElectricalSeries" and "ElectricalSeries_extra_electrode").

Names are not for storing meta-data. If you need to place other data of the same neurodata_type, you will need to 
choose another name. Keep in mind that meta-data should not be stored solely in the name of objects. It is OK to name 
an object something like “ElectricalSeries_large_array” however the name alone is not sufficient documentation. In this 
case, the source of the signal will be clear from the device of the rows from the linked electrodes table region, and 
you should also include any important distinguishing information in the description field of the object. Make an effort 
to make meta-data as explicit as possible. Good names help users but do not help applications parse your file.

’/’ is not allowed in names. When creating a custom name, using the forward slash (/) is not allowed, as this can 
confuse h5py and lead to the creation of an additional group. Instead of including a forward slash in the name, please 
use “Over” like in DfOverF.


Processing Modules
------------------


Indicate Modality
~~~~~~~~~~~~~~~~~

Give preference to default processing module names. These names mirror the extension module names: “ecephys”, 
“icephys”, “behavior”, “ophys”, “misc”. 

We encourage the use of these defaults, but there may be some cases when deviating from this pattern is appropriate. 

For instance, if there is a processing step that involves data from multiple modalities, or if the user wants to 
compare two processing pipelines for a single modality (e.g. different spike sorters), you should create 
Processing Modules with custom names.

ProcessingModules are themselves neurodata_types, and the other rules for neurodata_types also apply here. 
