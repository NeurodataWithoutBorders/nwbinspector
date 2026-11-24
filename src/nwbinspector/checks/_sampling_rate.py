"""
Checks for implausible sampling rates and time scales.

These checks look for timing errors that make every derived quantity wrong while leaving the file valid: a sampling
period stored as a rate, timestamps written in milliseconds, an ImagingPlane.imaging_rate that disagrees with the
timing of the series that use the plane, and starting times written as absolute Unix times.

Several checks compare an object with the rest of the file (the "session span"), which they reach through
``get_ancestor("NWBFile")``. A per-file summary of every TimeSeries (start, end, length and effective rate) is
computed once and cached, so that the cost on a streamed file is a handful of small reads per series.
"""

import math
from typing import Iterable, Optional

import numpy as np
from pynwb import NWBFile, TimeSeries
from pynwb.ecephys import ElectricalSeries, SpikeEventSeries
from pynwb.icephys import PatchClampSeries
from pynwb.image import ImageSeries
from pynwb.ophys import ImagingPlane, RoiResponseSeries

from .._registration import Importance, InspectorMessage, register_check
from ..utils import get_data_shape

# How many leading timestamps are read to estimate the sampling interval of a timestamped series.
_N_TIMESTAMPS_FOR_RATE = 10_000

# A series whose sampling intervals vary more than this (median absolute deviation over median) is treated as
# event-like, and no rate is inferred from its timestamps.
_MAX_IRREGULARITY = 0.1

# Two rates are taken to agree when they are within this relative tolerance.
_RATE_TOLERANCE = 0.03

# Plausible sampling rates (Hz) for voltage and current recordings.
_EPHYS_RATE_RANGE = (10.0, 1_000_000.0)

# No acquired time series in neurophysiology is sampled faster than this.
_MAX_ANY_RATE = 1_000_000.0

_SECONDS_PER_DAY = 86_400.0


# ---------------------------------------------------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------------------------------------------------


def _rate_from_timestamps(time_series: TimeSeries) -> Optional[float]:
    """Return 1 / (median sampling interval) when the leading timestamps are regular, else None."""
    timestamps = time_series.timestamps
    if timestamps is None:
        return None
    shape = get_data_shape(timestamps)
    if shape is None or shape[0] < 3:
        return None
    head = np.asarray(timestamps[: min(shape[0], _N_TIMESTAMPS_FOR_RATE)], dtype=float)
    head = head[np.isfinite(head)]
    if head.size < 3:
        return None
    intervals = np.diff(head)
    median_interval = float(np.median(intervals))
    if median_interval <= 0:
        return None
    irregularity = float(np.median(np.abs(intervals - median_interval))) / median_interval
    if irregularity > _MAX_IRREGULARITY:
        return None
    return 1.0 / median_interval


def _effective_rate(time_series: TimeSeries) -> Optional[float]:
    """The stated rate, or the rate implied by regular timestamps."""
    rate = getattr(time_series, "rate", None)
    if rate is not None:
        return float(rate) if np.isfinite(rate) and rate > 0 else None
    return _rate_from_timestamps(time_series)


def _n_samples(time_series: TimeSeries) -> Optional[int]:
    """Number of samples, from the data or, for an ImageSeries whose frames are in an external file, the timestamps."""
    n = None
    if time_series.data is not None:
        shape = get_data_shape(time_series.data)
        if shape is not None and len(shape) > 0:
            n = int(shape[0])
    if not n and time_series.timestamps is not None:
        shape = get_data_shape(time_series.timestamps)
        if shape is not None and len(shape) > 0:
            n = int(shape[0])
    return n


def _span(time_series: TimeSeries) -> Optional[tuple[float, float]]:
    """(first, last) sample time of a series, from timestamps or from starting_time, rate and length."""
    n = _n_samples(time_series)
    if time_series.timestamps is not None:
        shape = get_data_shape(time_series.timestamps)
        if shape is None or shape[0] < 2:
            return None
        first, last = float(time_series.timestamps[0]), float(time_series.timestamps[-1])
    elif time_series.rate is not None and time_series.rate > 0 and n is not None and n > 1:
        first = float(time_series.starting_time or 0.0)
        last = first + (n - 1) / float(time_series.rate)
    else:
        return None
    if not (np.isfinite(first) and np.isfinite(last)):
        return None
    return first, last


