"""The module's judgement of a dated event against its stated causes (Complaints/266).

Needs: opening_civilisation, civilisation, population_total, real_output_hours, literacy, nutrition_ratio_last_year,
state_budget_figures, army_figures, state_knows, home_strata_rows, tiles_listed_by."""
from typing import Any, Dict, Optional, Tuple

from . import cause_report
from .cause_quantities import QUANTITIES


class Causes:

    def event_cause_report(self, hazard: Dict[str, Any]) -> Dict[str, Any]:
        """`{checked, conditions, failed, strength}` for an event, each cause read from its owner's view as things stand."""
        rows = []
        for cause in hazard.get("causes") or []:
            quantity = QUANTITIES[cause["quantity"]]
            start_value = None
            if cause.get("relative_to_start"):
                start_value = self.needs.opening_civilisation().get(quantity.start_field)
            rows.append(cause_report.judge_cause(cause, quantity.read(self.needs, cause.get("node")), start_value))
        return cause_report.report_of(hazard, rows)

    def effective_hazard(self, hazard: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """(the event as its stated causes leave it now, or None when they skip it; the report of which causes hold)."""
        report = self.event_cause_report(hazard)
        return cause_report.hazard_after_causes(hazard, report), report
