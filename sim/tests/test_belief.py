"""Complaints/488: beliefs (estimate, spread, year learned) merge, age and lag; spies sharpen signals and raise leaks."""

QUICK_TOPIC = True

import unittest

from sim.economy import merchants_stretch
from sim.seats import intelligence_rules
from sim.seats.sight_rules import nodes_heard_of
from sim.world import belief, espionage


class BeliefRules(unittest.TestCase):
    def test_first_signal_is_the_belief(self):
        self.assertEqual(belief.merge(None, 100.0, 0.09, 5, 0.03), {"value": 100.0, "variance": 0.09, "year": 5})

    def test_merge_weighs_by_precision_and_sharpens(self):
        old = {"value": 100.0, "variance": 0.01, "year": 5}
        merged = belief.merge(old, 200.0, 0.09, 5, 0.03)
        self.assertAlmostEqual(merged["value"], (100.0 / 0.01 + 200.0 / 0.09) / (1 / 0.01 + 1 / 0.09))
        self.assertLess(merged["variance"], 0.01)

    def test_old_belief_counts_for_less_the_older_it_is(self):
        fresh = belief.merge({"value": 100.0, "variance": 0.01, "year": 5}, 200.0, 0.09, 5, 0.03)
        stale = belief.merge({"value": 100.0, "variance": 0.01, "year": 0}, 200.0, 0.09, 5, 0.03)
        self.assertGreater(stale["value"], fresh["value"])

    def test_reliability_lapses(self):
        old = {"value": 1.0, "variance": 0.01, "year": 0}
        self.assertTrue(belief.is_reliable(old, 7, 0.03, 0.25))
        self.assertFalse(belief.is_reliable(old, 9, 0.03, 0.25))
        self.assertFalse(belief.is_reliable(None, 0, 0.03, 0.25))
        self.assertIsNone(belief.believed_value(None))

    def test_years_until_unreliable(self):
        self.assertEqual(belief.years_until_unreliable(0.01, 0.03, 0.25), 8)
        self.assertEqual(belief.years_until_unreliable(0.3, 0.03, 0.25), 0)

    def test_news_age_is_distance_over_speed(self):
        self.assertEqual(belief.news_age_years(10000.0, 20000.0), 0.5)

    def test_draw_is_fixed_by_its_key(self):
        self.assertEqual(belief.signal_noise_draw("a", "b", 3), belief.signal_noise_draw("a", "b", 3))
        self.assertNotEqual(belief.signal_noise_draw("a", "b", 3), belief.signal_noise_draw("a", "b", 4))

    def test_reading_scales_true_value_by_spread(self):
        self.assertEqual(belief.reading(100.0, 0.04, 0.0), 100.0)
        self.assertAlmostEqual(belief.reading(100.0, 0.04, 1.0), 120.0)
        self.assertEqual(belief.reading(100.0, 4.0, -5.0), 0.0)


class EspionageRules(unittest.TestCase):
    def test_no_contacts_no_spies_is_the_base_share(self):
        self.assertAlmostEqual(espionage.secret_exposure(0.25, 2.0, 0, 0, 0.15, 0.5), 0.125)

    def test_contacts_and_spies_raise_exposure(self):
        base = espionage.secret_exposure(0.25, 2.0, 0, 0, 0.15, 0.5)
        contacts = espionage.secret_exposure(0.25, 2.0, 4, 0, 0.15, 0.5)
        spied = espionage.secret_exposure(0.25, 2.0, 4, 3, 0.15, 0.5)
        self.assertLess(base, contacts)
        self.assertLess(contacts, spied)
        self.assertLess(spied, 1.0)

    def test_hard_to_copy_leaks_slower(self):
        easy = espionage.secret_exposure(0.25, 1.0, 2, 2, 0.15, 0.5)
        hard = espionage.secret_exposure(0.25, 4.0, 2, 2, 0.15, 0.5)
        self.assertLess(hard, easy)

    def test_spies_sharpen_signals(self):
        self.assertEqual(espionage.observation_variance(0.09, 0, 1.0), 0.09)
        self.assertLess(espionage.observation_variance(0.09, 2, 1.0), 0.09)

    def test_lapsing_spies_when_purse_is_short(self):
        self.assertEqual(espionage.affordable_spies(5, 250.0, 100.0), 2)
        self.assertEqual(espionage.affordable_spies(5, -10.0, 100.0), 0)
        self.assertEqual(espionage.affordable_spies(5, 1e9, 100.0), 5)


class SeatIntelligence(unittest.TestCase):
    def test_merchant_memory_is_the_belief_lifetime(self):
        self.assertEqual(merchants_stretch.memory_years(), 8)

    def test_spies_are_paid_in_target_order_and_the_rest_lapse(self):
        self.assertEqual(intelligence_rules.fielded_spies({"b": 2, "a": 2}, 300.0, 100.0), {"a": 2, "b": 1})
        self.assertEqual(intelligence_rules.fielded_spies({"a": 2}, 0.0, 100.0), {})

    def test_year_of_signals_makes_beliefs_and_spies_sharpen_them(self):
        truths = {"techniques": 40.0, "cash": 1000.0}
        blind = intelligence_rules.beliefs_after_year(None, truths, "me", "them", 3, 2000.0, 0)
        spied = intelligence_rules.beliefs_after_year(None, truths, "me", "them", 3, 2000.0, 4)
        self.assertEqual(sorted(blind), ["cash", "techniques"])
        self.assertLess(spied["cash"]["variance"], blind["cash"]["variance"])
        self.assertEqual(blind["cash"]["year"], 3)

    def test_a_later_year_merges_into_the_held_belief(self):
        truths = {"cash": 1000.0}
        first = intelligence_rules.beliefs_after_year(None, truths, "me", "them", 3, 0.0, 0)
        second = intelligence_rules.beliefs_after_year(first, truths, "me", "them", 4, 0.0, 0)
        self.assertLess(second["cash"]["variance"], first["cash"]["variance"] + 0.03)
        self.assertEqual(second["cash"]["year"], 4)

    def test_spies_make_a_secret_visible_that_stays_hidden_without_them(self):
        built, kept = {"secret_craft"}, {"secret_craft": {"mode": "secret"}}
        def heard(spies):
            return nodes_heard_of(built, set(), kept, set(), 0.0, lambda node_id: 4.0,
                                  lambda node_id: espionage.secret_exposure(0.25, 4.0, 1, spies, 0.15, 0.5))
        self.assertEqual(heard(0), set())
        self.assertEqual(heard(6), built)


if __name__ == "__main__":
    unittest.main()
