"""`households_store._store_weights` reads the offered and usual prices of a tile as blocks (`YearView.offered_prices_on`, `usual_prices_on`);
it gives what the good-by-good reads (`area_of`, `offered_price`, `usual_price`) gave, on the fixture economies with prices written to the
memory's usual column. No game."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import households_store
from sim.economy.market_memory import KEY_SEPARATOR
from sim.economy.store_return import service_values_per_year
from sim.economy.types import GoodSpec
from sim.tests.year_close_fixture import GOODS, TILES, economy_of

STORABLE = {good: GoodSpec(good, 0.05 + 0.1 * number, 0.0, 30.0, "x") for number, good in enumerate(GOODS) if number % 2 == 1}
OTHERS = {good: GoodSpec(good, 1.0, 0.2, 0.0, "x") for number, good in enumerate(GOODS) if number % 2 == 0}
SPECS = {**OTHERS, **STORABLE}
PRICED = [types.SimpleNamespace(spec=types.SimpleNamespace(subsistence_per_person=10.0, need_id="food"),
                                price_index=0.5, ceilings=(), goods=((GOODS[0], 0.5, 1.0, 1.0),))]


def per_good_weights(tile, view, specs, priced):
    """`_store_weights` as it was written: each storable good's area, offered price and usual price read one at a time."""
    staple = households_store.staple_price_per_kg(priced, specs)
    prices, usual_prices = {}, {}
    money_level = households_store._money_level(view, tile, specs)
    for good, spec in specs.items():
        if not households_store._can_be_stored(spec):
            continue
        area = view.area_of(good, tile)
        price = view.offered_price(good, area)
        if price:
            prices[good] = price
            usual = view.usual_price(good, area)
            if usual:
                usual_prices[good] = usual
    weights = households_store.store_candidates(specs, prices, staple, usual_prices, service_values_per_year(priced, specs), money_level=money_level)
    return weights, {good: prices[good] for good in weights}


class StorableGoods(unittest.TestCase):
    def test_the_storable_goods_are_those_that_can_be_stored_in_the_order_of_the_specs(self):
        self.assertEqual(households_store.storable_goods(SPECS), [good for good, spec in SPECS.items() if households_store._can_be_stored(spec)])
        self.assertEqual(households_store.storable_goods(SPECS), [good for good in SPECS if good in STORABLE])

    def test_weights_with_the_storable_goods_handed_in_equal_those_without(self):
        _setup, record, view, _ledger, _area_map = economy_of(0)
        for tile in TILES:
            self.assertEqual(households_store._store_weights(tile, view, SPECS, PRICED, households_store.storable_goods(SPECS)),
                             households_store._store_weights(tile, view, SPECS, PRICED))


class StoreOffersAreas(unittest.TestCase):
    def test_areas_handed_in_give_the_offers_the_view_asked_good_by_good_gives(self):
        cohort = types.SimpleNamespace(agent_id="household:a", tile="t0", expected_inflation=0.01)
        view = types.SimpleNamespace(area_of=lambda good, tile: "area_" + good, currency_of=lambda area: "coin", interest_rate=lambda currency: 0.05,
                                     opening_wage_level=lambda currency: 1.0)
        specs = {"gold": GoodSpec("gold", 0.0, 0.0, 30.0, "x"), "silver": GoodSpec("silver", 0.0, 0.0, 30.0, "x")}
        weights, prices, held = {"gold": 0.5, "silver": 0.5}, {"gold": 100.0, "silver": 20.0}, {"gold": 3.0, "silver": 40.0}
        asked = households_store.store_offers(cohort, view, specs, weights, prices, held, 100.0, 0.02, 5.0, 400.0)
        given = households_store.store_offers(cohort, view, specs, weights, prices, held, 100.0, 0.02, 5.0, 400.0,
                                              {"gold": "area_gold", "silver": "area_silver"})
        self.assertTrue(asked)
        self.assertEqual(given, asked)

    def test_nothing_held_offers_nothing_and_asks_for_no_area(self):
        cohort = types.SimpleNamespace(agent_id="household:a", tile="t0", expected_inflation=0.01)
        view = types.SimpleNamespace(area_of=lambda good, tile: 1 / 0)
        self.assertEqual(households_store.store_offers(cohort, view, {}, {"gold": 1.0}, {"gold": 100.0}, {"gold": 0.0}, 100.0, 0.02, 5.0, 400.0), [])


class StoreWeightsOnBlocks(unittest.TestCase):
    def test_weights_and_prices_equal_the_good_by_good_read(self):
        found = 0
        for seed in range(8):
            _setup, record, view, _ledger, area_map = economy_of(seed)
            for number, good in enumerate(GOODS):
                for tile in TILES:
                    key = good + KEY_SEPARATOR + area_map.area_of(good, tile)
                    record.memory.prices[key] = 40.0 + 7.0 * number           # dear per kg against the staple, so the goods qualify
                    record.memory.note_trading([key])
                    if number % 3 != 0:
                        record.memory.usual_prices[key] = 30.0 + 11.0 * number
            for tile in TILES:
                got = households_store._store_weights(tile, view, SPECS, PRICED)
                expected = per_good_weights(tile, view, SPECS, PRICED)
                self.assertEqual(got, expected)
                found += len(got[0])
        self.assertGreater(found, 8, "the weights are exercised")

    def test_a_tile_the_area_map_does_not_hold_is_read_good_by_good(self):
        _setup, _record, view, _ledger, _area_map = economy_of(2)
        self.assertEqual(households_store._store_weights("nowhere", view, SPECS, PRICED), per_good_weights("nowhere", view, SPECS, PRICED))


if __name__ == "__main__":
    unittest.main()
