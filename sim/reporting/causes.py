"""The cause book: why a seat's wage, state notice and concerns moved, kept per seat (reporting/cause_rules.py has the rules)."""
from typing import Any, Dict, List, Optional

from sim.agents.api import demand_answer
from sim.assembly.api import Part

from . import cause_rules


class Causes(Part):
    """Needs: year, money_per_labour_hour, state_reach, headcount, acting_balance, standing, visible_scale."""

    def note_concern_change(self, command: Any) -> None:
        """A concern opened or closed: the row carries what the node earns and costs a year."""
        cause_rules.append_row(self.seat.cause_rows, command.kind, command.node_id, command.cause, 1.0,
                               {"revenue": command.revenue, "upkeep": command.upkeep})

    def note_wage_shock(self, command: Any) -> None:
        """A shock hit; name it, to be given its share of the wage change when the period closes."""
        cause_rules.append_row(self.seat.cause_rows, cause_rules.WAGE, "wage", command.cause, 0.0, {"unmeasured": True})

    def close_cause_period(self, command: Any) -> None:
        """End the open period of the acting seat's cause book and take the readings the next one is measured from."""
        standing = self.needs.standing()
        now = {"wage": self.needs.money_per_labour_hour(), "state_reach": self.needs.state_reach(),
               "headcount": self.needs.headcount(),
               "wealth": demand_answer.visible_wealth(self.needs.acting_balance(), standing["concealed"]),
               "eminence": standing["eminence"], "defiance": standing["defiance"]}

        def notice_of(capacity: float, headcount: float, wealth: float, eminence: float, defiance: float) -> float:
            return capacity * self.needs.visible_scale(headcount, wealth, eminence, defiance)
        self.seat.cause_rows = cause_rules.close_period(self.seat.cause_rows, self.seat.cause_mark, now, self.needs.year(), notice_of)
        self.seat.cause_mark = now

    def cause_rows(self, kind: Optional[str] = None, years: Optional[int] = None) -> List[Dict[str, Any]]:
        """The acting seat's rows of one kind (all kinds when None) from the latest `years` years, oldest first."""
        return cause_rules.rows_of(self.seat.cause_rows, self.needs.year(), kind, years)

    def causes_since(self, kind: str, year: Optional[int]) -> Dict[str, float]:
        """Signed amount per cause for `kind` since the snapshot of `year` (all kept rows when None)."""
        return cause_rules.totals_since(self.seat.cause_rows, kind, year)
