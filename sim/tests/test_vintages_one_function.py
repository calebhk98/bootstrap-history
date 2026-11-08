"""The money vintage rules, each on written-out inputs: the state's real programme level, the home cohorts, the opening
wage at the index base, an unpriced mine's running cost, the washed-fill residue and a late good's price in opening-year money."""
QUICK_TOPIC = True

import importlib
import types
import unittest
from unittest import mock

importlib.import_module("sim.economy.api")     # loads the package in its own import order
from sim.economy import home_scope, state_budget, year_accounts
from sim.economy.goods_market_fills import make_fill, without_washed
from sim.markets import port_late
from sim.resources.costs import MineCosts


class RealProgrammeLevel(unittest.TestCase):
    def test_the_target_is_scaled_by_the_level_kept_across_the_rebase_not_the_reset_chained_level(self):
        policy = types.SimpleNamespace(real_spending_target=100.0, reserve_years_of_revenue=0.0, cash_spend_share=0.0,
                                       wage_share=0.0)
        book = types.SimpleNamespace(balance=lambda agent, money: 1.0e9)
        record = types.SimpleNamespace(state_budget=state_budget.StateBudget(), book=book)
        setup = types.SimpleNamespace(state_policy=policy, currency_id="coin", state_agent="state")
        view = types.SimpleNamespace(chained_price_level=lambda money: 1.0, opening_wage_level=lambda money: 3.0)
        with mock.patch.object(state_budget.state_finance, "finance_deficit", lambda *arguments: (0.0, 0.0, {})), \
                mock.patch.object(state_budget, "wage_bid_figures", lambda *arguments: []):
            state_budget.plan_year(setup, record, view, [])
        self.assertAlmostEqual(record.state_budget.goods_budget, 300.0)


def EconomySetup_for_scope(owners):
    tiles = {"t1": types.SimpleNamespace(country=None), "t2": types.SimpleNamespace(country=None)}
    return types.SimpleNamespace(
        civ_id="home", tiles=tiles, tile_owners=owners,
        country_of=lambda tile: owners[tile]["owner"] if tile in owners else "home",
        countries=lambda: ("home",) + tuple(sorted({owners[tile]["owner"] for tile in tiles if tile in owners} - {"home"})))


class HomeCohorts(unittest.TestCase):
    def test_only_cohorts_on_home_tiles_are_home_cohorts(self):
        setup = types.SimpleNamespace(countries=lambda: ["home", "away"], civ_id="home",
                                      country_of=lambda tile: "home" if tile.startswith("h") else "away")
        record = types.SimpleNamespace(cohorts={"a": types.SimpleNamespace(tile="h1"), "b": types.SimpleNamespace(tile="x1")})
        self.assertEqual([cohort.tile for cohort in home_scope.home_cohorts(setup, record)], ["h1"])

    def test_a_tile_changing_hands_changes_the_answer(self):
        owners = {}
        setup = EconomySetup_for_scope(owners)
        self.assertFalse(home_scope.has_partners(setup))
        owners["t1"] = {"owner": "away", "control": "away"}
        self.assertTrue(home_scope.has_partners(setup))
        self.assertFalse(home_scope.on_home_tile(setup, "t1"))

    def test_with_one_country_every_tile_is_home(self):
        setup = types.SimpleNamespace(countries=lambda: ["home"], civ_id="home", country_of=lambda tile: "other")
        self.assertTrue(home_scope.on_home_tile(setup, "anywhere"))


class OpeningWageAtIndexBase(unittest.TestCase):
    def test_the_opening_wage_is_scaled_by_the_level_the_rebase_kept(self):
        setup = types.SimpleNamespace(opening_wages={"mason": 2.0}, currency_id="coin")
        record = types.SimpleNamespace(memory=types.SimpleNamespace(opening_wage_levels={"coin": 4.0}))
        self.assertEqual(year_accounts.opening_wage_at_index_base(setup, record, "mason"), 8.0)

    def test_before_any_rebase_the_opening_wage_stands_and_an_unpaid_trade_has_none(self):
        setup = types.SimpleNamespace(opening_wages={"mason": 2.0}, currency_id="coin")
        record = types.SimpleNamespace(memory=types.SimpleNamespace(opening_wage_levels={}))
        self.assertEqual(year_accounts.opening_wage_at_index_base(setup, record, "mason"), 2.0)
        self.assertIsNone(year_accounts.opening_wage_at_index_base(setup, record, "scribe"))

    def test_the_real_wage_index_is_one_when_wage_and_basket_both_rose_by_the_kept_level(self):
        wage = year_accounts.RealWage("mason", 8.0, 8.0, 40.0, 40.0, 2000.0)
        self.assertAlmostEqual(wage.real_wage_index, 1.0)


class UnpricedMineCost(unittest.TestCase):
    def test_a_material_nothing_prices_has_no_running_cost_not_a_free_one(self):
        costs = types.SimpleNamespace(capex_opex=lambda material: (None, None))
        self.assertIsNone(MineCosts.mine_opex(costs, "unobtainium"))
        costs.mine_opex = lambda material: None
        self.assertIsNone(MineCosts.operating_cost_of(costs, {"material": "unobtainium", "capacity": 5.0}))


class WashedResidue(unittest.TestCase):
    def test_float_dust_left_after_the_washed_quantity_is_not_a_fill(self):
        fill = make_fill("edge", "grain", "area", "tile", 1.0 + 1e-15, 2.0, "buy")
        self.assertEqual(without_washed([fill], {"edge": 1.0}), [])

    def test_a_real_remainder_survives_at_its_price(self):
        fill = make_fill("edge", "grain", "area", "tile", 3.0, 2.0, "sell")
        kept = without_washed([fill], {"edge": 1.0})
        self.assertEqual([(each.quantity, each.price) for each in kept], [(2.0, 2.0)])


class LateGoodPriceVintage(unittest.TestCase):
    def test_a_late_good_is_priced_in_opening_year_money(self):
        production = {"cement_kg": {"outputs": {"cement_kg": 1000.0}, "inputs": {"lime_kg": 1000.0},
                                "labour_hours": {"kilnman": 20.0}, "unit_dimension": "mass", "requires_node": "kiln_node"}}
        society = types.SimpleNamespace(
            economy=types.SimpleNamespace(agent_prices=lambda: {"lime_kg": 6.0}, labour=types.SimpleNamespace(quote=lambda trade: 5.0)),
            scenario=types.SimpleNamespace(held_civ={"id": "testland"}), finance=types.SimpleNamespace(market_rate=lambda: 0.0),
            state=types.SimpleNamespace(trade_registry={"kilnman": {}}))
        cost = port_late.late_goods_costs(society, {}, ["cement_kg"], frozenset({"kiln_node"}), production, 3.0)
        self.assertAlmostEqual(cost["cement_kg"], (1000.0 * 6.0 + 20.0 * 5.0) / 1000.0 / 3.0)


if __name__ == "__main__":
    unittest.main()
