"""Farmland trade (Complaint 288): the agriculture module's `InvestFarm` buys hectares at `farm_land_price` and `SellFarm` sells them
back at the same price, nothing taken as a fee. The module is built over plain values and the money it sends is recorded."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.agriculture.commands import InvestFarm, SellFarm
from sim.agriculture.constants import FARM_LABOUR_HOURS_PER_HA
from sim.agents.api import edges
from sim.ledger.api import PayEdge, ReceiveFromEdge
from sim.refusal import Refusal
from sim.tests import agriculture_stand_in, module_harness

MONEY_PER_HOUR = 2.0
PRICE_INDEX = 1.5
PRICE = FARM_LABOUR_HOURS_PER_HA * MONEY_PER_HOUR * PRICE_INDEX


def farm(owned=100.0, capital=1.0e9):
    holdings = SimpleNamespace(farm_hectares=owned, farm_stock_kg=0.0)
    module = agriculture_stand_in.build(views={
        "money_per_labour_hour": MONEY_PER_HOUR, "price_index": PRICE_INDEX, "acting_balance": capital,
        "legacy_farm_holdings": holdings})
    return module, holdings


class PriceTests(unittest.TestCase):
    def test_a_hectare_costs_its_labour_hours_at_the_coins_hourly_value_and_the_price_index(self):
        self.assertEqual(farm()[0].farm_land_price(), PRICE)


class SellTests(unittest.TestCase):
    def test_selling_removes_the_hectares_and_pays_what_buying_charges_per_hectare(self):
        module, holdings = farm(100.0)
        answer = module.sell_farm(SellFarm(40.0))
        self.assertEqual((answer, holdings.farm_hectares), ({"hectares": 40.0, "price": 40.0 * PRICE, "remaining": 60.0}, 60.0))
        self.assertEqual(module_harness.sent(module), [ReceiveFromEdge(edges.EDGE_LANDOWNERS, 40.0 * PRICE, "farmland sold")])

    def test_more_than_is_owned_is_refused_and_changes_nothing(self):
        module, holdings = farm(60.0)
        answer = module.sell_farm(SellFarm(61.0))
        self.assertEqual((answer.cause, answer.facts, holdings.farm_hectares, module_harness.sent(module)),
                         ("not_owned", {"owned": 60.0, "hectares": 61.0}, 60.0, []))

    def test_a_sale_of_nothing_is_refused(self):
        module, holdings = farm(100.0)
        self.assertEqual((module.sell_farm(SellFarm(0.0)).cause, holdings.farm_hectares), ("not_positive", 100.0))


class InvestTests(unittest.TestCase):
    def test_buying_adds_the_hectares_and_pays_the_edge(self):
        module, holdings = farm(10.0)
        self.assertEqual(module.invest_farm(InvestFarm(5.0)), 5.0)
        self.assertEqual((holdings.farm_hectares, module_harness.sent(module)), (15.0, [PayEdge(edges.EDGE_LANDOWNERS, 5.0 * PRICE, "farmland bought")]))

    def test_the_first_farm_starts_from_nothing_held(self):
        module, holdings = farm(None)
        module.invest_farm(InvestFarm(5.0))
        self.assertEqual(holdings.farm_hectares, 5.0)

    def test_more_than_the_purse_pays_for_is_refused_and_changes_nothing(self):
        module, holdings = farm(10.0, capital=PRICE * 5.0 - 1.0)
        answer = module.invest_farm(InvestFarm(5.0))
        self.assertEqual((isinstance(answer, Refusal), answer.cause, holdings.farm_hectares, module_harness.sent(module)),
                         (True, "cannot_afford", 10.0, []))

    def test_no_hectares_is_refused(self):
        module, _holdings = farm()
        self.assertEqual(module.invest_farm(InvestFarm(0.0)).cause, "not_positive")


if __name__ == "__main__":
    unittest.main()
