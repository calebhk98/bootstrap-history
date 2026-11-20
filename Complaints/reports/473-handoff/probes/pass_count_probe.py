"""How many opening passes a solve takes, with experiment toggles. Usage: python3 pass_count_probe.py <civ> [nocarry] [notools]"""
import random, sys, time
from sim.economy import api as economy_api, opening, opening_own, opening_plot_tools
from sim.engine.ui_port import Sim, load, load_civ
civ, toggles = sys.argv[1], set(sys.argv[2:])
if "nocarry" in toggles:
    opening_own.plot_land = lambda held, kept_last: dict(held)
if "notools" in toggles:
    opening_plot_tools.add_wear = lambda *args: None
    opening_plot_tools.seed_moves = lambda *args: []
count = [0]
original = opening._open
def counted(*args, **more):
    count[0] += 1
    return original(*args, **more)
opening._open = counted
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
started = time.time()
economy = economy_api.blank_economy(setup)
print(civ, sorted(toggles), "passes", count[0], "seconds %.0f" % (time.time() - started))
