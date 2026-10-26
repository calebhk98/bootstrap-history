"""A civilisation that exists only in memory (Complaint 355) is priced and placed by its own fields, not by a file
with the same id."""

QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.engine import data
from sim.tests import prices_stand_in
from sim.geography.api import tiles_held


def priced_module(civ):
    """Only what the incumbents' price tables read."""
    granted = {"a"}
    module = prices_stand_in.build(civilisation=civ, techniques_granted=granted, techniques_in_use=frozenset(granted),
                                   farm_land_hectares=1000.0, money_per_labour_hour=2.0)
    module.banded_market_rate = lambda: 0.05
    return module


class PricedByItsOwnFields(unittest.TestCase):

    def test_the_solver_is_given_the_civilisation_dict_itself_even_when_a_file_shares_its_id(self):
        civ = {"id": "rome_100ad", "starting_interest_rate": 0.31}
        seen = []

        def table(held, **keywords):
            seen.append(keywords)
            return {"grain": 3.0}, {"grain": "solved"}

        with mock.patch.object(data, "calculated_goods_table", table):
            prices = priced_module(civ).material_prices()
        self.assertIs(seen[0]["civilization"], civ)
        self.assertEqual(seen[0]["civilization_id"], "rome_100ad")
        self.assertEqual(prices, {"grain": 6.0})


class TerritoryOfAVariant(unittest.TestCase):

    def test_a_variant_with_regions_and_no_tiles_holds_those_regions(self):
        variant = {"id": "variant_with_no_file", "home_regions": ["scandinavia"]}
        tiles = tiles_held(variant)
        self.assertTrue(tiles)
        self.assertEqual(tiles, tiles_held({"home_regions": ["scandinavia"]}))


if __name__ == "__main__":
    unittest.main()
