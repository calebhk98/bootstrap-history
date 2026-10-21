"""How concentrated land titles are: the hectares each holder holds, summarised as a Gini over holders, read two
ways because the sources differ in whether the landless are in the denominator. A validation read (CLAUDE.md 4.2),
never an input to the model.

`LAND_GINI_SOURCED` is the table of measured land Ginis by setting and denominator, from
Complaints/reports/research-household-wealth-and-land-concentration.md section 2.1 (each row names the source that
report opened). The band a check uses for a denominator is the hull of the rows with that denominator (`band`).
Han China and the Mexica have no land figure in anything opened: no band, a check skips them. No opened source
gives a land top-decile share, so the top decile is printed, never checked.
"""
from typing import Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple

from . import titles, titles_ground
from .types import AgentId, TileId

LANDHOLDERS_ONLY = "landholders_only"       # holders with no land are left out of the Gini
LANDLESS_COUNTED = "landless_counted"       # every household is in it, with zero hectares if it holds none


class SourcedGini(NamedTuple):
    setting: str
    denominator: str
    low: float
    high: float
    source: str


LAND_GINI_SOURCED: Tuple[SourcedGini, ...] = (
    SourcedGini("england_1279_hundred_rolls", LANDHOLDERS_ONLY, 0.59, 0.59,
                "Kumon 2021 (IAST wp 124), Hundred Rolls section, from Kanzaka 2002; biased up by aggregating villages"),
    SourcedGini("england_1279_simulated", LANDHOLDERS_ONLY, 0.625 - 0.026, 0.625 + 0.026,
                "Bekar and Reed 2009 (Oxford Economic and Social History 79): land Gini 120 years from 0.135 (sd 0.026)"),
    SourcedGini("roman_egypt_villages", LANDHOLDERS_ONLY, 0.374, 0.518,
                "Scheidel 2019 (Roman wealth and wealth inequality, zenodo 3458611): Kerkeosiris 0.374, Karanis 0.478, "
                "Philadelphia 0.518; registers of villagers only, not whole districts"),
    SourcedGini("roman_egypt_urban_owners", LANDHOLDERS_ONLY, 0.623, 0.758,
                "Scheidel 2019: Aphrodito 0.623, Hermopolis 0.715, Antinoopolis 0.758 (urban and absentee owners)"),
    SourcedGini("england_1279_landless_assumed", LANDLESS_COUNTED, 0.78, 0.78,
                "Kumon 2021: landless set at 47 percent of the rural population (Campbell 2008); an assumption"),
    SourcedGini("england_enclosure_parishes", LANDLESS_COUNTED, 0.65, 0.82,
                "Kumon 2021: 18th to 19th century enclosure parishes, landless 40 to 50 percent"),
)
NO_LAND_BAND = ("han_china", "mexica")      # nothing opened gives a land Gini for them: no band, a check skips them


def band(denominator: str, settings: Optional[Sequence[str]] = None) -> Optional[Tuple[float, float]]:
    """(low, high) land Gini the sources span for the denominator (only the named settings when given); None when
    no row matches."""
    rows = [row for row in LAND_GINI_SOURCED if row.denominator == denominator
            and (settings is None or row.setting in settings)]
    return (min(row.low for row in rows), max(row.high for row in rows)) if rows else None


def hectares_by_holder(tiles: Mapping[TileId, object], record) -> Dict[AgentId, float]:
    """Hectares of cropland each holder holds through its titles; every cohort is a holder, with zero if it holds none."""
    held: Dict[AgentId, float] = {cohort_id: 0.0 for cohort_id in record.cohorts}
    for tile_id, tile in sorted(tiles.items()):
        for holder, share in titles.shares(record, tile_id).items():
            held[holder] = held.get(holder, 0.0) + share * titles_ground.arable_hectares(record, tile_id, tile)
    return held


def top_decile_share(holdings: Sequence[float]) -> float:
    """Share of all land held by the richest tenth of holders (at least one holder)."""
    ordered = sorted(holdings)
    total = sum(ordered)
    if total <= 0.0:
        return 0.0
    top_count = max(1, round(0.1 * len(ordered)))
    return sum(ordered[-top_count:]) / total


def gini(holdings: Sequence[float]) -> float:
    ordered = sorted(holdings)
    count, total = len(ordered), sum(ordered)
    if count == 0 or total <= 0.0:
        return 0.0
    return sum((2 * (rank + 1) - count - 1) * amount for rank, amount in enumerate(ordered)) / (count * total)


def gini_by_denominator(holdings: Sequence[float]) -> Dict[str, float]:
    """The Gini with the landless left out and with them counted."""
    return {LANDHOLDERS_ONLY: gini([amount for amount in holdings if amount > titles.EPSILON]),
            LANDLESS_COUNTED: gini(holdings)}


def summary(tiles: Mapping[TileId, object], record) -> Dict[str, float]:
    holdings: List[float] = list(hectares_by_holder(tiles, record).values())
    by_denominator = gini_by_denominator(holdings)
    landless = sum(1 for amount in holdings if amount <= titles.EPSILON)
    return {"holders": float(len(holdings)), "top_decile_share": top_decile_share(holdings),
            "gini": by_denominator[LANDLESS_COUNTED], "gini_landholders_only": by_denominator[LANDHOLDERS_ONLY],
            "landless_share": landless / len(holdings) if holdings else 0.0}
