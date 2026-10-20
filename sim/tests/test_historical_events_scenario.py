"""Scenarios: a hazard's condition is resolved on a live game and the player is told which way it went
(Complaint 640). The rules are in test_historical_events."""
from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of, facts_of

_rome_crossing = next(hazard for hazard in S.load_civ("rome_100ad")["hazards"] if hazard["name"] == "The crossings, and the sack of Rome")

_unmet_game = sim(civ="rome_100ad")
_unmet = _unmet_game._resolve_hazard_condition(dict(_rome_crossing), 406, 406)
check("Rome, dependent on the African grain fleet: the hazard fires as written and the player is told why",
      _unmet.get("output_factor") == _rome_crossing["output_factor"]
      and cause_of(_unmet_game.log[0][1]) == "hazard_condition_unmet"
      and facts_of(_unmet_game.log[0][1])["hazard"] == _rome_crossing["name"],
      _unmet_game.log)

_met_game = sim(civ="rome_100ad")
run_it(_met_game, "endowment_land", "crop_rotation")
_met = _met_game._resolve_hazard_condition(dict(_rome_crossing), 406, 406)
check("a household that feeds itself has the output hit averted and is told with the real cause",
      "output_factor" not in _met and "sack_chance" in _met and "staff_loss" in _met
      and cause_of(_met_game.log[0][1]) == "hazard_condition_met"
      and facts_of(_met_game.log[0][1])["hazard"] == _rome_crossing["name"],
      _met)

_met_game._resolve_hazard_condition(dict(_rome_crossing), 406, 406)
check("the same hazard is told once, however many times its window is resolved",
      sum(1 for _year, line in _met_game.log if cause_of(line) == "hazard_condition_met") == 1, _met_game.log)
