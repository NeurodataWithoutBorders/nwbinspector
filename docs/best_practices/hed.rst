HED Annotations
===============

`HED <https://www.hedtags.org/hed-resources/>`_ (Hierarchical Event Descriptors) is a controlled vocabulary for
annotating events and other tabular data. In NWB, HED annotations are stored with the
`ndx-hed <https://github.com/hed-standard/ndx-hed>`_ extension, which provides:

- ``HedTags``: a column named ``HED`` in any :ref:`hdmf-schema:sec-dynamictable` that holds a HED string for
  each row.
- ``HedValueVector``: a column of values with a HED template, such as ``Age/# s``, that each value is
  substituted into.
- ``HedDurationVector``: the ``duration`` column of an ``EventsTable``, with such a template.
- ``HedTags`` in a ``MeaningsTable``: a column named ``HED`` that gives the HED of each value of a categorical
  column.
- ``HedLabMetaData``: the version of the HED schema in use and any HED definitions.

.. note::

    ``MeaningsTable`` and ``EventsTable`` were added in NWB schema 2.10.0 (``MeaningsTable`` through
    hdmf-common schema 1.9.0). Writing them requires PyNWB 4.0.0 or later and HDMF 5.0.0 or later. ``ndx-hed``
    0.3.0, the first release that supports them, requires PyNWB 4.2.0 and HDMF 6.2.0.

.. _best_practice_hed_lab_metadata:

Declare the HED Schema Version
------------------------------

A file that contains HED annotations should also contain a ``HedLabMetaData`` object giving the version of the
HED schema that the annotations were written against. The vocabulary changes between versions, so without the
version the annotations cannot be interpreted or validated:

.. code-block:: python

    from ndx_hed import HedLabMetaData

    nwbfile.add_lab_meta_data(HedLabMetaData(hed_schema_version="8.4.0"))

Check function: :py:meth:`~nwbinspector.checks._hed.check_hed_lab_metadata_exists`

.. _best_practice_hed_annotations:

Use Valid HED Annotations
-------------------------

Every HED annotation in the file should be valid against the declared HED schema:

- Every tag should be in the schema, spelled as the schema spells it.
- Every ``Def/`` tag should refer to a definition given in the ``HedLabMetaData``.
- The template of a ``HedValueVector`` or ``HedDurationVector`` should be valid, and every value of the column
  should be valid in its place, for example a number where the tag takes a number with units.
- The HED of a categorical value belongs in a ``HedTags`` column named ``HED`` in the ``MeaningsTable`` of the
  column, one complete HED string for each value. A ``MeaningsTable`` should not hold a ``HedValueVector``.
- The HED of each row, combined from the ``HED`` column, the HED of the row's categorical values, and the
  templates of its value columns, should also be valid as a whole. For example, the same tag should not appear
  both in the ``HED`` column and in the HED of a categorical value of the same row.

Check function: :py:meth:`~nwbinspector.checks._hed.check_hed_annotations_valid`

.. _best_practice_hed_extensions:

Prefer Tags from the Schema
---------------------------

HED allows a tag to be extended with a term of your own, such as ``Item/My-device``, but other people and tools
know only the terms in the schema. Use a tag from the schema where one fits, and extend a tag only where none does.

Check function: :py:meth:`~nwbinspector.checks._hed.check_hed_annotations_warnings`
