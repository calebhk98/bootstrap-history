"""`spin-up-trace --stages`: the text and CSV of the replayed spin-up's rows (sim/markets/spin_up_stages.py) and of the
gaps the opening ends with."""
import csv

from sim.markets.port_trace_holders import HOLDER_COLUMNS

SETTLE_COLUMNS = ("real_output", "hired_hours", "idle_hours", "inventory_value", "unmet_need", "food_need")
FIGURE_COLUMNS = ("struck", "wear")
CSV_COLUMNS = (("stage", "year") + SETTLE_COLUMNS + ("price_level", "rate", "wage", "money_supply") + HOLDER_COLUMNS
               + FIGURE_COLUMNS)


def _short(value, pattern="%.6g"):
    return "-" if value is None else pattern % value


def header_line(watched):
    """The column names of `row_line`, the watched goods last."""
    return " ".join(["%-7s %4s" % ("stage", "year")] + ["%12s" % name for name in SETTLE_COLUMNS]
                    + ["%11s %8s %10s %12s %12s %12s" % ("price level", "rate", "wage", "money supply", "struck", "wear")]
                    + ["%12s" % good[:12] for good in watched])


def row_line(row, watched):
    """One line for a replayed year: stage, year, the settle quantities, price level, rate, wage, money supply, the
    mint's strikes and wear, then the watched goods' prices."""
    return " ".join(["%-7s %4d" % (row["stage"], row["year"])] + ["%12s" % _short(row.get(name)) for name in SETTLE_COLUMNS]
                    + ["%11s %8s %10s %12s %12s %12s" % (
                        _short(row["price_level"], "%.4g"), _short(row["rate"], "%.4f"), _short(row["wage"], "%.4g"),
                        _short(row["money_supply"]), _short(row.get("struck")), _short(row.get("wear")))]
                    + ["%12s" % _short(row["prices"].get(good), "%.4g") for good in watched])


def format_end_gaps(report):
    """The gap by quantity over the measured final years and the watched good that moved most."""
    if report["gaps"] is None:
        return "end gaps: fewer than two trimmed years measured"
    good, gap = report["worst_price"]
    lines = ["end gaps over the last %d trimmed years (largest change between consecutive years):" % report["measured_years"]]
    lines.extend("  %-16s %.4f" % (name, value) for name, value in report["gaps"].items())
    lines.append("  largest price change: %s %.4f" % (good, gap))
    lines.append("  largest of all: %.4f" % max(report["gaps"].values()))
    return "\n".join(lines)


def write_stage_csv(rows, watched, path):
    """Every column of the rows, the watched goods' prices as one column each; empty where none."""
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_COLUMNS + tuple(watched))
        for row in rows:
            writer.writerow(["" if row.get(name) is None else row[name] for name in CSV_COLUMNS]
                            + ["" if row["prices"].get(good) is None else row["prices"][good] for good in watched])
