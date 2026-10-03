"""A labour market nobody offers hours in follows what a worker of the trade would ask, not its opening
seed; workers move toward trades that pay more than their training and danger ask for."""
import unittest

from sim.economy import labour_asks


class UntradedWageTests(unittest.TestCase):
    def test_an_untraded_wage_moves_toward_the_ask(self):
        wages = {"scribe|work@t1": 100.0}
        moved = labour_asks.untraded_wages(wages, offered_keys=set(), asks={"scribe|work@t1": 1.0})
        self.assertLess(moved["scribe|work@t1"], 100.0)
        self.assertGreater(moved["scribe|work@t1"], 1.0)

    def test_it_reaches_the_ask_over_the_years(self):
        wages = {"scribe|work@t1": 100.0}
        for _year in range(60):
            wages = labour_asks.untraded_wages(wages, offered_keys=set(), asks={"scribe|work@t1": 1.0})
        self.assertAlmostEqual(wages["scribe|work@t1"], 1.0, places=3)

    def test_a_market_with_hours_offered_keeps_its_cleared_wage(self):
        wages = {"scribe|work@t1": 100.0}
        moved = labour_asks.untraded_wages(wages, offered_keys={"scribe|work@t1"}, asks={"scribe|work@t1": 1.0})
        self.assertEqual(moved["scribe|work@t1"], 100.0)


class GapMobilityTests(unittest.TestCase):
    def test_workers_move_toward_a_trade_paid_far_above_its_ask(self):
        workforce = {"labourer": 1000.0, "smith": 1.0}
        moved = labour_asks.follow_pay(workforce, pay_over_ask={"labourer": 1.0, "smith": 50.0},
                                       wanted_workers={"labourer": 1000.0, "smith": 20.0})
        self.assertGreater(moved["smith"], 1.0)
        self.assertLess(moved["labourer"], 1000.0)
        self.assertAlmostEqual(sum(moved.values()), 1001.0)

    def test_nobody_moves_when_every_trade_pays_its_ask(self):
        workforce = {"labourer": 1000.0, "smith": 10.0}
        moved = labour_asks.follow_pay(workforce, pay_over_ask={"labourer": 1.0, "smith": 1.0},
                                       wanted_workers={"labourer": 1000.0, "smith": 20.0})
        self.assertEqual(moved, workforce)

    def test_nobody_joins_a_trade_no_employer_wants(self):
        workforce = {"labourer": 1000.0, "smith": 10.0}
        moved = labour_asks.follow_pay(workforce, pay_over_ask={"labourer": 1.0, "smith": 50.0},
                                       wanted_workers={"labourer": 1000.0})
        self.assertEqual(moved, workforce)

    def test_arrivals_never_exceed_the_workers_employers_want(self):
        workforce = {"labourer": 1000.0, "smith": 1.0}
        moved = labour_asks.follow_pay(workforce, pay_over_ask={"labourer": 1.0, "smith": 1e6},
                                       wanted_workers={"labourer": 1000.0, "smith": 20.0})
        self.assertLessEqual(moved["smith"], 20.0 + 1e-9)


if __name__ == "__main__":
    unittest.main()
