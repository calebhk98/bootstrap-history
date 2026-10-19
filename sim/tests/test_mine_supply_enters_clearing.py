"""Complaint 135: a mine's output is supply in the year's clearing, on both paths. Agent economy: a site-bound
mine is a producer whose output is the year's supply (sim/economy/sites.py caps its runs by the deposit's
limit). Engine path: the society's baseline capacity is the deposits' output (their quantities are shares of
the empire output table, scaled by the reach to the tiles held, geography.mineral_scale), and any mine a
concern runs is an offer at its own cost (producer_costs.founder_concern_offers, goods_market.others_offers)."""

QUICK_TOPIC = True

import unittest
from dataclasses import replace

from sim.economy.types import SiteLimit
from sim.tests import economy_fixture as fixture
from sim.world import market
from sim.world.producer_market import Offer


def runs_the_opening_asks_of_mines():
    """The runs of ore digging a year the fixture's opening is sized to need (its smelters' demand)."""
    from sim.economy import opening
    record, _areas, _carriage = opening.open_economy(fixture.small_setup())
    return sum(producer.expected_sales for producer in record.producers.values() if producer.recipe_id == fixture.MINE)


YEARS = 6      # years run: the opening stocks its smelters with a year of ore, so a shortage binds only after it is used


def ore_after_the_years(runs_allowed, runs_allowed_later=None):
    """(ore made, ore price) in the last year. The opening is sized to `runs_allowed`; from the second year the
    deposits allow `runs_allowed_later` (new mines found) when given."""
    recipes = fixture.recipes()
    recipes[fixture.MINE] = replace(recipes[fixture.MINE], site_bound=True)

    def limits(runs):
        return (SiteLimit(fixture.MINE, fixture.HILLS, runs, 1.0),)
    setup = fixture.small_setup(recipes=recipes, site_limits=limits(runs_allowed))

    def inputs_for_year(_economy, year):
        if year == 0 or runs_allowed_later is None:
            return fixture.quiet_year(setup)
        return fixture.quiet_year(setup, site_limits=limits(runs_allowed_later))
    _economy, outcomes = fixture.run(setup, years=YEARS, inputs_for_year=inputs_for_year)
    return outcomes[-1].output.get(fixture.ORE, 0.0), outcomes[-1].prices[fixture.ORE]


class AgentEconomyMineTests(unittest.TestCase):
    def test_a_mines_capacity_is_the_ore_supplied(self):
        need = runs_the_opening_asks_of_mines()
        small, _price = ore_after_the_years(0.1 * need)
        large, _price = ore_after_the_years(2.0 * need)
        self.assertGreater(large, 5.0 * small)

    def test_a_glut_from_mines_lowers_the_ore_price(self):
        # the opening fits its smelters to the ore its deposits allow, so a shortage that exists from the start
        # shows as less ore and not a dearer one; scarcity and glut are what happens to the deposits after it
        need = runs_the_opening_asks_of_mines()
        _output, scarce_price = ore_after_the_years(need, runs_allowed_later=0.3 * need)
        _output, glut_price = ore_after_the_years(need, runs_allowed_later=20.0 * need)
        self.assertLess(glut_price, scarce_price)


class EnginePathMineTests(unittest.TestCase):
    CONDITIONS = dict(household_demand_at_anchor_tonnes=100.0, committed_demand_tonnes=0.0,
                      society_capacity_tonnes=100.0, actor_supply_tonnes=0.0, founder_sales_tonnes=0.0,
                      stock_tonnes=0.0, floor_ratio=0.4)

    def test_a_concerns_mine_adds_supply_to_the_baseline_and_lowers_the_price(self):
        alone = market.clear_market(market.MarketConditions(**self.CONDITIONS))
        with_mine = market.clear_market(market.MarketConditions(**self.CONDITIONS, offers=(Offer(60.0, 0.5),)))
        self.assertLess(with_mine.price_ratio, alone.price_ratio)
        self.assertGreater(with_mine.offers_sold_tonnes, 0.0)


if __name__ == "__main__":
    unittest.main()
