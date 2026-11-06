"""A need plays a role in the economy's books (hunger, fuel, household work) by the `role` field in data/world/needs.json,
as a trade does in trades.json (sim/economy/need_roles.py)."""
QUICK_TOPIC = True

import os
import unittest

from sim.content.mods import ModError
from sim.content.need_data import check_needs
from sim.economy import need_roles
from sim.json_files import read_json

NEEDS = {"needs": {"b_meal": {"role": "hunger"}, "a_meal": {"role": "hunger"}, "stove": {"role": "fuel"}, "plain": {}}}
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "world", "needs.json")


class NeedOfRoleTests(unittest.TestCase):
    def test_the_need_with_the_role_is_found(self):
        self.assertEqual(need_roles.need_of_role(NEEDS, need_roles.FUEL_ROLE), "stove")

    def test_a_role_two_needs_have_is_refused(self):
        with self.assertRaises(ValueError):
            need_roles.need_of_role(NEEDS, need_roles.HUNGER_ROLE)

    def test_a_role_no_need_has_is_refused(self):
        with self.assertRaises(ValueError):
            need_roles.need_of_role(NEEDS, need_roles.HOUSEHOLD_WORK_ROLE)


class CheckNeedsTests(unittest.TestCase):
    def test_two_needs_with_one_role_are_refused(self):
        needs = {"a": {"surplus_budget_share": 0.1, "role": "hunger"}, "b": {"surplus_budget_share": 0.1, "role": "hunger"}}
        with self.assertRaises(ModError):
            check_needs(needs, {})

    def test_distinct_roles_pass(self):
        check_needs({"a": {"surplus_budget_share": 0.1, "role": "hunger"}, "b": {"surplus_budget_share": 0.1, "role": "fuel"}}, {})


class DataRolesTests(unittest.TestCase):
    def test_the_data_has_a_need_for_each_role(self):
        data = read_json(DATA_PATH)
        for role in (need_roles.HUNGER_ROLE, need_roles.FUEL_ROLE, need_roles.HOUSEHOLD_WORK_ROLE):
            self.assertIn(need_roles.need_of_role(data, role), data["needs"])


if __name__ == "__main__":
    unittest.main()
