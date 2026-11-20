"""Carriage of a good from one tile to each other tile, as money per unit and as a share of the good's opening price.
Usage: python3 carriage_probe.py <civ> <good> <source tile>"""
import random, sys
from sim.engine.ui_port import Sim, load, load_civ
civ, good, source = sys.argv[1], sys.argv[2], sys.argv[3]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
table = setup.carriage_table()
spec = setup.specs[good]
price = setup.opening_prices[good]
print("good", good, "price", price, "spec", {name: getattr(spec, name) for name in ("mass_kg", "unit_mass_kg", "kg_per_unit", "tonnes_per_unit") if hasattr(spec, name)})
print([name for name in dir(table) if not name.startswith("_")])
for tile in sorted(setup.tiles):
    try:
        cost = table.cost_per_tonne(source, tile); cost = "%.1f = %.0f%% of its price, %.0f days" % (cost, 100 * cost / (price * 1000.0), table.days_between(source, tile))
    except Exception as error:
        cost = repr(error)
    print("  %-12s per tonne %s" % (tile, cost))
