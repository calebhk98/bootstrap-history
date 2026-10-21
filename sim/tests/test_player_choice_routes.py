"""Complaints 225, 226, 228, 229, 232: the tree data offers routes a player can choose without the one they refuse.
Read straight off the tree; what a game does with them is in `test_player_choice_routes_scenario`.

229: the school has a paid-labour alternative to buying and freeing people.
232: lens_grinding and patron_local no longer promise each other."""

QUICK_TOPIC = True

import unittest

from sim.engine.data import closure
from sim.tests.harness import NODES


class SchoolWithoutBuyingPeople(unittest.TestCase):

    def setUp(self):
        self.school = NODES["school_founded"]
        self.groups = [group for group in self.school.get("req_any") or [] if "freedman_staff" in (group.get("options") or {})]
        self.alternatives = [option for option in (self.groups[0]["options"] if self.groups else {})
                             if option != "freedman_staff" and option in NODES]

    def test_school_founded_no_longer_hard_requires_the_buy_and_free_route(self):
        self.assertNotIn("freedman_staff", self.school["pre"])

    def test_freedman_staff_is_one_option_of_a_staffing_group(self):
        self.assertEqual(len(self.groups), 1)

    def test_the_group_has_a_second_real_node_as_an_alternative_that_does_not_buy_people(self):
        self.assertTrue(self.alternatives)
        for option in self.alternatives:
            self.assertNotIn("buys_people", NODES[option].get("traits", []), option)

    def test_the_alternative_is_paid_in_wages_for_labour_with_no_tuned_number(self):
        for option in self.alternatives:
            self.assertTrue(NODES[option]["lab"], option)
            self.assertGreater(NODES[option]["_total_cost"], 0, option)

    def test_freedman_staff_is_marked_as_buying_people(self):
        self.assertIn("buys_people", NODES["freedman_staff"].get("traits", []))

    def test_the_school_is_reachable_in_the_goal_independent_closure_without_freedman_staff(self):
        self.assertNotIn("freedman_staff", closure(NODES, "school_founded"))


class LensAndPatron(unittest.TestCase):

    def test_lens_grinding_is_behind_the_patron(self):
        self.assertIn("patron_local", closure(NODES, "lens_grinding"))

    def test_lens_grinding_s_note_does_not_claim_it_buys_the_first_patron(self):
        # presentation: what a note claims
        self.assertNotIn("buys you your first patron", NODES["lens_grinding"]["note"].lower())

    def test_patron_local_s_note_does_not_name_a_gift_that_sits_behind_the_patron(self):
        # presentation: what a note claims
        note = NODES["patron_local"]["note"].lower()
        self.assertFalse("lenses" in note and "bought" not in note, note)


if __name__ == "__main__":
    unittest.main()
