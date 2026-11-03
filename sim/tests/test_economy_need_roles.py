"""A need plays a role in the economy's books (hunger, fuel, household work) by the `role` field in data/world/needs.json,
as a trade does in trades.json (sim/economy/need_roles.py)."""
QUICK_TOPIC = True

import os
import unittest

from sim.economy import legacy_need_defaults, need_roles
from sim.json_files import read_json

NEEDS = {"needs": {"b_meal": {"role": "hunger"}, "a_meal": {"role": "hunger"}, "stove": {"role": "fuel"}, "plain": {}}}
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "world", "needs.json")


class NeedOfRoleTests(unittest.TestCase):
    def test_the_need_with_the_role_is_found(self):
        self.assertEqual(need_roles.need_of_role(NEEDS, need_roles.FUEL_ROLE), "stove")

    def test_the_first_by_id_wins_when_several_have_the_role(self):
        self.assertEqual(need_roles.need_of_role(NEEDS, need_roles.HUNGER_ROLE), "a_meal")

    def test_a_role_no_need_has_is_refused(self):
        with self.assertRaises(ValueError):
            need_roles.need_of_role(NEEDS, need_roles.HOUSEHOLD_WORK_ROLE)


class DataRolesTests(unittest.TestCase):
    def test_the_data_roles_name_the_setup_fallbacks(self):
        data = read_json(DATA_PATH)
        self.assertEqual(need_roles.need_of_role(data, need_roles.HUNGER_ROLE), legacy_need_defaults.HUNGER_NEED_ID)
        self.assertEqual(need_roles.need_of_role(data, need_roles.FUEL_ROLE), legacy_need_defaults.FUEL_NEED_ID)
        self.assertEqual(need_roles.need_of_role(data, need_roles.HOUSEHOLD_WORK_ROLE), legacy_need_defaults.WORK_NEED_ID)


if __name__ == "__main__":
    unittest.main()
