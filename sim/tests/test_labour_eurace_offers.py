"""Eurace-style wage moves, one function each: an employer's offer rises while vacancies stay unfilled, a worker's ask
falls while hours go unsold and stops at the floor (Complaints 608, 473)."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import asks, clearing
from sim.labour.market.records import Bid, MarketState

RESERVATION = 1.0
OFFERED = 1000.0


class VacancyRaise(unittest.TestCase):
    def test_unfilled_vacancies_raise_the_wage_by_the_offer_update_each_round(self):
        raised = clearing.vacancy_raise(wage=2.0, target=9.0, wanted=2000.0, offered=OFFERED)
        self.assertAlmostEqual(raised, 2.0 * (1.0 + clearing.WAGE_UPDATE_PER_ROUND) ** asks.SEARCH_ROUNDS_PER_YEAR)

    def test_the_raise_stops_at_the_clearing_target(self):
        self.assertEqual(clearing.vacancy_raise(wage=2.0, target=2.1, wanted=2000.0, offered=OFFERED), 2.1)

    def test_vacancies_under_the_threshold_do_not_raise_it(self):
        wanted = OFFERED * (1.0 + 0.5 * clearing.VACANCY_SHARE_THRESHOLD)
        self.assertEqual(clearing.vacancy_raise(wage=2.0, target=9.0, wanted=wanted, offered=OFFERED), 2.0)

    def test_a_wage_already_past_the_target_is_not_lowered(self):
        self.assertEqual(clearing.vacancy_raise(wage=5.0, target=3.0, wanted=2000.0, offered=OFFERED), 5.0)


class ReservationCut(unittest.TestCase):
    def test_every_hour_unsold_cuts_the_ask_by_the_reservation_cut_each_round(self):
        scale = asks.moved_scale(1.0, offered=OFFERED, wanted=0.0)
        self.assertAlmostEqual(scale, (1.0 - asks.RESERVATION_CUT_PER_ROUND) ** asks.SEARCH_ROUNDS_PER_YEAR)

    def test_half_the_hours_unsold_cut_half_as_far(self):
        full = 1.0 - asks.moved_scale(1.0, offered=OFFERED, wanted=0.0)
        half = 1.0 - asks.moved_scale(1.0, offered=OFFERED, wanted=OFFERED / 2.0)
        self.assertAlmostEqual(half, full / 2.0)

    def test_the_ask_never_falls_below_the_floor(self):
        state = MarketState()
        state.asks = {"vale": {"digger": 1.01}}
        asks.record(state, "vale", "digger", OFFERED, 0.0, wage=1.0, reservation=1.0, lowest=0.9)
        self.assertAlmostEqual(asks.scale_of(state, "vale", "digger"), 0.9)


class WageIterations(unittest.TestCase):
    def test_scarce_hours_walk_the_wage_up_to_the_clearing_point_without_passing_it(self):
        bids = [Bid("farm", "digger", "vale", 2000.0, 6.0)]
        target = clearing.clearing_target(RESERVATION, OFFERED, bids)
        wage, path = 2.0, []
        for _year in range(6):
            wage = clearing.market_wage(wage, RESERVATION, OFFERED, bids)
            path.append(wage)
        self.assertTrue(all(later >= earlier for earlier, later in zip(path, path[1:])), path)
        self.assertLessEqual(max(path), target + 1e-9)
        self.assertGreater(path[0], 3.2)      # faster than the sticky move alone (3.2 in the first year)

    def test_idle_hands_walk_the_wage_down_but_not_below_the_reservation(self):
        bids = [Bid("farm", "digger", "vale", 100.0, 6.0)]
        wage = 5.0
        for _year in range(30):
            wage = clearing.market_wage(wage, RESERVATION, OFFERED, bids)
        self.assertGreaterEqual(wage, RESERVATION)
        self.assertLess(wage, 5.0)


if __name__ == "__main__":
    unittest.main()
