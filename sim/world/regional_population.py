"""People by region: each region a `Population` stepped by the same code as the nation's.

A region is a tile the nation holds (the unit the agent economy places its household cohorts on). The nation's
`Population` is their sum. The regions are kept to it, so a change made to the nation outside the yearly step (a
settlers' departure, a hazard) is shared among the regions in proportion to their people.
"""
from typing import Dict, List, Mapping, Optional, Sequence

from .demography import (CHILD_CALORIE_EQUIVALENT, ELDERLY_CALORIE_EQUIVALENT, Population, StepFlows,
                         SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY)

BANDS = ("children", "working_age", "elderly")


def to_populations(stored: Mapping[str, Sequence[float]]) -> Dict[str, Population]:
    return {tile: Population(*bands) for tile, bands in stored.items()}


def to_stored(regions: Mapping[str, Population]) -> Dict[str, List[float]]:
    return {tile: [region.children, region.working_age, region.elderly] for tile, region in sorted(regions.items())}


def adult_equivalents(population: Population) -> float:
    return (population.children * CHILD_CALORIE_EQUIVALENT + population.working_age
            + population.elderly * ELDERLY_CALORIE_EQUIVALENT)


def kcal_per_day_fed(population: Population, eaten_over_need: float) -> float:
    """The calories a day that feed `population` at `eaten_over_need` of its need."""
    return eaten_over_need * adult_equivalents(population) * SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY


def kcal_per_day_by_region(regions: Mapping[str, Population], eaten_over_need_by_region: Mapping[str, float],
                           national_eaten_over_need: Optional[float], farm_kcal_per_day: float,
                           relief_kcal_per_day: float) -> Dict[str, float]:
    """{region: calories a day it is fed}: its households' eaten over need where the economy has booked it, else
    the nation's, else its share of the farm model's harvest; open works' relief is shared by need."""
    need = {tile: adult_equivalents(region) for tile, region in regions.items()}
    total_need = sum(need.values())
    fed = {}
    for tile, region in regions.items():
        ratio = eaten_over_need_by_region.get(tile, national_eaten_over_need)
        share = need[tile] / total_need if total_need > 0.0 else 0.0
        base = kcal_per_day_fed(region, ratio) if ratio is not None else farm_kcal_per_day * share
        fed[tile] = base + relief_kcal_per_day * share
    return fed


def keep_to_nation(regions: Dict[str, Population], national: Population, tiles: Sequence[str],
                   share_of_tile: Mapping[str, float]) -> None:
    """Make `regions` cover exactly `tiles` and sum, band by band, to `national`. A tile not yet tracked starts as its
    share of the nation with the nation's age mix; a tile no longer held drops out; each band is then scaled so the
    regions add up to the nation (a band the regions lack is spread by share)."""
    for tile in [tile for tile in regions if tile not in tiles]:
        del regions[tile]
    for tile in tiles:
        if tile not in regions:
            share = share_of_tile.get(tile, 0.0)
            regions[tile] = Population(*(getattr(national, band) * share for band in BANDS))
    weight = sum(share_of_tile.get(tile, 0.0) for tile in tiles)
    for band in BANDS:
        wanted = getattr(national, band)
        held = sum(getattr(region, band) for region in regions.values())
        for tile in tiles:
            if held > 0.0:
                setattr(regions[tile], band, getattr(regions[tile], band) * wanted / held)
            else:
                setattr(regions[tile], band, wanted * share_of_tile.get(tile, 0.0) / weight if weight > 0.0 else 0.0)


def step_regions(regions: Dict[str, Population], kcal_per_day_by_region: Mapping[str, float], disease_burden: float,
                 epidemic_deaths: Mapping[str, float], endemic_death_rates: Optional[Mapping[str, float]],
                 emigration: Mapping[str, float], immigration: Mapping[str, float]) -> Dict[str, StepFlows]:
    """One year for every region, each fed its own calories. The nation's epidemic deaths fall on a region in the
    share of the nation's band it holds; migrants leave and arrive in the working-age band. Returns each region's flows."""
    band_totals = {band: sum(getattr(region, band) for region in regions.values()) for band in BANDS}
    flows = {}
    for tile in sorted(regions):
        region = regions[tile]
        epidemic = {band: epidemic_deaths.get(band, 0.0) * getattr(region, band) / band_totals[band]
                    for band in BANDS if band_totals[band] > 0.0}
        flows[tile] = region.step(
            kcal_per_day_by_region[tile], immigration=immigration.get(tile, 0.0), emigration=emigration.get(tile, 0.0),
            jitter=False, disease_burden=disease_burden, epidemic_deaths=epidemic, endemic_death_rates=endemic_death_rates)
    return flows


def national_flows(flows: Mapping[str, StepFlows], nutrition_ratio: float) -> StepFlows:
    """The regions' flows added up; the nation's nutrition ratio is given (it is not a sum)."""
    total = lambda field: sum(getattr(flow, field) for flow in flows.values())
    return StepFlows(
        start_total=total("start_total"), births=total("births"), immigration=total("immigration"),
        deaths=total("deaths"), emigration=total("emigration"), end_total=total("end_total"),
        nutrition_ratio=nutrition_ratio, deaths_children=total("deaths_children"),
        deaths_working_age=total("deaths_working_age"), deaths_elderly=total("deaths_elderly"))
