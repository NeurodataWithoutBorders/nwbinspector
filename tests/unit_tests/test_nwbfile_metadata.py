from uuid import uuid4
from datetime import datetime, timezone

from pynwb import NWBFile, ProcessingModule
from pynwb.file import Subject

from nwbinspector import (
    InspectorMessage,
    Importance,
    check_experimenter,
    check_experiment_description,
    check_institution,
    check_keywords,
    check_doi_publications,
    check_subject_exists,
    check_subject_id_exists,
    check_subject_sex,
    check_subject_age,
    check_subject_species_exists,
    check_subject_species_latin_binomial,
    check_processing_module_name,
    check_session_start_time_old_date,
    check_session_start_time_future_date,
    PROCESSING_MODULE_CONFIG,
)
from nwbinspector.tools import make_minimal_nwbfile


minimal_nwbfile = make_minimal_nwbfile()


def test_check_session_start_time_old_date_pass():
    assert check_session_start_time_old_date(minimal_nwbfile) is None


def test_check_session_start_time_old_date_fail():
    nwbfile = NWBFile(
        session_description="",
        identifier=str(uuid4()),
        session_start_time=datetime(1970, 1, 1, 0, 0, 0, 0, timezone.utc),
    )
    assert check_session_start_time_old_date(nwbfile) == InspectorMessage(
        message="The session_start_time (1970-01-01 00:00:00+00:00) may not be set to the true date of the recording.",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_session_start_time_old_date",
        object_type="NWBFile",
        object_name="root",
        location="/",
    )


def test_check_session_start_time_future_date_pass():
    nwbfile = NWBFile(session_description="", identifier=str(uuid4()), session_start_time=datetime(2010, 1, 1))
    assert check_session_start_time_future_date(nwbfile) is None


def test_check_session_start_time_future_date_fail():
    nwbfile = NWBFile(
        session_description="",
        identifier=str(uuid4()),
        session_start_time=datetime(2030, 1, 1, 0, 0, 0, 0, timezone.utc),
    )
    assert check_session_start_time_future_date(nwbfile) == InspectorMessage(
        message="The session_start_time (2030-01-01 00:00:00+00:00) is set to a future date and time.",
        importance=Importance.CRITICAL,
        check_function_name="check_session_start_time_future_date",
        object_type="NWBFile",
        object_name="root",
        location="/",
    )


def test_check_experimenter_pass():
    nwbfile = NWBFile(
        session_description="",
        identifier=str(uuid4()),
        session_start_time=datetime.now().astimezone(),
        experimenter=["Last, First"],
    )
    assert check_experimenter(nwbfile) is None


def test_check_experimenter_bytestring_pass():
    nwbfile = NWBFile(
        session_description="",
        identifier=str(uuid4()),
        session_start_time=datetime.now().astimezone(),
        experimenter=[b"Last, First"],
    )
    assert check_experimenter(nwbfile) is None


def test_check_experimenter_fail():
    assert check_experimenter(minimal_nwbfile) == InspectorMessage(
        message="Experimenter is missing.",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_experimenter",
        object_type="NWBFile",
        object_name="root",
        location="/",
    )


def test_check_experiment_description():
    assert check_experiment_description(minimal_nwbfile) == InspectorMessage(
        message="Experiment description is missing.",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_experiment_description",
        object_type="NWBFile",
        object_name="root",
        location="/",
    )


def test_check_institution():
    assert check_institution(minimal_nwbfile) == InspectorMessage(
        message="Metadata /general/institution is missing.",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_institution",
        object_type="NWBFile",
        object_name="root",
        location="/",
    )


def test_check_keywords_pass():
    nwbfile = NWBFile(
        session_description="",
        identifier=str(uuid4()),
        session_start_time=datetime.now().astimezone(),
        keywords=["foo", "bar"],
    )
    assert check_keywords(nwbfile) is None


def test_check_keywords_fail():
    assert check_keywords(minimal_nwbfile) == InspectorMessage(
        message="Metadata /general/keywords is missing.",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_keywords",
        object_type="NWBFile",
        object_name="root",
        location="/",
    )


def test_check_doi_publications_pass():
    nwbfile = NWBFile(
        session_description="",
        identifier=str(uuid4()),
        session_start_time=datetime.now().astimezone(),
        related_publications=["doi:", "http://dx.doi.org/", "https://doi.org/"],
    )
    assert check_doi_publications(nwbfile) is None


def test_check_doi_publications_bytestring_pass():
    nwbfile = NWBFile(
        session_description="",
        identifier=str(uuid4()),
        session_start_time=datetime.now().astimezone(),
        related_publications=[b"doi:", b"http://dx.doi.org/", b"https://doi.org/"],
    )
    assert check_doi_publications(nwbfile) is None


