"""One search round and the year's rounds, one function each (Complaint 473, 608; Eurace Labour/ matching protocol)."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import applications
from sim.labour.market.applications import Searchers


class ApplyRound(unittest.TestCase):
    def test_a_firm_takes_no_more_hours_than_it_has_vacancies(self):
        hires = applications.apply_round([Searchers(10.0, 4.0)], {"mill": 4.0}, {"mill": 5.0})
        self.assertAlmostEqual(hires[0]["mill"], 4.0)

    def test_searchers_do_not_apply_where_the_offer_is_under_their_ask(self):
        hires = applications.apply_round([Searchers(10.0, 6.0)], {"mill": 4.0}, {"mill": 5.0})
        self.assertEqual(hires[0].get("mill", 0.0), 0.0)

    def test_everyone_who_applies_is_taken_when_vacancies_are_ample(self):
        hires = applications.apply_round([Searchers(10.0, 4.0)], {"mill": 40.0}, {"mill": 5.0})
        self.assertAlmostEqual(hires[0]["mill"], 10.0)

    def test_searchers_who_reach_every_firm_take_the_higher_offer(self):
        hires = applications.apply_round([Searchers(10.0, 4.0)], {"mill": 40.0, "forge": 40.0},
                                         {"mill": 5.0, "forge": 6.0})
        self.assertAlmostEqual(hires[0]["forge"], 10.0)
        self.assertAlmostEqual(hires[0]["mill"], 0.0)

    def test_searchers_limited_to_three_of_six_equal_firms_split_evenly_and_all_are_taken(self):
        firms = {f"firm{i}": 40.0 for i in range(6)}
        hires = applications.apply_round([Searchers(12.0, 4.0)], firms, {name: 5.0 for name in firms})
        self.assertAlmostEqual(hires[0]["firm0"], 2.0)
        self.assertAlmostEqual(sum(hires[0].values()), 12.0)


class LoweredAsk(unittest.TestCase):
    def test_a_failed_round_cuts_the_ask(self):
        self.assertLess(applications.lowered_ask(10.0, 1.0), 10.0)

    def test_the_ask_stops_at_the_floor(self):
        self.assertEqual(applications.lowered_ask(1.0, 1.0), 1.0)


class HireThroughRounds(unittest.TestCase):
    def test_dismissed_hours_are_taken_on_again_at_the_new_offer(self):
        hired, kept = {"mill": 100.0}, {"mill": 100.0}
        applications.hire_through_rounds(hired, kept, {"mill": 100.0}, {"mill": 5.0}, {"mill": 4.0},
                                         pool=50.0, ask=3.0, floor=1.0)
        self.assertGreater(hired["mill"], 99.0)
        self.assertLess(kept["mill"], 100.0)

    def test_dismissed_hours_whose_old_wage_is_over_the_offer_take_the_offer_rather_than_stay_idle(self):
        hired, kept = {"mill": 100.0}, {"mill": 100.0}
        applications.hire_through_rounds(hired, kept, {"mill": 100.0}, {"mill": 5.0}, {"mill": 9.0},
                                         pool=0.0, ask=3.0, floor=1.0)
        self.assertGreater(hired["mill"], 99.0)

    def test_dismissed_hours_return_once_their_cut_ask_reaches_the_offer(self):
        hired, kept = {"mill": 100.0}, {"mill": 100.0}
        applications.hire_through_rounds(hired, kept, {"mill": 100.0}, {"mill": 5.0}, {"mill": 5.2},
                                         pool=0.0, ask=3.0, floor=1.0)
        self.assertGreater(hired["mill"], 100.0 * 0.95 ** 12 + 5.0)


class CappedAsks(unittest.TestCase):
    def test_an_ask_over_every_posted_offer_falls_to_the_best_one(self):
        groups = applications.capped_asks([Searchers(10.0, 9.0), Searchers(10.0, 4.0)], {"mill": 3.0, "forge": 5.0},
                                          {"mill": 5.0, "forge": 6.0})
        self.assertEqual([group.ask for group in groups], [6.0, 4.0])

    def test_offers_of_employers_with_no_vacancy_do_not_count(self):
        groups = applications.capped_asks([Searchers(10.0, 9.0)], {"mill": 3.0, "forge": 0.0}, {"mill": 5.0, "forge": 6.0})
        self.assertEqual(groups[0].ask, 5.0)

    def test_with_no_vacancies_the_ask_is_kept(self):
        groups = applications.capped_asks([Searchers(10.0, 9.0)], {"mill": 0.0}, {"mill": 5.0})
        self.assertEqual(groups[0].ask, 9.0)


class OfferRaise(unittest.TestCase):
    def test_vacancies_over_the_threshold_raise_the_offer_by_the_update(self):
        raised = applications.raised_offer(offer=5.0, ceiling=9.0, wanted=100.0, hired=50.0)
        self.assertAlmostEqual(raised, 5.0 * (1.0 + applications.WAGE_UPDATE_PER_ROUND))

    def test_the_raise_stops_at_the_employers_maximum(self):
        self.assertEqual(applications.raised_offer(offer=5.0, ceiling=5.01, wanted=100.0, hired=50.0), 5.01)

    def test_an_offer_already_over_the_maximum_is_not_lowered(self):
        self.assertEqual(applications.raised_offer(offer=6.0, ceiling=5.0, wanted=100.0, hired=50.0), 6.0)

    def test_vacancies_under_the_threshold_do_not_raise_it(self):
        hired = 100.0 * (1.0 - 0.5 * applications.VACANCY_SHARE_THRESHOLD)
        self.assertEqual(applications.raised_offer(offer=5.0, ceiling=9.0, wanted=100.0, hired=hired), 5.0)


class HireWithRaisingOffers(unittest.TestCase):
    def test_the_offer_paid_never_passes_the_maximum(self):
        offers = {"mill": 5.0}
        applications.hire_through_rounds({"mill": 100.0}, {"mill": 100.0}, {"mill": 200.0}, offers, {"mill": 5.5},
                                         pool=50.0, ask=3.0, floor=1.0, ceilings={"mill": 5.2})
        self.assertLessEqual(offers["mill"], 5.2 + 1e-9)

    def test_the_offer_reported_is_the_mean_paid_to_the_hours_taken_on(self):
        offers = {"mill": 5.0}
        taken = applications.hire_through_rounds({"mill": 0.0}, {"mill": 0.0}, {"mill": 1000.0}, offers, {"mill": 0.0},
                                                 pool=10.0, ask=3.0, floor=1.0, ceilings={"mill": 9.0})
        self.assertGreater(taken["mill"], 0.0)
        self.assertGreater(offers["mill"], 5.0)
        self.assertLess(offers["mill"], 5.0 * (1.0 + applications.WAGE_UPDATE_PER_ROUND) ** 12)

    def test_without_ceilings_the_offer_stays(self):
        offers = {"mill": 5.0}
        applications.hire_through_rounds({"mill": 0.0}, {"mill": 0.0}, {"mill": 1000.0}, offers, {"mill": 0.0},
                                         pool=10.0, ask=3.0, floor=1.0)
        self.assertEqual(offers["mill"], 5.0)


if __name__ == "__main__":
    unittest.main()
