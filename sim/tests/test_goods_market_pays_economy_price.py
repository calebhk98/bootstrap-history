"""Stage 3 of the one-price-owner plan (Complaint 507): what an actor pays and is paid for a material is the economy's
price on its tile plus carriage, and the climb of price over an order is the economy's own response. Small fixtures: a
stub game whose economy answers prices, offered tonnes and responses; nothing builds a game."""

QUICK_TOPIC = True

import math
import types
import unittest

from sim.engine import purchase_rule  # noqa: F401  (first: the engine modules import each other in a fixed order)
from sim.tests import market_stand_in
from sim.markets.goods_market import GoodsMarket

TILE_PRICE_PER_UNIT = {"wheat_kg": 0.08, "silver_kg": 400.0}
TABLE_PRICE_PER_UNIT = {"wheat_kg": 0.03, "silver_kg": 20.0, "alum_kg": 0.5}     # the cost of making, in the engine's money
OFFERED_TONNES = {"wheat_kg": 100.0, "silver_kg": 5.0}
CARRIAGE_PER_TONNE = {"wheat_kg": 0.0, "silver_kg": 7.0}


class _Economy:
    """An economy whose wheat market takes a quadratic climb with what is bought and falls with what is sold."""

    def __init__(self):
        self.opened = True
        self.responses_asked = []
        self.tiles_asked = set()

    def acting_tile(self):
        return "tile"

    def agent_prices_at(self, tile=None):
        return dict(TILE_PRICE_PER_UNIT) if self.opened else None

    def agent_price_kind(self, good):
        return "traded" if self.opened and good in TILE_PRICE_PER_UNIT else None

    def agent_offered_tonnes(self, material, tile=None):
        return OFFERED_TONNES.get(material) if self.opened else None

    def agent_price_response(self, material, landed_tonnes, taken_tonnes, tile=None):
        self.responses_asked.append((material, landed_tonnes, taken_tonnes))
        self.tiles_asked.add(tile)
        if not self.opened or material not in OFFERED_TONNES:
            return None
        offered = OFFERED_TONNES[material]
        if taken_tonnes >= offered:
            return math.inf
        return (1.0 + (taken_tonnes / offered) ** 2) / (1.0 + (landed_tonnes / offered) ** 2)


def stub_game(partner_makes=(), partner_prices=None):
    flows = {"sold": {}, "bought": {}, "drawn": {}, "reservation": {}}
    game = types.SimpleNamespace(
        economy=_Economy(),
        _price_tables=lambda: ({}, {material: "solved" for material in TABLE_PRICE_PER_UNIT}),
        _material_prices=lambda: TABLE_PRICE_PER_UNIT,
        _material_tag=lambda material: (material, material),
        _priced_key=lambda tag, prices: tag if tag in prices else None,
        _material_price_per_kg=TABLE_PRICE_PER_UNIT.get,
        _material_market_tonnes=lambda key: 1000.0,
        material_carriage_per_tonne=lambda key, price_per_tonne: CARRIAGE_PER_TONNE.get(key, 0.0),
        _market_flows=lambda: flows,
        foreign_economies=lambda: [],
        state=types.SimpleNamespace(projects=types.SimpleNamespace(done=()), scenario=types.SimpleNamespace(year=100),
                                    acting_seat="founder"),
        market_rate=lambda: 0.05, partner_price_level=lambda partner: 1.0,
        **market_stand_in.market_memory(),
        _foreign_economy_facts=lambda partner: {"solved_materials": frozenset(partner_makes),
                                                "prices_in_home_money": partner_prices or {}})
    return game, GoodsMarket(game)


