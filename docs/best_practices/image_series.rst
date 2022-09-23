ImageSeries
===========

Storage of ImageSeries
----------------------

.. _best_practice_image_series_file_too_large:

Use external model when file is too large
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


When storing commmon multimedia formats using the :ref:`nwb-schema:sec-ImageSeries` the file should be stored as
an external file. That is, the file should be packaged together with the nwb file instead of stored inside the format.
This can be accomplished by using  the ``external_file`` file option to store the path instead.

Check function: :py:meth:`~nwbinspector.checks.check_image_series_too_large`

.. _best_practice_image_series_external_mode_path:

Use relative path for external mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using ``external_file`` the paths passed in the ``external_file`` option should be relative to the location of the nwb file.

Check function: :py:meth:`~nwbinspector.checks.check_image_series_external_file_relative`
