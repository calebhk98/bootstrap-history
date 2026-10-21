"""Complaint 538, the buyer of cleared ground: a hectare is worth its earning (crop margin or rent) capitalised, an
actor bids for it only when that beats the going price and only for what its spare hours can work, and a hectare it
takes up (bought, or kept from its own clearer's stock) is new arable land titled to it. Built inputs, the rules (`sim/economy/land_bid.py`) called."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import land_bid, land_bid_year, titles, titles_ground, titles_value
from sim.economy.accounts import Book
from sim.economy.households_cohort import cohort_id, cohorts_for_tile
from sim.economy.market_memory import MarketMemory
from sim.economy.producers import Producer
from sim.economy.record import EconomyRecord
from sim.economy.protocols import AgentOrders
from sim.economy.types import CurrencySpec, FundsOffer, GoodSpec, GoodsMove, Recipe, TileSpec

GROUND, CROP, TILE, AREA = "ground", "grain", "t", "area"
RATE, OPENING_RATE = 0.1, 0.05
HECTARES_ON_TILE = 100.0
BUYER, SELLER = cohort_id(TILE, 0), cohort_id(TILE, 2)
GRAIN_RECIPE = Recipe("farm", {CROP: 10.0}, {}, {"farmer": 20.0})


class MarginTests(unittest.TestCase):
    def test_margin_is_output_value_less_hours_at_the_wage_per_hectare(self):
        margin = land_bid.crop_margin_per_hectare(GRAIN_RECIPE, 2.0, 1.0, {CROP: 3.0}, 0.5)
        self.assertAlmostEqual(margin, (10.0 * 3.0 - 20.0 * 0.5) / 2.0)

    def test_fertility_scales_the_crop_not_the_hours(self):
        poor = land_bid.crop_margin_per_hectare(GRAIN_RECIPE, 1.0, 0.5, {CROP: 3.0}, 0.5)
        rich = land_bid.crop_margin_per_hectare(GRAIN_RECIPE, 1.0, 1.5, {CROP: 3.0}, 0.5)
        self.assertAlmostEqual(rich - poor, 10.0 * 3.0)

    def test_a_hectare_earns_the_better_of_farming_and_rent_never_less_than_nothing(self):
        self.assertEqual(land_bid.earning_per_hectare(4.0, 1.0), 4.0)
        self.assertEqual(land_bid.earning_per_hectare(-4.0, 1.0), 1.0)
        self.assertEqual(land_bid.earning_per_hectare(-4.0, 0.0), 0.0)

    def test_spare_hours_work_so_many_hectares(self):
        hours = land_bid.hours_per_hectare(GRAIN_RECIPE, 2.0)
        self.assertAlmostEqual(land_bid.workable_hectares(50.0, hours), 5.0)
        self.assertEqual(land_bid.workable_hectares(50.0, 0.0), float("inf"))     # nothing to work: only cash limits it


class BidTests(unittest.TestCase):
    def bid(self, earning=1.0, going_price=5.0, hectares=4.0, cash=1000.0, rate=RATE):
        return land_bid.hectare_bid(BUYER, GROUND, AREA, TILE, earning, going_price, rate, hectares, cash)

    def test_the_most_it_bids_is_the_earning_over_the_rate(self):
        bid = self.bid(earning=1.0)
        self.assertAlmostEqual(bid.maximum_price, titles_value.hectare_value(1.0, RATE))
        self.assertAlmostEqual(bid.flexible_quantity, 4.0)

    def test_no_bid_when_a_hectare_costs_at_least_what_it_is_worth(self):
        self.assertIsNone(self.bid(earning=1.0, going_price=10.0))
        self.assertIsNone(self.bid(earning=1.0, going_price=12.0))

    def test_no_bid_without_a_price_hands_or_cash(self):
        self.assertIsNone(self.bid(going_price=None))
        self.assertIsNone(self.bid(hectares=0.0))
        self.assertIsNone(self.bid(cash=0.0))

    def test_the_budget_is_its_cash_when_cash_is_short(self):
        self.assertAlmostEqual(self.bid(cash=7.0).budget, 7.0)

    def test_it_asks_for_no_more_hectares_than_its_cash_buys_at_the_going_price(self):
        self.assertAlmostEqual(self.bid(hectares=float("inf"), cash=20.0, going_price=5.0).flexible_quantity, 4.0)

    def test_a_dearer_going_price_withdraws_the_bid(self):
        self.assertIsNotNone(self.bid(going_price=9.0))
        self.assertIsNone(self.bid(going_price=11.0))


class TitleTests(unittest.TestCase):
    def world(self):
        record = EconomyRecord(book=Book(), memory=MarketMemory(), currency=CurrencySpec("coin", "fiat", None, 0.0, None))
        for cohort in cohorts_for_tile(TILE, 300.0, 0.5, 0.4, class_count=3):
            record.cohorts[cohort.agent_id] = cohort
        titles.seed(record)
        return record

    def test_cleared_ground_is_new_arable_land_titled_to_the_taker(self):
        record = self.world()
        seller_hectares = titles.holding(record, TILE, SELLER) * HECTARES_ON_TILE
        added = land_bid.take_up(record, BUYER, TILE, 25.0, HECTARES_ON_TILE)
        self.assertAlmostEqual(added, 25.0)
        self.assertAlmostEqual(sum(titles.shares(record, TILE).values()), 1.0)
        self.assertAlmostEqual(record.cleared_hectares[TILE], 25.0)
        self.assertAlmostEqual(titles.holding(record, TILE, SELLER) * (HECTARES_ON_TILE + 25.0), seller_hectares)

    def test_nobody_else_gives_up_a_hectare(self):
        record = self.world()
        before = {holder: share * HECTARES_ON_TILE for holder, share in titles.shares(record, TILE).items()}
        land_bid.take_up(record, BUYER, TILE, 25.0, HECTARES_ON_TILE)
        after = {holder: share * (HECTARES_ON_TILE + 25.0) for holder, share in titles.shares(record, TILE).items()}
        for holder, hectares in before.items():
            self.assertAlmostEqual(after[holder] - hectares, 25.0 if holder == BUYER else 0.0)

    def test_tenancies_and_pledges_keep_their_hectares(self):
        record = self.world()
        record.tenancies = {TILE: [{"tenant": BUYER, "lessor": SELLER, "share": 0.2, "arrears": 0.0}]}
        record.loans = [types.SimpleNamespace(borrower=SELLER, collateral_tile=TILE, collateral_share=0.1)]
        land_bid.take_up(record, BUYER, TILE, 100.0, HECTARES_ON_TILE)
        self.assertAlmostEqual(record.tenancies[TILE][0]["share"] * 2.0 * HECTARES_ON_TILE, 0.2 * HECTARES_ON_TILE)
        self.assertAlmostEqual(record.loans[0].collateral_share * 2.0 * HECTARES_ON_TILE, 0.1 * HECTARES_ON_TILE)

    def test_no_ground_or_no_arable_land_adds_nothing(self):
        record = self.world()
        self.assertEqual(land_bid.take_up(record, BUYER, TILE, 0.0, HECTARES_ON_TILE), 0.0)
        self.assertEqual(land_bid.take_up(record, BUYER, TILE, 5.0, 0.0), 0.0)
        self.assertEqual(record.cleared_hectares, {})

    def test_the_tiles_arable_land_counts_what_was_cleared(self):
        record = self.world()
        tile = TileSpec(TILE, 40.0, 10.0, 1.0, False, (), 1.0, 1.0)
        land_bid.take_up(record, BUYER, TILE, 25.0, titles_ground.arable_hectares(record, TILE, tile))
        self.assertAlmostEqual(titles_ground.arable_hectares(record, TILE, tile), HECTARES_ON_TILE + 25.0)
        self.assertEqual(titles_ground.arable_hectares(record, TILE, None), 0.0)

    def test_cleared_hectares_survive_a_save_and_load(self):
        record = self.world()
        land_bid.take_up(record, BUYER, TILE, 25.0, HECTARES_ON_TILE)
        loaded = EconomyRecord.from_record(record.to_record())
        self.assertEqual(loaded.cleared_hectares, record.cleared_hectares)

    def test_an_owner_keeps_of_its_own_stock_what_its_plots_need_beyond_its_land(self):
        self.assertAlmostEqual(land_bid.own_use(stock=50.0, hectares_needed=30.0, hectares_held=12.0), 18.0)
        self.assertAlmostEqual(land_bid.own_use(stock=10.0, hectares_needed=30.0, hectares_held=12.0), 10.0)
        self.assertEqual(land_bid.own_use(stock=50.0, hectares_needed=30.0, hectares_held=40.0), 0.0)


class SellerAndGroundTests(unittest.TestCase):
    def test_ground_is_an_immobile_good_a_recipe_makes_from_nothing(self):
        specs = {GROUND: GoodSpec(GROUND, float("inf"), 0.0, 0.0, ""), CROP: GoodSpec(CROP, 1.0, 0.0, 0.0, ""),
                 "heat": GoodSpec("heat", float("inf"), 0.0, 0.0, "")}
        recipes = {"clear": Recipe("clear", {GROUND: 1.0}, {}, {}), "farm": GRAIN_RECIPE,
                   "burn": Recipe("burn", {"heat": 1.0}, {CROP: 1.0}, {})}
        self.assertEqual(land_bid.land_goods(specs, recipes), (GROUND,))

    def test_a_sold_hectare_is_the_land_of_the_producers_owner(self):
        recipes = {"clear": Recipe("clear", {GROUND: 1.0}, {}, {})}
        record = types.SimpleNamespace(producers={"p": Producer("p", SELLER, "clear", TILE, 10.0)})
        self.assertEqual(land_bid.owners_of_sellers(record, recipes, GROUND, TILE), [SELLER])
        self.assertEqual(land_bid.owners_of_sellers(record, recipes, GROUND, "elsewhere"), [])


class YearWiringTests(unittest.TestCase):
    def world(self):
        record = TitleTests().world()
        record.producers = {"p": Producer("p", SELLER, "clear", TILE, 10.0)}
        tile = TileSpec(TILE, 40.0, 10.0, 1.0, False, (), 1.0, 1.0)      # a hundred hectares
        specs = {GROUND: GoodSpec(GROUND, float("inf"), 0.0, 0.0, "")}
        setup = types.SimpleNamespace(tiles={TILE: tile}, specs=specs, recipes={"clear": Recipe("clear", {GROUND: 1.0}, {}, {})})
        return setup, record

    def test_ground_a_cohort_bought_becomes_its_title_and_leaves_its_stock(self):
        setup, record = self.world()
        record.book.move_many([GoodsMove("edge:production", BUYER, GROUND, TILE, 5.0, "bought")])
        titled = land_bid_year.take_up_bought(setup, record)
        self.assertAlmostEqual(titled[BUYER], 5.0)
        self.assertAlmostEqual(record.cleared_hectares[TILE], 5.0)
        self.assertEqual(record.book.stock(BUYER, GROUND, TILE), 0.0)

    def test_a_seller_with_no_land_of_its_own_still_sells_ground_it_cleared(self):
        setup, record = self.world()
        record.titles[TILE] = {BUYER: 1.0}
        record.book.move_many([GoodsMove("edge:production", BUYER, GROUND, TILE, 10.0, "bought")])
        land_bid_year.take_up_bought(setup, record)
        self.assertEqual(record.book.stock(BUYER, GROUND, TILE), 0.0)

    def own_world(self, stock, people_floor_hectares):
        setup, record = self.world()
        setup.basket_for = lambda tile: types.SimpleNamespace(needs=(types.SimpleNamespace(need_id="food", subsistence_per_person=1.0),))
        setup.land_per_run = {"farm": 1.0}
        setup.recipes["farm"] = Recipe("farm", {CROP: 1.0}, {}, {"farmer": 1.0})
        setup.tiles[TILE] = TileSpec(TILE, 40.0, 10.0, 1.0, False, (), 1.0, 1.0)
        owner = record.cohorts[SELLER]
        options = {"food": [(1.0, "farm", CROP, 1.0)]}
        record.book.move_many([GoodsMove("edge:production", "p", GROUND, TILE, stock, "cleared")])
        record.titles[TILE] = {SELLER: people_floor_hectares / HECTARES_ON_TILE}
        return setup, record, options, owner

    def test_the_clearers_owner_farms_what_its_floors_need_of_its_own_stock_before_it_is_sold(self):
        setup, record, options, owner = self.own_world(stock=1000.0, people_floor_hectares=0.0)
        needed = owner.people          # one hectare grows one need unit at fertility one
        kept = land_bid_year.take_up_own(setup, record, options)
        self.assertAlmostEqual(kept[SELLER], needed)
        self.assertAlmostEqual(record.book.stock("p", GROUND, TILE), 1000.0 - needed)
        self.assertAlmostEqual(titles.holding(record, TILE, SELLER) * (HECTARES_ON_TILE + needed), needed)

    def test_an_owner_that_holds_enough_land_keeps_nothing_of_its_stock(self):
        setup, record, options, owner = self.own_world(stock=1000.0, people_floor_hectares=HECTARES_ON_TILE)
        self.assertEqual(land_bid_year.take_up_own(setup, record, options), {})
        self.assertAlmostEqual(record.book.stock("p", GROUND, TILE), 1000.0)

    def test_what_the_owner_keeps_is_no_more_than_the_stock(self):
        setup, record, options, owner = self.own_world(stock=3.0, people_floor_hectares=0.0)
        self.assertAlmostEqual(land_bid_year.take_up_own(setup, record, options)[SELLER], 3.0)

    def test_the_money_set_aside_for_ground_comes_off_the_savings_on_offer(self):
        bid = land_bid.hectare_bid(BUYER, GROUND, AREA, TILE, 1.0, 5.0, RATE, 4.0, 30.0)
        orders = land_bid_year.with_land_bids(AgentOrders(funds_offers=(FundsOffer(BUYER, "coin", 100.0, 0.05),)), [bid])
        self.assertEqual(orders.bids, (bid,))
        self.assertAlmostEqual(orders.funds_offers[0].amount, 70.0)

    def test_savings_all_set_aside_leave_no_offer_to_lend(self):
        bid = land_bid.hectare_bid(BUYER, GROUND, AREA, TILE, 1.0, 5.0, RATE, 4.0, 40.0)
        orders = land_bid_year.with_land_bids(AgentOrders(funds_offers=(FundsOffer(BUYER, "coin", 40.0, 0.05),)), [bid])
        self.assertEqual(orders.funds_offers, ())


if __name__ == "__main__":
    unittest.main()
