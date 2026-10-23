"""A civilisation that exists only in memory (Complaint 355) is priced and placed by its own fields, not by a file
with the same id."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import data
from sim.engine.incumbent_prices import IncumbentPricesMixin
from sim.geography.api import regions_of_tiles, tiles_held


class PricedGame(IncumbentPricesMixin):
    """Only what the incumbents' price tables read."""

    def __init__(self, civ):
        self.civ = civ
        self.state = types.SimpleNamespace(projects=types.SimpleNamespace(granted={"a"}, done={"a"}))
        self.farm_land = types.SimpleNamespace(hectares=1000.0)
        self.labour = types.SimpleNamespace(money_per_labour_hour=lambda: 2.0)

    def techniques_in_use(self):
        return frozenset(self.state.projects.granted)

    def _banded_market_rate(self):
        return 0.05


class PricedByItsOwnFields(unittest.TestCase):

    def test_the_solver_is_given_the_civilisation_dict_itself_even_when_a_file_shares_its_id(self):
        civ = {"id": "rome_100ad", "starting_interest_rate": 0.31}
        seen = []

        def table(held, **keywords):
            seen.append(keywords)
            return {"grain": 3.0}, {"grain": "solved"}

        with mock.patch.object(data, "calculated_goods_table", table):
            prices = PricedGame(civ)._material_prices()
        self.assertIs(seen[0]["civilization"], civ)
        self.assertEqual(seen[0]["civilization_id"], "rome_100ad")
        self.assertEqual(prices, {"grain": 6.0})


class TerritoryOfAVariant(unittest.TestCase):

    def test_a_variant_with_regions_and_no_tiles_holds_those_regions(self):
        variant = {"id": "variant_with_no_file", "home_regions": ["scandinavia"]}
        self.assertEqual(regions_of_tiles(tiles_held(variant)), ["scandinavia"])


if __name__ == "__main__":
    unittest.main()
