Using the Library
=================

For users familiar with Python, our core functions may also be used directly to allow greater freedom in handling input and output.


InspectorMesssage objects
-------------------------

In order to understand the output of the core functions, we must first explain the most important data structure in our
library, the `InspectorMessage`. This is a standalone data class that contains all values that could be useful or 
related to a detected Best Practice issue. These values include the text-based `message` displayed in the report, 
the `importance` of the check (how crucial it is to fix), the name of the object that triggered the issue, where that
object can be found within the NWBFile itself, and the file path of the NWBFile relative to the directory the inspection
function was called from.


Inspect a single NWBFile
------------------------

The most basic function to use when inspecting a single NWBFile is the `inspect_nwb` function.

.. :code-block:: python
    from nwbinspector import inspect_nwb
    
    results = list(inspect_nwb(nwbfile_path="path_to_single_nwbfile"))

This returns a `list` of `InspectorMessage` objects.


Inspect a Directory or List of Paths to NWBFiles
------------------------------------------------

If you want to run essentially the same code as the CLI, use the `inspect_all` function.

.. :code-block:: python
    from nwbinspector import inspect_all
    
    all_results = list(inspect_all(path=file_paths_or_folder, ...))

This has the same return structure as `inspect_nwb`


.. note::

    For convenience, all path-based arguments in the NWBInspector library support both `str` and `pathlib.Path` types.


Examining the Default Check Registry
------------------------------------

While it does not need to be imported directly for default usage, an interested user may inspect the `list` of all
available check functions via

.. :code-block:: python
    from nwbinspector import available_checks

