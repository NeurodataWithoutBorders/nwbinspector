Naming
======



Neurodata Types
---------------



.. _best_practice_object_names:

Naming Conventions
~~~~~~~~~~~~~~~~~~

As a default, name class instances with the same name as the class.  *E.g.*, if your :nwb-schema:ref:`sec-NWBFile` has
only one :nwb-schema:ref:`sec-ElectricalSeries` for the raw acquisition, then simply name it ``ElectricalSeries``.

Many of the Neurodata Types in NWB allow you to set their name to something other than the default name, and this should
be done any time there are multiple types of the same class. *E.g.*, if you have several
:nwb-schema:ref:`sec-ElectricalSeries` for different segments or devices, then add some distinguishing information to
each name: ``ElectricalSeries1`` vs. ``ElectricalSeries2``, or ``ElectricalSeriesSegment1`` vs.
``ElectricalSeriesSegment2``, etc. This allows multiple objects of the same type to be stored side-by-side and allows
data writers to provide human-readable information about the contents of the ``neurodata_type``.

It is recommended to use :wikipedia:`CamelCase <Camel_case>` when naming instances of schematic classes.



.. _best_practice_description:

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
add any explicit metadata explaining these details.

Slash-like characters ``'/'``, ``'\'``, or ``'|'``  are not not allowed in the ``name`` of an object. This can be
confusing to systems that parse HDF5 files (which NWB uses, see the
:nwb-overview:`NWB FAQ <faq_details/why_hdf5.html#why-hdf5>` for more details) because similar protocols are used to
specify the location of ``groups`` within the file.

For mathematical expressions, instead of including the special character in the name, please use an English equivalent
instead. *E.g.*, instead of "Df/f" use "DfOverF".



Processing Modules
------------------


.. _best_practice_processing_module_names:

Indicate Modality
~~~~~~~~~~~~~~~~~

Give preference to default :nwb-schema:ref:`sec-processingmodule` names. These names mirror the most common modalities:
``ecephys``, ``icephys``, ``behavior``, ``ophys``, ``misc``.

We encourage the use of these defaults, but there may be some cases when deviating from this pattern is appropriate,
such as a non-standard modality or a mixture of processing data combined across multiple modalities.

:nwb-schema:ref:`ProcessingModules <sec-processingmodule>` are themselves ``neurodata_types``, and the other rules for
``neurodata_types`` also apply here.
