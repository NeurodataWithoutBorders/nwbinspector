# Upcoming

# v0.4.13

### DANDI Configuration
* `check_subject_sex`, `check_subject_species`, `check_subject_age`, `check_subject_proper_age_range` are now elevated to `CRITICAL` importance when using the "DANDI" configuration. Therefore, these are now required for passing `dandi validate`.

### Improvements
* Enhanced human-readability of the return message from `check_experimenter_form`. [PR #254](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/254)
* Extended check for ``Subject.age`` field with estimated age range using '/' separator. [PR #247](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/247)
* Allowed network-dependent tests to be skipped by specifying the `NWBI_SKIP_NETWORK_TESTS` environment variable. [PR #261](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/261)

### New Checks
* Added check for existence of ``IntracellularElectrode.cell_id`` [PR #256](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/256)
* Added check that bounds of age range for ``Subject.age`` using the '/' separator are properly increasing. [PR #247](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/247)
* Added check for existence of ``IntracellularElectrode.cell_id`` [PR #256](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/256)
* Added check for shape consistency between ``reference_images`` and the x, y, (z) dimensions of the ``image_mask`` of ``PlaneSegmentation``objects. [PR #257](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/257)

### Fixes
* Fixed the folder-wide `identifier` pre-check for `inspect_all` to read NWB files with extensions. [PR #262](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/262)