def test_check_doi_publications_fail():
    nwbfile = NWBFile(
        session_description="",
        identifier=str(uuid4()),
        session_start_time=datetime.now().astimezone(),
        related_publications=["wrong"],
    )
    assert check_doi_publications(nwbfile) == [
        InspectorMessage(
            message=(
                "Metadata /general/related_publications 'wrong' does not start with 'doi: ###' and is not an external "
                "'doi' link."
            ),
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            check_function_name="check_doi_publications",
            object_type="NWBFile",
            object_name="root",
            location="/",
        )
    ]


def test_check_doi_publications_multiple_fail():
    nwbfile = NWBFile(
        session_description="",
        identifier=str(uuid4()),
        session_start_time=datetime.now().astimezone(),
        related_publications=["wrong1", "wrong2"],
    )
    assert check_doi_publications(nwbfile) == [
        InspectorMessage(
            message=(
                "Metadata /general/related_publications 'wrong1' does not start with 'doi: ###' and is not an external "
                "'doi' link."
            ),
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            check_function_name="check_doi_publications",
            object_type="NWBFile",
            object_name="root",
            location="/",
        ),
        InspectorMessage(
            message=(
                "Metadata /general/related_publications 'wrong2' does not start with 'doi: ###' and is not an external "
                "'doi' link."
            ),
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            check_function_name="check_doi_publications",
            object_type="NWBFile",
            object_name="root",
            location="/",
        ),
    ]


def test_check_subject_sex():

    nwbfile = NWBFile(session_description="", identifier=str(uuid4()), session_start_time=datetime.now().astimezone())
    nwbfile.subject = Subject(subject_id="001")

    assert check_subject_sex(nwbfile.subject) == InspectorMessage(
        message="Subject.sex is missing.",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_subject_sex",
        object_type="Subject",
        object_name="subject",
        location="/general/subject",
    )


def test_check_subject_sex_other_value():
    subject = Subject(subject_id="001", sex="Male")

    assert check_subject_sex(subject) == InspectorMessage(
        message="Subject.sex should be one of: 'M' (male), 'F' (female), 'O' (other), or 'U' (unknown).",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_subject_sex",
        object_type="Subject",
        object_name="subject",
        location="/general/subject",
    )


def test_check_subject_age_missing():
    subject = Subject(subject_id="001", sex="Male")
    assert check_subject_age(subject) == InspectorMessage(
        message="Subject is missing age and date_of_birth.",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_subject_age",
        object_type="Subject",
        object_name="subject",
        location="/general/subject",
    )


def test_check_subject_age_iso8601():
    subject = Subject(subject_id="001", sex="Male", age="9 months")
    assert check_subject_age(subject) == InspectorMessage(
        message=(
            "Subject age, '9 months', does not follow ISO 8601 duration format, e.g. 'P2Y' for 2 years or 'P23W' "
            "for 23 weeks."
        ),
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_subject_age",
        object_type="Subject",
        object_name="subject",
        location="/general/subject",
    )


def test_pass_check_subject_age_with_dob():
    subject = Subject(subject_id="001", sex="Male", date_of_birth=datetime.now())
    assert check_subject_age(subject) is None


def test_pass_check_subject_species_exists():
    subject = Subject(subject_id="001", species="Homo sapiens")
    assert check_subject_species_exists(subject) is None


def test_check_subject_species_missing():
    subject = Subject(subject_id="001")
    assert check_subject_species_exists(subject) == InspectorMessage(
        message="Subject species is missing.",
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_subject_species_exists",
        object_type="Subject",
        object_name="subject",
        location="/general/subject",
    )


def check_subject_species_latin_binomial_pass():
    subject = Subject(subject_id="001", species="Homo sapiens")
    assert check_subject_species_latin_binomial(subject) is None


def test_check_subject_species_not_binomial():
    subject = Subject(subject_id="001", species="Human")

    assert check_subject_species_latin_binomial(subject) == InspectorMessage(
        message="Subject species 'Human' should be in latin binomial form, e.g. 'Mus musculus' and 'Homo sapiens'",
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_subject_species_latin_binomial",
        object_type="Subject",
        object_name="subject",
        location="/general/subject",
    )


def test_pass_check_subject_age():
    subject = Subject(subject_id="001", sex="Male", age="P9M")
    assert check_subject_age(subject) is None


def test_check_subject_exists():
    assert check_subject_exists(minimal_nwbfile) == InspectorMessage(
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
        message="subject_id is missing.",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_subject_id_exists",
        object_type="Subject",
        object_name="subject",
        location="/general/subject",
    )


def test_pass_check_subject_id_exist():
    subject = Subject(subject_id="001", sex="Male")
    assert check_subject_id_exists(subject) is None


def test_check_processing_module_name():
    processing_module = ProcessingModule("test", "desc")
    assert check_processing_module_name(processing_module) == InspectorMessage(
        message=(
            f"Processing module is named test. It is recommended to use the schema "
            f"module names: {', '.join(PROCESSING_MODULE_CONFIG)}"
        ),
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_processing_module_name",
        object_type="ProcessingModule",
        object_name="test",
        location="/",
    )


def test_pass_check_processing_module_name():
    processing_module = ProcessingModule("ecephys", "desc")
    assert check_processing_module_name(processing_module) is None
