"""One seat hears of what another has built, as an onlooker would: by what can be seen of it from its place.

Under fog a seat sees what it has built, what it has revealed and what it could begin next. Another seat's work
becomes known to it only when enough of it shows at the observer's distance (the same visibility an actor
copying from sight gets, sim/engine/visibility.py); a secret shows little, a published invention shows widely."""
from typing import Callable, Set

from sim.agents.api import OBSERVATION_RANGE_KM, PLAYER_VISIBLE_EXPOSURE, SECRET_EXPOSURE

from .agents_port import SimWorld
from .state import ProjectsState
from .visibility import base_visibility, seen_from


def nodes_heard_of(builder: ProjectsState, observer: ProjectsState, distance_km: float,
                   copy_difficulty: Callable[[str], float]) -> Set[str]:
    """The nodes `builder` made that `observer` has not got or heard of and can see enough of from `distance_km`."""
    heard = set()
    for node_id in builder.done - builder.granted - observer.done - observer.revealed:
        mode = (builder.disclosures.get(node_id) or {}).get("mode", "default")
        visibility = base_visibility(mode, node_id in builder.operating, copy_difficulty(node_id), SECRET_EXPOSURE)
        if seen_from(visibility, distance_km, OBSERVATION_RANGE_KM) >= PLAYER_VISIBLE_EXPOSURE:
            heard.add(node_id)
    return heard


class SeatSightMixin:

    def hear_of_other_seats(self) -> Set[str]:
        """The acting seat reveals what other seats have built that it can see enough of; returns what it heard of."""
        if not self.state._fog or len(self.state.seats) < 2:
            return set()
        observer_id = self.state.acting_seat
        observer = self.state.projects
        heard = set()
        for builder_id, builder in self.state.seats.items():
            if builder_id == observer_id or not (builder.projects.done - builder.projects.granted):
                continue
            distance = self.distance_between_seats(builder_id, observer_id)
            heard |= nodes_heard_of(builder.projects, observer, distance, self.copy_difficulty)
        observer.revealed.update(heard)
        return heard

    def distance_between_seats(self, first_id: str, second_id: str) -> float:
        """Great-circle kilometres between two seats' places."""
        return float(SimWorld(self).distance_km(self.seat_place(first_id), self.seat_place(second_id)))
