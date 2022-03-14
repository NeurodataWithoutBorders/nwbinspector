Ecephys
=======


Electrodes
----------


Location
~~~~~~~~

The ‘location’ field should reflect your best estimate of the recorded brain area. 

The 'location' column of the electrodes table is meant to store the brain region that the electrode as in.

Different labs have different standards for electrode localization.

Some use atlases and coordinate maps to precisely place an electrode, and use physiological measures to confirm its 
placement. Others use histology or imaging processing algorithms to identify regions after-the-fact. You fill this 
column with localization results from your most accurate method. For instance, if you target electrodes using 
physiology, and later use histology to confirm placement, we would recommend that you add a new column to the electrodes 
table called 'location_target', set those values to the original intended target, and alter the values of 'location' to 
match the histology results. 

The location column of the electrodes table is required. If you do not know the location of an electrode, use 'unknown'.


Ontologies
~~~~~~~~~~

It is preferable to use established ontologies instead of lab conventions for indicating anatomical region.
We recommend the Allen Brain Atlas terms for mice, and you may use either the full name or the abbreviation (do not 
make up your own terms.)



Anatomical Coordinates
~~~~~~~~~~~~~~~~~~~~~~

x,y,z are for the precise anatomical coordinates within the Subject. 

For mice, use the Allen Institute Common Coordinate Framework v3, which follows the convention 
(+x = posterior, +y = inferior, +z = right).



Relative Coordinates
~~~~~~~~~~~~~~~~~~~~

For relative position of an electrode on a probe, use rel_x, rel_y, and rel_z. These positions will be used by spike 
sorting software to determine electrodes that are close enough to share a neuron.
