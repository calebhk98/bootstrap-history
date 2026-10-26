"""The seat's workings: what stands, what is being sunk, how worked out each is, and the yearly step that commissions and
ages them.

A working is its own record (material, rated capacity, the year it came on stream, what it cost, its own depletion clock
and the deposit it names); the capacity of a material is always summed from the list, never held beside it."""
from typing import Any, Dict, List

from sim.reporting.api import RecordEvent

from . import rules
from .channels import MINES
from .constants import DEPLETION_FLOOR, DEPLETION_HALF_LIFE_YRS, MINING_COST_SCALE_CEILING, MINING_COST_SCALE_FLOOR


class Workings:
    """Needs: year. Sends RecordEvent."""

    def changed_mines(self) -> None:
        self.bump_seat(MINES)

    def mine_workings(self) -> List[Dict[str, Any]]:
        """The acting seat's standing workings, in the order they were commissioned."""
        return self.seat.mines

    def mine_capacity(self) -> Dict[str, float]:
        """Rated capacity of the acting seat's workings, summed by material."""
        return rules.capacity_by_material(self.seat.mines)

    def mines_being_sunk(self) -> Dict[str, Any]:
        """{tranches: [material, tonnes a year, year ready, cost, order id, deposit id] being sunk, pending: material ->
        tonnes a year being sunk}."""
        return {"tranches": self.seat.mine_tranches or [], "pending": self.seat.mine_pending}

    def workings_of(self, material: str) -> List[Dict[str, Any]]:
        """The acting seat's workings raising `material`, in commission order."""
        return [working for working in self.seat.mines if working.get("material") == material]

    def depletion_of(self, working: Dict[str, Any]) -> float:
        """Share of day-one yield this working still gets, from its own clock since its own commissioning."""
        return rules.depletion_factor(working.get("intensity_yrs", 0.0), DEPLETION_FLOOR, DEPLETION_HALF_LIFE_YRS)

    def mine_depletion(self, material: str) -> float:
        """The material's typical depletion, the capacity-weighted mean over its workings; 1.0 with none."""
        workings = self.workings_of(material)
        return rules.average_depletion([working["capacity"] for working in workings],
                                       [self.depletion_of(working) for working in workings])

    def cost_scale_of(self, working: Dict[str, Any]) -> float:
        return rules.cost_scale(self.depletion_of(working), MINING_COST_SCALE_FLOOR, MINING_COST_SCALE_CEILING)

    def cost_scale_for_material(self, material: str) -> float:
        return rules.cost_scale(self.mine_depletion(material), MINING_COST_SCALE_FLOOR, MINING_COST_SCALE_CEILING)

    def yield_of(self, working: Dict[str, Any]) -> float:
        """Tonnes a year this working raises: its capacity after its own depletion, bounded by its deposit."""
        remaining = self.deposit_remaining_tonnes(working["material"], working["deposit"]) if working.get("deposit") else None
        return rules.working_yield(working["capacity"], self.depletion_of(working), remaining)

    def mine_yield(self, material: str) -> float:
        """Tonnes a year all the workings of `material` raise this year."""
        return sum(self.yield_of(working) for working in self.workings_of(material))

    def mine_depletion_note(self, material: str) -> Any:
        """Why the material's workings, on average, yield less than the tonnage sunk; None with nothing to explain."""
        if not self.workings_of(material):
            return None
        return rules.depletion_note(self.mine_depletion(material))

    def working_report(self, working: Dict[str, Any]) -> Dict[str, Any]:
        """{depletion, yield_tonnes, operating_cost, note} of one working, from its own figures."""
        depletion = self.depletion_of(working)
        return {"depletion": depletion, "yield_tonnes": self.yield_of(working), "operating_cost": self.operating_cost_of(working),
                "note": rules.depletion_note(depletion)}

    def commission_mines(self) -> None:
        """Move finished tranches into standing workings, then age every working one year."""
        seat = self.seat
        commissioned, still, pending = rules.commission_due(seat.mine_tranches or [], seat.mine_pending, self.needs.year())
        seat.mines.extend(commissioned)
        seat.mine_pending = pending
        seat.mine_tranches = still
        self.advance_depletion()

    def advance_depletion(self) -> None:
        """One year of intensity for every working, each aged from its own commissioning year; the deposit it names is
        drawn down by the year's yield first. Workings whose deposit is empty then close."""
        ceilings: Dict[str, float] = {}
        for working in self.seat.mines:
            material = working["material"]
            if material not in ceilings:
                ceilings[material] = self.mine_land_ceiling(material)
            if working.get("deposit"):
                self.draw(working["deposit"], self.yield_of(working))
            working["intensity_yrs"] = rules.next_intensity(working.get("intensity_yrs", 0.0), working["capacity"], ceilings[material])
        self.close_worked_out()
        self.changed_mines()

    def close_worked_out(self) -> None:
        kept = []
        for working in self.seat.mines or ():
            deposit_id = working.get("deposit")
            if deposit_id and self.deposit_remaining_tonnes(working["material"], deposit_id) <= 0.0:
                self.needs.send(RecordEvent.of("workings_exhausted", "the %s workings at %s are worked out and close"
                                               % (working["material"], deposit_id)))
            else:
                kept.append(working)
        self.seat.mines = kept
