"""Agriculture's commands: what any actor sends to buy or sell farmland."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class InvestFarm(Command):
    """The acting seat buys `hectares` of farmland at the quoted price (`farm_land_price`). Answers the hectares bought, or
    a refusal with cause `not_positive` or `cannot_afford`."""
    hectares: float


@dataclass(frozen=True)
class SellFarm(Command):
    """The acting seat sells `hectares` of its farmland back to the land market at the price a purchase charges. Answers
    {hectares, price, remaining}, or a refusal with cause `not_positive` or `not_owned` (facts: owned)."""
    hectares: float
