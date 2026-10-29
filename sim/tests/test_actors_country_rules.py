"""The cast's answers about countries and treasuries (sim/actors/country_rules.py), each a plain function of written-out inputs."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.actors import country_rules


def group(country, members, grievance, organised):
    return SimpleNamespace(record=SimpleNamespace(country=country, members=members, grievance=grievance), organised=lambda: organised)


def stratum(country, members, literacy):
    return SimpleNamespace(record=SimpleNamespace(country=country, members=members, literacy=literacy, exited_year=None, plan={}))


class CountryRulesTests(unittest.TestCase):
    def test_the_home_country_and_the_countries_of_the_cast_have_states(self):
        countries = {"gaul": object()}
        self.assertEqual([country_rules.is_country_with_state(owner, "rome", countries) for owner in ("rome", "gaul", "colony")],
                         [True, True, False])

    def test_the_home_country_facts_hold_its_centre_or_none(self):
        self.assertEqual(country_rules.home_country_facts("rome", {"rome": SimpleNamespace(location="t1")}), {"id": "rome", "location": "t1"})
        self.assertEqual(country_rules.home_country_facts("rome", {}), {"id": "rome", "location": None})

    def test_only_organised_groups_of_the_owner_count_and_an_unset_country_is_home(self):
        groups = [group(None, 10.0, 0.5, True), group("gaul", 4.0, 0.2, True), group(None, 7.0, 0.9, False)]
        self.assertEqual(country_rules.organised_factions(groups, "rome", "rome"), [(10.0, 0.5)])
        self.assertEqual(country_rules.organised_factions(groups, "rome", "gaul"), [(4.0, 0.2)])

    def test_dues_go_to_a_seat_itself_else_to_the_government_else_to_the_id_it_would_have(self):
        self.assertEqual(country_rules.treasury_account("seat_a", ["seat_a"], "government:seat_a"), "seat_a")
        self.assertEqual(country_rules.treasury_account("gaul", ["seat_a"], "government:gaul"), "government:gaul")
        self.assertEqual(country_rules.treasury_account("gaul", [], None), "government:gaul")

    def test_a_countrys_literacy_is_read_from_its_own_strata(self):
        registry = SimpleNamespace(state=SimpleNamespace(home_country="rome"),
                                   of_kind=lambda kind: [stratum(None, 10.0, 0.2), stratum("gaul", 10.0, 0.6)])
        self.assertAlmostEqual(country_rules.country_literacy(registry, None).get("literacy_general"), 0.2)
        self.assertAlmostEqual(country_rules.country_literacy(registry, "gaul").get("literacy_general"), 0.6)


if __name__ == "__main__":
    unittest.main()
