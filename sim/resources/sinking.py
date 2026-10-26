"""Sinking, closing and mothballing workings: the commands that change what the seat's mines are."""
from typing import Any

from sim.agents.api import edges
from sim.ledger.api import PayEdge, ReceiveFromEdge
from sim.refusal import Refusal
from sim.reporting.api import RecordEvent

from . import ceilings, rules
from .commands import CloseMine, MothballMines, NoteMineCostPaid, OpenMine
from .constants import MINE_LEAD_YEARS, MOTHBALL_CUT_SHARE
from .deposits import NO_DEPOSIT_TEXT


class Sinking:
    """Needs: year, price_index, normalized_material, can_pay, affordable_units, acting_balance. Sends PayEdge,
    ReceiveFromEdge, RecordEvent."""

    def open_mine(self, command: OpenMine) -> Any:
        """Open workings, each naming a deposit found (`deposit` picks one; otherwise the deposits with most room are worked
        first) and bounded by it. A material with no deposit data is bounded by the ceiling alone.

        The ceiling is about standing, state reach and geology, not the attested output of a historical empire: a founder who
        needs twenty thousand tonnes of coal a year is not throttled by it. What a mine is not is free or instant: it is paid
        for when sunk, takes `MINE_LEAD_YEARS` to come on stream, and costs to run every year after."""
        tonnes = command.tonnes_per_year
        if tonnes <= 0:
            return Refusal("nothing_asked", "say how many tonnes a year to sink")
        material = self.needs.normalized_material[command.material]
        capex = self.mine_capex(material)
        if capex is None:
            return Refusal("not_minable", "nothing prices %s" % material, material=material)
        ceiling = self.mine_land_ceiling(material)
        have_capacity = self.mine_capacity()
        seat = self.seat
        tonnes = min(tonnes, ceilings.room_under_ceiling(ceiling, have_capacity.get(material, 0.0),
                                                         seat.mine_pending.get(material, 0.0)))
        deposit_room = self.mine_room_in_deposits(material, command.deposit)
        if deposit_room is not None:
            if deposit_room <= 0.0:
                return Refusal("no_deposit_found", NO_DEPOSIT_TEXT % (material, material), material=material)
            tonnes = min(tonnes, deposit_room)
        if tonnes <= 0:
            return Refusal("no_room", "the ground here holds no more of %s than is already worked" % material, material=material)
        # deeper ones cost more: the scale is 1.0 on a fresh deposit with no relevant technology
        scale = self.cost_scale_for_material(material)
        price_index = self.needs.price_index()
        cost = tonnes * capex * price_index * scale
        # a shaft that costs nothing needs no budget check
        if cost > 0 and not self.needs.can_pay(cost):
            # a typed command is not a standing order to spend everything: it is refused and the price quoted; the automatic
            # policy buys what it can afford, because spending spare cash on a bottleneck is the whole of its job
            if not command.partial:
                return Refusal("cannot_afford", "the workings cost more than the purchase budget covers", cost=cost)
            tonnes = self.needs.affordable_units(capex * price_index * scale, decimals=6)
            cost = tonnes * capex * price_index * scale
        if tonnes <= 0:
            return Refusal("cannot_afford", "the purchase budget does not cover a tonne of these workings")
        self.needs.send(PayEdge(edges.EDGE_BUILDERS, cost, "mines opened"))
        # each investment is its own working with its own sinking time and carries the cost it was sunk for
        if seat.mine_tranches is None:
            seat.mine_tranches = []
        for deposit_id, share in self.allocate_to_deposits(material, tonnes, command.deposit):
            seat.mine_tranches.append([material, share, self.needs.year() + MINE_LEAD_YEARS, cost * share / tonnes,
                                       command.order, deposit_id])
        seat.mine_pending[material] = seat.mine_pending.get(material, 0.0) + tonnes
        self.changed_mines()
        return tonnes

    def close_mine(self, command: CloseMine) -> Any:
        """Shut the seat's workings of a material on purpose, and drop the shafts still being sunk."""
        material = self.needs.normalized_material[command.material]
        workings = self.workings_of(material)
        sinking = [tranche for tranche in (self.seat.mine_tranches or []) if tranche[0] == material]
        if not workings and not sinking:
            minable = self.mineable(material)
            return Refusal("no_workings", ("you have no %s workings, and none being sunk" % material if minable
                                           else "no such material: %s. %s" % (material, self.mine_catalog_hint())),
                           material=material, minable=minable)
        # each working's own cost, not the material average: closing two of very different ages saves what those two cost
        saved = sum(self.operating_cost_of(working) for working in workings)
        seat = self.seat
        seat.mines = [working for working in seat.mines if working.get("material") != material]
        seat.mine_tranches = [tranche for tranche in (seat.mine_tranches or []) if tranche[0] != material]
        self.changed_mines()
        self.needs.send(RecordEvent.of("workings_closed", "you close the %s workings" % material, material=material,
                                       saved_per_year=saved))
        return {"material": material, "saved_per_year": saved}

    def mothball_mines(self, command: MothballMines = None) -> None:
        """Stop working what cannot be paid for, worst value first: every working of the worst-value material is cut by half
        (the survivors keep their own commissioning year and depletion clock) and the running cost saved is paid back. The
        shaft floods and the crew disperses, so bringing the capacity back means sinking it again."""
        seat = self.seat
        order = sorted(self.mine_capacity(), key=lambda material: -self.mine_opex(material))
        for material in order:
            if self.needs.acting_balance() >= 0:
                break
            kept = []
            for working in self.workings_of(material):
                cut = working["capacity"] * MOTHBALL_CUT_SHARE
                self.needs.send(ReceiveFromEdge(edges.EDGE_SUPPLIERS, cut * self.mine_opex(material) * self.needs.price_index(),
                                                "mine running costs saved by mothballing"))
                working["capacity"] -= cut
                if working["capacity"] >= 1.0:
                    kept.append(working)
            seat.mines = [working for working in seat.mines if working.get("material") != material] + kept
            self.changed_mines()
            self.needs.send(RecordEvent.of("mines_mothballed", "MOTHBALLED half the %s workings; you could "
                                           "not pay to keep them running" % material))

    def note_mine_cost_paid(self, command: NoteMineCostPaid) -> None:
        self.seat.mine_cost_paid += command.amount
