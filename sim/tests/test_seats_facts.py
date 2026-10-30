"""The seats module's own facts: the automatic policy, the patronage figures, the goal's closure and the win condition's sentence.
Each is a method of the module over written-out views and a plain seat state."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.seats import founder_rules
from sim.seats.api import ForgetGoalClosure, RememberGoalClosure
from sim.seats.module import Seats
from sim.seats.state import SeatsSeat
from sim.tests import module_harness


def seats_over(views, acting="founder", seat=None):
    module = module_harness.build(Seats, seat=seat or SeatsSeat(), views=views)
    module.clock.act_as(acting)
    return module


class AutomaticPolicyRule(unittest.TestCase):

    def test_a_policy_the_seat_set_is_answered_whatever_the_mode(self):
        self.assertTrue(founder_rules.automatic_policy({"auto_hire": True}, "auto_hire", manual=True))
        self.assertFalse(founder_rules.automatic_policy({"auto_hire": False}, "auto_hire", manual=False))

    def test_a_policy_not_set_follows_the_mode(self):
        self.assertTrue(founder_rules.automatic_policy({}, "auto_hire", manual=False))
        self.assertFalse(founder_rules.automatic_policy({}, "auto_hire", manual=True))

    def test_a_seat_with_no_policies_follows_the_mode(self):
        self.assertTrue(founder_rules.automatic_policy(None, "auto_mine", manual=False))


class AutomaticPolicyView(unittest.TestCase):

    def test_the_seats_own_setting_comes_through(self):
        module = seats_over({"automation": {"manual": False, "bounty_set": False}}, seat=SeatsSeat(policy={"auto_mine": False}))
        self.assertFalse(module.automatic_policy("auto_mine"))
        self.assertTrue(module.automatic_policy("auto_hire"))


class PatronageRules(unittest.TestCase):

    def test_the_founders_age_grows_with_the_years_since_the_start(self):
        self.assertEqual(founder_rules.founder_age(40, 120, 100), 60)

    def test_deputies_work_hours_in_proportion_to_their_number(self):
        self.assertEqual(founder_rules.deputy_hours(0.5, 1000.0), 500.0)

    def test_deputies_carry_the_work_at_the_level_needed_and_above(self):
        self.assertTrue(founder_rules.deputies_carry_the_work(0.5, 0.5))
        self.assertFalse(founder_rules.deputies_carry_the_work(0.49, 0.5))


class PatronageView(unittest.TestCase):

    def test_the_figures_come_from_the_staff_the_year_and_the_terms(self):
        module = seats_over({"game_config": {"founder_arrival_age": 40, "start_year": 100, "director_hours_per_year": 800.0},
                             "year": 110, "staff": {"directors_extra": 1.0}, "dissolution_terms": {"deputies_needed": 0.5}})
        self.assertEqual(module.patronage(), {"founder_age": 50, "deputies": 1.0, "deputy_hours": 800.0,
                                              "deputies_needed": 0.5, "deputies_carry_the_work": True})


class GoalClosureKept(unittest.TestCase):

    def test_nothing_is_known_until_a_closure_is_remembered(self):
        self.assertIsNone(seats_over({}).goal_closure())

    def test_a_remembered_closure_comes_back_for_that_seat_only(self):
        module = seats_over({})
        module.remember_goal_closure(RememberGoalClosure({"a", "b"}))
        self.assertEqual(module.goal_closure(), {"a", "b"})
        module.clock.act_as("other")
        self.assertIsNone(module.goal_closure())

    def test_forgetting_drops_it(self):
        module = seats_over({})
        module.remember_goal_closure(RememberGoalClosure({"a"}))
        module.forget_goal_closure(ForgetGoalClosure())
        self.assertIsNone(module.goal_closure())

    def test_an_empty_closure_is_kept_as_empty_not_as_unknown(self):
        module = seats_over({})
        module.remember_goal_closure(RememberGoalClosure(set()))
        self.assertEqual(module.goal_closure(), set())


class WinConditionTextView(unittest.TestCase):

    def test_the_sentence_is_built_from_the_labels_the_content_module_gives(self):
        module = seats_over({"win_condition_labels": {"literacy_general": "literacy reaches %s"}})
        node = {"win_condition": {"metric": "literacy_general", "op": ">=", "value": 0.5}}
        self.assertEqual(module.win_condition_text(node), "literacy reaches 50%")


if __name__ == "__main__":
    unittest.main()
