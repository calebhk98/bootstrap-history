"""One year of every pathogen in play over a nation split into age bands, and what it hands back (deaths by band).

The caller owns births, baseline deaths and ageing of the people (the demography module); this package follows
only who is susceptible, infected or immune inside each band. At the start of a year each band's counts are
fitted to the people the caller says are there: the share that aged across a band edge carries its immunity
with it, a shortfall removes people from every compartment alike, a surplus (births) arrives susceptible.
"""
from dataclasses import dataclass, field
from typing import Dict, List

from . import network
from .step import advance_groups, wane_idle
from .types import Patch

DAYS_PER_YEAR = 365.0


@dataclass
class YearResult:
    deaths_by_band: Dict[str, int] = field(default_factory=dict)
    deaths_by_pathogen: Dict[str, Dict[str, int]] = field(default_factory=dict)
    introduced: List[str] = field(default_factory=list)


def is_circulating(records, pathogen_id):
    """Whether anyone in the saved `records` is infected with `pathogen_id` right now."""
    bands = records.get(pathogen_id)
    if not bands:
        return False
    return any(count > 0 for plain in bands.values() for name, count in plain["counts"].items()
               if name not in (network.SUSCEPTIBLE, network.RECOVERED))


def advance_year(pathogens, records, people_by_band, seed_text, introductions=(), introduction_band=None,
                 introduction_size=0, ageing=None, fatality_scale=None, transmission_scale=None,
                 fatality_factor=None, crowding=1.0, care_collapse=None):
    """Run a year for every pathogen with saved `records` (`{pathogen id: {band: plain Patch}}`, rewritten in
    place) or in `introductions`, and return a YearResult.

    `people_by_band` is the living people the caller holds per band, in the band order to use. `ageing` is
    `{band: (next band, share of the band that crosses into it per year)}`, applied to the saved counts
    before fitting. `fatality_scale` is `{band: multiplier on the pathogen's case fatality}`;
    `transmission_scale` and `fatality_factor` are `{pathogen id: multiplier}` (what the caller's technology does
    to that pathogen's spread and to its case fatality). `crowding` is the nation's person-weighted density
    relative to the density the transmissibilities are stated at; contact scales as it to the power of each
    pathogen's `density_exponent`. `care_collapse` is `(caregiver bands, sensitivity)`: fatality rises with
    the share of those bands ill at once."""
    result = YearResult()
    bands = list(people_by_band)
    transmission_scale = transmission_scale or {}
    fatality_factor = fatality_factor or {}
    for pathogen_id in sorted(set(records) | set(introductions)):
        pathogen = pathogens[pathogen_id]
        patches = _patches_for(pathogen, records.get(pathogen_id), bands, people_by_band, seed_text, ageing)
        if pathogen_id in introductions:
            patches[introduction_band].seed_infection(pathogen, introduction_size)
            result.introduced.append(pathogen_id)
        before = {band: patches[band].deaths_from_disease for band in bands}
        if any(patch.infected_now() for patch in patches.values()):
            scale = {band: (fatality_scale or {}).get(band, 1.0) * fatality_factor.get(pathogen_id, 1.0) for band in bands}
            advance_groups(pathogen, patches, DAYS_PER_YEAR, fatality_scale=scale,
                           transmission_scale=transmission_scale.get(pathogen_id, 1.0) * crowding ** pathogen.density_exponent,
                           care_collapse=care_collapse)
        else:
            for patch in patches.values():
                wane_idle(pathogen, patch, DAYS_PER_YEAR)
        deaths = {band: patches[band].deaths_from_disease - before[band] for band in bands}
        result.deaths_by_pathogen[pathogen_id] = deaths
        for band, count in deaths.items():
            result.deaths_by_band[band] = result.deaths_by_band.get(band, 0) + count
        records[pathogen_id] = {band: patches[band].to_plain() for band in bands}
    return result


def _patches_for(pathogen, saved, bands, people_by_band, seed_text, ageing):
    if saved is None:
        return {band: Patch.naive(pathogen, round(people_by_band[band]), seed="%s:%s:%s" % (seed_text, pathogen.id, band))
                for band in bands}
    patches = {band: Patch.from_plain(saved[band]) for band in bands}
    for band, (next_band, share) in (ageing or {}).items():
        if band in patches and next_band in patches:
            _move_share(patches[band], patches[next_band], share)
    for band in bands:
        _fit_to_people(patches[band], round(people_by_band[band]))
    return patches


def _move_share(source, target, share):
    for name, count in source.counts.items():
        moved = int(round(count * share))
        source.counts[name] -= moved
        target.counts[name] += moved


def _fit_to_people(patch, target):
    total = patch.living()
    if total == target:
        return
    if target > total:
        patch.counts[network.SUSCEPTIBLE] += target - total
        return
    kept = {name: int(count * target / total) for name, count in patch.counts.items()}
    biggest = max(kept, key=lambda name: patch.counts[name])
    kept[biggest] += target - sum(kept.values())
    patch.counts.update(kept)
