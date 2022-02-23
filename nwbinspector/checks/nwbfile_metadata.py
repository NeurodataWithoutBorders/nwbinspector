"""Check functions that examine general NWBFile metadata."""
import re

from pynwb import NWBFile
from pynwb.file import Subject, ProcessingModule

from ..register_checks import register_check, InspectorMessage, Importance

duration_regex = r"^P(?!$)(\d+(?:\.\d+)?Y)?(\d+(?:\.\d+)?M)?(\d+(?:\.\d+)?W)?(\d+(?:\.\d+)?D)?(T(?=\d)(\d+(?:\.\d+)?H)?(\d+(?:\.\d+)?M)?(\d+(?:\.\d+)?S)?)?$"
species_regex = r"[A-Z][a-z]* [a-z]+"

PROCESSING_MODULE_CONFIG = ["ophys", "ecephys", "icephys", "behavior", "misc", "ogen", "retinotopy"]


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=NWBFile)
def check_experimenter(nwbfile: NWBFile):
    """Check if an experimenter has been added for the session."""
    if not nwbfile.experimenter:
        return InspectorMessage(message="Experimenter is missing.")


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=NWBFile)
def check_experiment_description(nwbfile: NWBFile):
    """Check if a description has been added for the session."""
    if not nwbfile.experiment_description:
        return InspectorMessage(message="Experiment description is missing.")


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=NWBFile)
def check_institution(nwbfile: NWBFile):
    """Check if a description has been added for the session."""
    if not nwbfile.institution:
        return InspectorMessage(message="Metadata /general/institution is missing.")


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=Subject)
def check_subject_age(subject: Subject):
    if subject.age is None:
        return InspectorMessage(message="Subject is missing age.")
    if not re.fullmatch(duration_regex, subject.age):
        return InspectorMessage(
            message="Subject age does not follow ISO 8601 duration format, e.g. 'P2Y' for 2 years or 'P23W' for 23 "
            "weeks."
        )


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=NWBFile)
def check_subject_exists(nwbfile: NWBFile):
    """Check if subject exists."""
    if nwbfile.subject is None:
        return InspectorMessage(message="Subject is missing.")


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=Subject)
def check_subject_id_exists(subject: Subject):
    """Check if subject_id is defined."""
    if subject.subject_id is None:
        return InspectorMessage(message="subject_id is missing.")


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=Subject)
def check_subject_sex(subject: Subject):
    """Check if the subject sex has been specified, if one exists."""
    if subject and not subject.sex:
        return InspectorMessage(message="Subject.sex is missing.")
    elif subject.sex not in ("M", "F", "O", "U"):
        return InspectorMessage(
            message="Subject.sex should be one of: 'M' (male), 'F' (female), 'O' (other), or 'U' (unknown)."
        )


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=Subject)
def check_subject_species(subject: Subject):
    """Check if the subject species has been specified and follows latin binomial form."""
    if not subject.species:
        return InspectorMessage(message="Subject species is missing.")
    if not re.fullmatch(species_regex, subject.species):
        return InspectorMessage(
            message="Species should be in latin binomial form, e.g. 'Mus musculus' and 'Homo sapiens'",
        )


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=ProcessingModule)
def check_processing_module_name(processing_module: ProcessingModule):
    if processing_module.name not in PROCESSING_MODULE_CONFIG:
        return InspectorMessage(
            f"Processing module is named {processing_module.name}. It is recommended to use the "
            f"schema module names: {', '.join(PROCESSING_MODULE_CONFIG)}"
        )


# @nwbinspector_check(severity=1, neurodata_type=NWBFile)
# def check_keywords(nwbfile: NWBFile):
#     """Check if keywords have been added for the session."""
#     if not nwbfile.keywords:
#         return "Metadata /general/keywords is missing!"


# @nwbinspector_check(severity=1, neurodata_type=NWBFile)
# def check_doi_publications(nwbfile: NWBFile):
#     """Check if related_publications have been added as doi links."""
#     valid_starts = ["doi:", "http://dx.doi.org/", "https://doi.org/"]
#     if nwbfile.related_publications:
#         for publication in nwbfile.related_publications:
#             if any([publication.startswith(valid_start) for valid_start in valid_starts]):
#                 return f"Metadata /general/related_publications '{publication}' does not include 'doi'!"
