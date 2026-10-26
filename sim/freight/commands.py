"""The freight module's commands."""
from dataclasses import dataclass
from typing import Optional

from sim.assembly.api import Command

from .route import Route


@dataclass(frozen=True)
class PayRouteDues(Command):
    """An actor of the cast (named by its id) pays the holders of the tiles a haul's dues are levied at, for `tonnes`
    carried over `route`, never more than `limit` in all (no limit when None). Answers the money paid."""
    payer: str
    route: Route
    tonnes: float
    limit: Optional[float] = None
