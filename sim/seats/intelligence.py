"""Spies and beliefs: a seat funds spies against another, and holds an estimate of what each other seat knows and has."""
from typing import Any, Dict

from sim.assembly.api import Part
from sim.ledger.api import DebitSeat
from sim.refusal import Refusal
from sim.unit_conversions import HOURS_PER_PERSON_YEAR

from . import intelligence_rules


class Intelligence(Part):

    def seat_beliefs(self) -> Dict[str, Any]:
        """A copy of what the acting seat believes of each other seat: target id -> kind -> {value, variance, year}."""
        return {target: {kind: dict(entry) for kind, entry in kinds.items()} for target, kinds in self.seat.beliefs.items()}

    def seat_spies(self) -> Dict[str, int]:
        """The spies the acting seat funds, by target seat id."""
        return dict(self.seat.spies)

    def place_spies(self, command: Any) -> Any:
        """Set the acting seat's spies against a seat; the count placed, or a Refusal."""
        seats = self.needs.registered_seats()
        if command.target_id not in seats or command.target_id == self.clock.acting_seat:
            return Refusal("unknown_target", "spies can only be placed against another seat", target=command.target_id)
        if command.count < 0:
            return Refusal("negative_count", "a seat cannot place fewer than no spies", count=command.count)
        if command.count:
            self.seat.spies[command.target_id] = int(command.count)
        else:
            self.seat.spies.pop(command.target_id, None)
        return int(command.count)

    def pay_for_spies(self) -> Dict[str, int]:
        """Charge the acting seat a year's labour for each spy it can pay for and drop the rest; the spies fielded by target."""
        placed = dict(self.seat.spies)
        if not placed:
            return {}
        cost = self.needs.money_per_labour_hour() * HOURS_PER_PERSON_YEAR
        fielded = intelligence_rules.fielded_spies(placed, self.needs.seat_balance[self.clock.acting_seat], cost)
        if fielded:
            self.needs.send(DebitSeat(self.clock.acting_seat, cost * sum(fielded.values()), "espionage"))
        self.seat.spies = dict(fielded)
        return fielded
