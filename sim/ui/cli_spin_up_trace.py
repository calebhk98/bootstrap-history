"""`spin-up-trace`: run a civilisation's hidden spin-up for many years and print the price level, the money
stock and the mint's strikes by year (sim/engine/economy_port_trace.py)."""
import random

from sim.engine import economy_port_trace
from sim.engine.ui_port import Sim, default_civilisation_id, load, load_civ


def format_trace(rows):
    """The trace as text: a header, then one line per year."""
    lines = ["%5s %12s %16s %8s %16s %16s %16s %10s %10s" % (
        "year", "price level", "money supply", "rate", "coin worn", "coin struck net", "metal at mint", "wage",
        "hired")]
    for row in rows:
        lines.append("%5d %12.4g %16.6g %8.4f %16.6g %16.6g %16.6g %10.4f %10.3g" % (
            row["year"], row["price_level"], row["money_supply"], row["rate"], row["wear"], row["struck"],
            row["metal_held"], row["wage"], row["hired_hours"]))
    return "\n".join(lines)


def cmd_spin_up_trace(args):
    _tree, _prices, nodes, _wages, _goods = load()
    game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(args.civ or default_civilisation_id()))
    print(format_trace(economy_port_trace.spin_up_trace(game, args.years)))
    return 0
