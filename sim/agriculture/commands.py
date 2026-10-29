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


@dataclass(frozen=True)
class SetFarmLand(Command):
    """The farm holds `hectares` of cleared ground of the given yield `quality` (the farm workforce sets it as it clears ground)."""
    hectares: float
    quality: float


@dataclass(frozen=True)
class SetFarmTechnique(Command):
    """The farming technique chosen for the year: `technique`, an immutable value the farm year reads."""
    technique: object


@dataclass(frozen=True)
class SetFarmTerritory(Command):
    """The held tiles' `ladder` (`[(yield factor, cropped hectares)]`, best ground first) and their cropland `ceiling`."""
    ladder: object
    ceiling: float


@dataclass(frozen=True)
class RecordOpeningFarm(Command):
    """The ground cleared now is the opening's farmed area, an initial condition the price tables read."""
