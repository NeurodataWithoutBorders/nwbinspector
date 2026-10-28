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


.. _best_practice_photon_series_depth_axis:

Depth Axis
~~~~~~~~~~

The ``data`` of a ``TwoPhotonSeries`` or ``OnePhotonSeries`` is either ``(time, width, height)`` for a single plane or
``(time, width, height, depth)`` for a volume. Readers use the number of axes to tell the two apart, so a trailing axis
of length one turns a planar recording into a one-plane volume: viewers render it as a volume, archive metadata counts
it as volumetric, and readers that expect planar data reject it. This usually happens when a channel or plane axis is
left in place after splitting a multi-channel recording into one series per channel, which leaves each series with a
shape like ``(time, width, height, 1)``. If the recording is a single plane, store it with three axes.

If the recording is volumetric, describe the depth geometry so the volume can be interpreted. Set a three-component
``grid_spacing`` on the ``ImagingPlane``, which gives the spacing between planes, and where known a three-component
``origin_coords``. Without the spacing, the planes have no known distance from each other, and the volume cannot be
measured, rendered to scale, or registered to anything.

Check function: :py:meth:`~nwbinspector.checks._ophys.check_photon_series_undeclared_depth`
