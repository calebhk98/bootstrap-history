"""An unaffordable purchase's refusal lists the commands that raise cash,
with the amounts those commands themselves charge or pay."""
import unittest

from .harness import *  # noqa: F401,F403


def _indebted_household():
    household = sim(civ="rome_100ad", capital=5000)
    household.state.household.capital = -6000
    return household


def _refusal(household):
    node_id = next(node_id for node_id in NODES
                   if node_id not in household.done and household.start_reason(node_id)[0]
                   and household.start_refusal(node_id))
    return household.start_refusal(node_id)


class RefusalListsRemedies(unittest.TestCase):

    def test_stock_sale_remedy_quotes_what_sell_pays(self):
        household = _indebted_household()
        household._material_stock()["iron"] = 40.0
        _, tonnes, money = household.goods_market.quote_sell("iron", 40.0)
        self.assertGreater(money, 0)
        text = _refusal(household)
        self.assertIn("sell iron", text)
        self.assertIn("{:,.0f}".format(money), text)
        before = household.capital
        household.sell_material_stock("iron", 40.0)
        self.assertAlmostEqual(household.capital - before, money, places=3)

    def test_breeding_stock_is_not_offered_for_sale(self):
        from sim.engine.living_stock_yearly import stock_rates
        household = _indebted_household()
        stock_material = sorted(stock_rates())[0]
        household.grant_stock(stock_material, 5000.0)
        household._material_stock()["iron"] = 40.0
        text = _refusal(household)
        self.assertIn("sell iron", text)
        self.assertNotIn("sell " + stock_material, text)

    def test_mothball_remedy_quotes_the_upkeep_it_stops(self):
        household = _indebted_household()
        node_id = next(node_id for node_id in NODES if NODES[node_id].get("up", 0) > 0
                       and node_id not in household.state.projects.granted)
        household.state.projects.done.add(node_id)
        household.state.projects.operating.add(node_id)
        saving = household.venture_real_upkeep(node_id)
        text = _refusal(household)
        self.assertIn("mothball " + node_id, text)
        self.assertIn("{:,.0f}".format(saving), text)

    def test_fire_remedy_quotes_the_wage_it_stops(self):
        household = _indebted_household()
        household.state.household.employees["smith"] = 2
        wage = household.labour.market.quote_annual("smith")
        text = _refusal(household)
        self.assertIn("fire smith", text)
        self.assertIn("{:,.0f}".format(wage), text)

    def test_no_remedy_line_when_nothing_to_offer(self):
        household = _indebted_household()
        household.state.household.employees.clear()
        household.state.projects.operating.clear()
        self.assertNotIn("To raise cash", _refusal(household))


if __name__ == "__main__":
    unittest.main()
