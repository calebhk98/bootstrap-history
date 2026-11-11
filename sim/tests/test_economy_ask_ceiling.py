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

    def test_without_an_alternative_the_stated_multiple_stands_in_for_inelastic_demand(self):
        self.assertEqual(band_multiple(1.0, ask_ceiling.NO_ALTERNATIVES, None), ask_adjust.ASK_BAND_CEILING)

    def test_without_an_alternative_the_markup_is_kept_inside_the_stated_multiple(self):
        self.assertEqual(band_multiple(1.2, ask_ceiling.NO_ALTERNATIVES, None), ask_adjust.ASK_BAND_CEILING)
        self.assertAlmostEqual(band_multiple(3.0, ask_ceiling.NO_ALTERNATIVES, None), 1.5)

    def test_a_ceiling_with_no_cost_to_scale_against_falls_back_to_the_stand_in(self):
        self.assertEqual(band_multiple(1.0, AskCeiling(2.0, None), None), ask_adjust.ASK_BAND_CEILING)


class AskAlternativesTests(unittest.TestCase):
    def alternatives(self, prices, costs):
        setup = types.SimpleNamespace(basket_for=lambda tile: types.SimpleNamespace(substitution=1.0, needs=(HEAT,)))
        found = ask_ceiling.AskAlternatives(setup, None)
        found._prices, found._costs = prices, costs      # the year's national prices and making costs, written out
        return found

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
    def asked(self, alternatives):
        recipe = Recipe("burn", {GOOD: 1.0}, {"wood_kg": 2.0}, {"labour": 4.0})
        producer = Producer(SELLER, "lord", "burn", TILE, 10.0)
        setup = types.SimpleNamespace(specs={}, currency_id="coin", recipes={"burn": recipe},
                                      basket_for=lambda tile: types.SimpleNamespace(substitution=1.0, needs=(HEAT,)))
        record = types.SimpleNamespace(producers={SELLER: producer},
                                       memory=types.SimpleNamespace(volume_weights={GOOD + "|" + AREA: 100.0}),
                                       goods=types.SimpleNamespace(unmet={}))
        buyer = Bid("buyer", GOOD, AREA, TILE, 0.0, 200.0, 10.0, 1.0, 2000.0)      # a sum to spend whatever the price
        costs = seller_offers.UnitCosts(alternatives)
        chosen = seller_offers.strategic_offers(setup, record, View(), [buyer], [Offer(SELLER, GOOD, AREA, TILE, 1000.0, 0.97 * 1.5 * RUN_COST_PER_UNIT)],
                                                10.0, costs)
        return chosen[0].reservation_price

    def test_a_charcoal_seller_facing_inelastic_demand_is_held_to_the_wood_its_buyers_can_burn(self):
        # wood at 0.5 gives one unit of heat, charcoal two: parity is 1.0, about 0.67 of what a unit costs to make, so no markup
        alternatives = ask_ceiling.AskAlternatives(None, None)
        alternatives.multiple = lambda good, tile: ask_ceiling.band_multiple(1.0, AskCeiling(1.5 * RUN_COST_PER_UNIT, None), RUN_COST_PER_UNIT)
        self.assertLessEqual(self.asked(alternatives), 1.5 * RUN_COST_PER_UNIT * (1.0 + 1e-9))

    def test_without_the_years_alternatives_the_stated_multiple_is_the_bound(self):
        self.assertLessEqual(self.asked(None), ask_adjust.ASK_BAND_CEILING * RUN_COST_PER_UNIT * (1.0 + 1e-9))


if __name__ == "__main__":
    unittest.main()
