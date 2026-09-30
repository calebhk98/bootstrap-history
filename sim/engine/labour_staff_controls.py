"""Staffing controls an actor can set: concerns to keep staffed.

Methods of Sim, a mixin only so they live in a file of their own. Written
against the household actor's employees, so a firm or state can use them.
Both run in the yearly staff step, ahead of the closure rule, and hire through
`hire` so its cash, room and literacy limits apply unchanged.
"""
import math
from collections import defaultdict

GENERIC_RESOURCE_TRADES = {"scholars": "scholar", "craftsmen": "artisan"}


class StaffControlsMixin:

    def keep_staffed_concerns(self):
        """Flagged concerns that are running, or shut for want of staff."""
        projects = self.state.projects
        return [node_id for node_id in sorted(projects.keep_staffed)
                if node_id in projects.done and node_id in self.nodes
                and (node_id in projects.operating or self.staff_closure_age(node_id) is not None)]

    def keep_flagged_concerns_staffed(self):
        """Hire what the flagged concerns need and the household lacks.

        Counts every running concern's draw plus the flagged shut ones', so
        the shortfall is the one the closure rule would act on; hires only up
        to what the flagged concerns themselves hold."""
        flagged = self.keep_staffed_concerns()
        if not flagged:
            return
        operating = self.state.projects.operating
        claimed = defaultdict(float)
        totals = defaultdict(float, self.staffing_held_totals())
        for node_id in flagged:
            shut = node_id not in operating
            for resource, amount in self._staffing_draw_of(
                    node_id, self.reopen_units(node_id) if shut else None).items():
                claimed[resource] += amount
                if shut:
                    totals[resource] += amount
        shortfalls = self._staffing_shortfalls(totals, strict=True)
        for resource in sorted(claimed):
            short = math.ceil(min(shortfalls.get(resource, 0.0), claimed[resource]) - 0.01)
            self.hire_to_cover(GENERIC_RESOURCE_TRADES.get(resource, resource), short,
                               "keep_staffed", partial=True)
