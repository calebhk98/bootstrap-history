"""Commands the root applies, because what they change is composition and no module's: the seat registry (which holds each
seat's record and the module slots in it) and the tree object every module reads. The assembly's own module applies them by
the hooks the game sets on the assembly (`Assembly.add_seat`, `move_seat`, `reprice_tree`), so a module that sends one shows in
the module graph as depending on the assembly."""
from dataclasses import dataclass
from typing import Any, Dict

from .spec import Command


@dataclass(frozen=True)
class AddSeat(Command):
    """Put a new seat, built from `template`, in the seat registry with a slot of every module that keeps state per seat.
    Answers a Refusal with the cause `seat_exists` when the id is taken, else None. Money, life and watches are the seats
    module's to set up afterwards."""
    seat_id: str
    template: Dict[str, Any]


@dataclass(frozen=True)
class MoveSeat(Command):
    """Move `from_id`'s seat to `to_id` in the registry and rename it in every store keyed by seat id the root keeps; the
    modules' own stores are renamed by their owners. Answers the account of what moved."""
    from_id: str
    to_id: str


@dataclass(frozen=True)
class RepriceTree(Command):
    """Count the tree's money fields at the money an hour of work is worth now, and keep that figure in the save."""
