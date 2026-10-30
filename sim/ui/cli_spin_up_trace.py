"""`spin-up-trace`: run a civilisation's hidden spin-up for many years and print the price level, the money
stock and the mint's strikes by year (sim/markets/port_trace.py)."""
import csv
import random

from sim.markets import api as markets_api
from sim.engine.ui_port import Sim, default_civilisation_id, load, load_civ

MACRO_COLUMNS = ("year", "price_level", "wage", "unemployment", "real_output")


def format_trace(rows):
    """The trace as text: a header, then one line per year."""
    lines = ["%5s %12s %16s %8s %16s %16s %16s %10s %10s %10s %12s" % (
        "year", "price level", "money supply", "rate", "coin worn", "coin struck net", "metal at mint", "wage",
        "hired", "unemployed", "real output")]
    for row in rows:
        lines.append("%5d %12.4g %16.6g %8.4f %16.6g %16.6g %16.6g %10s %10.3g %10s %12.6g" % (
            row["year"], row["price_level"], row["money_supply"], row["rate"], row["wear"], row["struck"],
            row["metal_held"], _short(row["wage"], "%.4f"), row["hired_hours"],
            _short(row["unemployment"], "%.3f"), row["real_output"]))
    return "\n".join(lines)


def _short(value, pattern):
    return "-" if value is None else pattern % value


def write_csv(rows, path):
    """One row per year of the macro columns (year, price_level, wage, unemployment, real_output); empty where none."""
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(MACRO_COLUMNS)
        for row in rows:
            writer.writerow(["" if row[name] is None else row[name] for name in MACRO_COLUMNS])


def cmd_spin_up_trace(args):
    _tree, _prices, nodes, _wages, _goods = load()
    game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(args.civ or default_civilisation_id()))
    rows = markets_api.spin_up_trace(game, args.years)
    print(format_trace(rows))
    if args.csv:
        write_csv(rows, args.csv)
    return 0
