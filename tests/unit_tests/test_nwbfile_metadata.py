from uuid import uuid4
from datetime import datetime

from pynwb import NWBFile
import pytest

from nwbinspector import InspectorMessage, Importance
from nwbinspector.checks.nwbfile_metadata import check_experimenter, check_experiment_description,  check_institution
from nwbinspector.register_checks import Severity


minimal_nwbfile = NWBFile(session_description="", identifier=str(uuid4()), session_start_time=datetime.now().astimezone())

def test_check_experimenter():
    assert check_experimenter(minimal_nwbfile) == InspectorMessage(
        severity=Severity.NO_SEVERITY,
        message="Experimenter is missing.",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_experimenter",
        object_type="NWBFile",
        object_name="root",
        location="/",
    )


def test_check_experiment_description():
    assert check_experiment_description(minimal_nwbfile) == InspectorMessage(
        severity=Severity.NO_SEVERITY,
        message="Experiment description is missing.",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_experiment_description",
        object_type="NWBFile",
        object_name="root",
        location="/",
    )


def test_check_institution():
    assert check_institution(minimal_nwbfile) == InspectorMessage(
        severity=Severity.NO_SEVERITY,
        message="Metadata /general/institution is missing.",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_institution",
        object_type="NWBFile",
        object_name="root",
        location="/",
    )


@pytest.mark.skip(reason="TODO")
def test_check_keywords():
    pass


@pytest.mark.skip(reason="TODO")
def test_check_doi_publications():
    pass


@pytest.mark.skip(reason="TODO")
def test_check_subject_sex():
    pass


@pytest.mark.skip(reason="TODO")
def test_check_subject_id():
    pass


@pytest.mark.skip(reason="TODO")
def test_check_subject_species():
    pass
