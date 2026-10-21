"""Complaint 640: the state's standing lines, army size, levy and notice rules on built inputs, no game."""

QUICK_TOPIC = True

import unittest

from sim.agents import budget
from sim.agents.tuning import ADMINISTRATIVE_SPAN, ARMY_ADJUSTMENT_RATE, LEVY_RATE_CEILING
from sim.engine import state_notice_rules as rules

WAGE = {"soldier": 10.0, "scribe": 30.0}
PRICE_PER_TONNE = 200.0


class StubWorld:
    """What the line rules read of a world: wages, an equipment burden, a price for the iron, the head count."""

    def __init__(self, people=1.0e6, iron_on_sale=True):
        self.people = people
        self.iron_on_sale = iron_on_sale

    def equipment_kg_per_soldier(self):
        return 20.0

    def pay_per_person_year(self, trade):
        return WAGE[trade]

    def commodity_of(self, material):
        return "iron"

    def material_cost(self, material, tonnes):
        return tonnes * PRICE_PER_TONNE if self.iron_on_sale else None

    def population_total(self):
        return self.people


class StandingLines(unittest.TestCase):
    def test_army_pay_is_the_paid_soldiers_at_the_soldier_wage_and_all_of_them_wear_iron(self):
        line = budget.army_line(StubWorld(), 1000.0, conscripts=250.0)[0]
        self.assertEqual(line.labour, {"soldier": 750.0})
        self.assertAlmostEqual(line.wages, 750.0 * WAGE["soldier"])
        self.assertAlmostEqual(line.materials["iron"], 1000.0 * 20.0 / 1000.0)
        self.assertAlmostEqual(line.material_cost, line.materials["iron"] * PRICE_PER_TONNE)

    def test_no_soldiers_is_no_army_line(self):
        self.assertEqual(budget.army_line(StubWorld(), 0.0), [])

    def test_an_army_of_conscripts_draws_no_pay_but_still_wears_iron(self):
        line = budget.army_line(StubWorld(), 100.0, conscripts=100.0)[0]
        self.assertEqual((line.labour, line.wages), ({}, 0.0))
        self.assertGreater(line.material_cost, 0.0)

    def test_iron_nobody_sells_is_unbuyable_not_free(self):
        line = budget.army_line(StubWorld(iron_on_sale=False), 1000.0)[0]
        self.assertEqual(line.materials, {})
        self.assertGreater(line.unbuyable["iron"], 0.0)

    def test_officials_are_scribes_and_follow_the_people(self):
        small = budget.administration_line(StubWorld(people=ADMINISTRATIVE_SPAN * 100.0))[0]
        large = budget.administration_line(StubWorld(people=ADMINISTRATIVE_SPAN * 200.0))[0]
        self.assertAlmostEqual(small.labour["scribe"], 100.0)
        self.assertAlmostEqual(large.wages, 2.0 * small.wages)
        self.assertEqual(small.materials, {})
        self.assertEqual(budget.administration_line(StubWorld(people=0.0)), [])


class ArmySize(unittest.TestCase):
    def test_a_state_that_paid_for_its_army_moves_toward_the_force_it_wants_at_a_bounded_rate(self):
        self.assertAlmostEqual(budget.army_next_year(1000.0, 1050.0, 1.0), 1050.0)
        self.assertAlmostEqual(budget.army_next_year(1000.0, 5000.0, 1.0), 1000.0 * (1.0 + ARMY_ADJUSTMENT_RATE))

    def test_a_state_that_could_not_pay_shrinks_its_army_by_at_most_the_rate(self):
        self.assertAlmostEqual(budget.army_next_year(1000.0, 5000.0, 0.0), 1000.0 * (1.0 - ARMY_ADJUSTMENT_RATE))
        self.assertAlmostEqual(budget.army_next_year(1000.0, 5000.0, 0.95), 950.0)

    def test_the_funded_share_cuts_every_line_alike_and_never_goes_negative(self):
        self.assertEqual(budget.funded_share(100.0, 100.0), 1.0)
        self.assertEqual(budget.funded_share(0.0, 0.0), 1.0)
        self.assertAlmostEqual(budget.funded_share(100.0, 40.0), 0.4)
        self.assertEqual(budget.funded_share(100.0, -5.0), 0.0)


