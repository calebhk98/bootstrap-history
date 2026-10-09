"""The founder's practice earns through the founder's own hours, not through a typed node revenue: the hours
not sold for wages, at the going wage of the trade the practised skills are worked as."""
import unittest
from types import SimpleNamespace

from sim.engine.economy_production import ProductionMixin

QUICK_TOPIC = True

HOURS_OWN = 2000.0
WAGES = {"scholar": 4.0, "artisan": 2.5}


def founder(practised, sold_hours=0.0, alive=True):
    """Only what practice_income reads: the practised nodes, the founder's hours and the trade wages."""
    nodes = {"cure": {"sch": 1, "art": 0, "rev": 0.0}, "splint": {"sch": 0, "art": 1, "rev": 0.0}}
    stub = SimpleNamespace(
        nodes=nodes, _practice_set=lambda: frozenset(practised),
        labour=SimpleNamespace(director_pool=lambda: HOURS_OWN, wage_per_hour=lambda trade: WAGES[trade]),
        state=SimpleNamespace(founder=SimpleNamespace(founder_alive=alive),
                              household=SimpleNamespace(wage_hours_this_year=sold_hours)))
    stub.practice_trade = lambda: ProductionMixin.practice_trade(stub)
    stub.practice_attention = lambda: ProductionMixin.practice_attention(stub)
    return stub


class PracticeIncome(unittest.TestCase):
    def test_income_is_the_free_hours_at_the_trades_wage(self):
        self.assertEqual(ProductionMixin.practice_income(founder({"cure"})), HOURS_OWN * WAGES["scholar"])

    def test_a_practice_with_no_scholar_skill_is_worked_as_an_artisan(self):
        stub = founder({"splint"})
        self.assertEqual(ProductionMixin.practice_trade(stub), "artisan")
        self.assertEqual(ProductionMixin.practice_income(stub), HOURS_OWN * WAGES["artisan"])

    def test_several_skills_earn_once(self):
        self.assertEqual(ProductionMixin.practice_income(founder({"cure", "splint"})),
                         ProductionMixin.practice_income(founder({"cure"})))

    def test_hours_sold_for_wages_come_out_of_the_practice(self):
        free = ProductionMixin.practice_income(founder({"cure"}))
        sold = ProductionMixin.practice_income(founder({"cure"}, sold_hours=HOURS_OWN / 4))
        self.assertAlmostEqual(sold, 0.75 * free)

    def test_no_skill_or_no_founder_means_no_practice(self):
        self.assertEqual(ProductionMixin.practice_income(founder(set())), 0.0)
        self.assertEqual(ProductionMixin.practice_income(founder({"cure"}, alive=False)), 0.0)


if __name__ == "__main__":
    unittest.main()
