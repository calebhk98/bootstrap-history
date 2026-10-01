"""The wage floor comes from the solved cost of food in labour hours, and
money is anchored to the civilisation's coin, not to a book price."""
import copy
import json
import os
import unittest

from sim.engine import catalog, data, prices as engine_prices, wage_provider
from sim.validate_production import load_production

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CIVILISATIONS = ["rome_100ad", "han_china_100ad", "england_1300",
                 "norse_900ad", "mexica_1500"]


def _registry():
    return catalog.load_trade_registry(ROOT)


def _schedule(civ, production_entries=None):
    return wage_provider.build_schedule(_registry(), civ, production_entries=production_entries)


def _entries():
    entries, _duplicates = load_production()
    return copy.deepcopy(entries)


class WageFloorFollowsSolvedFoodTests(unittest.TestCase):

    def test_worse_land_raises_the_floor(self):
        civ = data.load_civ("rome_100ad")
        normal = _schedule(civ)
        entries = _entries()
        entries["wheat_kg"]["land_hectare_years"] *= 3.0
        worse = _schedule(civ, entries)
        self.assertGreater(worse.subsistence_hours_per_hour,
                           normal.subsistence_hours_per_hour)
        self.assertGreater(worse.floor_per_hour, normal.floor_per_hour)

    def test_more_labour_per_harvest_raises_the_floor(self):
        civ = data.load_civ("rome_100ad")
        entries = _entries()
        entries["wheat_kg"]["labour_hours"]["labourer"] *= 2.0
        self.assertGreater(_schedule(civ, entries).floor_per_hour,
                           _schedule(civ).floor_per_hour)

    def test_floor_is_the_solved_basket_in_hours_times_the_money_per_hour(self):
        schedule = _schedule(data.load_civ("rome_100ad"))
        self.assertAlmostEqual(
            schedule.floor_per_hour,
            schedule.subsistence_hours_per_hour * schedule.money_per_labour_hour)
        self.assertGreater(schedule.subsistence_hours_per_hour, 0.0)

    def test_no_wage_falls_below_the_floor(self):
        schedule = _schedule(data.load_civ("rome_100ad"))
        for trade in schedule.trades():
            self.assertGreaterEqual(schedule.wage_per_hour(trade), schedule.floor_per_hour)

    def test_a_floor_above_the_market_wage_lifts_the_labourer_wage(self):
        civ = data.load_civ("rome_100ad")
        entries = _entries()
        entries["wheat_kg"]["land_hectare_years"] *= 400.0
        schedule = _schedule(civ, entries)
        self.assertGreater(schedule.subsistence_hours_per_hour, 1.0)
        self.assertAlmostEqual(schedule.wage_per_hour("labourer"), schedule.floor_per_hour)


class CoinStandardMoneyTests(unittest.TestCase):

    def test_more_silver_per_coin_lowers_the_money_per_labour_hour(self):
        civ = data.load_civ("rome_100ad")
        heavier = copy.deepcopy(civ)
        heavier["coin_standard"]["kg_per_unit"] *= 2.0
        base = _schedule(civ)
        other = _schedule(heavier)
        self.assertAlmostEqual(other.money_per_labour_hour * 2.0, base.money_per_labour_hour)

    def test_hours_and_the_basket_in_hours_do_not_depend_on_the_coin(self):
        civ = data.load_civ("rome_100ad")
        heavier = copy.deepcopy(civ)
        heavier["coin_standard"]["kg_per_unit"] *= 2.0
        self.assertAlmostEqual(_schedule(civ).subsistence_hours_per_hour,
                               _schedule(heavier).subsistence_hours_per_hour)

    def test_a_display_name_or_price_index_does_not_change_the_conversion(self):
        civ = data.load_civ("rome_100ad")
        renamed = copy.deepcopy(civ)
        renamed["currency"] = "something else"
        renamed["price_index"] = 3.0
        self.assertEqual(_schedule(civ).money_per_labour_hour,
                         _schedule(renamed).money_per_labour_hour)

    def test_money_is_hours_over_the_coin_in_labour_hours(self):
        civ = data.load_civ("rome_100ad")
        standard = wage_provider.coin_standard(civ)
        solved = engine_prices.solved_prices(
            civ["starting_techs"], _schedule(civ).ratio_document(), civilization_id="rome_100ad")
        coin_hours = standard["kg_per_unit"] * solved.prices_in_labour_hours[standard["material"]]
        schedule = _schedule(civ)
        self.assertAlmostEqual(schedule.money_per_labour_hour, 1.0 / coin_hours)
        document = schedule.document()
        self.assertAlmostEqual(engine_prices.hours_to_denarii(2.5, document),
                               2.5 / coin_hours)

    def test_solved_prices_in_money_move_with_the_coin(self):
        civ = data.load_civ("rome_100ad")
        light = copy.deepcopy(civ)
        light["coin_standard"]["kg_per_unit"] /= 2.0
        held = civ["starting_techs"]
        table_civ, _p = engine_prices.priced_goods_table(
            held, _schedule(civ).document(), civilization_id="rome_100ad")
        table_light, _p = engine_prices.priced_goods_table(
            held, _schedule(light).document(), civilization_id="rome_100ad")
        self.assertAlmostEqual(table_light["wheat_kg"], 2.0 * table_civ["wheat_kg"])


