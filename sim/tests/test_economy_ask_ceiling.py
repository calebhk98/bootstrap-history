"""Complaint 643: a seller's ask is bounded by what its buyers' cheapest alternative way to meet the same need costs them
(another good of the need, bought or made from its recipe), not by a stated multiple, wherever such an alternative exists.
Written-out inputs shaped like the complaint's cases: charcoal, whose buyers can burn wood made at a low cost, and raw glass,
whose buyers can use ceramic."""
QUICK_TOPIC = True

import types
import unittest

from sim.economy import ask_adjust, ask_ceiling, seller_offers
from sim.economy.ask_ceiling import AskCeiling, alternative_ceiling, band_multiple
from sim.economy.producers import Producer
from sim.economy.types import Bid, Offer, Recipe
from sim.tests.economy_view_defaults import ViewDefaults
from sim.world.need_basket import NeedSpec

# a unit of heat from charcoal is worth two from wood
HEAT = NeedSpec("heat", 1.0, 1.0, (("charcoal_kg", 2.0), ("wood_kg", 1.0), ("coal_kg", 1.5)))
VESSEL = NeedSpec("vessels", 1.0, 1.0, (("glass_raw_kg", 1.0), ("ceramic_kg", 1.0)))
LONE = NeedSpec("light", 1.0, 1.0, (("lamp_oil_l", 1.0),))


class AlternativeCeilingTests(unittest.TestCase):
    def test_a_seller_of_a_good_with_a_cheaper_substitute_is_bounded_by_the_substitute_per_need_unit(self):
        # wood costs 0.5 for one unit of heat, coal 2.0 for 1.5 units (1.33 a unit): charcoal gives two units, so parity is 1.0
        ceiling = alternative_ceiling("charcoal_kg", [HEAT], {"wood_kg": 0.5, "coal_kg": 2.0}.get, {}.get)
        self.assertEqual(ceiling, AskCeiling(1.0, None))

    def test_a_substitute_the_buyer_can_make_cheaper_than_it_is_sold_sets_the_ceiling(self):
        ceiling = alternative_ceiling("charcoal_kg", [HEAT], {"wood_kg": 0.5, "coal_kg": 2.0}.get, {"wood_kg": 0.1}.get)
        self.assertAlmostEqual(ceiling.price, 0.2)

    def test_raw_glass_is_bounded_by_ceramic_not_by_a_multiple_of_its_own_cost(self):
        ceiling = alternative_ceiling("glass_raw_kg", [VESSEL], {"ceramic_kg": 1.5}.get, {"ceramic_kg": 1.2}.get)
        self.assertAlmostEqual(ceiling.price, 1.2)

    def test_the_good_itself_is_not_its_own_alternative(self):
        ceiling = alternative_ceiling("charcoal_kg", [HEAT], {"charcoal_kg": 0.01}.get, {"charcoal_kg": 0.01}.get)
        self.assertEqual(ceiling.cause, ask_ceiling.CAUSE_NO_ALTERNATIVE)

    def test_a_good_alone_in_its_need_has_no_ceiling_and_says_why(self):
        ceiling = alternative_ceiling("lamp_oil_l", [LONE], {"wood_kg": 0.5}.get, {}.get)
        self.assertEqual(ceiling, AskCeiling(None, ask_ceiling.CAUSE_NO_ALTERNATIVE))

    def test_an_intermediate_good_that_meets_no_need_says_so(self):
        self.assertEqual(alternative_ceiling("ore_kg", [HEAT], {}.get, {}.get), AskCeiling(None, ask_ceiling.CAUSE_NO_NEED))

    def test_a_good_in_two_needs_is_unbounded_if_either_has_no_alternative(self):
        light = NeedSpec("light", 1.0, 1.0, (("charcoal_kg", 1.0),))
        ceiling = alternative_ceiling("charcoal_kg", [HEAT, light], {"wood_kg": 0.5}.get, {}.get)
        self.assertIsNone(ceiling.price)

    def test_a_good_in_two_needs_takes_the_higher_ceiling(self):
        fuel = NeedSpec("fuel", 1.0, 1.0, (("charcoal_kg", 1.0), ("peat_kg", 1.0)))
        ceiling = alternative_ceiling("charcoal_kg", [HEAT, fuel], {"wood_kg": 0.5, "peat_kg": 0.9}.get, {}.get)
        self.assertAlmostEqual(ceiling.price, 1.0)      # heat: 0.5 * 2 = 1.0; fuel: 0.9 * 1 = 0.9

    def test_unpriceable_alternatives_are_skipped(self):
        ceiling = alternative_ceiling("charcoal_kg", [HEAT], {"wood_kg": 0.0, "coal_kg": float("inf")}.get, {}.get)
        self.assertIsNone(ceiling.price)


