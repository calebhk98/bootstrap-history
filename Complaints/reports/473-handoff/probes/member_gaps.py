"""Per member of an ensemble_years.py file: the largest move of each checked quantity over the last measured years, and which fail.
Usage: python3 member_gaps.py <file.jsonl>"""
import json, sys
RATE_FLOOR, MEASURED, TOLERANCE = 0.01, 4, 0.02
names = ("hired_hours", "real_output", "price_level", "inventory_value", "rate", "unmet_need")
def move(name, before, after):
    old, new = before.get(name), after.get(name)
    floor = (RATE_FLOOR if name == "rate" else (before.get("food_need") or 0.0) if name == "unmet_need"
             else (before.get("real_output") or 0.0) if name == "inventory_value" else 0.0)
    base = max(abs(old), floor)
    return abs(new - old) / base if base > 0.0 else 0.0
def price_move(before, after):
    moves = {good: 1.0 if after["prices"].get(good) is None else abs(after["prices"][good] - old) / old for good, old in before["prices"].items() if old}
    weights = before.get("price_weights")
    return sum(weights.get(good, 0.0) * gap for good, gap in moves.items()) / sum(weights.values()), max(moves.items(), key=lambda item: weights.get(item[0], 0.0) * item[1])
rows = [json.loads(line) for line in open(sys.argv[1])]
by = {}
for row in rows:
    by.setdefault(row["member"], []).append(row)
fails = {}
for member, series in sorted(by.items()):
    last = [row for row in series if row["stage"] == "trimmed"][-MEASURED:]
    gaps = {name: max(move(name, a, b) for a, b in zip(last, last[1:])) for name in names}
    worst = max((price_move(a, b) for a, b in zip(last, last[1:])), key=lambda item: item[0])
    gaps["prices"] = worst[0]
    failing = [name for name, gap in gaps.items() if gap > TOLERANCE]
    for name in failing:
        fails[name] = fails.get(name, 0) + 1
    print("%2d " % member + " ".join("%s %.3f" % (name[:6], gap) for name, gap in gaps.items()) + "  worst price: %s %.3f" % (worst[1][0], worst[1][1]) + ("  FAILS " + ",".join(failing) if failing else "  passes"))
print("members failing on each:", fails)