_SUMMARY_CACHE: dict = {}


def _file_summary(nwbfile: NWBFile) -> dict:
    """Per-file table of every TimeSeries: name, type, length, effective rate and span. Cached per file object."""
    key = id(nwbfile)
    cached = _SUMMARY_CACHE.get(key)
    if cached is not None and cached[0] is nwbfile:
        return cached[1]
    summary = {}
    for neurodata_object in nwbfile.objects.values():
        if not isinstance(neurodata_object, TimeSeries) or isinstance(neurodata_object, SpikeEventSeries):
            continue
        try:
            summary[neurodata_object.object_id] = dict(
                object=neurodata_object,
                n=_n_samples(neurodata_object),
                rate=_effective_rate(neurodata_object),
                span=_span(neurodata_object),
            )
        except Exception:  # an unreadable series should not stop the other checks
            continue
    _SUMMARY_CACHE.clear()  # keep one file at a time
    _SUMMARY_CACHE[key] = (nwbfile, summary)
    return summary


def _reference_end(nwbfile: NWBFile, exclude: TimeSeries) -> Optional[float]:
    """
    The end time of the session as seen by the other series of the file.

    Acquired ElectricalSeries, PatchClampSeries and imaging series with at least 1000 samples are preferred as the
    anchor; otherwise the median end of every other series that has at least ten samples is used, which tolerates one
    or two badly scaled series. Series sampled faster than 1 MHz are left out, since their own time scale is wrong.
    """
    rows = [
        row
        for object_id, row in _file_summary(nwbfile).items()
        if object_id != exclude.object_id
        and row["span"] is not None
        and (row["n"] or 0) >= 10
        and (row["rate"] is None or row["rate"] <= _MAX_ANY_RATE)  # a series on the wrong time scale is no reference
    ]
    anchors = [
        row["span"][1]
        for row in rows
        if (row["n"] or 0) >= 1000
        and (isinstance(row["object"], (ElectricalSeries, PatchClampSeries)) or hasattr(row["object"], "imaging_plane"))
    ]
    ends = anchors or [row["span"][1] for row in rows]
    ends = [end for end in ends if end > 0]
    if not ends:
        return None
    return float(np.median(ends))


def _related_rates(time_series: TimeSeries, nwbfile: Optional[NWBFile]) -> list[tuple[str, float]]:
    """Rates of 1 Hz or more stated elsewhere in the file: other series and imaging planes."""
    related = []
    if nwbfile is not None:
        for object_id, row in _file_summary(nwbfile).items():
            if object_id != time_series.object_id and row["rate"] is not None and row["rate"] >= 1.0:
                related.append((row["object"].name, row["rate"]))
        for imaging_plane in nwbfile.imaging_planes.values():
            rate = imaging_plane.imaging_rate
            if rate is not None and np.isfinite(rate) and rate >= 1.0:
                related.append((f"{imaging_plane.name}.imaging_rate", float(rate)))
    return related


def _close(a: float, b: float, tolerance: float = _RATE_TOLERANCE) -> bool:
    return abs(a - b) <= tolerance * max(abs(a), abs(b))


def _format_duration(seconds: float) -> str:
    if seconds >= 2 * _SECONDS_PER_DAY:
        return f"{seconds / _SECONDS_PER_DAY:.1f} days"
    if seconds >= 7200:
        return f"{seconds / 3600:.1f} hours"
    return f"{seconds:.1f} s"


def _fits(duration: float, reference: float, low: float = 0.1, high: float = 1.5) -> bool:
    return low * reference <= duration <= high * reference


# ---------------------------------------------------------------------------------------------------------------------
# 1. A sampling period stored as a rate
# ---------------------------------------------------------------------------------------------------------------------


