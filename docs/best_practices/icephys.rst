Intracellular electrophysiology
================================



IntracellularElectrode
----------------------


.. _best_practice_icephys_location:

Location
~~~~~~~~

The ``location`` field of an ``IntracellularElectrode`` should reflect your best estimate of the recorded brain area.
For mouse subjects, we recommend using terms from the :allen-brain-map:`Allen Brain Atlas <atlas>`, either the full
name or the abbreviation (e.g., ``Primary visual area`` or ``VISp``).

Check function: :py:meth:`~nwbinspector.checks._icephys.check_intracellular_electrode_location_allen_ccf`