class BandMultipleTests(unittest.TestCase):
    def test_the_multiple_is_the_ceiling_over_the_sellers_cost(self):
        self.assertAlmostEqual(band_multiple(1.0, AskCeiling(1.5, None), 1.0), 1.5)

    def test_the_multiple_is_never_below_break_even(self):
        self.assertEqual(band_multiple(1.0, AskCeiling(0.4, None), 1.0), 1.0)

    def test_a_substitute_dearer_than_the_stated_multiple_still_bounds_it_at_the_substitute(self):
        self.assertAlmostEqual(band_multiple(1.0, AskCeiling(10.0, None), 1.0), 10.0)

    def test_the_tighter_of_the_substitution_markup_and_the_ceiling_applies(self):
        self.assertAlmostEqual(band_multiple(2.0, AskCeiling(5.0, None), 1.0), 2.0)      # markup 2 / (2 - 1)
        self.assertAlmostEqual(band_multiple(2.0, AskCeiling(1.3, None), 1.0), 1.3)

    def test_with_no_ceiling_and_no_substitution_the_seller_has_no_room_above_cost(self):
        self.assertEqual(band_multiple(1.0, ask_ceiling.NO_CEILING, None), ask_adjust.NO_BOUND_MULTIPLE)

    def test_with_no_ceiling_the_derived_markup_stands(self):
        self.assertAlmostEqual(band_multiple(3.0, ask_ceiling.NO_CEILING, None), 1.5)

    def test_a_ceiling_with_no_cost_to_scale_against_leaves_no_room_without_a_markup(self):
        self.assertEqual(band_multiple(1.0, AskCeiling(2.0, None), None), ask_adjust.NO_BOUND_MULTIPLE)


INF = float("inf")
WAGES = {"labour": 0.5}
# a smith makes a tool from ore and two hours; a second recipe makes the same tool from scrap with no ore
SMITH = Recipe("smith", {"tool": 1.0}, {"ore": 2.0}, {"labour": 2.0})
SCRAP = Recipe("scrap", {"tool": 1.0}, {"scrap": 1.0}, {"labour": 2.0})


class BuyerLimitTests(unittest.TestCase):
    def test_the_limit_is_the_budget_over_the_floor_units_of_the_best_funded_bid(self):
        self.assertEqual(ask_ceiling.buyer_limit([10.0, 5.0], [0.0, 0.0], [50.0, 100.0], [INF, INF]), 20.0)

    def test_a_bids_own_maximum_price_holds_its_limit_down(self):
        self.assertEqual(ask_ceiling.buyer_limit([10.0], [0.0], [1000.0], [7.0]), 7.0)

    def test_a_bid_with_no_floor_is_read_at_what_it_asks_for(self):
        self.assertEqual(ask_ceiling.buyer_limit([0.0], [4.0], [20.0], [INF]), 5.0)

    def test_bids_with_no_budget_or_nothing_wanted_take_none(self):
        self.assertIsNone(ask_ceiling.buyer_limit([10.0, 0.0], [0.0, 0.0], [0.0, 50.0], [INF, INF]))

    def test_no_bids_give_none(self):
        self.assertIsNone(ask_ceiling.buyer_limit([], [], [], []))


