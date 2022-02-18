from uuid import uuid4
from datetime import datetime

from pynwb import NWBFile
from pynwb.file import Subject
import pytest

from nwbinspector import InspectorMessage, Importance
from nwbinspector.checks.nwbfile_metadata import (
    check_experimenter,
    check_experiment_description,
    check_institution,
    check_subject_sex,
    check_subject_exists,
    check_subject_id_exists,
)
from nwbinspector.register_checks import Severity
from nwbinspector.tools import make_minimal_nwbfile


minimal_nwbfile = make_minimal_nwbfile()


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


def test_check_subject_sex():

    nwbfile = NWBFile(session_description="", identifier=str(uuid4()), session_start_time=datetime.now().astimezone())
    nwbfile.subject = Subject(subject_id="001")

    assert check_subject_sex(nwbfile.subject) == InspectorMessage(
        severity=Severity.NO_SEVERITY,
        message="Subject.sex is missing.",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_subject_sex",
        object_type="Subject",
        object_name="subject",
        location="",
    )


def test_check_subject_sex_other_value():
    nwbfile = NWBFile(session_description="", identifier=str(uuid4()), session_start_time=datetime.now().astimezone())
    nwbfile.subject = Subject(subject_id="001", sex="Male")

    assert check_subject_sex(nwbfile.subject) == InspectorMessage(
        severity=Severity.NO_SEVERITY,
        message="Subject.sex should be one of: 'M' (male), 'F' (female), 'O' (other), or 'U' (unknown).",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_subject_sex",
        object_type="Subject",
        object_name="subject",
        location="",
    )


def test_check_subject_exists():
    assert check_subject_exists(minimal_nwbfile) == InspectorMessage(
        severity=Severity.NO_SEVERITY,
        message="Subject is missing.",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_subject_exists",
        object_type="NWBFile",
        object_name="root",
        location="/",
    )


def test_pass_check_subject_exists():
    nwbfile = NWBFile(session_description="", identifier=str(uuid4()), session_start_time=datetime.now().astimezone())
    nwbfile.subject = Subject(subject_id="001", sex="Male")
    assert check_subject_exists(nwbfile) is None


def test_check_subject_id_exists():
    subject = Subject(sex="Male")
    assert check_subject_id_exists(subject) == InspectorMessage(
        severity=Severity.NO_SEVERITY,
        message="subject_id is missing.",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_subject_id_exists",
        object_type="Subject",
        object_name="subject",
        location="/",
    )


def test_pass_check_subject_id_exist():
    subject = Subject(subject_id="001", sex="Male")
    assert check_subject_id_exists(subject) is None


@pytest.mark.skip(reason="TODO")
def test_check_subject_id():
    pass


@pytest.mark.skip(reason="TODO")
def test_check_subject_species():
    pass
