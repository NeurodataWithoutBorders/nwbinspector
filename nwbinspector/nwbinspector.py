"""Cody Baker, Ben Dichter, and Ryan Ly."""
import argparse
import hdmf
import importlib
import numpy as np
import pathlib
import pynwb

import hdmf.backends.hdf5.h5_utils

from .inspect_nwb import inspect_nwb


def main():
    parser = argparse.ArgumentParser("python test.py [options]")
    parser.add_argument(
        "-m",
        "--modules",
        nargs="*",
        dest="modules",
        help="modules to import prior to reading the file(s)",
    )
    parser.add_argument(
        "path", help="path to an NWB file or directory containing NWB files"
    )
    parser.set_defaults(modules=[])
    args = parser.parse_args()

    in_path = pathlib.Path(args.path)
    if in_path.is_dir():
        files = list(in_path.glob("*.nwb"))
    elif in_path.is_file():
        files = [in_path]
    else:
        raise ValueError("%s should be a directory or an NWB file" % in_path)

    for module in args.modules:
        importlib.import_module(module)

    num_invalid_files = 0
    num_exceptions = 0
    for fi, filename in enumerate(files):
        print("%d/%d %s" % (fi + 1, len(files), filename))

        try:
            with pynwb.NWBHDF5IO(str(filename), "r", load_namespaces=True) as io:
                errors = pynwb.validate(io)
                if errors:
                    for e in errors:
                        print("Validator Error:", e)
                    num_invalid_files += 1
                else:
                    print("Validation OK!")

                nwbfile = io.read()
                # TODO, pass optional arguments from cmd line to inspect_nwb
                check_results = inspect_nwb(nwbfile=nwbfile)
                print(check_results)
        except Exception as ex:
            num_exceptions += 1
            print("ERROR:", ex)

    if num_invalid_files:
        print("%d/%d files are invalid." % (num_exceptions, num_invalid_files))
    if num_exceptions:
        print("%d/%d files had errors." % (num_exceptions, num_exceptions))


def check_timeseries(nwbfile):
    """Check dataset values in TimeSeries objects"""
    for ts in all_of_type(nwbfile, pynwb.TimeSeries):
        if ts.data is None:
            # exception to the rule: ImageSeries objects are allowed to have no data
            if not isinstance(ts, pynwb.image.ImageSeries):
                error_code = "A101"
                print(
                    "- %s: '%s' %s data is None"
                    % (error_code, ts.name, type(ts).__name__)
                )
            else:
                if ts.external_file is None:
                    error_code = "A101"
                    print(
                        "- %s: '%s' %s data is None and external_file is None"
                        % (error_code, ts.name, type(ts).__name__)
                    )
            continue

        if check_dataset_size(ts, "data"):
            check_data_uniqueness(ts)

        if check_dataset_size(ts, "timestamps"):
            check_regular_timestamps(ts)

        if (
            not (np.isnan(ts.resolution) or ts.resolution == -1.0)
            and ts.resolution <= 0
        ):
            error_code = "A101"
            print(
                "- %s: '%s' %s data attribute 'resolution' should use -1.0 or NaN for unknown instead of %f"
                % (error_code, ts.name, type(ts).__name__, ts.resolution)
            )

        if not ts.unit:
            error_code = "A101"
            print(
                "- %s: '%s' %s data is missing text for attribute 'unit'"
                % (error_code, ts.name, type(ts).__name__)
            )

        # check for correct data orientation
        if ts.data is not None and len(ts.data.shape) > 1:
            if ts.timestamps is not None:
                if not (len(ts.data) == len(ts.timestamps)):
                    error_code = "A101"
                    print(
                        "- %s: '%s' %s data orientation appears to be incorrect. \n    The length of the first "
                        "dimension of data does not match the length of timestamps."
                        % (error_code, ts.name, type(ts).__name__)
                    )
            else:
                if max(ts.data.shape[1:]) > ts.data.shape[0]:
                    error_code = "A101"
                    print(
                        "- %s: '%s' %s data orientation appears to be incorrect. \n    Time should be in the first "
                        "dimension, and is usually the longest dimension. Here, another dimension is longer. This is "
                        "possibly correct, but usually indicates that the data is in the wrong orientation."
                        % (error_code, ts.name, type(ts).__name__)
                    )


def check_data_uniqueness(ts):
    """Check whether data of a timeseries has few unique values and can be stored in a better way."""
    uniq = np.unique(ts.data)
    if len(uniq) == 1:
        error_code = "A101"
        print(
            "- %s: '%s' %s data has all values = %s"
            % (error_code, ts.name, type(ts).__name__, uniq[0])
        )
    elif np.array_equal(uniq, [0.0, 1.0]):
        if ts.data.dtype != bool and type(ts) is pynwb.TimeSeries:
            # if a base TimeSeries object has 0/1 data but is not using booleans
            # note that this tests only base TimeSeries objects. TimeSeries subclasses may require numeric/int/etc.
            error_code = "A101"
            print(
                "- %s: '%s' %s data only contains values 0 and 1. Consider changing to type boolean instead of %s"
                % (error_code, ts.name, type(ts).__name__, ts.data.dtype)
            )
    elif len(uniq) == 2:
        print(
            "- NOTE: '%s' %s data has only 2 unique values: %s. Consider storing the data as boolean."
            % (ts.name, type(ts).__name__, uniq)
        )
    elif len(uniq) <= 4:
        print(
            "- NOTE: '%s' %s data has only unique values %s"
            % (ts.name, type(ts).__name__, uniq)
        )


