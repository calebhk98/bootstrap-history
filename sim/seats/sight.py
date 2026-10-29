"""One seat hearing of what another has built (the rule is sight_rules.py)."""
from typing import Set

from sim.knowledge.api import RevealNodes

from .sight_rules import nodes_heard_of


class Sight:

    def hear_of_other_seats(self, seat_id: str = None) -> Set[str]:
        """The acting seat reveals what other seats have built that it can see enough of; returns what it heard of."""
        seats = self.needs.registered_seats()
        if not self.needs.fog_of_war() or len(seats) < 2:
            return set()
        observer_id = self.clock.acting_seat
        observer_held, observer_revealed = self.needs.techniques_held(), self.needs.techniques_revealed()
        techniques = self.needs.techniques_by_seat()
        operating = self.needs.operating_by_seat()
        heard = set()
        for builder_id in seats:
            built = techniques[builder_id].held - techniques[builder_id].granted
            if builder_id == observer_id or not built:
                continue
            distance = self.distance_between_seats(builder_id, observer_id)
            heard |= nodes_heard_of(built, operating[builder_id], self.needs.disclosures[builder_id],
                                    observer_held | observer_revealed, distance, self.needs.copy_difficulty.__getitem__)
        self.needs.send(RevealNodes(tuple(sorted(heard))))
        return heard

    def distance_between_seats(self, first_id: str, second_id: str) -> float:
        """Great-circle kilometres between two seats' places."""
        return float(self.needs.actor_world().distance_km(self.seat_place(first_id), self.seat_place(second_id)))

    def seat_place(self, seat_id: str) -> str:
        """Where a seat works from: its base tile."""
        return str(self.needs.seat_base_tile[seat_id])
