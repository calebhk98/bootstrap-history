"""A mortality shock's size, its wage premium and its recovery, and how a staff-loss wave is classified and worded,
called with figures built here (Complaint 640). The cohort cut is held by test_cross_system_invariants; the scenarios
that drive a hazard through a game are in test_demographics_and_plague."""
QUICK_TOPIC = True

import unittest

from sim.engine.mortality_shock import cut_cohorts
from sim.hazards import rules
from sim.hazards.staff_loss_words import defence_kind, national_toll_sentence, staff_clause
from sim.engine.wage_scarcity import wage_index_of
from sim.world.demography import Population

CHILD, WORKING_AGE, ELDERLY = 1.6, 1.0, 1.4   # the vulnerability ratios (sim/world/demography.py)


def exposure(historical, national_relief=0.0, household_relief=1.0):
    """The staff a household loses to one wave, from the historical rate, the country's own relief and the household's."""
    return rules.staff_exposure(historical, national_relief, household_relief)


class ExposureTests(unittest.TestCase):
    def test_a_country_without_public_health_takes_the_historical_rate(self):
        self.assertAlmostEqual(exposure(0.45)["before_defences"], 0.45)

    def test_the_countrys_public_health_lowers_the_rate_the_whole_society_takes(self):
        self.assertAlmostEqual(exposure(0.45, national_relief=0.2)["before_defences"], 0.36)

    def test_the_households_own_hedge_lowers_its_loss_but_not_the_societys(self):
        hedged = exposure(0.45, household_relief=0.1)
        bare = exposure(0.45)
        self.assertAlmostEqual(hedged["loss"], 0.045)
        self.assertAlmostEqual(hedged["before_defences"], bare["before_defences"])

    def test_a_milder_wave_costs_less_both_to_the_household_and_to_the_society(self):
        milder, severer = exposure(0.28, household_relief=0.5), exposure(0.45, household_relief=0.5)
        self.assertLess(milder["loss"], severer["loss"])
        self.assertLess(milder["before_defences"], severer["before_defences"])

    def test_a_smaller_raw_toll_cuts_fewer_people(self):
        lost = []
        for raw in (0.28, 0.45):
            population = Population(300.0, 600.0, 100.0)
            before = population.total
            cut_cohorts(population, raw, CHILD, WORKING_AGE, ELDERLY)
            lost.append(1.0 - population.total / before)
        self.assertAlmostEqual(lost[0], 0.28)
        self.assertAlmostEqual(lost[1], 0.45)


class WageTests(unittest.TestCase):
    def test_wages_rise_by_the_scarcity_elasticity_times_the_shortfall_in_the_population_scale(self):
        self.assertAlmostEqual(wage_index_of(1.0, 2.0, 0.55, 1.0), 1.0 + 2.0 * 0.45)

    def test_no_shortfall_leaves_the_index_at_its_base(self):
        self.assertEqual(wage_index_of(1.0, 2.0, 1.0, 1.0), 1.0)
        self.assertEqual(wage_index_of(1.5, 2.0, 1.0, 1.0), 1.5)

    def test_a_population_above_its_trend_does_not_pay_less(self):
        self.assertEqual(wage_index_of(1.0, 2.0, 1.4, 1.0), 1.0)

    def test_the_shortfall_is_read_against_the_unshocked_trend_not_against_one(self):
        self.assertEqual(wage_index_of(1.0, 2.0, 1.2, 1.2), 1.0)


class RecoveryTests(unittest.TestCase):
    """A shocked population fed at exactly its need resumes growth from its smaller base: it does not snap back."""

    def test_a_shocked_population_fed_at_its_need_grows_a_year_but_stays_far_below_its_opening_size(self):
        opening_total = 1000000.0
        population = Population(170000.0, 260000.0, 120000.0)          # the cohorts a cut of nearly half leaves
        before = population.total
        population.step(population._subsistence_food())
        self.assertGreater(population.total, before)
        self.assertLess(population.total, before * 1.05)
        self.assertLess(population.total, 0.6 * opening_total)


class WordingTests(unittest.TestCase):
    def test_a_household_with_no_defence_is_told_plain(self):
        self.assertEqual(defence_kind(1.0, []), "plain")
        self.assertEqual(defence_kind(0.1, []), "plain")        # relief with nothing named that did it

    def test_relief_of_a_quarter_or_less_is_held_off(self):
        self.assertEqual(defence_kind(0.25, ["quarantine"]), "held_off")
        self.assertEqual(defence_kind(0.02, ["quarantine"]), "held_off")

    def test_relief_between_a_quarter_and_three_quarters_is_softened(self):
        self.assertEqual(defence_kind(0.26, ["quarantine"]), "softened")
        self.assertEqual(defence_kind(0.75, ["quarantine"]), "softened")

    def test_relief_above_three_quarters_is_plain(self):
        self.assertEqual(defence_kind(0.76, ["quarantine"]), "plain")

    # presentation: the plague line's clauses
    def test_a_held_off_wave_quotes_the_loss_applied_not_the_historical_rate(self):
        clause = staff_clause(0.003, 0.1, ["quarantine"])
        self.assertIn("held off almost entirely", clause)
        self.assertNotIn("28", clause)
        self.assertTrue(clause.startswith("staff -0%"))

    # presentation: the plague line's clauses
    def test_a_softened_wave_names_what_softened_it(self):
        self.assertEqual(staff_clause(0.12, 0.5, ["quarantine", "sanitation"]),
                         "staff -12% (softened by quarantine; sanitation)")

    # presentation: the plague line's clauses
    def test_the_national_toll_is_a_separate_sentence_about_the_empire(self):
        sentence = national_toll_sentence(0.28, 0.28, 0.0, "")
        self.assertTrue(sentence.startswith(". Empire-wide, population -28%"))
        self.assertIn("either way", sentence)

    # presentation: the plague line's clauses
    def test_a_national_relief_is_told_as_softening_the_toll(self):
        sentence = national_toll_sentence(0.2, 0.28, 0.3, "boiled water")
        self.assertIn("30% softer", sentence)
        self.assertIn("boiled water", sentence)

    # presentation: the plague line's clauses
    def test_a_toll_that_barely_registers_is_told_only_when_public_health_did_it(self):
        self.assertEqual(national_toll_sentence(0.0, 0.0, 0.0, ""), "")
        self.assertIn("barely registers", national_toll_sentence(0.0, 0.28, 0.99, "boiled water"))


if __name__ == "__main__":
    unittest.main()
