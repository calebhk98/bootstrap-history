"""Complaint 423: a mod adds a `figures` entry by data (data/ui/figures.json), and the goods a mine supplies come
from the resource catalogue, so neither needs an engine or UI edit."""
import json
import os
import tempfile

from .harness import *  # noqa: F401,F403

from sim.engine.mods_base import ModError
from sim.ui import figures_data
from sim.ui import figures as figure_registry
from sim.ui.proto import dispatch_figures

MOD_ID = "tester_figs_k3f9"
OLD_DEMAND_KEYS = {"coal": ("coal_kg",), "iron": ("iron_bar_kg", "iron_ore_kg"),
                   "copper": ("copper_kg", "copper_wire_kg", "wire_drawn_kg"), "lead": ("lead_kg",),
                   "tin": ("tin_kg",), "silver": ("silver_kg",), "gold": ("gold_kg",)}


def write_mod(mods_dir, figures):
    folder = os.path.join(mods_dir, MOD_ID)
    os.makedirs(os.path.join(folder, "data", "ui"))
    with open(os.path.join(folder, "mod.json"), "w", encoding="utf-8") as handle:
        json.dump({"id": MOD_ID, "name": "Figures", "version": "1.0.0", "dependencies": [], "conflicts": []},
                  handle)
    with open(os.path.join(folder, "data", "ui", "figures.json"), "w", encoding="utf-8") as handle:
        json.dump({"figures": figures}, handle)


game = sim(capital=1_000_000.0)
base_figures = set(figure_registry.FIGURES)
check("the base figures declared as data are registered", {"income", "population"} <= base_figures)
population = figure_registry.read_figure(game, "population")
check("a declared figure reads its state paths",
      population["value"] == round(game.population.total) and set(population["components"])
      == {"children", "working age", "elderly"}, population)

figure_id = MOD_ID + ":capital_in_hand"
with tempfile.TemporaryDirectory() as mods_dir:
    write_mod(mods_dir, {figure_id: {"label": "cash again", "unit": "money", "value": "state.household.capital",
                                     "drivers": {"price level": "price_index"}}})
    figures_data.register_data_figures(mods_dir)
    listing = dispatch_figures.figure_listing()
    check("a mod's figure shows in the figures listing",
          figure_id in {row["name"] for row in listing["figures"]}, listing)
    reply = dispatch_figures.figure_reply(game, figure_id)
    check("a mod's figure reads the game", reply.get("ok") and abs(reply["current"] - game.capital) < 0.1, reply)
    check("a mod's figure shows its drivers", reply["drivers"][0]["driver"] == "price level", reply)
figures_data.register_data_figures()
check("the default registration drops the mod's figure", figure_id not in figure_registry.FIGURES)

with tempfile.TemporaryDirectory() as mods_dir:
    write_mod(mods_dir, {"unqualified": {"label": "x", "value": "capital"}})
    try:
        figures_data.register_data_figures(mods_dir)
        refused = False
    except ModError:
        refused = True
    figures_data.register_data_figures()
check("a mod figure id outside its namespace is refused", refused)

check("the goods a mine supplies come from the catalogue and equal the old table",
      all(game.mine_demand_goods(material) == goods for material, goods in OLD_DEMAND_KEYS.items()))
check("a material with no catalogue row is its own demand good", game.mine_demand_goods("unknown_kg") == ("unknown_kg",))
