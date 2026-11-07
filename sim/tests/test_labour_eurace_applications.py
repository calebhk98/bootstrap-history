"""The year's search rounds, one function each (Complaint 473, 608; Eurace Labour/ matching protocol)."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import applications
from sim.tests import labour_hiring_reference as reference
from sim.tests.labour_hiring_reference import Searchers


class LoweredAsk(unittest.TestCase):
    def test_a_failed_round_cuts_the_ask(self):
        self.assertLess(reference.lowered_ask(10.0, 1.0), 10.0)

    def test_the_ask_stops_at_the_floor(self):
        self.assertEqual(reference.lowered_ask(1.0, 1.0), 1.0)


class HireThroughRounds(unittest.TestCase):
    def test_dismissed_hours_are_taken_on_again_at_the_new_offer(self):
        hired, kept = {"mill": 100.0}, {"mill": 100.0}
        applications.hire_through_rounds(hired, kept, {"mill": 100.0}, {"mill": 5.0},
                                         pool=50.0, ask=3.0, floor=1.0)
        self.assertGreater(hired["mill"], 99.0)
        self.assertLess(kept["mill"], 100.0)

    def test_dismissed_hours_return_once_their_cut_ask_reaches_the_offer(self):
        hired, kept = {"mill": 100.0}, {"mill": 100.0}
        applications.hire_through_rounds(hired, kept, {"mill": 100.0}, {"mill": 5.0},
                                         pool=0.0, ask=3.0, floor=1.0)
        self.assertGreater(hired["mill"], 100.0 * 0.95 ** 12 + 5.0)


class CappedAsks(unittest.TestCase):
    def test_an_ask_over_every_posted_offer_falls_to_the_best_one(self):
        groups = reference.capped_asks([Searchers(10.0, 9.0), Searchers(10.0, 4.0)], {"mill": 3.0, "forge": 5.0},
                                          {"mill": 5.0, "forge": 6.0})
        self.assertEqual([group.ask for group in groups], [6.0, 4.0])

    def test_offers_of_employers_with_no_vacancy_do_not_count(self):
        groups = reference.capped_asks([Searchers(10.0, 9.0)], {"mill": 3.0, "forge": 0.0}, {"mill": 5.0, "forge": 6.0})
        self.assertEqual(groups[0].ask, 5.0)

    def test_with_no_vacancies_the_ask_is_kept(self):
        groups = reference.capped_asks([Searchers(10.0, 9.0)], {"mill": 0.0}, {"mill": 5.0})
        self.assertEqual(groups[0].ask, 9.0)


class OfferRaise(unittest.TestCase):
    def test_vacancies_over_the_threshold_raise_the_offer_by_the_update(self):
        raised = reference.raised_offer(offer=5.0, ceiling=9.0, wanted=100.0, hired=50.0)
        self.assertAlmostEqual(raised, 5.0 * (1.0 + reference.WAGE_UPDATE_PER_ROUND))

    def test_the_raise_stops_at_the_employers_maximum(self):
        self.assertEqual(reference.raised_offer(offer=5.0, ceiling=5.01, wanted=100.0, hired=50.0), 5.01)

    def test_an_offer_already_over_the_maximum_is_not_lowered(self):
        self.assertEqual(reference.raised_offer(offer=6.0, ceiling=5.0, wanted=100.0, hired=50.0), 6.0)

    def test_vacancies_under_the_threshold_do_not_raise_it(self):
        hired = 100.0 * (1.0 - 0.5 * reference.VACANCY_SHARE_THRESHOLD)
        self.assertEqual(reference.raised_offer(offer=5.0, ceiling=9.0, wanted=100.0, hired=hired), 5.0)


class HireWithRaisingOffers(unittest.TestCase):
    def test_the_offer_paid_never_passes_the_maximum(self):
        offers = {"mill": 5.0}
        applications.hire_through_rounds({"mill": 100.0}, {"mill": 100.0}, {"mill": 200.0}, offers,
                                         pool=50.0, ask=3.0, floor=1.0, ceilings={"mill": 5.2})
        self.assertLessEqual(offers["mill"], 5.2 + 1e-9)

    def test_the_offer_reported_is_the_mean_paid_to_the_hours_taken_on(self):
        offers = {"mill": 5.0}
        taken = applications.hire_through_rounds({"mill": 0.0}, {"mill": 0.0}, {"mill": 1000.0}, offers,
                                                 pool=10.0, ask=3.0, floor=1.0, ceilings={"mill": 9.0})
        self.assertGreater(taken["mill"], 0.0)
        self.assertGreater(offers["mill"], 5.0)
        self.assertLess(offers["mill"], 5.0 * (1.0 + reference.WAGE_UPDATE_PER_ROUND) ** 12)

    def test_without_ceilings_the_offer_stays(self):
        offers = {"mill": 5.0}
        applications.hire_through_rounds({"mill": 0.0}, {"mill": 0.0}, {"mill": 1000.0}, offers,
                                         pool=10.0, ask=3.0, floor=1.0)
        self.assertEqual(offers["mill"], 5.0)


if __name__ == "__main__":
    unittest.main()
