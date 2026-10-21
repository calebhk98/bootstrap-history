"""Buyers of ground other than cohorts (Complaint 538): a firm, a state or an institution bids through land_bid as any
actor, and an actor with no hands buys only to let the ground for its rent and leases it out."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import land_market, land_bid_year, land_lease_year, titles, titles_worked
from sim.economy.households_cohort import Cohort
from sim.economy.types import GoodSpec, GoodsMove, Recipe, TileSpec, Transfer
from sim.tests.test_economy_land_lease_year import BASKET, GRAIN_RECIPE, LAND, View
from sim.economy.households_own import own_production_options
from sim.economy.producers import Producer

TILE = "t"
GROUND = "ground"
CLEARER = "producer:clearer"
STATE = "state:crown"
HOUSE = "institution:house"
POOR = "household:t:0"
LANDLORD = "household:t:2"


class BuyerView(View):
    def interest_rate(self, currency):
        return 0.05

    def currency_of(self, area):
        return "coin"

    def price(self, good, area):
        return 100.0 if good == GROUND else super().price(good, area)


def world(rent=20.0):
    tile = TileSpec(TILE, 40.0, 10.0, 1.0, False, (), 1.0, 1.0, climate_class="Cfb")
    clear = Recipe("clear", {GROUND: 1.0}, {}, {})
    recipes = {"grow_grain": GRAIN_RECIPE, "clear": clear, "farm": Recipe("farm", {"grain": 10.0}, {}, {"hand": 4.0})}
    setup = types.SimpleNamespace(
        tiles={TILE: tile}, recipes=recipes, land_per_run={**LAND, "farm": 2.0}, servant_trade="servant", working_hours_per_year=2000.0,
        specs={GROUND: GoodSpec(GROUND, float("inf"), 0.0, 0.0, "")}, opening_rate=0.05, currency_id="coin",
        basket_for=lambda tile_id: BASKET)
    from sim.economy.accounts import Book
    record = types.SimpleNamespace(
        cohorts={POOR: Cohort(POOR, TILE, 0, 10.0, 10.0, 0.0), LANDLORD: Cohort(LANDLORD, TILE, 2, 0.0, 0.0, 1.0)},
        titles={TILE: {LANDLORD: 1.0}}, tenancies={}, loans=[], land_rent={TILE: rent}, cleared_hectares={},
        producers={CLEARER: Producer(CLEARER, LANDLORD, "clear", TILE, 10.0)}, book=Book())
    return setup, record, own_production_options(recipes, LAND, BASKET)


class ActorBidTests(unittest.TestCase):
    def test_an_actor_with_no_hands_bids_for_ground_to_let_it_for_its_rent(self):
        setup, record, _options = world(rent=20.0)
        bids = land_bid_year.actor_bids(setup, record, BuyerView(0.2), STATE, TILE, 0.0, 0.0, 0.0, 10000.0)
        self.assertEqual([(bid.buyer, bid.good) for bid in bids], [(STATE, GROUND)])
        self.assertLessEqual(bids[0].maximum_price, 20.0 / 0.05 + 1e-9)       # the rent capitalised at the rate
        self.assertGreater(bids[0].maximum_price, 100.0)

    def test_no_bid_when_the_rent_does_not_repay_the_going_price(self):
        setup, record, _options = world(rent=1.0)
        self.assertEqual(land_bid_year.actor_bids(setup, record, BuyerView(0.2), STATE, TILE, 0.0, 0.0, 0.0, 10000.0), [])

    def test_a_seller_does_not_bid_for_its_own_ground(self):
        setup, record, _options = world()
        self.assertEqual(land_bid_year.actor_bids(setup, record, BuyerView(0.2), LANDLORD, TILE, 0.0, 0.0, 0.0, 1e6), [])

    def test_a_farm_with_hands_bids_no_more_hectares_than_its_hours_work(self):
        setup, record, _options = world()
        bids = land_bid_year.actor_bids(setup, record, BuyerView(0.2), "household:t:9", TILE, 30.0, 2.0, 20.0, 1e6)
        self.assertAlmostEqual(bids[0].flexible_quantity, 10.0)         # twenty hours at two hours a hectare

    def test_a_firm_that_farms_bids_at_its_margin_out_of_the_cash_its_plan_left(self):
        setup, record, _options = world()
        record.producers["producer:farm"] = Producer("producer:farm", POOR, "farm", TILE, 10.0,
                                                     expected_prices={"grain": 5.0})
        record.book.transfer(Transfer("edge:legacy", "producer:farm", "coin", 10000.0, "opening"))
        view = BuyerView(0.2, tools=100.0)
        planned = land_bid_year.firm_land_bids(setup, record, view, {"producer:farm": 5.0}, {"producer:farm": 10000.0})
        free = land_bid_year.firm_land_bids(setup, record, view, {"producer:farm": 5.0}, {"producer:farm": 5000.0})
        self.assertEqual(land_market.demands_of(setup, record, view, {"producer:farm": 5.0})[0].agent_id, "producer:farm")
        self.assertEqual(planned, [])                                     # the plan took the cash
        self.assertEqual([bid.buyer for bid in free], ["producer:farm"])
        self.assertLessEqual(free[0].budget, 5000.01)


class TitleAndLetTests(unittest.TestCase):
    def test_ground_any_actor_bought_becomes_its_title_and_a_rent_only_holder_lets_it_to_a_landless_cohort(self):
        setup, record, options = world()
        record.titles[TILE] = {LANDLORD: 1.0}
        record.book.move_many([GoodsMove("edge:production", STATE, GROUND, TILE, 6.0, "bought")])
        record.book.move_many([GoodsMove("edge:production", CLEARER, GROUND, TILE, 4.0, "cleared")])
        titled = land_bid_year.take_up_bought(setup, record)
        self.assertAlmostEqual(titled[STATE], 6.0)
        self.assertAlmostEqual(record.book.stock(CLEARER, GROUND, TILE), 4.0)       # the clearer's stock is not a purchase
        self.assertGreater(titles.holding(record, TILE, STATE), 0.0)
        record.titles[TILE] = {STATE: record.titles[TILE][STATE]}                  # the rest of the land is not on offer
        leases = land_lease_year.lease_in_market(setup, record, BuyerView(0.2, tools=100.0), options)
        self.assertEqual([(lease.tenant, lease.lessor) for lease in leases], [(POOR, STATE)])
        self.assertGreater(titles_worked.worked_share(record, TILE, POOR), 0.0)
        self.assertAlmostEqual(titles_worked.worked_share(record, TILE, STATE), titles.holding(record, TILE, STATE) - titles.let_out_share(record, TILE, STATE))

    def test_two_kinds_of_actor_buy_the_same_way(self):
        setup, record, _options = world()
        for actor, hectares in ((STATE, 3.0), (HOUSE, 2.0)):
            record.book.move_many([GoodsMove("edge:production", actor, GROUND, TILE, hectares, "bought")])
        titled = land_bid_year.take_up_bought(setup, record)
        self.assertEqual(sorted(titled), [HOUSE, STATE])


if __name__ == "__main__":
    unittest.main()
