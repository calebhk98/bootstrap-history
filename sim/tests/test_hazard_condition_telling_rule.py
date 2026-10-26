"""A hazard with a `condition` is resolved against what the household has, and the player is told which way it went, once
(`HazardsMixin._resolve_hazard_condition`, called on a stand-in game that holds only the tech set and the log)."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.engine.society_hazards import HazardsMixin
from sim.refusal import cause_of, facts_of
from sim.tests import event_stand_in


def stand_in_game(known):
    log = []
    return event_stand_in.stood_in(SimpleNamespace(has=lambda tech_id: tech_id in known, state=SimpleNamespace(
        scenario=SimpleNamespace(_said_condition=set(), year=100), household=SimpleNamespace(log=log)))), log


def crossing():
    return {"name": "The crossings", "output_factor": 0.6, "sack_chance": 0.3, "staff_loss": 0.2,
            "condition": {"field": "output_factor", "requires_all": ["rotation", "land"], "outcome": "avert",
                          "met_message": "you feed yourself", "unmet_message": "the grain fleet fails"}}


def resolve(game, year=406, start=406):
    return HazardsMixin._resolve_hazard_condition(game, crossing(), year, start)


class TellingTheCondition(unittest.TestCase):
    def test_a_condition_not_met_fires_as_written_and_says_so_with_its_cause(self):
        game, log = stand_in_game({"rotation"})
        result = resolve(game)
        self.assertEqual(result["output_factor"], 0.6)
        self.assertEqual([cause_of(line) for _year, line in log], ["hazard_condition_unmet"])
        self.assertEqual(facts_of(log[0][1])["hazard"], "The crossings")

    def test_a_condition_met_averts_the_field_and_says_so_with_its_cause(self):
        game, log = stand_in_game({"rotation", "land"})
        result = resolve(game)
        self.assertNotIn("output_factor", result)
        self.assertIn("sack_chance", result)
        self.assertIn("staff_loss", result)
        self.assertEqual([cause_of(line) for _year, line in log], ["hazard_condition_met"])

    def test_the_hazard_is_told_once_however_often_its_window_is_resolved(self):
        game, log = stand_in_game({"rotation", "land"})
        resolve(game)
        resolve(game)
        self.assertEqual(len(log), 1)

    def test_a_year_inside_the_window_but_not_its_first_says_nothing(self):
        game, log = stand_in_game(set())
        resolve(game, year=407, start=406)
        self.assertEqual(log, [])

    def test_a_hazard_with_no_condition_is_returned_untouched_and_unannounced(self):
        game, log = stand_in_game(set())
        plain = {"name": "plain", "output_factor": 0.5}
        self.assertIs(HazardsMixin._resolve_hazard_condition(game, plain, 406, 406), plain)
        self.assertEqual(log, [])


if __name__ == "__main__":
    unittest.main()
