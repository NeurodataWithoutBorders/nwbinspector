Optical physiology
==================



Plane Segmentation
------------------


.. _best_practice_plane_segmentation_image_mask_shape_against_ref_images:

Image Shape Consistency
~~~~~~~~~~~~~~~~~~~~~~~

The ``image_mask`` column of a ``PlaneSegmentation``, if specified, should have the same image shape as each item in the ``reference_images``.


ImagingPlane
------------


.. _best_practice_ophys_location:

Location
~~~~~~~~

The ``location`` field of an ``ImagingPlane`` should reflect your best estimate of the recorded brain area. For mouse
subjects, we recommend using terms from the :allen-brain-map:`Allen Brain Atlas <atlas>`, either the full name or the
abbreviation (e.g., ``Primary visual area`` or ``VISp``).

Check function: :py:meth:`~nwbinspector.checks._ophys.check_imaging_plane_location_allen_ccf`


Photon Series
-------------


.. _best_practice_photon_series_declared_depth:

Declaring a Depth Axis
~~~~~~~~~~~~~~~~~~~~~~

NWB defines the fourth axis of a ``TwoPhotonSeries`` or ``OnePhotonSeries`` as depth, so any reader is obliged to treat
a four-dimensional series as volumetric. Nothing else in the file says how those planes are spaced or where they sit
unless you declare it, so a four-dimensional series with no depth geometry cannot be interpreted as a volume.

If the data is volumetric, declare it: give the ``ImagingPlane`` a three-component ``grid_spacing`` (or
``origin_coords``), or set a three-component ``dimension`` on the series. If the depth is one, the axis is usually a
channel or plane axis that was never squeezed out after splitting the data into one series per channel, and the data
should be stored as ``(time, rows, columns)`` instead.

Check function: :py:meth:`~nwbinspector.checks._ophys.check_photon_series_undeclared_depth`
