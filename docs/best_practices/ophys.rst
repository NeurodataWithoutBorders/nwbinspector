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
