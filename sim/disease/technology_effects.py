"""What taken-up technologies and a year's deaths do to the disease model's inputs: plain arithmetic over what the
engine hands in."""


def technology_scales(pathogen_ids, effects):
    """({pathogen id: multiplier on case fatality}, {pathogen id: multiplier on transmission}). `effects` is
    (`disease_effects` spec, share of the country holding the technology) pairs; the share scales how much of the
    relief applies, and a spec naming no pathogens acts on all of them."""
    fatality = {pathogen_id: 1.0 for pathogen_id in pathogen_ids}
    transmission = dict(fatality)
    for spec, reach in effects:
        if reach <= 0.0:
            continue
        target = fatality if spec["acts_on"] == "case_fatality" else transmission
        for pathogen_id in spec.get("pathogens") or pathogen_ids:
            if pathogen_id in target:
                target[pathogen_id] *= 1.0 - (1.0 - spec["factor"]) * reach
    return fatality, transmission


def working_age_death_share(deaths_by_band, working_age):
    """The share of working-age people the year's epidemics killed (zero when none were alive)."""
    killed = deaths_by_band.get("working_age", 0.0)
    return killed / (working_age + killed) if working_age > 0 else 0.0