@register_check(importance=Importance.CRITICAL, neurodata_type=TimeSeries)
def check_rate_is_not_sampling_period(
    time_series: TimeSeries,
) -> Optional[InspectorMessage]:
    """
    Check that a rate below 1 Hz is not a sampling period (or a rate in kHz) entered in place of a rate in Hz.

    A rate below 1 Hz is reported only when one of two pieces of evidence points to a mistake:

    1. its reciprocal equals (within 3%) a rate of 1 Hz or more stated elsewhere in the file, for example the
       imaging rate of the plane the series was recorded with; or
    2. read at the stated rate, the series would last more than ten times as long as the rest of the file, while
       read with the reciprocal (or with the rate taken as kHz) it fits inside the rest of the file.

    Slow signals such as temperature or trial-level series with a genuine low rate pass both tests, because their
    reciprocal matches nothing and their stated duration agrees with the session.
    """
    rate = getattr(time_series, "rate", None)
    if rate is None or not np.isfinite(rate) or not (0 < rate < 1):
        return None
    n = _n_samples(time_series)
    if n is None or n < 10:
        return None

    nwbfile = time_series.get_ancestor("NWBFile")
    inverse = 1.0 / rate

    for name, other_rate in _related_rates(time_series, nwbfile):
        if _close(inverse, other_rate):
            return InspectorMessage(
                message=(
                    f"'{time_series.name}' has a rate of {rate:g} Hz, whose reciprocal ({inverse:.4g} Hz) matches the "
                    f"rate of '{name}' ({other_rate:.4g} Hz). The sampling period appears to have been stored in "
                    f"place of the rate; the rate should probably be {inverse:.6g} Hz."
                )
            )

    if nwbfile is None:
        return None
    reference = _reference_end(nwbfile=nwbfile, exclude=time_series)
    if reference is None:
        return None
    start = float(time_series.starting_time or 0.0)
    stated_end = start + n / rate
    if stated_end <= 10 * reference:
        return None
    for label, alternative_rate in (
        ("the reciprocal of the rate", inverse),
        ("the rate read as kHz", rate * 1000),
    ):
        alternative_end = start + n / alternative_rate
        if _fits(alternative_end, reference):
            return InspectorMessage(
                message=(
                    f"At its stated rate of {rate:g} Hz, '{time_series.name}' ({n} samples) would last "
                    f"{_format_duration(n / rate)}, while the other series of the file end by about "
                    f"{_format_duration(reference)}. With {label} ({alternative_rate:.6g} Hz) it would last "
                    f"{_format_duration(n / alternative_rate)}, which fits the session. The rate appears to be "
                    "stored in the wrong unit or as a period."
                )
            )
    return None


@register_check(importance=Importance.CRITICAL, neurodata_type=ImagingPlane)
def check_imaging_rate_is_not_sampling_period(
    imaging_plane: ImagingPlane,
) -> Optional[InspectorMessage]:
    """Check that an imaging_rate below 1 Hz is not the reciprocal of the rate of a series recorded with the plane."""
    imaging_rate = imaging_plane.imaging_rate
    if imaging_rate is None or not np.isfinite(imaging_rate) or not (0 < imaging_rate < 1):
        return None
    nwbfile = imaging_plane.get_ancestor("NWBFile")
    if nwbfile is None:
        return None
    plane_name = imaging_plane.name
    for row in _file_summary(nwbfile).values():
        series = row["object"]
        if getattr(series, "imaging_plane", None) is imaging_plane and row["rate"] is not None:
            if _close(1.0 / imaging_rate, row["rate"]):
                return InspectorMessage(
                    message=(
                        f"The imaging_rate of '{plane_name}' is {imaging_rate:g} Hz, the reciprocal of the "
                        f"{row['rate']:.4g} Hz rate of '{series.name}', which uses this plane. The sampling period "
                        "appears to have been stored in place of the rate."
                    )
                )
    return None


# ---------------------------------------------------------------------------------------------------------------------
# 2. Timestamps on the wrong time scale
# ---------------------------------------------------------------------------------------------------------------------


