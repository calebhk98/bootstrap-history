"""The yearly staffing check: which concerns a real shortfall of people forces shut."""
from collections import defaultdict

from .staffing_choice import (HAND_RESOURCES, closures_for_shortfall, shortfalls_beyond, staffing_allowances)


class StaffingShortfallMixin:

    def _staffing_draw_of(self, node_id, foreman_units=None):
        """What one concern holds of each resource, whether or not it is running.

        `foreman_units` is the size the foreman share is scaled by; it
        defaults to the size the concern runs at now.
        """
        scholars, craftsmen = self.venture_hands(node_id)
        held = {"scholars": scholars, "craftsmen": craftsmen}
        units = self.institution_units(node_id) if foreman_units is None else foreman_units
        trade, fte = self.venture_foreman(node_id)
        if trade:
            held[trade] = held.get(trade, 0.0) + fte * units
        for trade, people in self.venture_garrison(node_id, units).items():
            held[trade] = held.get(trade, 0.0) + people
        return {resource: amount for resource, amount in held.items() if amount > 0.005}

    def _staffing_draws(self):
        """Per running concern, how much of each resource it holds.

        Resources are "scholars", "craftsmen", and a foreman trade name; the
        amounts are the ones `open_venture` weighs.
        """
        return {node_id: self._staffing_draw_of(node_id)
                for node_id in sorted(self.state.projects.operating) if node_id in self.nodes}

    def staffing_held_totals(self):
        """Resource -> amount all running concerns hold together."""
        totals = defaultdict(float)
        for held in self._staffing_draws().values():
            for resource, amount in held.items():
                totals[resource] += amount
        return totals

    def staffing_missing_to_open(self, node_id, held_totals=None):
        """Resource -> amount short if this shut concern were opened now.

        Uses the same allowances and shortfall test that decide which running
        concerns must close, so what it names is what would shut it again.
        Pass `staffing_held_totals()` to price many concerns against one walk.
        """
        totals = defaultdict(float, self.staffing_held_totals() if held_totals is None else held_totals)
        already = self._staffing_shortfalls(totals, strict=True)
        for resource, amount in self._staffing_draw_of(node_id, self.reopen_units(node_id)).items():
            totals[resource] += amount
        return {resource: amount - already.get(resource, 0.0)
                for resource, amount in self._staffing_shortfalls(totals, strict=True).items()
                if amount - already.get(resource, 0.0) > 0.005}

    def _staffing_allowances(self, trades, strict=False):
        """How much of each resource the household carries before a concern must close.

        `strict` drops the closure slack: what `open` weighs, not what
        keeps a running concern from being shut.
        """
        household = self.state.household
        own = self.FOUNDER_IS_WORTH if self.state.founder.founder_alive else 0.0
        return staffing_allowances(trades, self.labour.effective_scholars(), household.artisans + own,
                                   household.employees, self.STAFFING_CLOSURE_SLACK, strict)

    def _staffing_shortfalls(self, totals, strict=False):
        """Resource -> amount held beyond what the household carries (short ones only)."""
        return shortfalls_beyond(totals, self._staffing_allowances(
            [resource for resource in totals if resource not in HAND_RESOURCES], strict))

    def concerns_to_close_for_staffing(self):
        """The fewest running concerns, lowest net value first, whose closure covers every shortfall.

        A shortfall of one resource only closes concerns holding that
        resource. A concern chosen early that fits again once later closures
        freed enough is kept, so nothing shut here is one `open` would accept.
        """
        draws = self._staffing_draws()
        net_value = {node_id: self.nodes[node_id]["rev"] - self.nodes[node_id]["up"] for node_id in draws}
        # A concern flagged with `keep <id> staffed` is protected: it closes only after every unflagged one.
        return closures_for_shortfall(draws, net_value, self.state.projects.keep_staffed, self._staffing_shortfalls)
