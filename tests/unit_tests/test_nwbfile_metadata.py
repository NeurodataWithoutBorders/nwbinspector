from uuid import uuid4
from datetime import datetime

from pynwb import NWBFile
import pytest

from nwbinspector import check_experimenter, InspectorMessage, Importance
from nwbinspector.register_checks import Severity


def test_check_experimenter():
    assert check_experimenter(
        nwbfile=NWBFile(session_description="", identifier=str(uuid4()), session_start_time=datetime.now().astimezone())
    ) == InspectorMessage(
        severity=Severity.NO_SEVERITY,
        message="Experimenter metadata is missing!",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_experimenter",
        object_type="NWBFile",
        object_name="root",
        location="/",
    )


@pytest.mark.skip(reason="TODO")
def test_check_experiment_description():
    pass


@pytest.mark.skip(reason="TODO")
def test_check_institution():
    pass


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