@register_check(importance=Importance.CRITICAL, neurodata_type=TimeSeries)
def check_timestamps_time_scale(time_series: TimeSeries) -> Optional[InspectorMessage]:
    """
    Check that timestamps are in seconds, by comparing their extent with the rest of the file.

    Reported when the last timestamp is more than ten times the end of the other series and dividing by 1e3, 1e6 or
    1e9 brings it inside the session (milliseconds, microseconds or nanoseconds), or when a long regular series ends before 1% of the session and multiplying
    by 1000 brings it inside (thousands of seconds, or a rate written as kHz).
    """
    if time_series.timestamps is None:
        return None
    n = _n_samples(time_series)
    span = _span(time_series)
    nwbfile = time_series.get_ancestor("NWBFile")
    if n is None or n < 10 or span is None or nwbfile is None:
        return None
    reference = _reference_end(nwbfile=nwbfile, exclude=time_series)
    if reference is None:
        return None
    first, last = span
    for factor, unit in ((1e3, "milliseconds"), (1e6, "microseconds"), (1e9, "nanoseconds")):
        if not (last > 10 * reference and _fits(last / factor, reference, low=0.02, high=1.5)):
            continue
        head = np.asarray(time_series.timestamps[: min(n, 1000)], dtype=float)
        if factor == 1e3 and np.all(head == np.round(head)):
            diagnosis = "they are all whole numbers, so they may be frame or sample indices, or milliseconds."
        else:
            diagnosis = f"they appear to be in {unit}."
        return InspectorMessage(
            message=(
                f"The timestamps of '{time_series.name}' run to {last:.6g}, more than ten times the end of the other "
                f"series of the file (about {reference:.6g} s). Divided by {factor:.0e} they would end at "
                f"{last / factor:.6g} s; {diagnosis} NWB requires timestamps in seconds."
            )
        )
    if (
        n >= 1000
        and 0 < last < reference / 100
        and _rate_from_timestamps(time_series) is not None
        and _fits(last * 1000, reference, low=0.1, high=1.5)
    ):
        implied = _rate_from_timestamps(time_series)
        return InspectorMessage(
            message=(
                f"'{time_series.name}' holds {n} regularly spaced samples whose timestamps end at {last:.6g} s "
                f"(an implied rate of {implied:.4g} Hz), while the other series of the file run to about "
                f"{reference:.6g} s. Multiplied by 1000 they would cover the session; the timestamps appear to be in "
                "thousands of seconds."
            )
        )
    return None


# ---------------------------------------------------------------------------------------------------------------------
# 3. Rate outside the plausible range for the data type
# ---------------------------------------------------------------------------------------------------------------------


@register_check(importance=Importance.CRITICAL, neurodata_type=TimeSeries)
def check_rate_in_plausible_range(
    time_series: TimeSeries,
) -> Optional[InspectorMessage]:
    """
    Check that the sampling rate (stated, or implied by regular timestamps) is plausible for the type of data.

    Voltage and current recordings (ElectricalSeries, PatchClampSeries) must be sampled between 10 Hz and 1 MHz.
    Any other series is reported only above 1 MHz. No lower bound is applied to other types, because behavioral,
    environmental and trial-level series can legitimately be sampled very slowly.
    """
    if isinstance(time_series, SpikeEventSeries):
        return None
    n = _n_samples(time_series)
    if n is None or n < 10:
        return None
    rate = _effective_rate(time_series)
    if rate is None:
        return None
    source = "stated" if getattr(time_series, "rate", None) is not None else "implied by its timestamps"

    if isinstance(time_series, (ElectricalSeries, PatchClampSeries)):
        low, high = _EPHYS_RATE_RANGE
        if not (low <= rate <= high):
            hint = ""
            if low <= rate * 1000 <= high:
                hint = " The rate may have been given in kHz."
            elif low <= 1 / rate <= high:
                hint = f" Its reciprocal ({1 / rate:.6g} Hz) is plausible; the period may have been stored."
            return InspectorMessage(
                message=(
                    f"'{time_series.name}' is a {type(time_series).__name__} with a sampling rate of {rate:.6g} Hz "
                    f"({source}), outside the {low:g} Hz to {high:g} Hz range of electrophysiology recordings.{hint}"
                )
            )
        return None

    if rate > _MAX_ANY_RATE:
        return InspectorMessage(
            message=(
                f"'{time_series.name}' has a sampling rate of {rate:.6g} Hz ({source}), above 1 MHz. If its "
                "timestamps are in seconds this is implausible; they may be in another unit."
            )
        )
    return None


# ---------------------------------------------------------------------------------------------------------------------
# 4. ImagingPlane.imaging_rate against the series that use the plane
# ---------------------------------------------------------------------------------------------------------------------


