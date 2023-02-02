Extensions
==========

Extend the core NWB schema only when necessary. Extensions are an essential mechanism to integrate
data with NWB that is otherwise not supported. However, we here need to consider that there are certain costs associated
with extensions, *e.g.*, cost of creating, supporting, documenting, and maintaining new extensions and effort for users
to use and learn already-created extensions. As such, users should attempt to use core ``neurodata_types`` or
pre-existing extentions before creating new ones. :ref:`hdmf-schema:sec-dynamictable`, which are used throughout the
NWB schema to store information about time intervals, electrodes, or spiking output, provide the ability to
dynamically add columns without the need for extensions, and can help avoid the need for custom extensions in many
cases.

If an extension is required, tutorials for the process may be found through the
:nwb-overview:`NWB Overview for Extensions <extensions_tutorial/extensions_tutorial_home.html>`.

It is also encouraged for extensions to contain their own check functions for their own best practices.
See the` :ref:`adding_custom_checks` section of the Developer Guide for how to do this.

Define new ``neurodata_types`` at the top-level (a.k.a., do not nest type definitions)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Rather than nesting definitions of ``neurodata_types``, all new types should be defined
at the top-level of the schema. To include a specific ``neurodata_type`` in another type
use the ``neurodata_type_inc`` key instead. For example:

.. tabs::

    .. tab:: Do This

       .. tabs::

            .. code-tab:: py Python

                from pynwb.spec import NWBGroupSpec

                # Define the first type
                type1_ext = NWBGroupSpec(
                    name='custom_type1',
                    doc='Example extension type 1',
                    neurodata_type_def='MyNewType1',
                    neurodata_type_inc='LabMetaData',
                )

                # Then define the second type and include the first type
                type2_ext = NWBGroupSpec(
                    name='custom_type2',
                    doc='Example extension type 2',
                    neurodata_type_def='MyNewType2',
                    groups=[NWBGroupSpec(neurodata_type_inc='MyNewType1',
                                         doc='Included group of ype MyNewType1')]
                )

            .. code-tab:: yaml YAML

                groups:
                - neurodata_type_def: MyNewType1
                  neurodata_type_inc: LabMetaData
                  name: custom_type1
                  doc: Example extension type 1
                - neurodata_type_def: MyNewType2
                  neurodata_type_inc: NWBContainer
                  name: custom_type2
                  doc: Example extension type 2
                  groups:
                  - neurodata_type_inc: MyNewType1
                    doc: Included group of ype MyNewType1

    .. tab:: DON'T do this

        .. tabs::

            .. code-tab:: py Python

                from pynwb.spec import NWBGroupSpec

                # Do NOT define a new type via ``neurodata_type_def`` within the
                # definition of another type. Always define the types separately
                # and use ``neurodata_type_inc`` to include the type
                type2_ext = NWBGroupSpec(
                    name='custom_type2',
                    doc='Example extension type 2',
                    neurodata_type_def='MyNewType2',
                    groups=[NWBGroupSpec(
                        name='custom_type1',
                        doc='Example extension type 1',
                        neurodata_type_def='MyNewType1',
                        neurodata_type_inc='LabMetaData',
                    )]
                )

            .. code-tab:: yaml YAML

                groups:
                - neurodata_type_def: MyNewType2
                  neurodata_type_inc: NWBContainer
                  name: custom_type2
                  doc: Example extension type 2
                  groups:
                  - neurodata_type_def: MyNewType1
                    neurodata_type_inc: LabMetaData
                    name: custom_type1
                    doc: Example extension type 1

Build on and Reuse Existing Neurodata Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When possible, use existing types when creating extensions either by creating new ``neurodata_types`` that inherit from
existing ones, or by creating ``neurodata_types`` that contain existing ones. Building on existing types facilitates the
reuse of existing functionality and interpretation of the data. If a community extension already exists that has a
similar scope, it is preferable to use that extension rather than creating a new one. For example:
* Extend ``TimeSeries`` for storing timeseries data. NWB provides main types of ``TimeSeries``
  and you should identify the most specific type of ``TimeSeries`` relevant for your use case
  (e.g., extend ``ElectricalSeries`` to define a new kind of electrical recording).
* Extend ``DynamicTable`` to store tabular data/
* Extend ``TimeIntervals`` to store specific annotations of intervals in time.


Provide Documentation
~~~~~~~~~~~~~~~~~~~~~

When creating extensions be sure to provide thorough, meaningful documentation as part of the extension specification.
Explain all fields (groups, datasets, attributes, links etc.) and describe what they store and how they
should be used.


Write the Specification to the NWBFile
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can store the specification (core and extension) within the NWBFile through caching.
Caching the specification is preferable, particularly if you are using a custom extension, because this ensures that
anybody who receives the data also receives the necessary data to interpret it.

.. note::
    In :pynwb-docs:`PyNWB <>`, the extension is cached automatically. This can be specified explicitly with
    ``io.write(filepath, cache_spec=True)``


Use Attributes for small metadata related to a particular data object (Group or Dataset)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Attributes should be used mainly to store small metadata (usually less than 64 Kbytes) that
is associated with a particular Group or Dataset. Typical uses of attributes are, e.g., to
define the ``unit`` of measurement of a dataset or to store a short ``description`` of
a group or dataset. For larger data, datasets should be used instead.

In practice, the main difference is that in PyNWB and MatNWB all Attributes are read into memory when reading the
NWB file. If you would like to allow users to read a file without reading all of these particular data values, use a
Dataset.


Link data to relevant metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Often metadata relevant to a particular type of data is stored elsewhere, e.g., information
about the ``Device`` used. To ensure relevant metadata can be uniquely identified, the data
should include links to the relevant metadata. NWB provides a few key mechanisms for linking:

* Use ``links`` (defined via ``NWBLinkSpec``) to link to a particular dataset or group
* Use ``DynamicTableRegion`` to link to a set of rows in a ``DynamicTable``
* Use a ``dataset`` with an object reference data type to store collections of links
  to other objects, e.g., the following dtype to define a dataset of links to ``TimeSeries``

  .. code-block:: yaml
        dtype:
            target_type: TimeSeries
            reftype: object


Best practices for object names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Names for groups, datasets, attributes, or links should typically:

* **Use lowercase letters only**
* **Use ``_`` instead of `` `` to separate parts in names**. E.g., use the name
  ``starting_time`` instead of ``starting time``
* **Explicit**. E.g., avoid the use of ambiguous abbreviation in names.


Best practices for naming ``neurodata_types``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For defining new types via ``neurodata_type_def`` use:

* **Use camelcase:**  notation, i.e., names of types should NOT include spaces,
  always start with an uppercase letter, and use a single capitalized letter to
  separate parts of the name. E.g,. ``neurodata_type_def: LaserMeasurement``
* **Use the postfix ``Series`` when extending a ``TimeSeries`` type.** E.g., when
  creating a new ``TimeSeries`` for laser measurements then add ``Series`` to
  the type name, e.g,. ``neurodata_type_def: LaserMeasurementSeries``
* **Use the postfix ``Table`` when extending a ``DynamicTable`` type.** e.g.,
  ``neurodata_type_def: LaserSettingsTable``
* **Explicit**. E.g., avoid the use of ambiguous abbreviation in names.

Use the ``ndx-template`` to create new extensions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By using the :nwb_extension_git:`ndx-template` to create new extensions helps ensure
that extensions can be easily shared and reused and published via the :ndx-catalog:`NDX Catalog <>`.
