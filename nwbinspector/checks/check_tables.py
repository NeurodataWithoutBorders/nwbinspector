"""Authors: Cody Baker, Ben Dichter, and Ryan Ly."""
import numpy as np

import pynwb
import hdmf

from ..tools import all_of_type
from ..utils import nwbinspector_check


@nwbinspector_check(severity=3, neurodata_type=pynwb.core.DynamicTable)
def check_empty_tables(nwbfile):
    """Check if DynamicTable is empty."""
    for tab in all_of_type(nwbfile, pynwb.core.DynamicTable):
        if len(tab.id) == 0:
            print("NOTE: '%s' %s has no rows" % (tab.name, type(tab).__name__))
            continue
        if len(tab.id) == 1:
            print("NOTE: '%s' %s has one row" % (tab.name, type(tab).__name__))
            continue


@nwbinspector_check(severity=1, neurodata_type=pynwb.core.DynamicTable)
def check_single_tables(nwbfile):
    """Check if DynamicTable has only a single row; may be better represented by another data type."""
    for tab in all_of_type(nwbfile, pynwb.core.DynamicTable):
        if len(tab.id) == 1:
            print("NOTE: '%s' %s has one row" % (tab.name, type(tab).__name__))
            continue


@nwbinspector_check(severity=1, neurodata_type=pynwb.core.DynamicTable)
def check_column_data_is_not_none(nwbfile):
    """Check column values in DynamicTable to enssure they are not None."""
    for tab in all_of_type(nwbfile, pynwb.core.DynamicTable):
        for col in tab.columns:
            if not isinstance(col, hdmf.common.table.DynamicTableRegion) and col.data is None:
                return f"'{tab.name}' {type(tab).__name__} column {col.name} data is None"
                # continue
                # TODO: think about how to handle this continuable logic in new refactor


# TODO, continue to break this up
@nwbinspector_check(severity=1, neurodata_type=pynwb.core.DynamicTable)
def check_column_table(nwbfile):
    """Check column values in DynamicTable objects"""
    for tab in all_of_type(nwbfile, pynwb.core.DynamicTable):
        for col in tab.columns:
            if isinstance(col, hdmf.common.table.DynamicTableRegion):
                continue

            if col.name.endswith("index"):  # skip index columns
                continue

            if isinstance(col.data, hdmf.backends.hdf5.h5_utils.DatasetOfReferences):  # TODO find a better way?
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
