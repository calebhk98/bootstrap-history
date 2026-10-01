"""Who left the payroll and why, which specialists nothing uses, and which
open concern hangs on a single person.

Methods of Sim, a mixin only so they live in a file of their own. Written
against the household actor's `employees`, so a firm or state can use them.
"""
import math

GENERIC_TRADES = ("artisan", "scholar", "labourer", "slave")


class StaffLedgerMixin:

    def staff_snapshot(self):
        """Headcount by trade now, to diff against after something trims it."""
        return dict(self.state.household.employees)

    def log_staff_reduction(self, cause, before):
        """Log every trade whose headcount fell since `before`, with why.

        `cause` completes "you lose <people> to <cause>"."""
        now = self.state.household.employees
        parts = []
        for trade in sorted(before):
            drop = before[trade] - now.get(trade, 0.0)
            if drop <= 0.005:
                continue
            count = ("%d" % round(drop) if abs(drop - round(drop)) < 0.05
                     else "%.1f" % drop)
            parts.append("%s %s%s" % (count, trade, "" if count == "1" else "s"))
        if parts:
            self.state.household.log.append(
                (self.state.scenario.year, "you lose %s to %s" % (", ".join(parts), cause)))

    def trades_drawn_on(self):
        """Specialist trades some active project or open concern needs, with why."""
        drawn = {}
        projects = self.state.projects
        for node_id in sorted(projects.active):
            node = self.nodes.get(node_id)
            if not node:
                continue
            record = projects.active[node_id]
            lab_left = (record.get("lab_left") if isinstance(record, dict)
                        else getattr(record, "lab_left", None)) or node.get("lab") or {}
            for trade, hours in lab_left.items():
                if trade not in GENERIC_TRADES and hours > 0:
                    drawn.setdefault(trade, []).append("project " + node_id)
        for trade in sorted(self.venture_foremen_used()):
            drawn.setdefault(trade, []).append("open concern")
        return drawn

    def idle_specialists(self):
        """Specialists on the payroll that no active project or open concern
        draws on, with what they cost a year."""
        drawn = self.trades_drawn_on()
        rows = []
        for trade, count in sorted(self.state.household.employees.items()):
            if trade in GENERIC_TRADES or trade in drawn or count < 0.5:
                continue
            rows.append({"trade": trade, "count": round(count, 1),
                         "wage_bill_per_year": round(count * self.labour_market.quote_annual(trade), 1),
                         "taught_by_you": trade in self.state.household.trades_created})
        return rows

    def sole_supervisors(self):
        """Open concerns whose specialist foreman trade has exactly one person."""
        rows = []
        for node_id in sorted(self.state.projects.operating):
            if node_id not in self.nodes:
                continue
            trade, _fte = self.venture_foreman(node_id)
            if trade and round(self.state.household.employees.get(trade, 0.0)) == 1:
                rows.append({"concern": self.nodes[node_id].get("name", node_id),
                             "trade": trade,
                             "warning": "depends on one %s; losing them closes it" % trade})
        return rows

    def workforce_report(self):
        """Where the payroll is fragile: single-person dependencies, expected yearly losses, reserve and training."""
        household = self.state.household
        policy = self.state.founder.policy
        return {
            "depends_on_one_person": self.sole_supervisors(),
            "expected_losses_per_year": round(sum(household.employees.values()) * self.STAFF_ATTRITION_RATE, 2),
            "reserve": ({"craftsmen": household.reserve_craftsmen, "scholars": household.reserve_scholars}
                        if policy.get("reserve_staff", False) else None),
            "in_training": len(household.training),
        }

    def hire_to_cover(self, trade, short, label, partial=False):
        """Hire `short` whole people of `trade` for a stated policy; the count taken on.

        `partial` takes as many as the household has room for instead of
        refusing the lot. The wall, the cash and the literacy limit are
        `hire`'s own, so a refusal simply hires nobody."""
        if short <= 0:
            return 0
        if partial:
            short = min(short, max(0, int(self.household_room() + 1e-9)))
            if short <= 0:
                return 0
        hired, _why = self.hire(trade, short)
        if not hired:
            return 0
        self.state.household.log.append((self.state.scenario.year,
                                         "%s: you hire %d %s%s to keep your concerns supervised"
                                         % (label, short, trade, "" if short == 1 else "s")))
        return short

    def replace_lost_foremen(self):
        """auto_replace_foreman: hire the specialists open concerns need and lack."""
        household = self.state.household
        for trade, used in sorted(self.venture_foremen_used().items()):
            short = math.ceil(used - household.employees.get(trade, 0.0) - 0.01)
            self.hire_to_cover(trade, short, "auto_replace_foreman")
