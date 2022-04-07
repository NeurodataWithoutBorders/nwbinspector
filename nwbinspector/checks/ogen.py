from pynwb.ogen import OptogeneticSeries, OptogeneticStimulusSite

from ..register_checks import register_check, Importance, InspectorMessage


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=OptogeneticStimulusSite)
def check_optogenetic_stimulus_site_has_optogenetic_series(ogen_site: OptogeneticStimulusSite):
    """
    Ensures that each OptogeneticStimulusSite object present in an NWBFile is referenced by at least one
    OptogeneticSeries in the same file.

    Parameters
    ----------
    ogen_site: OptogeneticStimulusSite

    Returns
    -------
    InspectorMessage or None

    """
    nwbfile = ogen_site.get_ancestor("NWBFile")
    for obj in nwbfile.objects.values():
        if isinstance(obj, OptogeneticSeries):
            if obj.site == ogen_site:
                return
    return InspectorMessage(message="OptogeneticStimulusSite is not referenced by any OptogeneticStimulusSite.")
