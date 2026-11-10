"""`year_tax_in_kind.reached_by` (the producers the state's tax in kind takes from, from the year's table) against the loop over every
producer's tile and recipe that `year_goods._tax_in_kind` made each time, on written-out and seeded random producers."""
QUICK_TOPIC = True

import random
import types
import unittest

from sim.economy import year_tax_in_kind
from sim.economy.home_scope import on_home_tile
from sim.economy.producer_blocks import recipes_of, tiles_of
from sim.economy.producer_store import ProducerStore
from sim.economy.producers import Producer

RECIPES = {"grow_wheat": ("wheat",), "grow_wine": ("wine",), "mill": ("flour", "bran"), "mine": ("iron",)}
TILES = {"town": "rome", "farms": "rome", "far": "gaul", "wild": "gaul"}


def setup_of(partners=True):
    countries = ("rome", "gaul") if partners else ("rome",)
    return types.SimpleNamespace(
        civ_id="rome", recipes={name: types.SimpleNamespace(outputs={good: 1.0 for good in goods}) for name, goods in RECIPES.items()},
        country_of=lambda tile: TILES.get(tile, "rome"), countries=lambda: countries)


def store_of(rows):
    return ProducerStore({producer_id: Producer(producer_id, "owner", recipe, tile, 1.0) for producer_id, recipe, tile in rows})


def plain_reached(setup, store, taxed, producer_ids):
    """The loop `_tax_in_kind` ran per call, as (producer id, tile, outputs)."""
    found = []
    producer_ids = list(producer_ids)
    for producer_id, tile, recipe_id in zip(producer_ids, tiles_of(store, producer_ids), recipes_of(store, producer_ids)):
        recipe = setup.recipes[recipe_id]
        if (taxed is not None and taxed.isdisjoint(recipe.outputs)) or not on_home_tile(setup, tile):
            continue
        found.append((producer_id, tile, tuple(recipe.outputs)))
    return found


class FormsTest(unittest.TestCase):
    def test_harvest_forms_tax_the_goods_they_are_paid_in(self):
        forms = [types.SimpleNamespace(basis="harvest", paid_in="wheat"), types.SimpleNamespace(basis="harvest", paid_in="wine")]
        self.assertEqual(year_tax_in_kind.taxed_goods(forms), {"wheat", "wine"})

    def test_a_form_of_another_basis_taxes_every_producer(self):
        forms = [types.SimpleNamespace(basis="harvest", paid_in="wheat"), types.SimpleNamespace(basis="head", paid_in="wine")]
        self.assertIsNone(year_tax_in_kind.taxed_goods(forms))


class ReachedByTest(unittest.TestCase):
    def test_written_out_producers_on_and_off_the_home_tiles(self):
        setup = setup_of()
        store = store_of([("p1", "grow_wheat", "town"), ("p2", "grow_wheat", "far"), ("p3", "mill", "farms"), ("p4", "grow_wine", "town")])
        table = year_tax_in_kind.home_outputs(setup, store, frozenset({"wheat", "flour"}))
        self.assertEqual(list(table), ["p1", "p3"])
        self.assertEqual(year_tax_in_kind.reached_by(setup, store, frozenset({"wheat", "flour"}), ["p4", "p3", "p2", "p1"], table),
                         [("p3", "farms", ("flour", "bran")), ("p1", "town", ("wheat",))])

    def test_one_country_reaches_every_tile(self):
        setup = setup_of(partners=False)
        store = store_of([("p1", "grow_wheat", "far")])
        table = year_tax_in_kind.home_outputs(setup, store, None)
        self.assertEqual(year_tax_in_kind.reached_by(setup, store, None, ["p1"], table), [("p1", "far", ("wheat",))])

    def test_the_table_agrees_with_the_loop_on_random_producers(self):
        rng = random.Random(7)
        for partners in (True, False):
            setup = setup_of(partners)
            for taxed in (None, frozenset({"wheat"}), frozenset({"bran", "iron"}), frozenset()):
                rows = [("p%02d" % number, rng.choice(sorted(RECIPES)), rng.choice(sorted(TILES))) for number in range(40)]
                rng.shuffle(rows)
                store = store_of(rows)
                table = year_tax_in_kind.home_outputs(setup, store, taxed)
                asked = [rng.choice(rows)[0] for _ in range(25)]
                expected = plain_reached(setup, store, taxed, asked)
                self.assertEqual(year_tax_in_kind.reached_by(setup, store, taxed, asked, table), expected)
                self.assertEqual(year_tax_in_kind.reached_by(setup, store, taxed, asked, None), expected)

    def test_a_producer_the_table_lacks_is_asked_of_the_store(self):
        setup = setup_of()
        store = store_of([("p1", "grow_wheat", "town")])
        table = year_tax_in_kind.home_outputs(setup, store, None)
        store["p2"] = Producer("p2", "owner", "mine", "farms", 1.0)
        self.assertEqual(year_tax_in_kind.reached_by(setup, store, None, ["p2", "p1"], table),
                         [("p2", "farms", ("iron",)), ("p1", "town", ("wheat",))])


if __name__ == "__main__":
    unittest.main()
