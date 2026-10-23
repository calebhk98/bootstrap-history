"""historical_events: what a dated hazard becomes under its `condition` (Complaint 640: rules on built
hazards; the telling is in test_resolve_hazard_condition_telling)."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.engine.hazard_condition import hazard_given_condition


def _hazard(condition=None, **fields):
    hazard = {"name": "test hazard", "output_factor": 0.6, "sack_chance": 0.3, "staff_loss": 0.2}
    hazard.update(fields)
    if condition is not None:
        hazard["condition"] = condition
    return hazard


_avert = {"field": "output_factor", "requires_all": ["x"], "outcome": "avert"}
_alter = {"field": "output_factor", "requires_all": ["x"], "outcome": "alter", "alter_scale": 0.5}

_unmet = hazard_given_condition(_hazard(_avert), False)
check("a condition not met leaves the hazard exactly as written", _unmet == _hazard(_avert), _unmet)

_averted = hazard_given_condition(_hazard(_avert), True)
check("avert drops the one named field and leaves the sack risk and staff loss alone",
      "output_factor" not in _averted and _averted["sack_chance"] == 0.3 and _averted["staff_loss"] == 0.2, _averted)

_source = _hazard(_avert)
hazard_given_condition(_source, True)
check("the input hazard is not mutated (a shallow copy is adjusted)", "output_factor" in _source, _source)

_altered = hazard_given_condition(_hazard(_alter), True)
check("alter on output_factor keeps alter_scale of the shortfall (1 minus the factor)",
      abs(_altered["output_factor"] - (1.0 - 0.4 * 0.5)) < 1e-9 and _altered["sack_chance"] == 0.3, _altered)

_altered_loss = hazard_given_condition(_hazard({"field": "staff_loss", "requires_all": [], "outcome": "alter", "alter_scale": 0.25}), True)
check("alter on any other field scales the field itself", abs(_altered_loss["staff_loss"] - 0.05) < 1e-9, _altered_loss)

_no_field = _hazard({"field": "values", "requires_all": [], "outcome": "avert"})
check("a condition naming a field the hazard lacks changes nothing", hazard_given_condition(_no_field, True) == _no_field, _no_field)

_plain = _hazard()
check("a hazard with no condition is returned untouched", hazard_given_condition(_plain, True) is _plain, _plain)

_diocletian = next(hazard for hazard in S.load_civ("rome_100ad")["hazards"] if hazard["name"] == "Diocletian's reforms and the Price Edict")
check("a purely political hazard in the civilisation file carries no condition", "condition" not in _diocletian, _diocletian)
