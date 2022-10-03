.. _units:

Units Formatting
================

As described in the :ref:`best_practice_unit_of_measurement`,
the specification of units should follow the International System of Units (SI).

The `CMIXF-12 <https://people.csail.mit.edu/jaffer/MIXF/CMIXF-12>`_ convention for encoding
SI units is recommended to minimize the variability of representation of unit values.
If the unit of measurement is unknown or unavailable, the unit can be declared as "a.u."
which stands for arbitrary units.
Please note the appropriate upper- or lower- casing when using CMIXF-12.

The `cmixf <https://github.com/sensein/cmixf>`_ Python package is used to check whether
the formatting of unit is compliant.

Unit table
^^^^^^^^^^
.. list-table::
   :widths: 25 25 50
   :align: center
   :header-rows: 1

   * - Neurodata type
     - Unit in CMIXF-12
     - Unit Name
   * - :py:class:`~pynwb.behavior.SpatialSeries`
     - "m"
     - Meters
   * - :py:class:`~pynwb.ecephys.ElectricalSeries`
     - "V"
     - Volts
   * - :py:class:`~pynwb.ecephys.SpikeEventSeries`
     - "V"
     - Volts
   * - :py:class:`~pynwb.icephys.PatchClampSeries`
     - "V"
     - Volts
   * - :py:class:`~pynwb.icephys.CurrentClampSeries`
     - "V"
     - Volts
   * - :py:class:`~pynwb.icephys.IZeroClampSeries`
     - "V"
     - Volts
   * - :py:class:`~pynwb.icephys.CurrentClampStimulusSeries`
     - "A"
     - Amperes
   * - :py:class:`~pynwb.icephys.VoltageClampSeries`
     - "A"
     - Amperes
   * - :py:class:`~pynwb.icephys.VoltageClampStimulusSeries`
     - "V"
     - Volts
   * - :py:class:`~pynwb.image.ImageSeries`
     - "a.u."
     - Arbitrary Units (unknown)
   * - :py:class:`~pynwb.image.IndexSeries`
     - "a.u."
     - Arbitrary Units (unknown)
   * - :py:class:`~pynwb.image.ImageMaskSeries`
     - "a.u."
     - Arbitrary Units (unknown)
   * - :py:class:`~pynwb.image.OpticalSeries`
     - "a.u."
     - Arbitrary Units (unknown)
