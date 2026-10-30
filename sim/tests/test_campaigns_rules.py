"""The campaigns module's rules (`sim/campaigns/rules.py`), one function per test on written-out records and numbers."""
QUICK_TOPIC = True

import unittest

from sim.campaigns import rules
from sim.refusal import Refusal
from sim.world.army_record import Army

OWNER, RIVAL = "rome", "han"


def record(army_id="a1", owner=OWNER, soldiers=100.0, tile="t_home"):
    return Army(army_id, owner, tile, soldiers, 10.0, food_kg=40.0, animals=8.0, pay_owed=20.0, home_tile="t_home").to_dict()


class ArmyIdTests(unittest.TestCase):

    def test_the_id_is_the_counter_after_the_word_army(self):
        self.assertEqual(rules.army_id(7), "army_7")


class OwnArmyTests(unittest.TestCase):

    def test_the_owners_army_is_handed_back_as_an_army(self):
        found = rules.own_army({"a1": record()}, OWNER, "a1")
        self.assertEqual((found.army_id, found.owner, found.soldiers), ("a1", OWNER, 100.0))

    def test_an_unknown_army_is_refused_with_the_owners_armies_as_choices(self):
        refused = rules.own_army({"a1": record(), "a2": record("a2", RIVAL), "a0": record("a0")}, OWNER, "a9")
        self.assertIsInstance(refused, Refusal)
        self.assertEqual((refused.cause, refused.choices), ("unknown_army", ["a0", "a1"]))

    def test_another_owners_army_is_refused(self):
        self.assertEqual(rules.own_army({"a1": record()}, RIVAL, "a1").cause, "not_your_army")


class OrderTests(unittest.TestCase):

    def test_an_order_sets_the_target_and_clears_the_progress(self):
        army = Army("a1", OWNER, "t_home", 100.0, 10.0, progress_days=3.0)
        rules.order(army, "t_far")
        self.assertEqual((army.target, army.progress_days), ("t_far", 0.0))

    def test_an_order_to_where_the_army_stands_clears_the_target(self):
        army = Army("a1", OWNER, "t_home", 100.0, 10.0, target="t_far")
        rules.order(army, "t_home")
        self.assertIsNone(army.target)


class RecallTileTests(unittest.TestCase):

    def test_a_home_tile_still_the_owners_is_where_the_army_goes(self):
        self.assertEqual(rules.recall_tile("t_home", OWNER, OWNER, ["t_a", "t_b"]), "t_home")

    def test_a_lost_home_tile_sends_the_army_to_a_tile_the_owner_holds(self):
        self.assertIn(rules.recall_tile("t_home", RIVAL, OWNER, ["t_a", "t_b"]), ["t_a", "t_b"])

    def test_an_owner_with_no_tile_has_nowhere_to_recall_to(self):
        self.assertIsNone(rules.recall_tile("t_home", None, OWNER, []))


class KeepWithinForceTests(unittest.TestCase):

    def test_armies_over_the_force_are_scaled_by_the_same_share_and_the_emptied_are_dropped(self):
        records = {"a1": record("a1", soldiers=300.0), "a2": record("a2", soldiers=100.0), "b1": record("b1", RIVAL, 50.0)}
        kept = rules.keep_within_force(records, [OWNER, RIVAL], {OWNER: 200.0, RIVAL: 500.0})
        self.assertEqual({key: value["soldiers"] for key, value in kept.items()}, {"a1": 150.0, "a2": 50.0, "b1": 50.0})
        self.assertEqual(kept["a1"]["food_kg"], 20.0)

    def test_an_army_scaled_below_one_soldier_is_not_kept(self):
        kept = rules.keep_within_force({"a1": record("a1", soldiers=100.0)}, [OWNER], {OWNER: 0.5})
        self.assertEqual(kept, {})

    def test_armies_of_an_owner_not_listed_are_left_alone(self):
        records = {"b1": record("b1", RIVAL, 50.0)}
        self.assertEqual(rules.keep_within_force(records, [OWNER], {OWNER: 0.0}), records)


class StateGrievanceTests(unittest.TestCase):

    def test_no_visible_taxpayer_income_is_no_reading(self):
        self.assertIsNone(rules.state_grievance(0.0, 10.0, 2000.0, 100.0, 50.0, 0.0, 0.0, 0.0))

    def test_what_is_taken_and_owed_beyond_the_dole_is_a_grievance_against_the_income(self):
        taken_more = rules.state_grievance(1000.0, 10.0, 2000.0, 400.0, 100.0, 0.0, 0.0, 0.0)
        taken_less = rules.state_grievance(1000.0, 10.0, 2000.0, 400.0, 50.0, 0.0, 0.0, 0.0)
        self.assertGreater(taken_more, taken_less)

    def test_the_dole_that_was_paid_lowers_the_grievance(self):
        unpaid = rules.state_grievance(1000.0, 10.0, 2000.0, 0.0, 100.0, 50.0, 50.0, 50.0)
        paid = rules.state_grievance(1000.0, 10.0, 2000.0, 0.0, 100.0, 50.0, 0.0, 0.0)
        self.assertLess(paid, unpaid)

    def test_a_corvee_with_no_hours_in_the_year_costs_nothing(self):
        self.assertEqual(rules.state_grievance(1000.0, 10.0, 0.0, 400.0, 100.0, 0.0, 0.0, 0.0),
                         rules.state_grievance(1000.0, 10.0, 2000.0, 0.0, 100.0, 0.0, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
