# Upcoming

### New Checks

* Added `check_ascending_spike_times` for ensuring spike times are sorted in ascending order. [#394](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/394)

# v0.4.30

### Fixes

* Fixed issue in `check_empty_string_for_optional_attribute` where it would not skip optional non-`str` fields. [#400](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/400)



# v0.4.29

* Support for Python 3.7 has officially been dropped by the NWB Inspector. Please use Python 3.8 and above. [#380](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/380)

### Fixes

* `check_time_interval_time_columns` now only checks for `start_time`  with `is_ascending_series`. [#382](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/382)

* `is_acending_series` no longer asserts series to be strictly monotonic. [#374](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/374)



# v0.4.28

### Pending Deprecation (API)

* To reduce ambiguity of the new intermediate workflow calls in the API, `inspect_nwb` will be deprecated in the next major release. It is replaced by either `inspect_nwbfile` (applied to a written file on disk) or `inspect_nwbfile_object` (an open object in memory). [#364](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/364)

### New Checks

* Added support for new options to `subject.sex` (`XX` or `XO`) conditional on the `subject.species` being either "C. elegens" or "Caenorhabditis  elegens". [#353](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/353)

### Improvements

* Added an intermediate workflow to the main `nwbinspector` call pattern, named `inspect_nwbfile_object`. [#364](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/364)



# v0.4.27

### Fixes

* Added a false positive skip condition to `check_binary_columns` when applied to special tables with pre-defined columns, such as the `electrodes` of `Units`. [#349](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/349)



# v0.4.26

### Fixes

* Added a false positive skip condition to `check_timestamps_match_first_dimension` when applied to an `ImageSeries` that is using an `external_file` and therefore has an empty array set to `data`, but could have non-empty irregular `timestamps` for the video. [PR #335](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/335)

* Fixed the skip condition for `images` checks that were incorrectly run when using PyNWB v2.0.0. [PR #341](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/341)



# v0.4.25

### Improvements

* The version of the NWB Inspector can now be returned directly from the CLI via the `--version` flag. [PR # 333](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/333)



# v0.4.24

### Dependencies

* Loosened upper bound of numpy version. [PR # 330](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/330)


# v0.4.23

### New Checks

* Added check `check_index_series_points_to_image` to additionally about future deprecation of `indexed_timeseries` linked in `IndexSeries`. [# 322](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/322)



# v0.4.22

### Fixes

* Add a special skip condition to `check_timestamps_match_first_dimension` when an `IndexSeries` uses an `ImageSeries` as a target. [PR #321](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/321)



# v0.4.21

### New Checks

* Added check for unique ids for DynamicTables. [PR #316](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/316)

### Fixes

* Fix `check_subject_proper_age_range` to parse years. [PR #314](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/314)

* Write a custom `get_data_shape` method that does not return `maxshape`, which fixes errors in parsing shape. [PR #315](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/315)



# v0.4.20

### Improvements

* Added compression size consideration to `check_image_series_size`. [PR #311](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/311)

* Added false positive skip condition for `check_image_series_size` for `TwoPhotonSeries` neurodata types. [PR #301](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/301)

### Testing

* Added downstream testing of DANDI to the per-PR suite as a requirement for merging. [PR #306](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/306)

### Fixes

* Fixed issue in `run_checks` following [PR #303](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/303) that prevented iteration over certain check output types. [PR #306](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/306)



# v0.4.19

### Fixes

* Fixed an issue with table checks that attempted to retrieve data from on-disk NWB files in a non-lazy manner. Also improved `check_timestamps_match_first_dimension` for `TimeSeries` objects, which similarly attempted to load unnecessary data into memory. [PR #296](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/296) [PR #307](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/307)



# v0.4.18

### Hotfix

* Fix to the assigned `importance` output of configured checks, which was reverting to pre-configuration values. [PR #303](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/303)



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
