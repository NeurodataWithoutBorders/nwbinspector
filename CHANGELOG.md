# Upcoming

# v0.4.17

### Hotfix

* Fix to skip certain tests if optional testing config path was not specified (mostly for conda-forge).



# v0.4.16

### Improvements

* Allow NCBI taxonomy references for Subject.species. [PR #290](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/290)
* Added PyNWB v2.1.0 specific file generation functions to the `testing` submodule, and altered the tests for `ImageSeries` to use these pre-existing files when available. Also included automated workflow to push the generated files to a DANDI-staging server for public access. [PR #288](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/288)

### Fixes

* Fixed relative path detection for cross-platform strings in `check_image_series_external_file_relative` [PR #288](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/288)



# v0.4.14

### Fixes
* Fixed an error with attribute retrieval specific to the `cell_id` of the `IntracellularElectrode` neurodata type that occured with respect to older versions of PyNWB. [PR #264](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/264)



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
