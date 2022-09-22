Using the Library
=================

For users familiar with Python, our core functions may also be used directly to allow greater freedom in handling input
and output.



InspectorMesssage objects
-------------------------

In order to understand the output of the core functions, we must first explain the most important data structure in our
library, the :py:class:`~nwbinspector.register_checks.InspectorMessage`. This is a standalone data class that contains
all values that could be useful or related to a detected Best Practice issue. These values include the text-based
``message`` displayed in the report, the ``importance`` of the check (how crucial it is to fix), the ``object_name``
and ``object_type`` that triggered the issue, the ``location`` of that object within the NWBFile, and the ``file_path``
of the NWBFile relative to the directory the inspection function was called from.



Inspect a single NWBFile
------------------------

The most basic function to use when inspecting a single NWBFile is the
:py:class:`~nwbinspector.nwbinspector.inspect_nwb` function.

.. code-block:: python

    from nwbinspector import inspect_nwb

    results = list(inspect_nwb(nwbfile_path="path_to_single_nwbfile"))

This returns a ``list`` of :py:class:`~nwbinspector.register_checks.InspectorMessage` objects.



Inspect a Directory or List of Paths to NWBFiles
------------------------------------------------

If you want to run essentially the same code as the CLI, use the :py:class:`~nwbinspector.nwbinspector.inspect_all`
function.

.. code-block:: python

    from nwbinspector import inspect_all

    all_results = list(inspect_all(path=file_paths_or_folder, ...))

This has the same return structure as :py:class:`~nwbinspector.nwbinspector.inspect_nwb`.


.. note::

    For convenience, all path-based arguments in the NWBInspector library support both ``str`` and ``pathlib.Path`` types.



.. simple_streaming_api:

Running inspection on a entire DANDI set (ROS3)
-----------------------------------------------

It is a common use case to want to inspect and review entire datasets of NWBFiles that have already been
uploaded to the :dandi-archive:`DANDI Archive <>`. While one could technically just download the DANDI set and
use the NWB Inspector as normal, there is another, less expensive possibility in terms of bandwith. This is especially
useful when the underlying dataset is quite large and thus impractical to download - some DANDI sets can even be on the
terabyte (TB) scale!

The general tutorial for using the :code:`ros3` driver can be found :ros3-tutorial:`here <>` - however, the NWB Inspector has implemented automatic resolution of asset paths so that the only thing required is the DANDI set ID (six-digit identifier)...

.. code-block:: python

    from nwbinspector import inspect_all

    dandiset_id = "..."  # for example, 000004

    messages = list(inspect_all(nwbfile_path=dandiset_id, stream=True))

If there are multiple versions of the DANDI set available (*e.g.*, separate 'draft' and 'published' versions) you can additionally specify this with the `version_id` argument...

.. code-block:: python

    from nwbinspector import inspect_all

    dandiset_id = "..."  # for example, 000004
    version_id = "draft"  # or "published", if it has an official doi associated

    messages = list(inspect_all(nwbfile_path=dandiset_id, stream=True, version=version_id))



Examining the Default Check Registry
------------------------------------

While it does not need to be imported directly for default usage, an interested user may inspect the ``list`` of all
available check functions via

.. code-block:: python

    from nwbinspector import available_checks