class ArmyWanted(unittest.TestCase):
    HAZARDS = [{"sack_chance": 0.1, "years": [200, 260]}, {"sack_chance": 0.05, "years": [230, 300]}, {"years": [0, 999]},
               {"sack_chance": 0.9}]

    def test_the_sack_pressure_adds_the_chances_of_the_hazards_running_that_year(self):
        self.assertEqual(budget.sack_pressure(self.HAZARDS, 100), 0.0)
        self.assertAlmostEqual(budget.sack_pressure(self.HAZARDS, 210), 0.1)
        self.assertAlmostEqual(budget.sack_pressure(self.HAZARDS, 240), 0.15)
        self.assertAlmostEqual(budget.sack_pressure(self.HAZARDS, 300), 0.05)

    def test_a_threat_raises_the_opening_force_and_no_threat_leaves_it(self):
        self.assertEqual(budget.army_goal(1000.0, 0.0), 1000.0)
        self.assertGreater(budget.army_goal(1000.0, 0.1), 1000.0)
        self.assertGreater(budget.army_goal(1000.0, 0.2), budget.army_goal(1000.0, 0.1))
        self.assertEqual(budget.army_goal(-5.0, 0.1), 0.0)


class StubPeople:
    def __init__(self, working_age, soldiers):
        self.working_age, self.soldiers = working_age, soldiers

    def national_people(self, trade):
        return self.working_age

    def soldiers_under_arms(self):
        return self.soldiers

    def pay_per_person_year(self, trade):
        return 7.0


class PollTax(unittest.TestCase):
    def test_soldiers_under_arms_owe_no_poll_tax_so_the_base_shrinks_with_the_army(self):
        from sim.agents import revenue_bases
        everyone = revenue_bases.adult_labour_years(StubPeople(1000.0, 0.0)).value
        garrisoned = revenue_bases.adult_labour_years(StubPeople(1000.0, 400.0)).value
        self.assertAlmostEqual(everyone, 1000.0 * 7.0)
        self.assertAlmostEqual(garrisoned, 600.0 * 7.0)
        self.assertEqual(revenue_bases.adult_labour_years(StubPeople(1000.0, 5000.0)).value, 0.0)


class StubHarvest:
    def __init__(self, tonnes):
        self.tonnes = tonnes

    def harvest_tonnes(self):
        return self.tonnes

    def material_price(self, material):
        return 3.0

    def arable_share(self, tiles):
        return 0.5


class Harvest(unittest.TestCase):
    def test_a_failed_harvest_cuts_what_the_state_can_take_and_tiles_take_their_arable_share(self):
        from sim.agents import revenue_bases
        steady = revenue_bases.harvest(StubHarvest(2000.0)).value
        slump = revenue_bases.harvest(StubHarvest(1000.0)).value
        self.assertLess(slump, steady)
        self.assertAlmostEqual(steady, 2000.0 * 3.0)
        self.assertAlmostEqual(revenue_bases.harvest(StubHarvest(2000.0), frozenset({"a"})).value, 1000.0 * 3.0)


