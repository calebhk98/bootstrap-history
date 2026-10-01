"""The yearly staffing check: which concerns a real shortfall of people forces shut."""
from collections import defaultdict


class StaffingShortfallMixin:

    def _staffing_draw_of(self, node_id, foreman_units=None):
        """What one concern holds of each resource, whether or not it is running.

        `foreman_units` is the size the foreman share is scaled by; it
        defaults to the size the concern runs at now.
        """
        scholars, craftsmen = self.venture_hands(node_id)
        held = {"scholars": scholars, "craftsmen": craftsmen}
        trade, fte = self.venture_foreman(node_id)
        if trade:
            units = self.institution_units(node_id) if foreman_units is None else foreman_units
            held[trade] = held.get(trade, 0.0) + fte * units
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
        slack = 0.0 if strict else self.STAFFING_CLOSURE_SLACK
        allowances = {"scholars": self.effective_scholars() + slack,
                      "craftsmen": household.artisans + own + slack}
        for trade in trades:
            allowances[trade] = household.employees.get(trade, 0.0) + (0.0 if strict else 0.01)
        return allowances

    def _staffing_shortfalls(self, totals, strict=False):
        """Resource -> amount held beyond what the household carries (short ones only)."""
        allowances = self._staffing_allowances(
            [resource for resource in totals if resource not in ("scholars", "craftsmen")], strict)
        return {resource: totals[resource] - allowances[resource]
                for resource in sorted(totals) if totals[resource] > allowances[resource]}

    def concerns_to_close_for_staffing(self):
        """The fewest running concerns, lowest net value first, whose closure covers every shortfall.

        A shortfall of one resource only closes concerns holding that
        resource. A concern chosen early that fits again once later closures
        freed enough is kept, so nothing shut here is one `open` would accept.
        """
        draws = self._staffing_draws()
        totals = defaultdict(float)
        for held in draws.values():
            for resource, amount in held.items():
                totals[resource] += amount
        net_value = {node_id: self.nodes[node_id]["rev"] - self.nodes[node_id]["up"] for node_id in draws}
        # A concern flagged with `keep <id> staffed` is protected: it closes only after every unflagged one.
        protected = self.state.projects.keep_staffed
        order = sorted(draws, key=lambda node_id: (node_id in protected, net_value[node_id], node_id))
        chosen = []
        unfixable = set()
        while True:
            short = [resource for resource in self._staffing_shortfalls(totals) if resource not in unfixable]
            if not short:
                break
            holders = [node_id for node_id in order
                       if node_id not in chosen and short[0] in draws[node_id]]
            if not holders:
                unfixable.add(short[0])
                continue
            chosen.append(holders[0])
            for resource, amount in draws[holders[0]].items():
                totals[resource] -= amount
        kept_open = []
        for node_id in sorted(chosen, key=lambda node_id: (-net_value[node_id], node_id)):
            for resource, amount in draws[node_id].items():
                totals[resource] += amount
            if self._staffing_shortfalls(totals):
                for resource, amount in draws[node_id].items():
                    totals[resource] -= amount
            else:
                kept_open.append(node_id)
        return [node_id for node_id in chosen if node_id not in kept_open]
