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



.. _simple_streaming_api:

Inspect a DANDI set (ROS3)
--------------------------

It is a common use case to want to inspect and review entire datasets of NWB files that have already been
uploaded to the :dandi-archive:`DANDI Archive <>`. While it is possible to simply download the entire dandiset to your local computer and
run the NWB Inspector as usual, there is an alternative which is less expensive in terms of bandwith. This can be especially
useful when the DANDI set is large and impractical to download in full, such as one that is multiple terabytes in total size.

A general tutorial for using the :code:`ros3` driver can be found in the :ros3-tutorial:`PyNWB documentation <>`. The NWB Inspector has also automated functionality for resolving the technical identification of assets such that the only piece of information needed is the six-digit DANDI set identifier...

.. code-block:: python

    from nwbinspector import inspect_all

    dandiset_id = "..."  # for example, 000004

    messages = list(inspect_all(nwbfile_path=dandiset_id, stream=True))

If there are multiple versions of the dandiset available (*e.g.*, separate 'draft' and 'published' versions) you can additionally specify this with the ``version_id`` argument...

.. code-block:: python

    from nwbinspector import inspect_all

    dandiset_id = "..."  # for example, 000004
    version_id = "draft"  # or "published", or can also set this to the exact DOI value

    messages = list(inspect_all(nwbfile_path=dandiset_id, stream=True, version=version_id))

See the section on :ref:`advanced_streaming_api` for more customized usage of the streaming feature.



Examining the Default Check Registry
------------------------------------

While it does not need to be imported directly for default usage, an interested user may inspect the ``list`` of all
available check functions via

.. code-block:: python

    from nwbinspector import available_checks