class RecipeCeilingTests(unittest.TestCase):
    def test_a_maker_with_another_recipe_pays_up_to_where_the_other_is_cheaper(self):
        # scrap route: 4 + 2 hours * 0.5 = 5 a tool; ore route at price p: 2p + 1; they meet at p = 2
        ceiling = ask_ceiling.recipe_ceiling("ore", SMITH, [SMITH, SCRAP], {"tool": 20.0, "scrap": 4.0}, WAGES, 0.0)
        self.assertAlmostEqual(ceiling, 2.0)

    def test_a_maker_with_no_other_recipe_pays_up_to_its_break_even(self):
        # revenue 20, labour 1: the run breaks even when two ore cost 19
        ceiling = ask_ceiling.recipe_ceiling("ore", SMITH, [SMITH], {"tool": 20.0}, WAGES, 0.0)
        self.assertAlmostEqual(ceiling, 9.5)

    def test_the_switch_never_lifts_the_ceiling_past_break_even(self):
        # the other route is dear (90 a tool) but the tool sells for 20, so the run's break-even binds
        ceiling = ask_ceiling.recipe_ceiling("ore", SMITH, [SMITH, SCRAP], {"tool": 20.0, "scrap": 89.0}, WAGES, 0.0)
        self.assertAlmostEqual(ceiling, 9.5)

    def test_a_recipe_that_loses_money_even_with_the_input_free_gives_no_ceiling(self):
        self.assertIsNone(ask_ceiling.recipe_ceiling("ore", SMITH, [SMITH], {"tool": 0.5}, WAGES, 0.0))

    def test_a_recipe_that_cannot_be_priced_gives_no_ceiling(self):
        self.assertIsNone(ask_ceiling.recipe_ceiling("ore", SMITH, [SMITH], {}, WAGES, 0.0))

    def test_a_recipe_not_using_the_good_gives_no_ceiling(self):
        self.assertIsNone(ask_ceiling.recipe_ceiling("ore", SCRAP, [SCRAP], {"tool": 20.0, "scrap": 4.0}, WAGES, 0.0))

    def test_the_main_output_is_the_most_valuable_one(self):
        joint = Recipe("joint", {"meat": 1.0, "bone": 1.0}, {"cattle": 1.0}, {})
        self.assertEqual(ask_ceiling.main_output(joint, {"meat": 5.0, "bone": 1.0}), "meat")


class BuyerLimitRecordTests(unittest.TestCase):
    def test_a_limit_is_kept_and_a_year_without_one_forgets_it(self):
        from sim.economy.goods_record import GoodsRecord
        record = GoodsRecord()
        record.note_buyer_limit("lamp_oil_l", 4.0)
        self.assertEqual(record.buyer_limits, {"lamp_oil_l": 4.0})
        record.note_buyer_limit("lamp_oil_l", None)
        self.assertEqual(record.buyer_limits, {})


class GoodCeilingTests(unittest.TestCase):
    def test_the_highest_leg_is_the_ceiling(self):
        self.assertEqual(ask_ceiling.good_ceiling(AskCeiling(3.0, None), None, [2.0, None, 4.0]), AskCeiling(4.0, None))

    def test_a_good_alone_in_its_need_is_bounded_by_the_households_budget(self):
        household = AskCeiling(None, ask_ceiling.CAUSE_NO_ALTERNATIVE)
        self.assertEqual(ask_ceiling.good_ceiling(household, 12.0, []), AskCeiling(12.0, None))

    def test_a_good_in_no_need_is_bounded_by_the_recipes_that_use_it(self):
        household = AskCeiling(None, ask_ceiling.CAUSE_NO_NEED)
        self.assertEqual(ask_ceiling.good_ceiling(household, 12.0, [6.0]), AskCeiling(6.0, None))

    def test_a_good_with_no_buyer_that_bounds_it_says_so(self):
        household = AskCeiling(None, ask_ceiling.CAUSE_NO_NEED)
        self.assertEqual(ask_ceiling.good_ceiling(household, None, [None]), AskCeiling(None, ask_ceiling.CAUSE_NO_BUYER))


