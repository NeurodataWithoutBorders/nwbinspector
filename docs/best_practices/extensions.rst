Extensions
==========

Extend only when necessary.

Extensions are an essential mechanism to integrate data with NWB that is otherwise not supported. However, we here need 
to consider that there are certain costs associated with extensions, e.g., cost of creating, supporting, documenting, 
and maintaining new extensions and effort for users to use and learn extensions. As such, we should create new 
extensions only when necessary and use existing neurodata_types as much as possible. DynamicTables used in NWB, 
e.g., to store information about time intervals and electrodes, provide the ability to dynamically add columns without 
the need for extensions and, as such, can help avoid the need for custom extensions in many cases.

TODO, add links to the tutorials for extensions


Use Existing Neurodata Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When possible, use existing types when creating extensions either by creating new neurodata_types that inherit from 
existing ones, or by creating neurodata_types that contain existing ones. Building on existing types facilitates the 
reuse of existing functionality and interpretation of the data. If a community extension already exists that has a 
similar scope, it is preferable to use that extension rather than creating a new one.


Provide Documentation
~~~~~~~~~~~~~~~~~~~~~

When creating extensions be sure to provide meaningful documentation as part of the extension specification, of all 
fields (groups, datasets, attributes, links etc.) to describe what they store and how they are used.


Write the Specification to the NWBFile
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using pynwb, you can store the specification (core and extension)  within the  NWBFile by using
```io.write(filepath, cache_spec=True)```. Caching the specification is preferable, particularly if you are using a 
custom extension, because this ensures that anybody who receives the data also receives the necessary data to 
interpret it.
