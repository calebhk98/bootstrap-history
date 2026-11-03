"""The founder works a normal job (Complaint 518): the hours the founder has not spoken for are offered in the trade
the founder holds and paid that trade's market wage, like any worker's. There is no separate practice income."""
import unittest
from types import SimpleNamespace

from sim.labour.labour_hours import FounderHours
from sim.labour.labour_wages import Wages

QUICK_TOPIC = True

POOL_HOURS = 2000.0
HOURLY_WAGE = {"scholar": 4.0, "scribe": 1.5}


class Household(SimpleNamespace):
    pass


def labour(wages=None, alive=True, wage_hours=0.0, teaching=0.0, relocation=0.0, supervision=0.0):
    """Only what the job reads: the pool, the hours already spoken for, and a market wage per hour."""
    wages = wages or HOURLY_WAGE
    household = Household(wage_hours_this_year=wage_hours, teaching_hours_this_year=teaching,
                          relocation_hours_this_year=relocation, supervision_hours_this_year=supervision,
                          bondage_years_left=0, directors_extra=0.0)
    world = SimpleNamespace(
        directors=SimpleNamespace(overhead_hours=lambda: 0.0),
        scenario=SimpleNamespace(cfg={"founder_hours_per_year": POOL_HOURS, "director_hours_per_year": 0.0}),
        founder_alive=alive, workforce=household, bondage_years_left=0)
    hours_part = SimpleNamespace(_world=world, BONDAGE_HOURS_SHARE=0.25)
    hours_part.director_pool = lambda: FounderHours.director_pool(hours_part)
    hours_part.director_hours_committed = lambda: FounderHours.director_hours_committed(hours_part)
    stub = SimpleNamespace(_world=world, hours=hours_part)
    stub.wage_for_hours = lambda trade, hours: hours * wages[trade]
    stub.hours_for_sale = lambda: Wages.hours_for_sale(stub)
    return stub


class FounderJob(unittest.TestCase):
    def test_income_is_hours_sold_times_the_trades_wage(self):
        self.assertEqual(Wages.standing_job_pay(labour(), "scholar"), POOL_HOURS * HOURLY_WAGE["scholar"])

    def test_income_changes_with_the_wage(self):
        cheap = Wages.standing_job_pay(labour(wages={"scholar": 2.0}), "scholar")
        dear = Wages.standing_job_pay(labour(wages={"scholar": 3.0}), "scholar")
        self.assertEqual(dear - cheap, POOL_HOURS)

    def test_the_trade_sold_sets_the_wage(self):
        self.assertEqual(Wages.standing_job_pay(labour(), "scribe"), POOL_HOURS * HOURLY_WAGE["scribe"])

    def test_hours_supervising_reduce_hours_sold_one_for_one(self):
        free = labour().hours_for_sale()
        for hours in (100.0, 640.0):
            self.assertEqual(labour(supervision=hours).hours_for_sale(), free - hours)

    def test_every_kind_of_hour_already_spoken_for_comes_out_of_the_sale(self):
        self.assertEqual(labour(teaching=100.0, relocation=200.0, wage_hours=300.0, supervision=400.0).hours_for_sale(),
                         POOL_HOURS - 1000.0)

    def test_supervising_more_than_the_pool_sells_nothing(self):
        stub = labour(supervision=POOL_HOURS * 2)
        self.assertEqual(stub.hours_for_sale(), 0.0)
        self.assertEqual(Wages.standing_job_pay(stub, "scholar"), 0.0)

    def test_no_trade_held_earns_nothing_and_a_dead_founder_sells_nothing(self):
        self.assertEqual(Wages.standing_job_pay(labour(), None), 0.0)
        self.assertEqual(Wages.standing_job_pay(labour(alive=False), "scholar"), 0.0)


if __name__ == "__main__":
    unittest.main()
