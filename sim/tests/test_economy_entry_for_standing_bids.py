"""Complaint 512: a standing bid for a good no one makes (a fixed quantity, no price schedule, as a merchant's
replacement carriers or a project's draw are) is demand firm entry sees: a maker enters within a few years when
the recipe pays at the price the bid offers. The bid's demand and the founder's draws becoming bids: test_standing_bids_rule."""

QUICK_TOPIC = False   # clears whole economies over several years

import dataclasses
import unittest

from sim.economy.economy import Economy
from sim.economy.protocols import AgentOrders
from sim.economy.types import Bid, GoodSpec, Recipe
from sim.tests import economy_fixture as fixture

GADGET, MAKE_GADGET = "gadget", "make_gadget"
UNITS_WANTED = 4.0
YEARS = 5


def gadget_setup(price=400.0):
    specs = dict(fixture.specs())
    specs[GADGET] = GoodSpec(GADGET, 20.0, 0.0, 0.0, "carrier")
    recipes = dict(fixture.recipes())
    recipes[MAKE_GADGET] = Recipe(MAKE_GADGET, {GADGET: 1.0}, {fixture.METAL: 1.0}, {fixture.SMITH: 40.0})
    base = fixture.small_setup()
    return dataclasses.replace(base, specs=specs, recipes=recipes,
                               opening_prices=dict(base.opening_prices, **{GADGET: price}))


def standing_bid(economy, setup):
    """The state's fixed-quantity bid for the gadget delivered to its capital: no flexible part."""
    area = economy.area_map.area_of(GADGET, setup.capital_tile)
    money = economy.record.book.balance(setup.state_agent, setup.currency_id)
    return Bid(setup.state_agent, GADGET, area, setup.capital_tile, UNITS_WANTED, 0.0, setup.opening_prices[GADGET],
               1.0, min(money, UNITS_WANTED * setup.opening_prices[GADGET] * 2.0))


def economy_without_gadget_makers(setup):
    """The opening seeds a maker of every recipe; take them out so no one makes the gadget."""
    economy = Economy(setup)
    for producer_id in [each for each, producer in economy.record.producers.items() if producer.recipe_id == MAKE_GADGET]:
        del economy.record.producers[producer_id]
    return economy


def run_with_bid(setup):
    economy = economy_without_gadget_makers(setup)
    for _year in range(YEARS):
        bid = standing_bid(economy, setup)
        inputs = fixture.quiet_year(setup, engine_orders={setup.state_agent: AgentOrders(bids=(bid,))})
        economy.step(inputs)
    return economy


def gadget_capacity(economy):
    return sum(producer.capacity_runs + economy.record.expansion_runs.get(producer_id, 0.0)
               for producer_id, producer in economy.record.producers.items() if producer.recipe_id == MAKE_GADGET)


class StandingBidDrawsAMakerTests(unittest.TestCase):
    def test_a_fixed_quantity_bid_for_an_unmade_good_draws_a_maker(self):
        economy = run_with_bid(gadget_setup())
        self.assertGreater(gadget_capacity(economy), 0.0)


class StandingBidsTests(unittest.TestCase):
    """Demand settled outside the book (the founder's project draws) is read by entry as bids and clears nothing."""

    def run_with_standing(self, with_bid):
        setup = gadget_setup()
        economy = economy_without_gadget_makers(setup)
        for _year in range(YEARS):
            area = economy.area_map.area_of(GADGET, setup.capital_tile)
            bids = (Bid("standing:founder", GADGET, area, setup.capital_tile, UNITS_WANTED, 0.0, 400.0, 0.0,
                        UNITS_WANTED * 400.0),) if with_bid else ()
            economy.step(fixture.quiet_year(setup, standing_bids=bids))
        return economy

    def test_a_standing_bid_draws_a_maker_though_nothing_clears_against_it(self):
        self.assertGreater(gadget_capacity(self.run_with_standing(True)), 0.0)

    def test_without_the_standing_bid_no_one_makes_the_gadget(self):
        self.assertEqual(gadget_capacity(self.run_with_standing(False)), 0.0)


if __name__ == "__main__":
    unittest.main()