def check_regular_timestamps(ts):
    """Check whether rate should be used instead of timestamps."""
    time_tol_decimals = 9
    uniq_diff_ts = np.unique(np.diff(ts.timestamps).round(decimals=time_tol_decimals))
    if len(uniq_diff_ts) == 1:
        error_code = "A101"
        print(
            "- %s: '%s' %s has a constant sampling rate. Consider using starting_time %f and rate %f instead "
            "of using the timestamps array."
            % (
                error_code,
                ts.name,
                type(ts).__name__,
                ts.timestamps[0],
                uniq_diff_ts[0],
            )
        )


def check_tables(nwbfile):
    """Check column values in DynamicTable objects"""
    for tab in all_of_type(nwbfile, pynwb.core.DynamicTable):
        if len(tab.id) == 0:
            print("NOTE: '%s' %s has no rows" % (tab.name, type(tab).__name__))
            continue
        if len(tab.id) == 1:
            print("NOTE: '%s' %s has one row" % (tab.name, type(tab).__name__))
            continue

        for col in tab.columns:
            if isinstance(col, hdmf.common.table.DynamicTableRegion):
                continue

            if col.data is None:
                error_code = "A101"
                print(
                    "- %s: '%s' %s column '%s' data is None"
                    % (error_code, tab.name, type(tab).__name__, col.name)
                )
                continue

            if col.name.endswith("index"):  # skip index columns
                continue

            if isinstance(
                col.data, hdmf.backends.hdf5.h5_utils.DatasetOfReferences
            ):  # TODO find a better way?
                continue

            uniq = np.unique(col.data)
            # TODO only do this for optional columns
            if len(uniq) == 1:
                error_code = "A101"
                print(
                    "- %s: '%s' %s column '%s' data has all values = %s"
                    % (error_code, tab.name, type(tab).__name__, col.name, uniq[0])
                )
            elif np.array_equal(uniq, [0.0, 1.0]):
                if col.data.dtype.type != np.bool_:
                    error_code = "A101"
                    print(
                        "- %s: '%s' %s column '%s' data should be type boolean instead of %s"
                        % (
                            error_code,
                            tab.name,
                            type(tab).__name__,
                            col.name,
                            col.data.dtype,
                        )
                    )
            elif len(uniq) == 2:
                error_code = "A101"
                print(
                    (
                        "- %s: '%s' %s column '%s' data has only unique values %s. Consider storing the data "
                        "as boolean."
                    )
                    % (error_code, tab.name, type(tab).__name__, col.name, uniq)
                )


def check_icephys(nwbfile):
    for elec in all_of_type(nwbfile, pynwb.icephys.IntracellularElectrode):
        if not elec.description:
            error_code = "A101"
            print(
                "- %s: '%s' %s is missing text for attribute 'description'"
                % (error_code, elec.name, type(elec).__name__)
            )
        if not elec.filtering:
            error_code = "A101"
            print(
                "- %s: '%s' %s is missing text for attribute 'filtering'"
                % (error_code, elec.name, type(elec).__name__)
            )
        if not elec.location:
            error_code = "A101"
            print(
                "- %s: '%s' %s is missing text for attribute 'location'"
                % (error_code, elec.name, type(elec).__name__)
            )


def check_opto(nwbfile):
    opto_sites = list(all_of_type(nwbfile, pynwb.ogen.OptogeneticStimulusSite))
    opto_series = list(all_of_type(nwbfile, pynwb.ogen.OptogeneticSeries))
    for site in opto_sites:
        if not site.description:
            error_code = "A101"
            print(
                "%s: '%s' %s is missing text for attribute 'description'"
                % (error_code, site.name, type(site).__name__)
            )
        if not site.location:
            error_code = "A101"
            print(
                "%s: '%s' %s is missing text for attribute 'location'"
                % (error_code, site.name, type(site).__name__)
            )
    if opto_sites and not opto_series:
        error_code = "A101"
        print(
            "%s: OptogeneticStimulusSite object(s) exists without an OptogeneticSeries"
            % error_code
        )


def check_ecephys(nwbfile):
    # unit spike times should not be negative
    pass


def all_of_type(nwbfile, type):
    for obj in nwbfile.objects.values():
        if isinstance(obj, type):
            yield obj


if __name__ == "__main__":
    """
    Usage: python nwbinspector.py dir_name
    """
    main()
