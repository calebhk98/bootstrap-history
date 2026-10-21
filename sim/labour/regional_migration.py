"""Where a year's working-age migrants go between neighbouring regions, by the labour market's migration rule."""
from typing import Callable, Dict, List, Mapping, Tuple

from sim.unit_conversions import CIVIL_DAYS_PER_YEAR
from sim.world.demography import Population
from sim.world.military_logistics import ARMY_MARCH_RATE_KM_PER_DAY

from .market.migration import move_shares


def migrant_pairs(regions: Mapping[str, Population], eaten_over_need: Mapping[str, float],
                  borders: Mapping[str, List[str]], distance_km: Callable[[str, str], float]
                  ) -> List[Tuple[str, str, float]]:
    """[(origin, destination, working-age people moved)] this year, in origin then destination order. Where people
    ate better is the destination's real income over its subsistence; a day on the road costs a day of the origin's
    subsistence."""
    pairs: List[Tuple[str, str, float]] = []
    for origin in sorted(regions):
        real_origin = eaten_over_need.get(origin, 0.0)
        working_age = regions[origin].working_age
        if real_origin <= 0.0 or working_age <= 0.0:
            continue
        destinations = [tile for tile in sorted(borders.get(origin, ())) if tile in regions]
        options = [(eaten_over_need.get(tile), distance_km(origin, tile) / ARMY_MARCH_RATE_KM_PER_DAY / CIVIL_DAYS_PER_YEAR)
                   for tile in destinations]
        for destination, share in zip(destinations, move_shares(real_origin, options)):
            if share > 0.0:
                pairs.append((origin, destination, working_age * share))
    return pairs


def totals_of_pairs(pairs: List[Tuple[str, str, float]]) -> Tuple[Dict[str, float], Dict[str, float]]:
    """({region: people leaving}, {region: arriving}) summed from `migrant_pairs`."""
    leaving: Dict[str, float] = {}
    arriving: Dict[str, float] = {}
    for origin, destination, moved in pairs:
        leaving[origin] = leaving.get(origin, 0.0) + moved
        arriving[destination] = arriving.get(destination, 0.0) + moved
    return leaving, arriving


def moves_between_regions(regions: Mapping[str, Population], eaten_over_need: Mapping[str, float],
                          borders: Mapping[str, List[str]], distance_km: Callable[[str, str], float]
                          ) -> Tuple[Dict[str, float], Dict[str, float]]:
    """({region: working-age people leaving}, {region: arriving}) this year, summed from `migrant_pairs`."""
    return totals_of_pairs(migrant_pairs(regions, eaten_over_need, borders, distance_km))