class CoinStandardDataTests(unittest.TestCase):

    def test_every_civilisation_declares_a_sourced_coin_standard(self):
        for name in CIVILISATIONS + ["sample_egypt_100bc_e7k2:egypt"]:
            civ = data.load_civ(name)
            standard = civ["coin_standard"]
            self.assertGreater(standard["kg_per_unit"], 0.0, name)
            self.assertTrue(standard["material"].endswith("_kg"), name)
            self.assertTrue(standard["source"].strip(), name)

    def test_every_standard_can_be_priced_with_the_civilisations_technology(self):
        for name in CIVILISATIONS:
            schedule = _schedule(data.load_civ(name))
            self.assertGreater(schedule.money_per_labour_hour, 0.0, name)

    def test_a_missing_standard_is_a_clear_load_error(self):
        with tempfile_civ("rome_100ad", drop="coin_standard") as name:
            with self.assertRaises(ValueError) as caught:
                data.load_civ(name)
        self.assertIn("coin_standard", str(caught.exception))

    def test_a_standard_with_no_source_is_a_clear_load_error(self):
        with tempfile_civ("rome_100ad", source="") as name:
            with self.assertRaises(ValueError) as caught:
                data.load_civ(name)
        self.assertIn("source", str(caught.exception))

    def test_a_standard_that_cannot_be_priced_fails_clearly(self):
        civ = copy.deepcopy(data.load_civ("rome_100ad"))
        civ["coin_standard"]["material"] = "plutonium_kg"
        with self.assertRaises(ValueError) as caught:
            _schedule(civ)
        self.assertIn("plutonium_kg", str(caught.exception))


class tempfile_civ(object):
    """Points load_civ at a temporary civilisation directory holding one civ."""

    def __init__(self, base_name, drop=None, source=None):
        self.base_name, self.drop, self.source = base_name, drop, source

    def __enter__(self):
        import tempfile
        from unittest import mock
        self.directory = tempfile.TemporaryDirectory()
        civ = copy.deepcopy(data.load_civ(self.base_name))
        if self.drop:
            civ.pop(self.drop)
        if self.source is not None:
            civ["coin_standard"]["source"] = self.source
        with open(os.path.join(self.directory.name, self.base_name + ".json"), "w") as handle:
            json.dump(civ, handle)
        self.patch = mock.patch.object(data, "CIVDIR", self.directory.name)
        self.patch.start()
        return self.base_name

    def __exit__(self, *_exception):
        self.patch.stop()
        self.directory.cleanup()


class OpeningCapitalTests(unittest.TestCase):

    def _sim(self, civ_name, kit):
        import random
        from sim.tests import harness
        from sim.engine.core import Sim
        return Sim(harness.NODES, harness.ORDER, random.Random(1), events=False, manual=True,
                   civ=data.load_civ(civ_name), cfg={"start_kit": kit})

    def test_a_kit_is_labourer_years_of_the_opening_wage(self):
        civ = data.load_civ("rome_100ad")
        expected = (data.STARTING_KITS["merchant"]["labourer_years"]
                    * _schedule(civ).annual_wage("labourer"))
        self.assertAlmostEqual(data.kit_capital("merchant", civ), expected)

    def test_kit_money_follows_the_coin(self):
        civ = data.load_civ("rome_100ad")
        heavier = copy.deepcopy(civ)
        heavier["coin_standard"]["kg_per_unit"] *= 2.0
        self.assertAlmostEqual(data.kit_capital("artisan", heavier) * 2.0,
                               data.kit_capital("artisan", civ))

    def test_every_funded_kit_affords_a_skilled_hire_for_a_year(self):
        for civ_name in CIVILISATIONS + ["sample_egypt_100bc_e7k2:egypt"]:
            for kit, kit_data in data.STARTING_KITS.items():
                if kit_data["labourer_years"] <= 0.0:
                    continue
                engine = self._sim(civ_name, kit)
                self.assertGreaterEqual(
                    engine.household.capital, engine.annual_wage("smith"), (civ_name, kit))


class NoBookFoodTests(unittest.TestCase):

    def test_the_book_food_reader_is_gone(self):
        self.assertFalse(hasattr(data, "_book_food_price_per_kg"))
        self.assertFalse(hasattr(data, "FOOD_PRICE_PER_KG"))


if __name__ == "__main__":
    unittest.main()
