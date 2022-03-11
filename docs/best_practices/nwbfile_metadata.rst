NWBFile Metadata
================

An NWBFile object generally contains data from a single experimental session.



File Organization
-----------------


Acquisition & Processing
~~~~~~~~~~~~~~~~~~~~~~~~

The 'acquisition' group is specifically for time series measurements that are acquired from an acquisition system, 
e.g. an ElectricalSeries with the voltages from the recording systems or the output of the position sensors (like your wheel 
position).

The 'processing' modules are for intermediate data. If you take the wheel position and derive the position of the animal 
in meters, that would go in ```/processing/behavior/Position/SpatialSeries```.

An LFP signal that is a downsampled version of the acquired data would go in ```/processing/ecephys/LFP/ElectricalSeries```.

It may not always be 100% clear whether data is acquired or derived, so in those cases you should just use your best judgement.


File Identifiers
~~~~~~~~~~~~~~~~

NWBFile has two distinct places for ids: session_id and identifier.

The session_id field marks unique experimental sessions. The session_id should have a one-to-one relationship with a recording session. 
Sometimes you may find yourself having multiple NWB files that correspond to the same session. This can happen for instance if you separate 
out processing steps into multiple files or if you want to compare different processing systems. In this case, the session_id should be the 
same for each file. Each lab should use a standard for session_id so that sessions have unique names within the lab and the sessions ids are human-readable.
The identifier tag should be a globally unique value for the NWBFile. Two different NWBFiles from the same session should have different 
identifier values if they differ in any way. It is recommended that you use a unique id generator like uuid to ensure its uniqueness and it is 
not important that the identifier field is human readable.



Subject
-------

Subject ID
~~~~~~~~~~

Subject Sex
~~~~~~~~~~~

Subject Species
~~~~~~~~~~~~~~~