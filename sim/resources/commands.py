"""The resources module's commands: what any actor sends to open or close workings, prospect, draw a deposit, buy woodland
or lay nitre beds. Each acts on the acting seat's holdings."""
from dataclasses import dataclass
from typing import Optional, Tuple

from sim.assembly.api import Command


@dataclass(frozen=True)
class OpenMine(Command):
    """Sink workings for `tonnes_per_year` of a material, each naming a found deposit (`deposit` picks one, else the deposits
    with most room first). Answers the tonnes a year ordered, or a refusal with cause `nothing_asked`, `not_minable`,
    `no_room`, `no_deposit_found` or `cannot_afford` (only when `partial` is False: otherwise it buys what it can)."""
    material: str
    tonnes_per_year: float
    partial: bool = True
    order: str = ""
    deposit: Optional[str] = None


@dataclass(frozen=True)
class CloseMine(Command):
    """Shut the workings of a material, and drop the shafts still being sunk. Answers {saved_per_year}, or a refusal with
    cause `no_workings` (facts: material, minable)."""
    material: str


@dataclass(frozen=True)
class MothballMines(Command):
    """Cut the workings of the worst-value materials by half until the household's balance is no longer negative, each cut
    paying back the running cost it saves."""


@dataclass(frozen=True)
class DrawDeposit(Command):
    """`tonnes` of the resource are taken out of a deposit. Answers the tonnes."""
    deposit: str
    tonnes: float


@dataclass(frozen=True)
class Prospect(Command):
    """Prospect a held tile for a material with `person_days` of effort, paid at the mining trade's wage; the deposits found
    are kept. Answers {cost, found, message}, or a refusal with cause `no_deposit_data`, `not_held`, `no_effort` or
    `cannot_afford`."""
    tile: str
    material: str
    person_days: float


@dataclass(frozen=True)
class BuyForest(Command):
    """Buy `hectares` of coppice, no more than the ceiling leaves room for. Answers the hectares bought, or a refusal with
    cause `no_room` or `cannot_afford`."""
    hectares: float


@dataclass(frozen=True)
class LayNitreBeds(Command):
    """Lay `square_metres` of nitre bed at the quoted price. Answers the square metres laid, or a refusal with cause
    `nothing_asked` or `cannot_afford`."""
    square_metres: float


@dataclass(frozen=True)
class NoteMineCostPaid(Command):
    """The year's running cost of the workings, `amount`, was paid; added to the total the seat has paid."""
    amount: float


@dataclass(frozen=True)
class FellTimber(Command):
    """Wood is cut from tiles' standing timber: (tile, tonnes) in the order the felling is taken from them."""
    cuts: Tuple[Tuple[str, float], ...]


@dataclass(frozen=True)
class RegrowTimber(Command):
    """The felled tiles' stock a year on."""
