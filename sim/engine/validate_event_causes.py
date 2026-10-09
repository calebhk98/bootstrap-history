"""`validate` rejects an event whose causes name an unknown quantity, operator or technology."""
from typing import Any, List, Mapping

from . import event_causes


def check_event_causes(civilisations: Mapping[str, Mapping[str, Any]], node_ids: Any) -> List[str]:
    return ["%s: %s" % (civ_id, problem)
            for civ_id, civilisation in sorted(civilisations.items())
            for hazard in civilisation.get("hazards") or []
            for problem in event_causes.cause_problems(hazard, node_ids)]
