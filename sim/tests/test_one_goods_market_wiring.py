"""Complaints 359 and 364, the wiring: the founder's stock sale, an actor's sale and a firm's takings all go through the one goods
market. Each method is called on a stand-in carrying only what it reads; no game is built. The price rules are in
test_one_goods_market."""
import types
import unittest
from unittest import mock

from sim.agents.api import Actor
from sim.actors.world import ActorWorld
from sim.markets.module import Markets
from sim.markets.api import SellMaterial
from sim.tests import module_harness
from sim.engine.goods_market_api import GoodsMarket
from sim.tests.world_stand_in import fake_needs
from sim.markets.api import NoteActorSale

QUICK_TOPIC = True

MATERIAL = "iron"
FOUNDER = "seat:founder"


class Seller:
    party_id = FOUNDER

    def __init__(self):
        self.handed, self.received = [], []

    def hand_over(self, key, tonnes):
        self.handed.append((key, tonnes))

    def receive(self, money, purpose):
        self.received.append(money)


def market_over_flows():
    flows = {"sold": {}, "bought": {}, "drawn": {}, "reservation": {}}
    game = types.SimpleNamespace(_flows=flows, state=types.SimpleNamespace(acting_seat=FOUNDER))
    game._market_flows = lambda: flows
    return GoodsMarket(game)


class FounderSaleTests(unittest.TestCase):
    def test_the_sale_is_entered_in_the_book_under_the_sellers_party_and_paid_for(self):
        market, seller = market_over_flows(), Seller()
        with mock.patch.object(GoodsMarket, "quote_sell", lambda self, material, tonnes, who: ("iron_key", 4.0, 120.0)):
            sold = market.sell(seller, MATERIAL, 5.0)
        self.assertEqual(sold, 4.0)
        self.assertEqual(market.sold_tonnes("iron_key", FOUNDER), 4.0)
        self.assertEqual(market.others_sold_tonnes("iron_key"), 0.0)
        self.assertEqual(seller.handed, [("iron_key", 4.0)])
        self.assertEqual(seller.received, [120.0])

    def test_a_sale_the_market_takes_none_of_enters_nothing(self):
        market, seller = market_over_flows(), Seller()
        with mock.patch.object(GoodsMarket, "quote_sell", lambda self, material, tonnes, who: (None, 0.0, 0.0)):
            self.assertEqual(market.sell(seller, MATERIAL, 5.0), 0.0)
        self.assertEqual(market.sold_tonnes(MATERIAL), 0.0)
        self.assertEqual(seller.handed, [])

    def test_the_engines_stock_sale_is_the_markets_sale_by_the_asking_seat(self):
        seen = []
        market = types.SimpleNamespace(acting="the asking seat", sell=lambda seller, material, tonnes: seen.append((seller, material, tonnes)) or 2.5)
        game = types.SimpleNamespace(goods_market=market)
        self.assertEqual(module_harness.build(Markets, views={"legacy_game": game}).sell_material(SellMaterial(MATERIAL, 3.0)), 2.5)
        self.assertEqual(seen, [("the asking seat", MATERIAL, 3.0)])


class ActorWiringTests(unittest.TestCase):
    def test_an_actors_sale_is_noted_in_the_economys_book_with_the_concerns_that_made_it(self):
        needs = fake_needs()
        world = types.SimpleNamespace(needs=needs)
        ActorWorld.market_sale(world, "firm:iron1", "pig_iron_kg", 7.0, [("blast_furnace", 7.0)])
        self.assertEqual(needs.sent, [NoteActorSale("firm:iron1", "pig_iron_kg", 7.0, [("blast_furnace", 7.0)])])

    def test_an_actor_puts_what_its_concerns_make_into_the_market_each_at_its_own_cost(self):
        sales = []
        actor = types.SimpleNamespace(
            actor_id="firm:iron1", concerns={"blast_furnace": object()},
            output_by_concern=lambda material, world: [("blast_furnace", 7.0)] if material == "pig_iron_kg" else [])
        world = types.SimpleNamespace(materials_made_by=lambda node_id: ["pig_iron_kg"],
                                      market_sale=lambda *arguments: sales.append(arguments))
        Actor.sell_output(actor, world)
        self.assertEqual(sales, [("firm:iron1", "pig_iron_kg", 7.0, [("blast_furnace", 7.0)])])

    def test_takings_of_a_concern_outside_the_goods_categories_carry_the_output_market_factor(self):
        for factor in (0.5, 1.0, 2.0):
            world = takings_world("ENGINEERING", factor, ramp=0.8)
            self.assertAlmostEqual(ActorWorld.concern_takings(world, "blast_furnace", 90), 100.0 * 0.8 * factor)

    def test_the_same_concern_split_with_rivals_takes_a_share(self):
        alone = ActorWorld.concern_takings(takings_world("ENGINEERING", 1.5), "blast_furnace", 90, rivals=0.0)
        shared = ActorWorld.concern_takings(takings_world("ENGINEERING", 1.5), "blast_furnace", 90, rivals=3.0)
        self.assertAlmostEqual(shared, alone / 4.0)

    def test_a_goods_category_takes_the_categorys_factor_in_place_of_a_share_of_rivals(self):
        world = takings_world("GOODS", 1.5, category_factor=0.25)
        self.assertAlmostEqual(ActorWorld.concern_takings(world, "kiln", 90, rivals=3.0), 100.0 * 1.5 * 0.25)


def takings_world(category, factor, ramp=1.0, category_factor=1.0):
    needs = fake_needs(
        concern_takings=lambda node_id, at_ramp: 100.0 * at_ramp,
        node_output_market_factor=lambda node: factor, goods_category_factor=lambda cat: category_factor)
    return types.SimpleNamespace(needs=needs, goods_category_names=("GOODS",), nodes={"blast_furnace": {"cat": category}, "kiln": {"cat": category}},
                                 ramp=lambda opened_year, node_id=None: ramp)


if __name__ == "__main__":
    unittest.main()
