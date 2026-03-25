Checks by Importance
======================

This section lists the available checks organized by their importance level.

CRITICAL
---------

*  :py:func:`~nwbinspector.checks._behavior.check_spatial_series_dims`
*  :py:func:`~nwbinspector.checks._ecephys.check_electrical_series_dims`
*  :py:func:`~nwbinspector.checks._ecephys.check_ascending_spike_times`
*  :py:func:`~nwbinspector.checks._ecephys.check_units_table_duration`
*  :py:func:`~nwbinspector.checks._general.check_name_slashes`
*  :py:func:`~nwbinspector.checks._image_series.check_image_series_external_file_valid`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_session_start_time_future_date`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_subject_exists`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_subject_age`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_subject_id_exists`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_subject_weight`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_subject_sex`
*  :py:func:`~nwbinspector.checks._ophys.check_roi_response_series_dims`
*  :py:func:`~nwbinspector.checks._tables.check_dynamic_table_region_data_validity`
*  :py:func:`~nwbinspector.checks._tables.check_ids_unique`
*  :py:func:`~nwbinspector.checks._tables.check_time_intervals_duration`
*  :py:func:`~nwbinspector.checks._time_series.check_data_orientation`
*  :py:func:`~nwbinspector.checks._time_series.check_timestamps_match_first_dimension`
*  :py:func:`~nwbinspector.checks._time_series.check_rate_is_not_zero`
*  :py:func:`~nwbinspector.checks._time_series.check_rate_is_positive`

BEST PRACTICE VIOLATION
------------------------

*  :py:func:`~nwbinspector.checks._behavior.check_compass_direction_unit`
*  :py:func:`~nwbinspector.checks._behavior.check_spatial_series_radians_magnitude`
*  :py:func:`~nwbinspector.checks._behavior.check_spatial_series_degrees_magnitude`
*  :py:func:`~nwbinspector.checks._ecephys.check_negative_spike_times`
*  :py:func:`~nwbinspector.checks._ecephys.check_electrical_series_reference_electrodes_table`
*  :py:func:`~nwbinspector.checks._ecephys.check_spike_times_not_in_unobserved_interval`
*  :py:func:`~nwbinspector.checks._ecephys.check_electrical_series_unscaled_data`
*  :py:func:`~nwbinspector.checks._ecephys.check_electrodes_location_allen_ccf`
*  :py:func:`~nwbinspector.checks._icephys.check_intracellular_electrode_cell_id_exists`
*  :py:func:`~nwbinspector.checks._icephys.check_sweeptable_deprecated`
*  :py:func:`~nwbinspector.checks._icephys.check_intracellular_electrode_location_allen_ccf`
*  :py:func:`~nwbinspector.checks._image_series.check_image_series_external_file_relative`
*  :py:func:`~nwbinspector.checks._image_series.check_image_series_data_size`
*  :py:func:`~nwbinspector.checks._image_series.check_image_series_starting_frame_without_external_file`
*  :py:func:`~nwbinspector.checks._images.check_order_of_images_unique`
*  :py:func:`~nwbinspector.checks._images.check_order_of_images_len`
*  :py:func:`~nwbinspector.checks._images.check_index_series_points_to_image`
*  :py:func:`~nwbinspector.checks._nwb_containers.check_large_dataset_compression`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_subject_species_exists`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_subject_species_form`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_session_id_no_slashes`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_subject_id_no_slashes`
*  :py:func:`~nwbinspector.checks._ogen.check_optogenetic_stimulus_site_has_optogenetic_series`
*  :py:func:`~nwbinspector.checks._ophys.check_roi_response_series_link_to_plane_segmentation`
*  :py:func:`~nwbinspector.checks._ophys.check_emission_lambda_in_nm`
*  :py:func:`~nwbinspector.checks._ophys.check_excitation_lambda_in_nm`
*  :py:func:`~nwbinspector.checks._ophys.check_plane_segmentation_image_mask_shape_against_ref_images`
*  :py:func:`~nwbinspector.checks._ophys.check_imaging_plane_location_allen_ccf`
*  :py:func:`~nwbinspector.checks._tables.check_empty_table`
*  :py:func:`~nwbinspector.checks._tables.check_time_interval_time_columns`
*  :py:func:`~nwbinspector.checks._tables.check_time_intervals_stop_after_start`
*  :py:func:`~nwbinspector.checks._tables.check_table_values_for_dict`
*  :py:func:`~nwbinspector.checks._time_series.check_regular_timestamps`
*  :py:func:`~nwbinspector.checks._time_series.check_timestamps_ascending`
*  :py:func:`~nwbinspector.checks._time_series.check_timestamps_without_nans`
*  :py:func:`~nwbinspector.checks._time_series.check_missing_unit`
*  :py:func:`~nwbinspector.checks._time_series.check_resolution`
*  :py:func:`~nwbinspector.checks._time_series.check_time_series_duration`
*  :py:func:`~nwbinspector.checks._time_series.check_time_series_data_is_not_empty`
*  :py:func:`~nwbinspector.checks._time_series.check_rate_not_below_threshold`

BEST PRACTICE SUGGESTION
-------------------------

*  :py:func:`~nwbinspector.checks._general.check_name_colons`
*  :py:func:`~nwbinspector.checks._general.check_description`
*  :py:func:`~nwbinspector.checks._nwb_containers.check_small_dataset_compression`
*  :py:func:`~nwbinspector.checks._nwb_containers.check_empty_string_for_optional_attribute`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_session_start_time_old_date`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_experimenter_exists`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_experimenter_form`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_experiment_description`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_institution`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_keywords`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_doi_publications`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_subject_proper_age_range`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_processing_module_name`
*  :py:func:`~nwbinspector.checks._nwbfile_metadata.check_file_extension`
*  :py:func:`~nwbinspector.checks._tables.check_column_binary_capability`
*  :py:func:`~nwbinspector.checks._tables.check_single_row`
*  :py:func:`~nwbinspector.checks._tables.check_col_not_nan`
*  :py:func:`~nwbinspector.checks._tables.check_table_time_columns_are_not_negative`
*  :py:func:`~nwbinspector.checks._time_series.check_timestamp_of_the_first_sample_is_not_negative`

