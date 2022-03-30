General
=======


<<<<<<< HEAD:docs/best_practices/naming.rst

Neurodata Types
---------------
=======
>>>>>>> dev:docs/best_practices/general.rst

Names
-----



Standard Names
~~~~~~~~~~~~~~


.. _best_practice_object_names:

Naming Conventions
~~~~~~~~~~~~~~~~~~

As a default, name class instances with the same name as the class. If appropriate, simply use the name of the
``neurodata_type`` as the name of that object. *E.g.*, if your :nwb-schema:ref:`sec-NWBFile` has only a single
:nwb-schema:ref:`sec-ElectricalSeries` that holds voltage traces for a multichannel recording, then simply name it
``ElectricalSeries``.

There may be cases where you have multiple instances of the same ``neurodata_type`` in the same Group. In this case,
the instances must have unique names. An easy way to achieve this is to add an index or other minimal distinguishing
characteristics to the end of the name of that ``neurodata_type``; an example for multiple
:nwb-schema:ref:`sec-ElectricalSeries` (corresponding perhaps to differing segments or electrode regions) might be to
distinguish them as ``ElectricalSeries1`` and ``ElectricalSeries2``, or as ``ElectricalSeries`` and
``ElectricalSeriesExtraElectrodes``.

Following this practice allows multiple objects of the same type to be stored side-by-side and increase your chances
that analysis and visualization tools will operate seamlessly to provide human-readable information about the contents
of the file.

It is recommended to use :wikipedia:`CamelCase <Camel_case>` when naming instances of schematic classes.



.. _best_practice_description:

<<<<<<< HEAD:docs/best_practices/naming.rst
Metadata Descriptions
~~~~~~~~~~~~~~~~~~~~~

The ``name`` of an object is for identifying that object within the file; it is not for storing metadata. Instead, the
``description`` field for most objects can be used to include any important distinguishing information. When writing
metadata, make every effort to be as explicit and self-contained as possible in the explaining relevant details. Use
official ontologies whenever specific references are required, and provide external links to those ontologies.

It is OK to name an object something like ``ElectricalSeriesDuringSomeEvent``, however the name alone is not sufficient
documentation of the condition ``DuringSomeEvent``. In this case, the source of the signal will be clear from the
:nwb-schema:ref:`device` linkage in the rows of the passed :nwb-schema:ref:`sec-sec-dynamictableregion` subsetting
the full :nwb-schema:ref:`ElectrodeTable <groups-general-extracellular-ephys-electrodes>`, so you would not need to
add any explicit metadata explaining these details. Likewise, the event itself would be specified as an independent
component to the experiment stored under ``acquisition``, the :nwb-schema:ref:`trials <groups-intervals-trials>` or :nwb-schema:ref:`epochs <roups-intervals-epochs>` intervals, ``processing/behavior``
(see :ref:`best_practice_processing_module_names` for more details), or using an extension such as
:ndx-annotation-series:`ndx-events <>`.

Slash-like characters ``'/'`` or ``'\'``  are not not allowed in the ``name`` of an object. This can be
confusing to systems that parse HDF5 files (which NWB uses as the primary backend, see the
:nwb-overview:`NWB FAQ <faq_details/why_hdf5.html#why-hdf5>` for more details) because similar protocols are used to
specify the location of `Groups <https://schema-language.readthedocs.io/en/latest/description.html#groups>`_ within the file.

For mathematical expressions, instead of including the special character in the name, please use an English equivalent
instead. *E.g.*, instead of "Df/f" use "DfOverF".
=======
>>>>>>> dev:docs/best_practices/general.rst


.. _best_practice_name_slashes:

Do Not Use Slashes
~~~~~~~~~~~~~~~~~~

'/' is not allowed in Group or Dataset names, as this can confuse h5py and lead to the creation of an additional group.
Instead of including a forward slash in the name, please use "Over" like in DfOverF.

Check function: :py:meth:`~nwbinspector.checks.general.check_name_slashes`


<<<<<<< HEAD:docs/best_practices/naming.rst
.. _best_practice_processing_module_names:

Indicate Modality
~~~~~~~~~~~~~~~~~

Give preference to default :nwb-schema:ref:`sec-processingmodule` names. These names mirror the most common modalities:
``ecephys``, ``icephys``, ``behavior``, ``ophys``, ``misc``.

We encourage the use of these defaults, but there may be some cases when deviating from this pattern is appropriate,
such as a non-standard modality or a mixture of processing data combined across multiple modalities.

:nwb-schema:ref:`ProcessingModules <sec-processingmodule>` are themselves ``neurodata_types``, and the other rules for
``neurodata_types`` also apply here.
=======

Descriptions
------------



.. _best_practice_description:

Metadata and Descriptions
~~~~~~~~~~~~~~~~~~~~~~~~~

Names are not for storing meta-data, so meta-data should not be stored solely in the name of objects. It is OK to name
an object something like “ElectricalSeries_large_array” however the name alone is not sufficient documentation. In this
case, the source of the signal will be clear from the device of the rows from the linked electrodes table region, and
you should also include any important distinguishing information in the description field of the object. Make an effort
to make meta-data as explicit as possible. Good names help users but do not help applications parse your file.

As such, it is not recommended to use blank or default 'placeholder' descriptions.

Check function: :py:meth:`~nwbinspector.checks.general.check_description`
>>>>>>> dev:docs/best_practices/general.rst