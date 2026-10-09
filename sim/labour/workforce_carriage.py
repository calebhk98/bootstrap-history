"""Crew hours to carry goods, by trade: carriage as a labour need.

The goods households and producers use are moved, and the movers are sailors, carters and porters. The
hours per tonne-km are geography's (the physical inputs the route search prices a haul with), for the
carriage modes the society's technologies unlock. How far a tonne goes is geography's market reach: the
distance its value pays for at the mode's carriage cost, never more than the span between the realm's own
tiles. `workforce_spinup.need_shares_by_trade` turns a `Carriage` into hours per tonne by trade.
"""
import collections
import math
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

import sim.geography.api as geography


@dataclass(frozen=True)
class CarriageMode:
    crew_trade: str
    crew_hours_per_tonne_km: float
    cost_hours_per_tonne_km: float     # crew, feed and fuel together: what a tonne-km costs


@dataclass(frozen=True)
class Carriage:
    """The least-cost mode of each kind of way (land, water) the society can use."""
    modes: Tuple[CarriageMode, ...] = ()
    realm_span_km: Optional[float] = None    # mean distance between the realm's tiles; None for no limit

    def haul_km(self, mode: CarriageMode, value_hours_per_tonne: float) -> float:
        """Mean kilometres a tonne of this value is carried by `mode`: a share of the reach its value pays
        for (the mean distance inside a market area), at most the span between market areas."""
        reach = geography.market_radius_km(value_hours_per_tonne, mode.cost_hours_per_tonne_km)
        mean = reach * geography.MEAN_DISTANCE_IN_DISC
        return mean if self.realm_span_km is None else min(mean, self.realm_span_km)

    def hours_per_tonne_by_trade(self, value_hours_per_tonne: float,
                                 haul_km: Optional[float] = None) -> Dict[str, float]:
        """{trade: crew hours to carry a tonne worth `value_hours_per_tonne`} (labour-hours). [temporary_heuristic]
        Where several kinds of way are usable each carries an equal share of the tonnage, until haul shares
        come from where goods are made and used. `haul_km` fixes the distance instead of the value's reach."""
        hours: Dict[str, float] = collections.defaultdict(float)
        for mode in self.modes:
            distance = haul_km if haul_km is not None else self.haul_km(mode, value_hours_per_tonne)
            if math.isfinite(distance):
                hours[mode.crew_trade] += distance * mode.crew_hours_per_tonne_km / len(self.modes)
        return dict(hours)

    def trades(self) -> frozenset:
        return frozenset(mode.crew_trade for mode in self.modes)


def _carriage_group(edge_classes: Iterable[str]) -> str:
    return "land" if "land" in edge_classes else "water"


def carriage_for(reached_nodes: Iterable[str], realm_tiles: Iterable[str] = ()) -> Carriage:
    """The carriage a society holding `reached_nodes` has, over a realm made of `realm_tiles`."""
    rates = geography.carriage_rates(geography.usable_modes([frozenset(reached_nodes)]))
    best_by_group: Dict[str, Dict[str, object]] = {}
    for rate in rates.values():
        group = _carriage_group(rate["edge_classes"])
        held = best_by_group.get(group)
        if held is None or rate["cost_hours_per_tonne_km"] < held["cost_hours_per_tonne_km"]:
            best_by_group[group] = rate
    modes = tuple(CarriageMode(rate["crew_trade"], rate["crew_hours_per_tonne_km"], rate["cost_hours_per_tonne_km"])
                  for _group, rate in sorted(best_by_group.items()))
    return Carriage(modes, geography.realm_span_km(realm_tiles))
