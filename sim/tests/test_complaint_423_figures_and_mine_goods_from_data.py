"""Complaint 423: a mod adds a `figures` entry by data (data/ui/figures.json), and the goods a mine supplies come from
the resource catalogue, so neither needs an engine or UI edit. The figure registry reads state paths off any object, so
it is called here on a stand-in for the game; the catalogue is the real map's."""
QUICK_TOPIC = True

import json
import os
import tempfile
import unittest
from types import SimpleNamespace

from sim.tests import resources_stand_in
from sim.content.api import ModError
from sim.geography.api import open_map
from sim.ui import figures as figure_registry
from sim.ui import figures_data
from sim.ui.proto import dispatch_figures
from sim.tests.interface_fixture import declared_for, shipped_declared
from sim.tests.ui_stand_in import Game, ui_state

MOD_ID = "tester_figs_k3f9"
OLD_DEMAND_KEYS = {"coal": ("coal_kg",), "iron": ("iron_bar_kg", "iron_ore_kg"),
                   "copper": ("copper_kg", "copper_wire_kg", "wire_drawn_kg"), "lead": ("lead_kg",),
                   "tin": ("tin_kg",), "silver": ("silver_kg",), "gold": ("gold_kg",)}


def write_mod(mods_dir, figures):
    folder = os.path.join(mods_dir, MOD_ID)
    os.makedirs(os.path.join(folder, "data", "ui"))
    with open(os.path.join(folder, "mod.json"), "w", encoding="utf-8") as handle:
        json.dump({"id": MOD_ID, "name": "Figures", "version": "1.0.0", "dependencies": [], "conflicts": []}, handle)
    with open(os.path.join(folder, "data", "ui", "figures.json"), "w", encoding="utf-8") as handle:
        json.dump({"figures": figures}, handle)


def game(declared=None):
    """What the declared figures read: the population, the price level and the household's cash."""
    return Game(interface_declared=declared, population=Game(total=1000.4, children=300.0, working_age=600.0, elderly=100.4),
                           price_index=1.25, year=100, wage_index=1.5,
                           state=Game(household=Game(capital=4321.5), **vars(ui_state())))


class FigureTests(unittest.TestCase):
    def test_the_base_figures_declared_as_data_are_registered(self):
        self.assertTrue({"income", "population"} <= set(shipped_declared().figures))
        self.assertFalse({"income", "population"} & set(figure_registry.FIGURES))   # the shipped table holds code figures only

    def test_a_declared_figure_reads_its_state_paths(self):
        population = figure_registry.read_figure(game(shipped_declared()), "population")
        self.assertEqual(population["value"], 1000)
        self.assertEqual(set(population["components"]), {"children", "working age", "elderly"})

    def test_a_mods_figure_shows_in_the_listing_and_reads_the_game_and_its_drivers(self):
        figure_id = MOD_ID + ":capital_in_hand"
        with tempfile.TemporaryDirectory() as mods_dir:
            write_mod(mods_dir, {figure_id: {"label": "cash again", "unit": "money", "value": "state.household.capital",
                                             "drivers": {"price level": "price_index"}}})
            declared = declared_for(mods_dir)
            self.assertIn(figure_id, {row["name"] for row in dispatch_figures.figure_listing(game(declared))["figures"]})
            reply = dispatch_figures.figure_reply(game(declared), figure_id)
        self.assertTrue(reply.get("ok"))
        self.assertAlmostEqual(reply["current"], 4321.5, places=1)
        self.assertEqual(reply["drivers"][0]["driver"], "price level")

    def test_a_mods_figure_is_in_its_game_only(self):
        figure_id = MOD_ID + ":capital_in_hand"
        with tempfile.TemporaryDirectory() as mods_dir:
            write_mod(mods_dir, {figure_id: {"label": "x", "value": "price_index"}})
            self.assertIn(figure_id, declared_for(mods_dir).figures)
        self.assertNotIn(figure_id, shipped_declared().figures)
        self.assertNotIn(figure_id, figure_registry.FIGURES)

    def test_a_mod_figure_id_outside_its_namespace_is_refused(self):
        with tempfile.TemporaryDirectory() as mods_dir:
            write_mod(mods_dir, {"unqualified": {"label": "x", "value": "capital"}})
            with self.assertRaises(ModError):
                declared_for(mods_dir)

    def test_a_mod_figure_reading_a_path_that_is_not_readable_is_refused_naming_the_path(self):
        for bad_path in ("add_seat", "_workings_of", "population.__class__"):
            with tempfile.TemporaryDirectory() as mods_dir:
                write_mod(mods_dir, {MOD_ID + ":bad": {"label": "x", "value": bad_path}})
                with self.assertRaises(ModError) as caught:
                    declared_for(mods_dir)
            self.assertIn(bad_path, str(caught.exception))

    def test_a_path_follows_attributes_then_dict_keys(self):
        stand_in = Game(table={"iron": Game(price=7.0)})
        self.assertEqual(figures_data.read_path(stand_in, "table.iron.price"), 7.0)


class MineGoodsTests(unittest.TestCase):
    def goods(self, material):
        return resources_stand_in.build().mine_demand_goods(material)

    def test_the_goods_a_mine_supplies_come_from_the_catalogue_and_equal_the_old_table(self):
        for material, goods in OLD_DEMAND_KEYS.items():
            self.assertEqual(self.goods(material), goods, material)

    def test_a_material_with_no_catalogue_row_is_its_own_demand_good(self):
        self.assertEqual(self.goods("unknown_kg"), ("unknown_kg",))


if __name__ == "__main__":
    unittest.main()
