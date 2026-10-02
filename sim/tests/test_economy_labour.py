"""The labour market: a sticky wage that follows vacancies and idle hours toward the clearing wage."""
import random
import unittest

from sim.economy import labour
from sim.economy.types import LabourBid, LabourOffer


def offer(worker, hours, reservation, trade="smith", area="a"):
    return LabourOffer(worker, trade, area, hours, reservation)


def bid(employer, hours, maximum, trade="smith", area="a"):
    return LabourBid(employer, trade, area, hours, maximum)


def run_years(bids, offers, years, last_wage):
    wages = []
    for _ in range(years):
        result = labour.clear(bids, offers, "smith", "a", "coin", last_wage)
        last_wage = result.wage
        wages.append(result)
    return wages


class WageMovementTests(unittest.TestCase):
    def test_first_year_pays_the_clearing_wage(self):
        result = labour.clear([bid("e", 100, 2.0)], [offer("w", 100, 1.0)], "smith", "a", "coin", None)
        self.assertAlmostEqual(result.wage, 1.5)
        self.assertAlmostEqual(result.hours_hired, 100)

    def test_vacancies_raise_the_wage_without_overshooting(self):
        results = run_years([bid("e", 150, 2.0)], [offer("w", 100, 1.0)], 12, last_wage=1.0)
        wages = [result.wage for result in results]
        self.assertTrue(all(later >= earlier for earlier, later in zip(wages, wages[1:])))
        self.assertGreater(wages[0], 1.0)
        self.assertTrue(all(wage <= 2.0 + 1e-9 for wage in wages))   # employers left out bid it to their cap
        self.assertGreater(results[0].vacant_hours, 0)
        self.assertAlmostEqual(results[0].hours_hired, 100)

    def test_idle_hours_lower_the_wage_without_undershooting(self):
        results = run_years([bid("e", 100, 2.0)], [offer("w", 150, 1.0)], 12, last_wage=2.0)
        wages = [result.wage for result in results]
        self.assertTrue(all(later <= earlier for earlier, later in zip(wages, wages[1:])))
        self.assertLess(wages[0], 2.0)
        self.assertTrue(all(wage >= 1.0 - 1e-9 for wage in wages))   # idle workers undercut to their floor
        self.assertGreater(results[0].idle_hours, 0)

    def test_a_high_reservation_worker_stays_idle(self):
        offers = [offer("cheap", 50, 1.0), offer("proud", 50, 5.0)]
        result = labour.clear([bid("e", 100, 2.0)], offers, "smith", "a", "coin", None)
        self.assertAlmostEqual(result.hours_hired, 50)
        self.assertAlmostEqual(result.idle_hours, 50)
        self.assertAlmostEqual(result.vacant_hours, 50)
        self.assertEqual({fill.agent for fill in result.fills if fill.side == "sell"}, {"cheap"})

    def test_no_bids_leaves_the_wage_where_it_was_or_falls(self):
        result = labour.clear([], [offer("w", 10, 1.0)], "smith", "a", "coin", 2.0)
        self.assertLess(result.wage, 2.0)
        self.assertEqual(result.hours_hired, 0)
        self.assertEqual(result.fills, ())

    def test_other_trades_and_areas_are_ignored(self):
        result = labour.clear([bid("e", 10, 2.0, trade="other")], [offer("w", 10, 1.0)],
                              "smith", "a", "coin", None)
        self.assertEqual(result.hours_hired, 0)


class FillTests(unittest.TestCase):
    def test_fills_sum_and_price_is_the_wage(self):
        offers = [offer("w1", 40, 1.0), offer("w2", 40, 1.2), offer("w3", 40, 1.2)]
        bids = [bid("e1", 50, 3.0), bid("e2", 50, 2.5)]
        result = labour.clear(bids, offers, "smith", "a", "coin", None)
        sold = sum(fill.quantity for fill in result.fills if fill.side == "sell")
        bought = sum(fill.quantity for fill in result.fills if fill.side == "buy")
        self.assertAlmostEqual(sold, result.hours_hired, places=9)
        self.assertAlmostEqual(bought, result.hours_hired, places=9)
        self.assertTrue(all(fill.price == result.wage and fill.good == "smith" for fill in result.fills))

    def test_lowest_reservation_hired_first_and_pro_rata_at_the_margin(self):
        offers = [offer("low", 30, 1.0), offer("m1", 40, 1.2), offer("m2", 80, 1.2)]
        result = labour.clear([bid("e", 90, 3.0)], offers, "smith", "a", "coin", None)
        sold = {fill.agent: fill.quantity for fill in result.fills if fill.side == "sell"}
        self.assertAlmostEqual(sold["low"], 30)
        self.assertAlmostEqual(sold["m1"], 20)
        self.assertAlmostEqual(sold["m2"], 40)

    def test_highest_maximum_filled_first(self):
        offers = [offer("w", 60, 1.0)]
        bids = [bid("keen", 40, 4.0), bid("mid", 40, 3.0)]
        result = labour.clear(bids, offers, "smith", "a", "coin", None)
        bought = {fill.agent: fill.quantity for fill in result.fills if fill.side == "buy"}
        self.assertAlmostEqual(bought["keen"], 40)
        self.assertAlmostEqual(bought["mid"], 20)

    def test_result_does_not_depend_on_input_order(self):
        rng = random.Random(7)
        offers = [offer("w%d" % i, 10 + i, 1.0 + (i % 3) * 0.2) for i in range(9)]
        bids = [bid("e%d" % i, 12 + i, 2.0 - (i % 2) * 0.5) for i in range(6)]
        reference = labour.clear(bids, offers, "smith", "a", "coin", 1.4)
        for _ in range(5):
            rng.shuffle(offers)
            rng.shuffle(bids)
            self.assertEqual(labour.clear(bids, offers, "smith", "a", "coin", 1.4), reference)


class ReservationAndTrainingTests(unittest.TestCase):
    def test_reservation_wage_is_the_outside_option_without_danger(self):
        self.assertAlmostEqual(labour.reservation_wage(2000.0, 2000.0, 0.0, 30.0), 1.0)

    def test_danger_raises_the_reservation_wage(self):
        safe = labour.reservation_wage(2000.0, 2000.0, 0.001, 30.0)
        risky = labour.reservation_wage(2000.0, 2000.0, 0.02, 30.0)
        self.assertGreater(safe, 1.0)
        self.assertGreater(risky, safe)

    def test_training_premium_repays_the_forgone_income_as_an_annuity(self):
        premium = labour.training_premium(3.0, 0.05, 30.0)
        forgone_at_start = sum(1.05 ** (3 - year) for year in range(1, 4))
        annuity_factor = sum(1.05 ** -year for year in range(1, 31))
        self.assertAlmostEqual(premium, forgone_at_start / annuity_factor, places=9)

    def test_training_premium_without_interest_spreads_the_years(self):
        self.assertAlmostEqual(labour.training_premium(2.0, 0.0, 20.0), 0.1)
        self.assertEqual(labour.training_premium(0.0, 0.05, 20.0), 0.0)

    def test_longer_training_costs_more(self):
        self.assertGreater(labour.training_premium(5.0, 0.05, 30.0), labour.training_premium(2.0, 0.05, 30.0))


if __name__ == "__main__":
    unittest.main()
