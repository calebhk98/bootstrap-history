"""The yearly staffing check: which concerns a real shortfall of people forces shut."""
from collections import defaultdict


class StaffingShortfallMixin:

    def _staffing_draws(self):
        """Per running concern, how much of each resource it holds.

        Resources are "scholars", "craftsmen", and a foreman trade name; the
        amounts are the ones `open_venture` weighs.
        """
        draws = {}
        for node_id in sorted(self.state.projects.operating):
            if node_id not in self.nodes:
                continue
            scholars, craftsmen = self.venture_hands(node_id)
            held = {"scholars": scholars, "craftsmen": craftsmen}
            trade, fte = self.venture_foreman(node_id)
            if trade:
                held[trade] = held.get(trade, 0.0) + fte * self.institution_units(node_id)
            draws[node_id] = {resource: amount for resource, amount in held.items() if amount > 0.005}
        return draws

    def _staffing_allowances(self, trades):
        """How much of each resource the household carries before a concern must close."""
        household = self.state.household
        own = self.FOUNDER_IS_WORTH if self.state.founder.founder_alive else 0.0
        slack = self.STAFFING_CLOSURE_SLACK
        allowances = {"scholars": self.effective_scholars() + slack,
                      "craftsmen": household.artisans + own + slack}
        for trade in trades:
            allowances[trade] = household.employees.get(trade, 0.0) + 0.01
        return allowances

    def _staffing_shortfalls(self, totals):
        """Resource -> amount held beyond what the household carries (short ones only)."""
        allowances = self._staffing_allowances(
            [resource for resource in totals if resource not in ("scholars", "craftsmen")])
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
        order = sorted(draws, key=lambda node_id: (net_value[node_id], node_id))
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