class AskAlternativesTests(unittest.TestCase):
    def alternatives(self, prices, costs, needs=(HEAT,), recipes=(), limits=None):
        setup = types.SimpleNamespace(basket_for=lambda tile: types.SimpleNamespace(substitution=1.0, needs=needs),
                                      recipes={each.recipe_id: each for each in recipes})
        found = ask_ceiling.AskAlternatives(setup, types.SimpleNamespace(goods=types.SimpleNamespace(buyer_limits=limits or {})))
        found._prices, found._costs, found._wages, found._rate = prices, costs, WAGES, 0.0      # the year's figures, written out
        return found

    def test_a_good_alone_in_its_need_is_bounded_by_the_households_budget(self):
        found = self.alternatives({}, {"lamp_oil_l": 1.0}, needs=(LONE,), limits={"lamp_oil_l": 4.0})
        self.assertAlmostEqual(found.multiple("lamp_oil_l", "tile"), 4.0)

    def test_an_intermediate_good_is_bounded_by_its_makers_next_best_recipe(self):
        found = self.alternatives({"tool": 20.0, "scrap": 4.0}, {"ore": 1.0}, needs=(), recipes=(SMITH, SCRAP))
        self.assertAlmostEqual(found.multiple("ore", "tile"), 2.0)

    def test_an_intermediate_good_whose_makers_have_no_other_recipe_is_bounded_by_their_break_even(self):
        found = self.alternatives({"tool": 20.0}, {"ore": 1.0}, needs=(), recipes=(SMITH,))
        self.assertAlmostEqual(found.multiple("ore", "tile"), 9.5)

    def test_a_good_nobody_buys_has_no_room_above_cost(self):
        found = self.alternatives({}, {"dust": 1.0}, needs=(), recipes=())
        self.assertEqual(found.multiple("dust", "tile"), ask_adjust.NO_BOUND_MULTIPLE)

    def test_charcoal_whose_buyers_can_burn_cheap_wood_is_bounded_by_the_wood(self):
        found = self.alternatives({"wood_kg": 0.5}, {"charcoal_kg": 0.4})
        self.assertAlmostEqual(found.multiple("charcoal_kg", "tile"), 1.0 / 0.4)

    def test_a_good_dearer_to_make_than_its_substitute_is_sold_at_no_markup(self):
        found = self.alternatives({"wood_kg": 0.5}, {"charcoal_kg": 2.0})
        self.assertEqual(found.multiple("charcoal_kg", "tile"), 1.0)


GOOD, AREA, TILE, SELLER = "charcoal_kg", "area", "tile", "producer:charcoal"
RUN_COST_PER_UNIT = 2.0 * 0.5 + 4.0 * 0.5          # two of wood at half, four hours at half


class View(ViewDefaults):
    def interest_rate(self, currency):
        return 0.0

    def currency_of(self, area):
        return "coin"

    year = 3

    def price(self, good, area):
        return {"wood_kg": 0.5}.get(good)

    def wage(self, trade, area):
        return 0.5

    def area_of(self, good, tile):
        return AREA

    def stock(self, agent, good, tile):
        return 0.0


class SellerAskTests(unittest.TestCase):
    def asked(self, alternatives, start=0.97 * 1.5 * RUN_COST_PER_UNIT):
        recipe = Recipe("burn", {GOOD: 1.0}, {"wood_kg": 2.0}, {"labour": 4.0})
        producer = Producer(SELLER, "lord", "burn", TILE, 10.0)
        setup = types.SimpleNamespace(specs={}, currency_id="coin", recipes={"burn": recipe},
                                      basket_for=lambda tile: types.SimpleNamespace(substitution=1.0, needs=(HEAT,)))
        record = types.SimpleNamespace(producers={SELLER: producer},
                                       memory=types.SimpleNamespace(volume_weights={GOOD + "|" + AREA: 100.0}),
                                       goods=types.SimpleNamespace(unmet={}))
        buyer = Bid("buyer", GOOD, AREA, TILE, 0.0, 200.0, 10.0, 1.0, 2000.0)      # a sum to spend whatever the price
        costs = seller_offers.UnitCosts(alternatives)
        chosen = seller_offers.strategic_offers(setup, record, View(), [buyer], [Offer(SELLER, GOOD, AREA, TILE, 1000.0, start)],
                                                10.0, costs)
        return chosen[0].reservation_price

    def test_a_charcoal_seller_facing_inelastic_demand_is_held_to_the_wood_its_buyers_can_burn(self):
        # wood at 0.5 gives one unit of heat, charcoal two: parity is 1.0, about 0.67 of what a unit costs to make, so no markup
        alternatives = types.SimpleNamespace()
        alternatives.multiple = lambda good, tile: ask_ceiling.band_multiple(1.0, AskCeiling(1.5 * RUN_COST_PER_UNIT, None), RUN_COST_PER_UNIT)
        self.assertLessEqual(self.asked(alternatives), 1.5 * RUN_COST_PER_UNIT * (1.0 + 1e-9))

    def test_without_the_years_alternatives_a_seller_with_no_markup_derived_asks_no_more_than_cost(self):
        self.assertLessEqual(self.asked(None, start=RUN_COST_PER_UNIT), RUN_COST_PER_UNIT * (1.0 + 1e-9))


if __name__ == "__main__":
    unittest.main()