def _imaging_rate_message(imaging_plane: ImagingPlane, time_series: TimeSeries) -> Optional[InspectorMessage]:
    imaging_rate = imaging_plane.imaging_rate
    if imaging_rate is None or not np.isfinite(imaging_rate) or imaging_rate <= 0:
        return None
    series_rate = _effective_rate(time_series)
    if series_rate is None:
        return None
    ratio = imaging_rate / series_rate
    if 1 / 1.1 <= ratio <= 1.1:
        return None
    source = "stated" if time_series.rate is not None else "implied by its timestamps"
    hint = ""
    if _close(imaging_rate * series_rate, 1.0):
        hint = " The two are reciprocals, so one of them is probably a sampling period."
    elif 1.5 < ratio <= 16 and abs(ratio - round(ratio)) < 0.1:
        hint = (
            f" The ratio is close to {round(ratio)}, which would fit a volume of {round(ratio)} planes whose frame "
            "rate was stored on the plane; imaging_rate should then be the per-plane rate."
        )
    return InspectorMessage(
        message=(
            f"The imaging_rate of '{imaging_plane.name}' ({imaging_rate:.6g} Hz) disagrees with the rate of "
            f"'{time_series.name}' ({series_rate:.6g} Hz, {source}).{hint}"
        )
    )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=ImageSeries)
def check_imaging_rate_matches_series_rate(
    image_series: ImageSeries,
) -> Optional[InspectorMessage]:
    """
    Check that the imaging_rate of the plane agrees (within 10%) with the rate of the series recorded with it.

    The rate of the series is its stated rate or the rate implied by regular timestamps. A plane with a missing or NaN
    imaging_rate is not reported, since the schema prefers the rate on the series.
    """
    imaging_plane = getattr(image_series, "imaging_plane", None)
    if imaging_plane is None:
        return None
    return _imaging_rate_message(imaging_plane=imaging_plane, time_series=image_series)


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=RoiResponseSeries)
def check_imaging_rate_matches_roi_response_rate(
    roi_response_series: RoiResponseSeries,
) -> Optional[InspectorMessage]:
    """
    Check that the imaging_rate of the plane agrees (within 10%) with the rate of the ROI traces segmented from it.

    This covers processed-only files, which have no imaging series. When an ImageSeries of the file uses the same
    plane, that series is checked instead and the traces are not reported again.
    """
    rois = getattr(roi_response_series, "rois", None)
    plane_segmentation = getattr(rois, "table", None)
    imaging_plane = getattr(plane_segmentation, "imaging_plane", None)
    if imaging_plane is None:
        return None
    nwbfile = roi_response_series.get_ancestor("NWBFile")
    if nwbfile is not None:
        for row in _file_summary(nwbfile).values():
            if getattr(row["object"], "imaging_plane", None) is imaging_plane:
                return None
    return _imaging_rate_message(imaging_plane=imaging_plane, time_series=roi_response_series)


# ---------------------------------------------------------------------------------------------------------------------
# 5. Series with the same number of samples but different durations
# ---------------------------------------------------------------------------------------------------------------------


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=NWBFile)
def check_equal_length_series_have_equal_duration(
    nwbfile: NWBFile,
) -> Optional[Iterable[InspectorMessage]]:
    """
    Check that series with exactly the same number of samples (at least 100) span the same duration.

    Two series that share a sample count were almost always sampled on the same clock (photometry and the camera
    frames it was triggered by, or position and imaging frames). If one of them states a rate that gives a duration
    more than 10% different from the other's, one of the two timings is wrong. Only regularly sampled series without
    long pauses are compared, since a stimulus whose frames are shown in several blocks has a span that depends on
    the schedule.
    """
    by_length: dict[int, list] = {}
    for row in _file_summary(nwbfile).values():
        if row["n"] is not None and row["n"] >= 100 and row["span"] is not None and row["rate"] is not None:
            duration = row["span"][1] - row["span"][0]
            gapless = duration <= 1.1 * (row["n"] - 1) / row["rate"]  # timestamps without long pauses
            if duration > 0 and gapless:
                by_length.setdefault(row["n"], []).append((row["object"], duration))
    messages = []
    for n, rows in by_length.items():
        if len(rows) < 2:
            continue
        rows.sort(key=lambda row: row[1])
        (short, short_duration), (long, long_duration) = rows[0], rows[-1]
        ratio = long_duration / short_duration
        if ratio > 1.1:
            hint = ""
            for factor, unit in (
                (1e9, "nanoseconds"),
                (1e6, "microseconds"),
                (1e3, "milliseconds"),
            ):
                if _close(ratio, factor, tolerance=0.05):
                    hint = f" The ratio is close to {factor:.0e}, so the timestamps of '{long.name}' may be in {unit}."
                    break
            messages.append(
                InspectorMessage(
                    message=(
                        f"'{short.name}' and '{long.name}' both hold {n} samples, but span {short_duration:.6g} s and "
                        f"{long_duration:.6g} s (a ratio of {long_duration / short_duration:.3g}). Series of equal "
                        "length usually share a clock; check the rate or timestamps of each." + hint
                    )
                )
            )
    return messages or None


