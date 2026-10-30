"""`spin-up-sensitivity`: run a civilisation's spin-up under variants of how the economy adjusts and print each
variant's price-level and wage drift, cycle amplitude and cycle period (sim/economy/spin_up_sensitivity.py,
Complaint 553). A measurement for reading, never a pass or fail."""
import random

from sim.markets import api as markets_api
from sim.engine.ui_port import Sim, default_civilisation_id, load, load_civ


def cmd_spin_up_sensitivity(args):
    _tree, _prices, nodes, _wages, _goods = load()
    game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(args.civ or default_civilisation_id()))
    variants = [name for name in args.variants.split(",") if name] or None
    print(markets_api.sensitivity_table(game, args.years, args.skip, variants))
    return 0
