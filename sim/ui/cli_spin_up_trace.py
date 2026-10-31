"""`spin-up-trace`: run a civilisation's hidden spin-up for many years and print the price level, the money
stock and the mint's strikes by year (sim/markets/port_trace.py). With `--fixture`, step the hand-built economy
instead (sim/ui/spin_up_fixture_trace.py)."""
import csv
import random

from sim.markets import api as markets_api
from sim.engine.ui_port import Sim, default_civilisation_id, load, load_civ
from sim.markets.port_trace_holders import HOLDER_COLUMNS
from sim.ui.spin_up_fixture_trace import FIXTURE_COLUMNS, fixture_trace, format_fixture_trace

MACRO_COLUMNS = ("year", "price_level", "wage", "unsold_hours_share", "people_unemployment", "real_output",
                 "chained_price_level")


def format_trace(rows):
    """The trace as text: a header, then one line per year."""
    lines = ["%5s %12s %16s %8s %16s %16s %16s %10s %10s %12s %14s %12s %12s" % (
        "year", "price level", "money supply", "rate", "coin worn", "coin struck net", "metal at mint", "wage",
        "hired", "unsold hrs", "people unemp", "real output", "chained level")]
    for row in rows:
        lines.append("%5d %12.4g %16.6g %8.4f %16.6g %16.6g %16.6g %10s %10.3g %12s %14s %12.6g %12.6g" % (
            row["year"], row["price_level"], row["money_supply"], row["rate"], row["wear"], row["struck"],
            row["metal_held"], _short(row["wage"], "%.4f"), row["hired_hours"],
            _short(row["unsold_hours_share"], "%.3f"), _short(row["people_unemployment"], "%.3f"),
            row["real_output"], row["chained_price_level"]))
    return "\n".join(lines)


def _short(value, pattern):
    return "-" if value is None else pattern % value


def write_csv(rows, path, columns=MACRO_COLUMNS + HOLDER_COLUMNS):
    """One row per year of `columns` (by default the macro columns, then the money each kind of holder keeps); empty
    where none."""
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(["" if row[name] is None else row[name] for name in columns])


def cmd_spin_up_trace(args):
    if args.fixture:
        rows = fixture_trace(args.fixture, args.years)
        print(format_fixture_trace(rows))
        if args.csv:
            write_csv(rows, args.csv, FIXTURE_COLUMNS)
        return 0
    _tree, _prices, nodes, _wages, _goods = load()
    game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(args.civ or default_civilisation_id()))
    rows = markets_api.spin_up_trace(game, args.years)
    print(format_trace(rows))
    if args.csv:
        write_csv(rows, args.csv)
    return 0