# ---------------------------------------------------------------------------------------------------------------------
# 6. starting_time holding a Unix time
# ---------------------------------------------------------------------------------------------------------------------


@register_check(importance=Importance.CRITICAL, neurodata_type=TimeSeries)
def check_starting_time_is_not_absolute(
    time_series: TimeSeries,
) -> Optional[InspectorMessage]:
    """
    Check that starting_time (or the first timestamp) is relative to the session, not an absolute Unix time.

    Reported when the first sample time is more than about three years and lies within a day of the Unix time of
    timestamps_reference_time (which defaults to session_start_time). A file whose timestamps_reference_time is the
    Unix epoch may legitimately store Unix times, and is not reported.
    """
    span = _span(time_series)
    if span is not None:
        first = span[0]
    elif time_series.starting_time is not None:
        first = float(time_series.starting_time)
    else:
        return None
    if not np.isfinite(first) or first < 1e8:
        return None
    nwbfile = time_series.get_ancestor("NWBFile")
    if nwbfile is None:
        return None
    for reference_name in ("timestamps_reference_time",):
        reference = getattr(nwbfile, reference_name, None) or nwbfile.session_start_time
        if reference is not None and abs(first - reference.timestamp()) < _SECONDS_PER_DAY:
            return InspectorMessage(
                message=(
                    f"The first sample of '{time_series.name}' is at {first:.10g} s, which is the Unix time of "
                    f"{reference_name} ({reference.isoformat()}) give or take a day. starting_time and timestamps must "
                    f"be in seconds relative to {reference_name}; the first sample is probably near 0 s."
                )
            )
    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeSeries)
def check_starting_time_is_finite(
    time_series: TimeSeries,
) -> Optional[InspectorMessage]:
    """Check that a series timed by starting_time and rate has a finite starting_time."""
    if time_series.timestamps is not None or time_series.starting_time is None:
        return None
    if math.isfinite(time_series.starting_time):
        return None
    return InspectorMessage(
        message=(
            f"'{time_series.name}' has a starting_time of {time_series.starting_time}, so the time of its samples "
            "relative to the session is unknown."
        )
    )


# ---------------------------------------------------------------------------------------------------------------------
# 8. A series that runs far past the rest of the file, with no specific diagnosis
# ---------------------------------------------------------------------------------------------------------------------


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=TimeSeries)
def check_series_ends_within_session(
    time_series: TimeSeries,
) -> Optional[InspectorMessage]:
    """
    Check that a series does not run far past the end of the other series of the file.

    Reported when the last sample is more than ten times, and more than an hour, past the end of the rest of the file.
    This catches a wrong rate that is not a sampling period or a factor of 1000 (for example 1 Hz stated for data at
    50 Hz). Series that the more specific checks above already explain are not reported again. This is a suggestion
    rather than a violation, since a long continuous recording beside short imaging runs can be legitimate, and the
    check cannot tell which side is wrong.
    """
    span = _span(time_series)
    n = _n_samples(time_series)
    nwbfile = time_series.get_ancestor("NWBFile")
    if span is None or n is None or n < 10 or nwbfile is None:
        return None
    reference = _reference_end(nwbfile=nwbfile, exclude=time_series)
    if reference is None:
        return None
    last = span[1]
    if last <= 10 * reference or last - reference <= 3600:
        return None
    for specific_check in (
        check_rate_is_not_sampling_period,
        check_timestamps_time_scale,
    ):
        if specific_check(time_series) is not None:
            return None
    if not np.isfinite(last) or last > 1e8:  # a Unix time is reported by check_starting_time_is_not_absolute
        return None
    rate = _effective_rate(time_series)
    rate_text = f" at {rate:.6g} Hz" if rate is not None else ""
    return InspectorMessage(
        message=(
            f"'{time_series.name}' ({n} samples{rate_text}) runs to {_format_duration(last)}, while the other series "
            f"of the file end by about {_format_duration(reference)}. Either its rate or timestamps are wrong, or "
            "those of the other series are."
        )
    )
