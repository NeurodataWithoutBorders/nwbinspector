# v0.7.3 (Upcoming)

### New Checks
* Added `check_image_series_external_file_forward_slashes` to detect backslashes in `ImageSeries.external_file` paths. Such paths are produced by platform-dependent path joining on Windows and silently fail to resolve on POSIX systems and against archive asset keys such as those used by DANDI. [#697](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/697)
* Added `check_spike_times_without_nans` to detect NaN values in Units spike times, which indicate conversion bugs or unclean array padding. [#689](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/689)
* Added `check_subject_age_reference` to validate that `Subject.age__reference`, when present, is one of the supported values (`"birth"` or `"gestational"`). This catches invalid references in files written by tools that do not enforce the schema constraint. [#250](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/250)

### Improvements
* Raised the minimum required PyNWB to `>=4.0` to track the latest PyNWB release. [#708](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/708)
* Bumped GitHub Actions workflow dependencies (`actions/checkout` v4 -> v6, `actions/setup-python` v5 -> v6, `codecov/codecov-action` v4 -> v5) to migrate off Node.js 20, which GitHub is removing from runners on 2026-09-16. [#702](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/702)

### Fixes
* Fixed the docstring of `check_name_slashes` and a typo in the message of `check_empty_string_for_optional_attribute` ("Improve by omitting"). [#754](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/754)
* Fixed unit tests that failed at construction time against recent PyNWB and HDMF. [#707](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/707) [#708](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/708)
* Skipped Ontobee in the documentation external link check, which frequently timed out and caused spurious CI failures. [#709](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/709)
* Fixed `run_checks` raising `TypeError` when a `progress_bar_class` was passed without `progress_bar_options`; the keyword arguments are now coalesced to an empty dict before being forwarded to the progress-bar constructor. [#701](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/701)

# v0.7.2 (May 19, 2026)

### New Checks

### Improvements
* Made `hdmf-zarr` an optional dependency to restore pip-installability when `numcodecs` wheels are unavailable. Install with `pip install nwbinspector[zarr]` to enable Zarr-backed NWB file inspection. The local-file read path now delegates to `pynwb.read_nwb`, which produces a clear install hint when a Zarr file is encountered without the `[zarr]` extra. [#698](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/698)
* Reorganized CI so upstream-dev test failures no longer gate PRs. Dev-branch jobs (`test-pynwb-dev`, `test-dandi-dev`, `test-dandi-dev-live`) moved from `deploy-tests.yml` into a new `dev-dailies.yml` scheduled workflow. Also added per-workflow failure emails, centralized the `testing.yml` Python and OS matrices into shared text files, renamed `dev-gallery.yml` to `pynwb-dev-tests.yml`, and rewrote `read-nwbfile-tests.yml` to use a named conda environment (`environment-ros3.yml`) so the ROS3-enabled h5py from conda-forge activates correctly on Windows runners. [#700](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/700)

### Fixes
* Fixed ROS3 streaming in `read_nwbfile` after h5py began enforcing an explicit `aws_region` for the ROS3 driver. Added a `backend_kwargs` keyword-only parameter to `read_nwbfile` that forwards arbitrary kwargs to the underlying `NWBHDF5IO` constructor on the streaming paths (`fsspec`, `ros3`); ROS3 callers now pass `backend_kwargs={"aws_region": "us-east-1"}`. The generic escape hatch avoids having to surface each new upstream kwarg individually. [#700](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/700)
* Deprecated `read_nwbfile_and_io`; it will be removed after 2026-11-13. Use `read_nwbfile` instead; the IO object is accessible from the returned NWBFile via `nwbfile.get_read_io()`. [#700](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/700)

# v0.7.1 (March 26, 2026)

### New Checks

* Added `check_spatial_series_unit` to validate that SpatialSeries objects (outside of CompassDirection) have a recognized unit string from a curated allowlist of SI length units, angular units, and pixels. [#685](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/685)
* Added `check_imaging_plane_location_allen_ccf`, `check_electrodes_location_allen_ccf`, and `check_intracellular_electrode_location_allen_ccf` to validate location fields against Allen Mouse Brain CCF ontology terms when subject species is mouse. [#671](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/671)
* Added `check_time_intervals_start_time_not_constant` to flag TimeIntervals tables where all start_time values are identical, indicating times were likely not set relative to session start. [#677](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/677)
* Added `check_units_resolution_is_set` to flag when the Units table has spike_times but resolution is not set to a meaningful positive float. [#686](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/686)
* Added `check_spike_times_not_in_samples` to flag when spike times appear to be stored as sample indices rather than seconds, detected by all values being integer-valued with implausibly large magnitudes.
* Added `check_units_table_has_spikes` to flag Units tables that do not contain a spike_times column. [#691](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/691)


### Improvements
* Upgraded `check_ascending_spike_times` from `BEST_PRACTICE_VIOLATION` to `CRITICAL` and made it flag both descending and equal consecutive spike times. Setting the `resolution` field on the Units table suppresses the equal-timestamps check for recordings with limited temporal precision. [#684](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/684)

### Fixes
* Fixed `RuntimeWarning: All-NaN slice encountered` in `check_time_intervals_duration` when custom time columns contain all-NaN values. [#682](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/682)

# v0.7.0 (Feb 23, 2026)

### New Checks
* Added `check_file_extension` for NWB file extension best practice recommendations (`.nwb`, `.nwb.h5`, or `.nwb.zarr`) [#625](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/625)
* Added `check_time_series_duration` to detect unusually long TimeSeries durations (default threshold: 1 year). [#627](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/627)
* Added `check_rate_not_below_threshold` to detect suspiciously low sampling rates that may indicate period was used instead of rate. [#627](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/627)
* Added `check_units_table_duration` to detect if the duration of spike times in a Units table exceeds a threshold (default: 1 year), which may indicate spike_times are in the wrong units or there is a data quality issue. [#636](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/636)
* Added `check_time_intervals_duration`, which makes sure that `TimeInterval` objects do not have a duration greater than 1 year.
[#635](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/635)
* Added `check_electrical_series_unscaled_data` to warn when ElectricalSeries has integer data type with default conversion (1.0) and offset (0.0), which suggests raw acquisition units are not properly scaled to Volts. Also considers `channel_conversion` for per-channel scaling. [#408](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/408)
* Added `check_subject_weight` to ensure subject weight follows the form '[numeric] [unit]' (e.g., '2.3 kg' or '10 g'). [#647](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/647)
* Added `check_image_series_starting_frame_without_external_file` to verify that `starting_frame` is not set when `external_file` is not used in an `ImageSeries`. [#235](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/235)
* Added `check_sweeptable_deprecated` to detect usage of the deprecated `SweepTable` in NWB files with schema version >= 2.4.0, which should use `IntracellularRecordingsTable` instead. [#657](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/657)
* Added `check_time_series_data_is_not_empty` to detect empty `.data` fields in `TimeSeries` containers, which often indicate incomplete data entry or conversion errors. Skips `ImageSeries` with `external_file` set, where empty data is intentional. [#668](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/668)
* Added `check_publication_list_format` to detect comma-separated DOIs/URLs in `related_publications` entries that should be separate list entries. [#419](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/419)

### Improvements
* Added documentation to API and CLI docs on how to use the dandi config option. [#624](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/624)
* Updated report summary to include number of files detected and indicate when no issues are found. [#629](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/629)
* Made subject information checks (`check_subject_exists`, `check_subject_id_exists`, `check_subject_sex`, `check_subject_age`) CRITICAL by default to be consistent with DANDI requirements. [#648](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/648)
* Added `nwb_schema_version_lt` and `nwb_schema_version_gt` parameters to `register_check` to conditionally run checks based on the NWB schema version of the file being inspected. [#661](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/661)

### Fixes
* Fixed `check_subject_age` to allow `"/"` and `"/P3D"` style age ranges where the lower bound is unspecified. [#673](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/673)
* Fixed `check_timestamp_of_the_first_sample_is_not_negative` to handle empty timestamps arrays instead of throwing an `IndexError`. [#582](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/582)
* Fixed file count error when checking for non-unique identifiers in a folder [#629](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/629)
* Improved `check_data_orientation` error message to include the TimeSeries name, current shape, and a suggestion for transposing the data. [#1430](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/1430)
* Dropped Python 3.9 and middle Python versions (3.11, 3.12) from CI; now testing only Python 3.10 and 3.13. [#632](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/632)
* Updated macOS CI runner from `macos-13` to `macos-latest`. [#639](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/639)

# v0.6.5 (July 25, 2025)

### Fixes
* Fixed build configuration error in pyproject.toml [#605](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/605)

# v0.6.4 (July 24, 2025)

### New Checks
* Added checks to make sure subject_id and session_id do not contain slashes [#570](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/570)

### Fixes
* Fixed incorrect data orientation check for SpikeEventSeries [#592](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/592)
* Fixed dimensionality check for SpikeEventSeries validation [#581](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/581)
* Fixed error when checking for negative values in a time column with array data [#600](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/600)
* Fixed issue where the io object remained open after inspection was completed. [#601](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/601)

### Improvements
* Updated InspectorMessage reporting for PyNWB read errors to improve readability [#603](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/603)
* Added support for PyNWB 3.1 and NWB Schema 2.9 [#602](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/602)

# v0.6.3 (March 13, 2025)

### Improvements
* Added check for negative rates in TimeSeries [#423](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/423)
* Added check for ascending spike times in Units table [#575](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/575)
* Added support for PyNWB 3.0 [#557](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/557)
* Added support for Python 3.13 [#564](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/564)

# v0.6.2

### Deprecation
* Remove s3fs dependency, which was causing dependency management issues [#549](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/549)

### Fixes
* Fix wrongly triggered compression check [#552](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/552)
* Fixed URL inspection using the CLI [#559](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/559)

### Improvements
* Added a section for describing the issues with negative timestamps in `TimeSeries` [#545](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/545)
* Use alternate way of generating `TimeSeries` objects to avoid new pynwb error when the shape of the first dimension of
  data does not match the length of timestamps [#556](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/556)


# v0.6.1

### Improvements
* Added support for Numpy 2 and h5py 3.12, and pinned PyNWB to <3.0 temporarily. [#536](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/536)
* Added best practice around not using colons in object names. [#532](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/532)

### Fixes
* Fixed issue where the description check failed if the description was a list. [#535](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/535)


# v0.6.0

### Deprecation
* Support for Python 3.8 has been removed. [#508](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/508)

### Deprecation (API)
* The `inspect_nwb` method has been removed. Please use `inspect_nwbfile` or `inspect_nwbfile_object` instead. [#505](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/505)

### New Features
* Added Zarr support. [#513](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/513)

### Improvements
* Removed the `robust_ros3_read` utility helper. [#506](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/506)
* Simplified the `nwbinspector.testing` configuration framework. [#509](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/509)
* Cleaned old references to non-recent PyNWB and HDMF versions. Current policy is that latest NWB Inspector releases should only support compatibility with latest PyNWB and HDMF. [#510](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/510)
* Swapped setup approach to the modern `pyproject.toml` standard. [#507](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/507)
* Added complete annotation typing and integrated Mypy into pre-commit. [#520](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/520)

### Fixes
* Fixed incorrect error message for OptogeneticStimulusSite. [#524](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/524)
* Fixed detection of Zarr directories for inspection. [#531](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/531)


# v0.5.2

### Deprecation (API)
* The `driver` argument has been removed from `inspect_nwbfile`. Please use `nwbinspector.inspect_dandiset` or `nwbinspector.inspect_dandi_file_path` instead. [#490](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/490)

### Pending Deprecation (API)
* The `stream` and `version_id` arguments have been removed from `nwbinspector.inspect_all`. Please use `nwbinspector.inspect_dandiset` instead. [#490](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/490)

### New Features
* Introduced the `inspect_dandiset` and `inspect_dandi_file_path` API functions to replace the functionality in `nwbinspector --stream`. The new feature uses `remfile` instead of `ros3`. [#490](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/490)

### Fixes
* Fixed import error when using the CLI with `--config dandi`. [#494](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/494)
* Removed unused imports throughout package. [#496](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/496)



# v0.5.0

### Deprecation (API)
* Certain low-level functions have been marked as private (such as the former `nwbinspector.register_checks.auto_parse`) indicating they should not have been imported by downstream users. [#485](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/485)
* Various inappropriate imports from certain submodules have been hard deprecated (e.g., `from nwbinspector.inspector_tools import natsorted`). [#485](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/485)

### Pending Deprecation (API)
* The `inspector_tools`, `register_check`, and `` submodules have been soft deprecated and will be removed in the next major release. [#485](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/485)

### Improvements
* Update util function `is_ascending_series` to discard nan values and add `check_timestamps_without_nans` fun to check if timestamps contain NaN values [#476](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/476)
* Updated the import structure to match modern Python packaging standards. [#485](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/485)



# v0.4.37

### Fixes

* Equivocated timezone handling to target fields when checking for past and future dates. [#471](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/471)



# v0.4.36

### Fixes

* Fixed the suggested rate in `check_regular_timestamps` to be in Hz. [#467](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/467)
* Added a skip for mac sidecar files (._*). [#470](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/470)



# v0.4.35

### Fixes

* Extended `check_session_start_time_future_date` and `check_session_start_time_old_date` to be timezone optional as allowed by PyNWB > 2.6.0 versions. [#452](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/452)

### Improvements

* Exposed progress bar control to `inspect_all` and `run_checks` to allow compatibility with more generic visualizations of inspection progress related to the NWB GUIDED. [#443](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/443)
* Added Python 3.12 support. [#457](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/457)

### Testing

* Pinned action runners to MacOS x64 architecture; removed other deprecated steps of setup and continuous integration testing. [#450](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/450)



# v0.4.34

### Fixes

* Fixed `--modules` flag in `nwbinspector` command line interface to allow for import of additional modules in the command line. This was necessary to be able to register new customized checks to the NWB Inspector. [#446](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/446)

# v0.4.33

### Fixes

* Add safer retrieval of `subject_id` for _in vitro_ protein filtering. [#433](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/433)



# v0.4.32

### Fixes

* Use cached extension namespaces when calling pynwb validate instead of just the core namespace. [#425](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/425)

### Improvements

* Added automatic suppression of certain subject related checks when inspecting files using the "dandi" configuration that have a `subject_id` that starts with the keyphrase "protein"; _e.g._, "proteinCaMPARI3" to indicate the _in vitro_ subject of the experiment is a purified CaMPARI3 protein.



# v0.4.31

### New Checks

* Added `check_rate_is_not_zero` for ensuring non-zero rate value of `TimeSeries` that has more than one frame. [#389](https://github.com/NeurodataWithoutBorders/nwbinspector/issues/389)



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
* Fixed an error with attribute retrieval specific to the `cell_id` of the `IntracellularElectrode` neurodata type that occurred with respect to older versions of PyNWB. [PR #264](https://github.com/NeurodataWithoutBorders/nwbinspector/pull/264)



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
