"""Partible inheritance: land a household has gathered beyond what its class opened with divides among heirs.

A holder's estate does not stay whole across generations where heirs share it (Rome, Greece, Han China): each
year a generation's share of the land a cohort holds above its opening ownership share passes to the tile's
cohorts that hold less than they opened with, in proportion to what they lack. A tenant who inherits from its
own lessor holds that land outright, so the tenancy on it shrinks by the same share. Pledged land does not
move (the lender's claim stands).
"""
from typing import Dict

from sim.constants import declare

from . import titles
from .types import AgentId, TileId

GENERATION_YEARS = declare(
    "TITLE_INHERITANCE_GENERATION_YEARS", 25.0, kind="temporary_heuristic", unit="years",
    source=None, confidence="C",
    why="Households here do not die or have children, so a holder's estate is divided among heirs once a "
        "generation, spread over a year, by a fixed rate. Retired when demography divides households.",
    retire="538 household division in demography")
PARTIBLE_ESTATE_SHARE = declare(
    "TITLE_PARTIBLE_ESTATE_SHARE", 1.0, kind="temporary_heuristic", unit="share of estates divided among heirs",
    source=None, confidence="D",
    why="The share of estates a society's law divides among heirs (the rest pass whole to one). Societies "
        "differ (Rome, Greece, Han China partible; entailed estates not); a per-civilisation inheritance rule "
        "is not yet data.",
    retire="538 per-civilisation inheritance rule in data/civilizations")


def divide_estates(record, generation_years: float = GENERATION_YEARS,
                   partible_share: float = PARTIBLE_ESTATE_SHARE) -> Dict[TileId, float]:
    """One year of inheritance. Returns the share of land that changed hands, by tile."""
    rate = min(1.0, partible_share / generation_years) if generation_years > 0.0 else 0.0
    moved: Dict[TileId, float] = {}
    if rate <= 0.0:
        return moved
    by_tile: Dict[TileId, list] = {}
    for cohort in sorted(record.cohorts.values(), key=lambda cohort: cohort.agent_id):
        by_tile.setdefault(cohort.tile, []).append(cohort)
    for tile, cohorts in sorted(by_tile.items()):
        held = titles.shares(record, tile)
        lacking = {cohort.agent_id: cohort.ownership_share - held.get(cohort.agent_id, 0.0) for cohort in cohorts
                   if cohort.ownership_share - held.get(cohort.agent_id, 0.0) > titles.EPSILON}
        for cohort in cohorts:
            if not lacking:
                break
            estate = min(titles.free_share(record, cohort.agent_id, tile),
                         titles.holding(record, tile, cohort.agent_id) - cohort.ownership_share)
            if estate <= titles.EPSILON:
                continue
            passing = min(rate * estate, sum(lacking.values()))
            total_lacking = sum(lacking.values())
            for heir, lack in sorted(lacking.items()):
                titles.pass_title(record, tile, cohort.agent_id, heir, passing * lack / total_lacking)
            moved[tile] = moved.get(tile, 0.0) + passing
            lacking = {heir: lack - passing * lack / total_lacking for heir, lack in lacking.items()
                       if lack - passing * lack / total_lacking > titles.EPSILON}
    return moved
