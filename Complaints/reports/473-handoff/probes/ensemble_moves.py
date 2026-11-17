"""From ensemble_years.py files: per quantity, the mean and the median yearly move over the trimmed stage (the first
trimmed year, which follows the workforce trim, left out) across all members, and the median of the members' end gaps
(the largest move over the last measured years, what spin_up_settled tests), and how many members pass that test.
"prices" is the watched prices' change weighted by each good's share of the basket's spending (spin_up_gap.price_gap).
Usage: python3 ensemble_moves.py <label>=<file.jsonl>[@<weights.json>] [...]"""
import json, statistics, sys
RATE_FLOOR = 0.01
MEASURED = 4
TOLERANCE = 0.02      # sim.markets.spin_up.SPIN_UP_TOLERANCE
names = ("hired_hours", "real_output", "price_level", "inventory_value", "rate", "unmet_need", "wage", "money_supply")


def move(name, before, after):
    old, new = before.get(name), after.get(name)
    if old is None or new is None:
        return None
    floor = (RATE_FLOOR if name == "rate" else (before.get("food_need") or 0.0) if name == "unmet_need"
             else (before.get("real_output") or 0.0) if name == "inventory_value" else 0.0)
    base = max(abs(old), floor)
    return abs(new - old) / base if base > 0.0 else (0.0 if new == old else 1.0)


def price_move(before, after, weights=None):
    """spin_up_gap.price_gap: each watched price's change by its share of the basket's spending."""
    moves = {good: 1.0 if after["prices"].get(good) is None else abs(after["prices"][good] - old) / old
             for good, old in before["prices"].items() if old}
    weights = before.get("price_weights") or weights
    if not moves:
        return 0.0
    if not weights:
        return sum(moves.values()) / len(moves)
    return sum(weights.get(good, 0.0) * gap for good, gap in moves.items()) / sum(weights.values())


table = {}
settled = {}
for argument in sys.argv[1:]:
    label, path = argument.split("=", 1)
    path, _at, weights_path = path.partition("@")       # an older file with no shares: <file>@<watched_weights_probe.py output>
    weights = json.load(open(weights_path)) if weights_path else None
    by_member = {}
    for line in open(path):
        row = json.loads(line)
        if row["stage"] == "trimmed":
            by_member.setdefault(row["member"], []).append(row)
    result = {}
    for name in names + ("prices",):
        moves, ends = [], []
        for rows in by_member.values():
            pairs = list(zip(rows[1:], rows[2:]))
            series = [price_move(a, b, weights) if name == "prices" else move(name, a, b) for a, b in pairs]
            series = [value for value in series if value is not None]
            moves.extend(series)
            if series:
                ends.append(max(series[-(MEASURED - 1):]))
        result[name] = (statistics.mean(moves), statistics.median(moves), statistics.median(ends), len(by_member)) if moves else None
    table[label] = result
    checked = ("hired_hours", "real_output", "price_level", "inventory_value", "rate", "unmet_need")
    passing = 0
    for rows in by_member.values():
        pairs = list(zip(rows[1:], rows[2:]))[-(MEASURED - 1):]
        worst = max([move(name, a, b) or 0.0 for a, b in pairs for name in checked] + [price_move(a, b, weights) for a, b in pairs])
        passing += worst < TOLERANCE
    settled[label] = (passing, len(by_member))
labels = list(table)
print("%-16s" % "quantity" + "".join("  %-26s" % label[:26] for label in labels))
print("%-16s" % "" + "".join("  %-26s" % "mean / median / end-gap" for _label in labels))
for name in names + ("prices",):
    print("%-16s" % name + "".join("  %-26s" % ("%.4f / %.4f / %.4f" % table[label][name][:3] if table[label][name] else "n/a") for label in labels))
print("members: " + ", ".join("%s %d" % (label, table[label]["real_output"][3]) for label in labels))
print("members whose last measured years all move under the tolerance (what spin_up_settled reads): "
      + ", ".join("%s %d of %d" % (label, *settled[label]) for label in labels))
