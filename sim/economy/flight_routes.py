"""The state's take and the penalty of recapture, as the labour market's migration rule reads them (`YearInputs.taxed_share`,
`Route.expected_penalty`). The state's side of the penalty is the actors' rule, handed in through `EconomySetup.recapture_penalty`
so this package imports nothing from the actors.

A leaver's expected penalty at a destination is the rule's value for what he owes where he stood (the share the state
takes of a year at his area's subsistence) and the reach of the officials at the destination.
"""
from dataclasses import replace
from typing import Callable, Dict, List, Mapping, Optional

from sim.labour.api import Route

from .setup import area_tile, labour_area


def taxed_share_by_area(taxed_by_tile: Mapping[str, float]) -> Dict[str, float]:
    """The take by labour area, from the take by tile."""
    return {labour_area(tile): float(share) for tile, share in taxed_by_tile.items()}


def with_recapture_penalty(routes: Mapping[str, List[Route]], taxed_by_area: Mapping[str, float],
                           reach_by_tile: Mapping[str, float], subsistence_by_area: Mapping[str, float],
                           penalty: Optional[Callable[[float, float], float]]) -> Dict[str, List[Route]]:
    """Each route with what a leaver expects to lose if recaptured at its end: `penalty(owed, reach there)`, where he owes
    the take of a year at his own area's subsistence. No rule or no take leaves the routes as they are."""
    if penalty is None or not taxed_by_area:
        return {origin: list(ways) for origin, ways in routes.items()}
    penalised: Dict[str, List[Route]] = {}
    for origin, ways in routes.items():
        owed = taxed_by_area.get(origin, 0.0) * subsistence_by_area.get(origin, 0.0)
        penalised[origin] = [replace(route, expected_penalty=penalty(owed, reach_by_tile.get(area_tile(route.destination), 0.0)))
                             for route in ways]
    return penalised
