"""Staffing controls an actor can set: concerns to keep staffed, and a reserve of spare hands.

Methods of Labour, a mixin only so they live in a file of their own. Written
against the household actor's employees, so a firm or state can use them.
Both run in the yearly staff step, ahead of the closure rule, and hire through
`hire` so its cash, room and literacy limits apply unchanged.
"""
import math
from collections import defaultdict

from . import trade_data


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
        for resource in sorted(claimed):
            short = math.ceil(min(shortfalls.get(resource, 0.0), claimed[resource]) - 0.01)
            self.hire_to_cover(trade_data.staff_resource_trade(trade_data.registry_of(self._world), resource), short,
                               "keep_staffed", partial=True)

    def hold_staff_reserve(self):
        """reserve_staff: keep the set number of spare generic craftsmen and scholars.

        Spare means free after every open concern's claim (`venture_staff_free`).
        Buys housing first when the household has no room for them."""
        if not self._world.state.founder.policy.get("reserve_staff", False):
            return
        household = self._world.state.household
        scholars_free, craftsmen_free = self._world.venture_staff_free()
        for trade, target, free in ((trade_data.generic_craft_trade(), household.reserve_craftsmen, craftsmen_free),
                                    (trade_data.scholar_trade(), household.reserve_scholars, scholars_free)):
            short = math.ceil(target - free - 0.01)
            if short <= 0:
                continue
            self._house_for_reserve(trade, short)
            self.hire_to_cover(trade, short, "reserve_staff", partial=True)

    def _house_for_reserve(self, trade, count):
        """Buy worker housing for `count` more people if room is short and cash covers both."""
        places = math.ceil(count - max(0.0, self.household_room()) - 1e-9)
        if places <= 0:
            return
        cost = places * self._world.housing_price_per_place()
        if cost + count * self.labour_market.quote_annual(trade) > self._world.spending_power("buy"):
            return
        if self._world.build_worker_housing(places):
            self._world.state.household.log.append((self._world.state.scenario.year,
                                             "reserve_staff: you build housing for %d more people" % places))
