"""An unaffordable start's refusal, reached through a running game, lists the remedies of a household in debt, and the
stock-sale amount it quotes is what `sell` then pays. The remedy lines themselves are test_refusal_cash_remedies."""
import unittest

from .harness import *  # noqa: F401,F403


def _indebted_household():
    household = sim(civ="rome_100ad", capital=5000)
    household.state.household.capital = -6000
    return household


class RefusalListsRemediesInAGame(unittest.TestCase):

    def test_start_refusal_carries_the_remedies_and_the_sale_pays_the_quote(self):
        household = _indebted_household()
        household._material_stock()["iron"] = 40.0
        household.state.household.employees["smith"] = 2
        _, _tonnes, money = household.goods_market.quote_sell("iron", 40.0)
        node_id = next(node_id for node_id in NODES if node_id not in household.done
                       and household.start_reason(node_id)[0] and household.start_refusal(node_id))
        refusal = household.start_refusal(node_id)
        self.assertGreater(money, 0)
        # presentation: the refusal names the commands that raise cash, with their amounts
        self.assertIn("sell iron", refusal)
        self.assertIn("fire smith", refusal)
        self.assertIn("{:,.0f}".format(money), refusal)
        before = household.capital
        household.sell_material_stock("iron", 40.0)
        self.assertAlmostEqual(household.capital - before, money, places=3)

    def test_no_remedy_line_when_nothing_to_offer(self):
        household = _indebted_household()
        household.state.household.employees.clear()
        household.state.projects.operating.clear()
        node_id = next(node_id for node_id in NODES if node_id not in household.done
                       and household.start_reason(node_id)[0] and household.start_refusal(node_id))
        self.assertNotIn("To raise cash", household.start_refusal(node_id))


if __name__ == "__main__":
    unittest.main()
