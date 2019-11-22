import sys
from pathlib import Path
import pynwb
import numpy as np
import hdmf
import hdmf.backends.hdf5.h5_utils


def main(dir_name):
    data_dir = Path(dir_name)
    if not data_dir.is_dir():
        raise Exception('%s should be a directory' % dir_name)

    dir_files = list(data_dir.glob('*.nwb'))

    for fi, filename in enumerate(dir_files):
        print('%d/%d %s' % (fi + 1, len(dir_files), filename))

        try:
            with pynwb.NWBHDF5IO(str(filename), 'r') as io:
                pynwb.validate(io)
                nwbfile = io.read()
                # inspect NWBFile object
                check_timeseries(nwbfile)
                check_tables(nwbfile)

        except Exception as ex:
            print(ex)
        print()


def check_timeseries(nwbfile):
    """Check dataset values in TimeSeries objects"""
    for ts in all_timeseries(nwbfile):
        if ts.data is None:
            error_code = 'A101'
            print("%s: %s %s data is None" % (error_code, type(ts).__name__, ts.name))
            continue

        uniq = np.unique(ts.data)
        if len(uniq) == 1:
            error_code = 'A101'
            print("%s: '%s' %s data has all values = %s" % (error_code, ts.name, type(ts).__name__, uniq[0]))
        elif np.array_equal(uniq, [0., 1.]):
            error_code = 'A101'
            print("%s: '%s' %s data should be type boolean instead of %s"
                  % (error_code, ts.name, type(ts).__name__, ts.data.dtype))
        elif len(uniq) == 2:
            error_code = 'A101'
            print("%s: '%s' %s data has only unique values %s. Consider storing the data as boolean."
                  % (error_code, ts.name, type(ts).__name__, uniq))
        elif len(uniq) <= 4:
            print("NOTE: '%s' %s data has only unique values %s" % (ts.name, type(ts).__name__, uniq))

        # check whether rate should be used instead of timestamps
        time_tol_decimals = 9
        uniq_diff_ts = np.unique(np.diff(ts.timestamps).round(decimals=time_tol_decimals))
        if len(uniq_diff_ts) == 1:
            error_code = 'A101'
            print("%s: '%s' %s timestamps should use starting_time %f and rate %f"
                  % (error_code, ts.name, type(ts).__name__, ts.timestamps[0], uniq_diff_ts[0]))


def check_tables(nwbfile):
    """Check column values in DynamicTable objects"""
    for tab in all_tables(nwbfile):
        for col in tab.columns:
            if isinstance(col, hdmf.common.table.DynamicTableRegion):
                continue

            if col.data is None:
                error_code = 'A101'
                print("%s: '%s' %s column '%s' data is None" % (error_code, tab.name, type(tab).__name__, col.name))
                continue

            if col.name.endswith('index'):  # skip index columns
                continue

            if isinstance(col.data, hdmf.backends.hdf5.h5_utils.DatasetOfReferences):  # TODO find a better way?
                continue

            uniq = np.unique(col.data)
            # TODO only do this for optional columns
            if len(uniq) == 1:
                error_code = 'A101'
                print("%s: '%s' %s column '%s' data has all values = %s"
                      % (error_code, tab.name, type(tab).__name__, col.name, uniq[0]))
            elif np.array_equal(uniq, [0., 1.]):
                error_code = 'A101'
                print("%s: '%s' %s column '%s' data should be type boolean instead of %s"
                      % (error_code, tab.name, type(tab).__name__, col.name, col.data.dtype))
            elif len(uniq) == 2:
                error_code = 'A101'
                print(("%s: '%s' %s column '%s' data has only unique values %s. Consider storing the data "
                      "as boolean.") % (error_code, tab.name, type(tab).__name__, col.name, uniq))
            elif len(uniq) <= 4:
                print("NOTE: '%s' %s column '%s' data has only unique values %s"
                      % (tab.name, type(tab).__name__, col.name, uniq))


def all_timeseries(nwbfile):
    return all_of_type(nwbfile, pynwb.TimeSeries)


def all_tables(nwbfile):
    return all_of_type(nwbfile, pynwb.core.DynamicTable)


def all_of_type(nwbfile, type):
    for obj in nwbfile.objects.values():
        if isinstance(obj, type):
            yield obj


if __name__ == '__main__':
    """
    Usage: python nwbinspect.py dir_name
    """
    main(sys.argv[1])
