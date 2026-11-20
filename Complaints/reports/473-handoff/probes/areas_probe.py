"""The market areas of a civilisation's tiles for chosen goods.
Usage: python3 areas_probe.py <civ> <good> [<good> ...]"""
import random, sys
from sim.engine.ui_port import Sim, load, load_civ

civ = sys.argv[1]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
area_map = setup.area_map()
for good in sys.argv[2:]:
    print(good, "price", setup.opening_prices.get(good))
    for area in area_map.areas(good):
        print("   ", area.area_id, sorted(area.tiles))
