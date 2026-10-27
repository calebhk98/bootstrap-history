"""Staffing controls an actor can set: concerns to keep staffed, and a reserve of spare hands.

Methods of Labour, a mixin only so they live in a file of their own. Written
against the household actor's employees, so a firm or state can use them.
Both run in the yearly staff step, ahead of the closure rule, and hire through
`hire` so its cash, room and literacy limits apply unchanged.
"""
import math

from collections import defaultdict

from . import trade_data
from sim.reporting.api import RecordEvent


def housing_places_to_buy(count, room, cost_per_place, hiring_outlay, spending_power):
    """The worker housing to buy so `count` more people have room: the places short of `room`, or none when room
    suffices or the housing and the `hiring_outlay` together exceed `spending_power`."""
    places = math.ceil(count - max(0.0, room) - 1e-9)
    if places <= 0 or places * cost_per_place + hiring_outlay > spending_power:
        return 0
    return places


def people_to_hire_for(claimed, shortfalls):
    """Resource -> whole people to hire so flagged concerns stay staffed: the shortfall, no more than the flagged
    concerns themselves hold, rounded up past a hundredth of a person; resources with nothing to hire are left out."""
    hires = {}
    for resource in sorted(claimed):
        short = math.ceil(min(shortfalls.get(resource, 0.0), claimed[resource]) - 0.01)
        if short > 0:
            hires[resource] = short
    return hires


class StaffControlsMixin:

    def keep_staffed_concerns(self):
        """Flagged concerns that are running, or shut for want of staff."""
        projects = self._world.state.projects
        return [node_id for node_id in sorted(projects.keep_staffed)
                if node_id in projects.done and node_id in self._world.nodes
                and (node_id in projects.operating or self._world.staff_closure_age(node_id) is not None)]

    def keep_flagged_concerns_staffed(self):
        """Hire what the flagged concerns need and the household lacks.

        Counts every running concern's draw plus the flagged shut ones', so
        the shortfall is the one the closure rule would act on; hires only up
        to what the flagged concerns themselves hold."""
        flagged = self.keep_staffed_concerns()
        if not flagged:
            return
        operating = self._world.state.projects.operating
        claimed = defaultdict(float)
        totals = defaultdict(float, self._world.staffing_held_totals())
        for node_id in flagged:
            shut = node_id not in operating
            for resource, amount in self._world.staffing_draw_of(
                    node_id, self._world.reopen_units(node_id) if shut else None).items():
                claimed[resource] += amount
                if shut:
                    totals[resource] += amount
        shortfalls = self._world.staffing_shortfalls(totals, strict=True)
        for resource, short in people_to_hire_for(claimed, shortfalls).items():
            self.hire_to_cover(trade_data.staff_resource_trade(trade_data.registry_of(self._world), resource), short,
                               "keep_staffed", partial=True)

    def hold_staff_reserve(self):
        """reserve_staff: keep the set number of spare generic craftsmen and scholars.

        Spare means free after every open concern's claim (`venture_staff_free`).
        Buys housing first when the household has no room for them."""
        if not self._world.state.founder.policy.get("reserve_staff", False):
            return
        workforce = self._world.workforce
        scholars_free, craftsmen_free = self._world.venture_staff_free()
        for trade, target, free in ((trade_data.generic_craft_trade(), workforce.reserve_craftsmen, craftsmen_free),
                                    (trade_data.scholar_trade(), workforce.reserve_scholars, scholars_free)):
            short = math.ceil(target - free - 0.01)
            if short <= 0:
                continue
            self._house_for_reserve(trade, short)
            self.hire_to_cover(trade, short, "reserve_staff", partial=True)

    def _house_for_reserve(self, trade, count):
        """Buy worker housing for `count` more people if room is short and cash covers both."""
        self.buy_room_for(count, count * self.labour_market.quote_annual(trade), "reserve_staff")

    def buy_room_for(self, count, hiring_outlay, label):
        """Buy worker housing for `count` more people when room is short and the purchase budget covers
        the housing and the `hiring_outlay` together. The price and the budget are those of `buy housing`."""
        places = housing_places_to_buy(count, self.household_room(), self._world.housing_price_per_place(),
                                       hiring_outlay, self._world.spending_power("buy"))
        if places <= 0:
            return False
        if not self._world.build_worker_housing(places):
            return False
        self._world.send(RecordEvent.of("policy_housing", "%s: you build housing for %d more people" % (label, places), policy=label, places=places))
        return True

    def hire_buying_room(self, trade, count, label="auto_hire"):
        """`hire`, and when it is refused only for want of room, buy the room (see buy_room_for) and hire again."""
        hired, reply = self.hire(trade, count)
        if hired or getattr(reply, "cause", None) != "household_room":
            return hired, reply
        found = float(self.labour_market.whole_recruits(trade, count, 0.0))
        if not self.buy_room_for(found, self.labour_market.hire_cost(trade, found, 0.0), label):
            return hired, reply
        return self.hire(trade, count)
