"""The coin module's commands: the yearly charges that keep, lose and plunder coin and what is kept with it."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class ChargeKeeping(Command):
    """Every actor of the cast in business that holds money (a state, a firm) pays its guards to keep it as coin. The
    acting household pays its own keeping in its money step, from the `coin_keeping_due` quote."""


@dataclass(frozen=True)
class ChargeActorsTheft(Command):
    """Every home-country actor of the cast in business loses the theft expected of what it keeps."""


@dataclass(frozen=True)
class ChargeHouseholdTheft(Command):
    """The acting household loses its expected theft; its guarding counts for the share of its keeping cost that its
    purse could pay. Answers the money taken."""
    keeping_paid: float
    keeping_owed: float


@dataclass(frozen=True)
class PlunderHousehold(Command):
    """A sack or a bandit year takes from the acting household by the same exposure. A sack comes where order has failed
    (`order_holds` False). Answers the money taken."""
    strength: float
    cause: str
    order_holds: bool