class TilePriceTests(unittest.TestCase):

    def test_a_tonne_costs_the_economys_tile_price_plus_carriage(self):
        _game, market = stub_game()
        quote = market.quote("silver_kg")
        tile_per_tonne = TILE_PRICE_PER_UNIT["silver_kg"] * 1000.0
        self.assertAlmostEqual(quote["price_at_tile_per_tonne"], tile_per_tonne)
        self.assertAlmostEqual(quote["carriage_per_tonne"], CARRIAGE_PER_TONNE["silver_kg"])
        self.assertAlmostEqual(quote["buy_per_tonne"], tile_per_tonne + CARRIAGE_PER_TONNE["silver_kg"])

    def test_the_cost_table_no_longer_sets_what_is_paid(self):
        _game, market = stub_game()
        quote = market.quote("wheat_kg")
        self.assertAlmostEqual(quote["buy_per_tonne"], TILE_PRICE_PER_UNIT["wheat_kg"] * 1000.0)
        self.assertAlmostEqual(quote["making_cost_per_tonne"], TABLE_PRICE_PER_UNIT["wheat_kg"] * 1000.0)

    def test_while_the_economy_opens_the_cost_table_answers(self):
        game, market = stub_game()
        game.economy.opened = False
        self.assertAlmostEqual(market.quote("wheat_kg")["buy_per_tonne"], TABLE_PRICE_PER_UNIT["wheat_kg"] * 1000.0)

    def test_a_good_the_economy_does_not_trade_but_a_technique_makes_costs_what_it_costs_to_make(self):
        _game, market = stub_game()
        self.assertAlmostEqual(market.quote("alum_kg")["buy_per_tonne"], TABLE_PRICE_PER_UNIT["alum_kg"] * 1000.0)

    def test_the_quote_names_what_the_price_is(self):
        game, market = stub_game()
        self.assertEqual(market.quote("wheat_kg")["price_kind"], "traded")
        self.assertEqual(market.quote("alum_kg")["price_kind"], "making_cost_table")
        game.economy.opened = False
        self.assertEqual(market.quote("wheat_kg")["price_kind"], "making_cost_table")

    def test_a_good_no_seller_offers_has_no_price(self):
        _game, market = stub_game()
        self.assertIsNone(market.quote("cobalt_kg"))
        self.assertIsNone(market.purchase_cost("cobalt_kg", 1.0))
        self.assertIsNone(market.price("cobalt_kg"))
        self.assertFalse(market.can_be_bought("cobalt_kg"))

    def test_a_good_only_a_partner_makes_costs_its_landed_price_and_no_carriage(self):
        game, market = stub_game(partner_makes={"cassia_kg"}, partner_prices={"cassia_kg": 50.0})
        market._route_from = lambda partner: types.SimpleNamespace(cost_per_tonne=10.0)
        game.foreign_economies = lambda: ["partner"]
        game.foreign_supply_tonnes = lambda partner, material: 1000.0
        game.foreign_lift_left_tonnes = lambda partner, route: (math.inf, math.inf)
        game._trader_margin_share = lambda partner, route: 0.1
        game._cargo_lost_share = lambda route, material, partner: 0.0
        game._trader_cycle_years = lambda route, partner: 0.1
        game._agent_cost_per_tonne = lambda partner, route: 0.0
        quote = market.quote("cassia_kg")
        landed = market.landed_price("cassia_kg", "partner", market._route_from("partner"))
        self.assertAlmostEqual(quote["buy_per_tonne"], landed / 0.001)
        self.assertEqual(quote["carriage_per_tonne"], 0.0)


