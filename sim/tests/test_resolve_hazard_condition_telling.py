"""HazardsMixin._resolve_hazard_condition on a stand-in self: the player is told which way a hazard's condition went (a log line
of kind hazard_condition_met or hazard_condition_unmet naming the hazard), once, and only the year the window opens."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.engine.society_hazards import HazardsMixin
from sim.refusal import cause_of, facts_of

HAZARD = {"name": "The crossings", "output_factor": 0.6, "sack_chance": 0.1,
          "condition": {"field": "output_factor", "requires_all": ["a", "b"], "outcome": "avert",
                        "met_message": "fed itself", "unmet_message": "depends on the fleet"}}


def stand_in(held):
    return SimpleNamespace(has=lambda tech_id: tech_id in held,
                           state=SimpleNamespace(scenario=SimpleNamespace(_said_condition=set()),
                                                 household=SimpleNamespace(log=[])))


unmet = stand_in({"a"})
result = HazardsMixin._resolve_hazard_condition(unmet, dict(HAZARD), 406, 406)
line = unmet.state.household.log[0][1]
check("an unmet condition leaves the hazard as written", result.get("output_factor") == 0.6, result)
check("...and the log line is kind unmet naming the hazard",
      (cause_of(line), facts_of(line)["hazard"]) == ("hazard_condition_unmet", "The crossings"), line)

met = stand_in({"a", "b"})
result = HazardsMixin._resolve_hazard_condition(met, dict(HAZARD), 406, 406)
check("a met condition averts the named field and keeps the rest", "output_factor" not in result and result["sack_chance"] == 0.1, result)
check("...and the log line is kind met", cause_of(met.state.household.log[0][1]) == "hazard_condition_met", met.state.household.log)
HazardsMixin._resolve_hazard_condition(met, dict(HAZARD), 406, 406)
check("the same hazard is told once however often its window start is resolved", len(met.state.household.log) == 1, met.state.household.log)

later = stand_in({"a", "b"})
HazardsMixin._resolve_hazard_condition(later, dict(HAZARD), 407, 406)
check("a later year of the window says nothing", later.state.household.log == [], later.state.household.log)

plain = stand_in(set())
check("a hazard with no condition is returned as it is, unsaid",
      HazardsMixin._resolve_hazard_condition(plain, {"name": "x"}, 1, 1) == {"name": "x"} and plain.state.household.log == [])
