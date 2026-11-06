"""Who left the payroll and why, which specialists nothing uses, and which open concern hangs on a single person.

Written against the household actor's `employees`, so a firm or state can use them."""

from sim.world import demography

from . import trade_data
from .staff_events import staff_lost_line
from sim.reporting.api import RecordEvent


class StaffLedger:
    def __init__(self, world, book, market):
        self._world = world
        self.book = book
        self.market = market

    def staff_snapshot(self):
        """Headcount by trade now, to diff against after something trims it."""
        return self.book.employed_by_trade()

    def log_staff_lost(self, cause, counts):
        """Log people who left, by trade, with why and which running concerns the loss leaves unstaffed.

        `cause` completes "you lose <people> to <cause>". A loss that leaves a concern the staffing rule will
        shut is its own kind of event, one that stops a multi-year step."""
        if not any(count > 0 for count in counts.values()):
            return
        world = self._world
        stops = sorted(world.ventures.concerns_to_close_for_staffing())
        # plain line: staff_lost_line builds the LogLine and its kind
        self._world.send(RecordEvent.from_line(staff_lost_line(
            cause, counts, stops, self.yearly_value_of(stops))))

    def yearly_value_of(self, node_ids):
        """What the named running concerns take in a year, as the ledger credits it."""
        return self._world.ventures.stopped_yearly_value(node_ids)

    def log_staff_reduction(self, cause, before):
        """Log every trade whose headcount fell since `before`, with why."""
        now = self.book.employed_by_trade()
        self.log_staff_lost(cause, {trade: before[trade] - now.get(trade, 0.0) for trade in sorted(before)
                                    if before[trade] - now.get(trade, 0.0) > 0.005})

    def _generic_staff(self):
        return trade_data.generic_staff_trades(trade_data.trade_of_role(trade_data.registry_of(self._world), "unskilled"))

    def trades_drawn_on(self):
        """Specialist trades some active project or open concern needs, with why."""
        drawn = {}
        generic = self._generic_staff()
        projects = self._world.projects
        for node_id in sorted(projects.active):
            node = self._world.scenario.nodes.get(node_id)
            if not node:
                continue
            record = projects.active[node_id]
            lab_left = record.get("lab_left")
            if lab_left is None:
                lab_left = node.get("lab") or {}
            for trade, hours in lab_left.items():
                if trade not in generic and hours > 0:
                    drawn.setdefault(trade, []).append("project " + node_id)
        for trade in sorted(self._world.ventures.venture_foremen_used()):
            drawn.setdefault(trade, []).append("open concern")
        return drawn

    def idle_specialists(self):
        """Specialists on the payroll that no active project or open concern
        draws on, with what they cost a year."""
        drawn = self.trades_drawn_on()
        generic = self._generic_staff()
        rows = []
        for trade, count in sorted(self.book.employed_by_trade().items()):
            if trade in generic or trade in drawn or count < 0.5:
                continue
            rows.append({"trade": trade, "count": round(count, 1),
                         "wage_bill_per_year": round(count * self.market.quote_annual(trade), 1),
                         "taught_by_you": trade in self._world.workforce.trades_created})
        return rows

    def sole_supervisors(self):
        """Open concerns whose specialist foreman trade has exactly one person."""
        rows = []
        for node_id in sorted(self._world.projects.operating):
            if node_id not in self._world.scenario.nodes:
                continue
            trade, _fte = self._world.ventures.venture_foreman(node_id)
            if trade and round(self.book.employed(trade)) == 1:
                rows.append({"concern": self._world.scenario.nodes[node_id].get("name", node_id),
                             "trade": trade,
                             "warning": "depends on one %s; losing them closes it" % trade})
        return rows

    def workforce_report(self):
        """Where the payroll is fragile: single-person dependencies, expected yearly losses, reserve and training."""
        workforce = self._world.workforce
        policy = self._world.game.policy
        return {
            "depends_on_one_person": self.sole_supervisors(),
            "expected_losses_per_year": round(self.book.employed_total() * demography.BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE, 2),
            "reserve": ({"craftsmen": workforce.reserve_craftsmen, "scholars": workforce.reserve_scholars}
                        if policy.get("reserve_staff", False) else None),
            "in_training": sum(row.people for row in workforce.training),
        }