class ClimbTests(unittest.TestCase):

    def test_a_larger_order_costs_more_per_tonne(self):
        _game, market = stub_game()
        means = [market.purchase_cost("wheat_kg", tonnes)[1] for tonnes in (0.5, 5.0, 20.0, 60.0)]
        self.assertEqual(means, sorted(means))
        self.assertLess(means[0], means[-1])

    def test_the_bill_is_tonnes_times_the_mean_price(self):
        _game, market = stub_game()
        money, mean = market.purchase_cost("wheat_kg", 12.0)
        self.assertAlmostEqual(money, 12.0 * mean)

    def test_a_small_order_costs_the_quote(self):
        _game, market = stub_game()
        quote = market.quote("wheat_kg")["buy_per_tonne"]
        self.assertAlmostEqual(market.purchase_cost("wheat_kg", 1e-6)[1], quote, places=4)

    def test_the_climb_is_the_economys_response_and_the_carriage_comes_on_top_unclimbed(self):
        game, market = stub_game()
        mean = market.purchase_cost("silver_kg", 2.0)[1]
        tile = TILE_PRICE_PER_UNIT["silver_kg"] * 1000.0
        self.assertGreater(mean, tile + CARRIAGE_PER_TONNE["silver_kg"])
        self.assertTrue(game.economy.responses_asked)
        responses = [taken for _material, _landed, taken in game.economy.responses_asked]
        self.assertTrue(all(taken <= OFFERED_TONNES["silver_kg"] for taken in responses))

    def test_the_climb_is_read_on_the_acting_tile(self):
        game, market = stub_game()
        market.purchase_cost("wheat_kg", 10.0)
        market.sale_proceeds("wheat_kg", 10.0)
        self.assertEqual(game.economy.tiles_asked, {"tile"})

    def test_an_order_past_what_the_sellers_hold_still_has_a_finite_price(self):
        _game, market = stub_game()
        money, mean = market.purchase_cost("wheat_kg", 10 * OFFERED_TONNES["wheat_kg"])
        self.assertTrue(math.isfinite(money) and math.isfinite(mean))

    def test_what_was_already_bought_in_the_bill_moves_the_price(self):
        _game, market = stub_game()
        self.assertGreater(market.purchase_cost("wheat_kg", 5.0, already=40.0)[1], market.purchase_cost("wheat_kg", 5.0)[1])

    def test_what_the_founder_bought_this_year_moves_the_price_of_the_next_order(self):
        game, market = stub_game()
        before = market.quote("wheat_kg")["buy_per_tonne"]
        market.note_purchase("founder", "wheat_kg", 50.0)
        self.assertGreater(market.quote("wheat_kg")["buy_per_tonne"], before)

    def test_the_economy_without_a_book_for_the_good_adds_no_climb(self):
        _game, market = stub_game()
        self.assertAlmostEqual(market.purchase_cost("alum_kg", 50.0)[1], TABLE_PRICE_PER_UNIT["alum_kg"] * 1000.0)


class SaleTests(unittest.TestCase):

    def test_a_sale_fetches_the_tile_price_less_the_fall_its_own_supply_causes(self):
        _game, market = stub_game()
        tile = TILE_PRICE_PER_UNIT["wheat_kg"] * 1000.0
        money, mean = market.sale_proceeds("wheat_kg", 20.0)
        self.assertLess(mean, tile)
        self.assertAlmostEqual(money, mean * 20.0)

    def test_a_bigger_sale_fetches_less_per_tonne(self):
        _game, market = stub_game()
        means = [market.sale_proceeds("wheat_kg", tonnes)[1] for tonnes in (1.0, 10.0, 50.0)]
        self.assertEqual(means, sorted(means, reverse=True))

    def test_there_is_no_fixed_spread_between_the_buy_and_the_sell_quote(self):
        _game, market = stub_game()
        quote = market.quote("wheat_kg")
        self.assertAlmostEqual(quote["sell_per_tonne"], quote["buy_per_tonne"])

    def test_buying_and_selling_the_same_tonne_cannot_make_money(self):
        _game, market = stub_game()
        paid = market.purchase_cost("silver_kg", 1.0)[0]
        fetched = market.sale_proceeds("silver_kg", 1.0)[0]
        self.assertLess(fetched, paid)

    def test_a_good_with_no_price_has_no_sale_proceeds(self):
        _game, market = stub_game()
        self.assertIsNone(market.sale_proceeds("cobalt_kg", 5.0))


class CoinMetalTests(unittest.TestCase):

    def test_the_coin_metal_is_the_economys_tile_price(self):
        _game, market = stub_game()
        self.assertAlmostEqual(market.home_unit_price("silver_kg"), TILE_PRICE_PER_UNIT["silver_kg"])

    def test_the_coin_metal_follows_the_economys_price_when_it_moves(self):
        game, market = stub_game()
        before = market.home_unit_price("silver_kg")
        TILE_PRICE_PER_UNIT["silver_kg"] *= 0.5
        try:
            self.assertAlmostEqual(market.home_unit_price("silver_kg"), before * 0.5)
        finally:
            TILE_PRICE_PER_UNIT["silver_kg"] *= 2.0

    def test_a_metal_nothing_prices_has_no_coin_price(self):
        _game, market = stub_game()
        self.assertIsNone(market.home_unit_price("platinum_kg"))


if __name__ == "__main__":
    unittest.main()
