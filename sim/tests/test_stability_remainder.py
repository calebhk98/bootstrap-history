"""Complaint 486, the rest: a ruler's competence and what it does to reach and officials' take, the army as a faction (pay owed,
plunder, loyalty, what it backs and when it rises) and the strata's real incomes as grievance. Each test calls one rule."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.actors import country_rules
from sim.agents import army_faction, authority, group_servants, ruler, unrest


def world(**members):
    return SimpleNamespace(collection=SimpleNamespace(**members))


class CompetenceTests(unittest.TestCase):

    def test_the_median_draw_is_an_average_ruler_and_the_tails_are_weak_and_strong(self):
        self.assertAlmostEqual(ruler.draw_competence(0.5), 1.0)
        self.assertLess(ruler.draw_competence(0.05), 1.0)
        self.assertGreater(ruler.draw_competence(0.95), 1.0)

    def test_an_averaged_council_is_the_same_competence_whatever_the_draw(self):
        self.assertEqual(ruler.draw_competence(0.01, averaged=True), 1.0)
        self.assertEqual(ruler.draw_competence(0.99, averaged=True), 1.0)

    def test_a_weak_ruler_reaches_less_and_officials_keep_more(self):
        self.assertAlmostEqual(ruler.reach_factor(0.5), 0.5)
        self.assertEqual(ruler.reach_factor(2.0), 1.0)
        self.assertAlmostEqual(authority.kept_on(world(corruption_share=lambda tiles: 0.2), None, 0.5), 0.4)
        self.assertAlmostEqual(authority.kept_on(world(corruption_share=lambda tiles: 0.2), None, 2.0), 0.1)
        self.assertEqual(authority.kept_on(world(corruption_share=lambda tiles: 0.8), None, 0.1), 1.0)
        self.assertAlmostEqual(authority.levy_reach(world(collectible_share=lambda tiles=None: 0.4), 0.5), 0.2)


class ArmyFactionTests(unittest.TestCase):

    def test_plunder_covers_the_unpaid_part_of_the_fall_in_pay(self):
        self.assertAlmostEqual(army_faction.fall_after_plunder(0.4, arrears=100.0, plunder=25.0), 0.3)
        self.assertEqual(army_faction.fall_after_plunder(0.4, arrears=100.0, plunder=100.0), 0.0)
        self.assertEqual(army_faction.fall_after_plunder(0.4, arrears=0.0, plunder=0.0), 0.4)

    def test_captives_taken_are_plunder_by_years_of_pay(self):
        self.assertAlmostEqual(army_faction.plunder_of_captives(10.0, 50.0),
                               10.0 * 50.0 * army_faction.CAPTIVE_VALUE_IN_YEARS_OF_UNSKILLED_PAY)

    def test_an_army_defects_by_how_far_its_loyalty_is_below_the_mutiny_line(self):
        self.assertEqual(army_faction.defecting_share(group_servants.MUTINY_LOYALTY + 0.1), 0.0)
        self.assertAlmostEqual(army_faction.defecting_share(0.0), 1.0)
        self.assertAlmostEqual(army_faction.defecting_share(0.3 * group_servants.MUTINY_LOYALTY), 0.7)

    def test_the_army_joins_the_factions_backing_only_when_it_defects(self):
        self.assertEqual(army_faction.with_army({"a": 2.0}, 0.0), {"a": 2.0})
        backing = army_faction.with_army({"a": 2.0, "b": 1.0}, 0.5)
        self.assertAlmostEqual(backing[group_servants.SOLDIERS], 0.5 * 3.0 * army_faction.ARMY_WEIGHT_SHARE_OF_FACTIONS)

    def test_a_defecting_army_leaves_the_garrison_weaker_and_rises_with_its_soldiers(self):
        self.assertAlmostEqual(army_faction.remaining_garrison(10.0, 0.3), 7.0)
        self.assertAlmostEqual(army_faction.rising_soldiers(1000.0, 0.3), 300.0)
        self.assertEqual(army_faction.rising_soldiers(1000.0, 0.0), 0.0)


class StratumGrievanceTests(unittest.TestCase):

    def test_real_income_below_what_a_stratum_expects_is_its_grievance(self):
        self.assertAlmostEqual(unrest.stratum_grievance(0.6, 1.0), 0.4)
        self.assertEqual(unrest.stratum_grievance(1.2, 1.0), 0.0)
        self.assertEqual(unrest.stratum_grievance(0.5, 0.0), 0.0)

    def test_every_stratum_of_the_owner_counts_with_people_in_it(self):
        def stratum(country, members, welfare, reference):
            return SimpleNamespace(record=SimpleNamespace(country=country, members=members, welfare=welfare, welfare_reference=reference))
        strata = [stratum(None, 10.0, 0.5, 1.0), stratum("gaul", 4.0, 1.0, 1.0), stratum(None, 0.0, 0.1, 1.0)]
        self.assertEqual(country_rules.stratum_grievances(strata, "rome", "rome"), [(10.0, 0.5)])
        self.assertEqual(country_rules.stratum_grievances(strata, "rome", "gaul"), [(4.0, 0.0)])

    def test_the_felt_grievance_is_the_larger_of_the_groups_and_the_strata_not_their_sum(self):
        self.assertAlmostEqual(unrest.felt_pressure(0.2, 0.5), 0.5)
        self.assertAlmostEqual(unrest.felt_pressure(0.6, 0.5), 0.6)


if __name__ == "__main__":
    unittest.main()
