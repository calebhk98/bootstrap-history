"""The year's merchant shipments by route length (Complaints/517): how many tonnes went how far, and what the goods that went far were worth
a kilogram. Plain functions over `carried_book.CarriedGoods`; the length of a route is the days its cheapest haul takes."""
import math
from dataclasses import dataclass
from typing import Callable, Dict, List, Sequence, Tuple

from sim.unit_conversions import KILOGRAMS_PER_TONNE

from .carried_book import AT_ORIGIN, TONNES, CarriedGoods

DAY_EDGES = (30.0, 90.0, 365.0, 730.0)            # route length bands in days: up to the first edge, ..., beyond the last
VALUE_EDGES_PER_KG = (0.1, 1.0, 10.0, 100.0)      # value at the origin per kilogram, in the economy's money
UNPRICED = "unpriced"


@dataclass(frozen=True)
class LengthBand:
    length: str          # days band, e.g. "<=30 days"
    value: str           # value per kilogram band, or "unpriced" for goods with no price at either end
    tonnes: float
    value_at_origin: float


def band_label(edges: Sequence[float], index: int, unit: str) -> str:
    """The name of band `index` of `edges`: "<=edge" for all but the last, ">last edge" beyond."""
    if index < len(edges):
        return "<=%g %s" % (edges[index], unit)
    return ">%g %s" % (edges[-1], unit)


def band_index(edges: Sequence[float], figure: float) -> int:
    """The band a figure falls in: the first edge it does not exceed, else the band past the last edge."""
    for index, edge in enumerate(edges):
        if figure <= edge:
            return index
    return len(edges)


def tabulate(carried: CarriedGoods, days_between: Callable[[str, str], float], day_edges: Sequence[float] = DAY_EDGES,
             value_edges: Sequence[float] = VALUE_EDGES_PER_KG) -> List[LengthBand]:
    """The tonnes carried in each (route length band, value per kilogram band), shortest and cheapest band first.
    A route's length is `days_between(origin, destination)`; its value a kilogram is its value at the origin's price over its mass.
    A route with no price at either end is in the band "unpriced"; bands nothing was carried in are left out."""
    tonnes: Dict[Tuple[int, int], float] = {}
    value: Dict[Tuple[int, int], float] = {}
    unpriced_index = len(value_edges) + 1
    for _good, by_origin in carried.items():
        for origin, by_destination in by_origin.items():
            for destination, figures in by_destination.items():
                mass = figures[TONNES]
                if mass <= 0.0:
                    continue
                days = days_between(origin, destination)
                length = band_index(day_edges, days if not math.isnan(days) else math.inf)
                worth = figures[AT_ORIGIN]
                kind = band_index(value_edges, worth / (mass * KILOGRAMS_PER_TONNE)) if worth > 0.0 else unpriced_index
                key = (length, kind)
                tonnes[key] = tonnes.get(key, 0.0) + mass
                value[key] = value.get(key, 0.0) + worth
    return [LengthBand(band_label(day_edges, length, "days"),
                       UNPRICED if kind == unpriced_index else band_label(value_edges, kind, "per kg"), tonnes[(length, kind)],
                       value[(length, kind)])
            for length, kind in sorted(tonnes)]


def by_length(bands: Sequence[LengthBand]) -> Dict[str, float]:
    """The tonnes of each route length band (in band order), the value bands added up."""
    found: Dict[str, float] = {}
    for band in bands:
        found[band.length] = found.get(band.length, 0.0) + band.tonnes
    return found


def format_bands(bands: Sequence[LengthBand]) -> List[str]:
    """The table as text lines: a row for each band, then the share of the year's tonnes by length alone."""
    total = math.fsum(band.tonnes for band in bands)
    lines = ["  merchant tonnes by route length (days of the cheapest haul) and value per kg at the origin"]
    for band in bands:
        lines.append("    %-14s %-18s tonnes %12.5g  share %6.3f" % (band.length, band.value, band.tonnes,
                                                                    band.tonnes / total if total > 0.0 else 0.0))
    for length, tonnes in by_length(bands).items():
        lines.append("    %-14s all values        tonnes %12.5g  share %6.3f" % (length, tonnes, tonnes / total if total > 0.0 else 0.0))
    return lines
