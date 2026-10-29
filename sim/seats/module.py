"""The seats module: who plays, joining and handing over, goals and win conditions, dealings between seats, and sight.

The seat registry (`state.seats`), the acting seat's switch and the facades stay on `Sim`; the module reads the registry
through `legacy_seats` and changes it by the commands `RegisterSeat` and `MoveSeat`, which the engine applies."""
from typing import Any, Dict, List, Optional

from sim.assembly.api import Module

from . import builds
from .dealings import Dealings
from .founder import Founder
from .goals import Goals
from .handover import Handover
from .run import Run
from .sight import Sight


class Seats(Run, Handover, Sight, Dealings, Goals, Founder, Module):

    def setup(self) -> None:
        self._conditioned: Optional[List[str]] = None   # node ids that carry a win_condition, built on first ask
        self._closures: Dict[str, Any] = {}   # seat id -> the nodes its goal needs, once worked out

    def seat_holders(self, node_id: str) -> List[str]:
        """Ids of the seats that hold `node_id` at all, built or granted."""
        return builds.holders_of(self.needs.techniques_by_seat(), node_id)

    def built_by_any_seat(self, among: Any) -> set:
        """Every node of `among` some seat built itself."""
        return builds.built_by_any(self.needs.techniques_by_seat(), among)