class Levy(unittest.TestCase):
    def test_the_ask_for_arms_is_the_unfunded_army_by_the_taxpayers_part_of_visible_income(self):
        self.assertAlmostEqual(budget.military_ask_of(1000.0, 10000.0, 0.5, 4000.0), 1000.0 * 2000.0 / 10000.0)

    def test_the_ask_for_arms_never_passes_the_ceiling_on_the_taxpayers_income(self):
        self.assertAlmostEqual(budget.military_ask_of(1.0e9, 10000.0, 1.0, 4000.0), LEVY_RATE_CEILING * 4000.0)

    def test_a_state_with_no_unfunded_army_or_no_visible_base_asks_no_arms(self):
        self.assertEqual(budget.military_ask_of(0.0, 10000.0, 1.0, 4000.0), 0.0)
        self.assertEqual(budget.military_ask_of(1000.0, 0.0, 1.0, 4000.0), 0.0)

    def test_nothing_is_levied_below_the_notice_line(self):
        self.assertEqual(rules.levy_shares_at(0.0, 0.1, 0.2, 0.2, 0.0, 0.5), (0.0, 0.0))

    def test_requisition_is_the_ordinary_rate_plus_the_shortfall_rate_scaled_by_the_distance_past_the_line(self):
        requisition, office = rules.levy_shares_at(0.5, 0.1, 0.2, 0.06, 0.0, 0.55)
        self.assertAlmostEqual(requisition, 0.5 * 0.3)
        self.assertAlmostEqual(office, 0.5 * 0.06)

    def test_protection_bargains_requisition_down_and_leaves_the_office_alone(self):
        bare = rules.levy_shares_at(1.0, 0.1, 0.2, 0.06, 0.0, 0.55)
        shielded = rules.levy_shares_at(1.0, 0.1, 0.2, 0.06, 0.8, 0.55)
        self.assertAlmostEqual(shielded[0], bare[0] * (1.0 - 0.55 * 0.8))
        self.assertEqual(shielded[1], bare[1])

    def test_protection_bargains_down_but_never_below_nothing(self):
        self.assertGreaterEqual(rules.levy_shares_at(1.0, 0.1, 0.2, 0.0, 5.0, 1.0)[0], 0.0)


class NoticeLine(unittest.TestCase):
    def test_a_notice_at_or_below_the_line_is_not_over_it(self):
        self.assertEqual(rules.share_past(0.35, 0.35), 0.0)
        self.assertEqual(rules.share_past(0.1, 0.35), 0.0)

    def test_the_share_past_the_line_is_the_share_of_the_remaining_distance_and_saturates(self):
        self.assertAlmostEqual(rules.share_past(0.675, 0.35), 0.5)
        self.assertEqual(rules.share_past(1.0, 0.35), 1.0)
        self.assertEqual(rules.share_past(7.0, 0.35), 1.0)

    def test_a_military_demand_needs_both_leverage_and_visibility(self):
        self.assertTrue(rules.military_demand_eligible(0.2, 0.2, 0.25, 0.2))
        self.assertFalse(rules.military_demand_eligible(0.1, 0.2, 0.9, 0.2))
        self.assertFalse(rules.military_demand_eligible(0.9, 0.2, 0.2, 0.2))


class Confiscation(unittest.TestCase):
    def chance(self, over=1.0, protection=0.0, dispersal=0.0, leverage=0.0):
        return rules.confiscation_chance(over, 0.28, protection, 0.5, dispersal, leverage, 0.4)

    def test_nothing_is_at_risk_short_of_the_confiscation_line(self):
        self.assertEqual(self.chance(over=0.0), (0.0, []))

    def test_an_unprotected_household_at_the_top_risks_the_maximum_rate(self):
        self.assertEqual(self.chance(), (0.28, []))
        self.assertAlmostEqual(self.chance(over=0.5)[0], 0.14)

    def test_each_mitigation_cuts_the_risk_and_is_named(self):
        bare = self.chance()[0]
        for keyword, factor in (("protection", 1.0 - 0.5 * 0.8), ("dispersal", 1.0 - 0.3), ("leverage", 1.0 - 0.4 * 0.5)):
            value = {"protection": 0.8, "dispersal": 0.3, "leverage": 0.5}[keyword]
            chance, active = self.chance(**{keyword: value})
            self.assertAlmostEqual(chance, bare * factor)
            self.assertEqual(len(active), 1)

    def test_all_mitigations_together_cut_it_the_most_and_are_all_named(self):
        chance, active = self.chance(protection=0.8, dispersal=0.3, leverage=0.5)
        self.assertAlmostEqual(chance, 0.28 * (1.0 - 0.4) * 0.7 * 0.8)
        self.assertEqual(active, [0, 1, 2])
        self.assertLess(chance, min(self.chance(protection=0.8)[0], self.chance(dispersal=0.3)[0]))


if __name__ == "__main__":
    unittest.main()
