"""Per watched price: mean absolute yearly move, net drift a year, and the lag-one correlation of yearly moves
(negative = zigzag, positive = trend), over the trimmed stage, averaged over members.
Usage: python3 price_kinds.py <years.jsonl> [stage]"""
import json, math, sys
from collections import defaultdict
rows = [json.loads(line) for line in open(sys.argv[1])]
stage = sys.argv[2] if len(sys.argv) > 2 else "trimmed"
members = defaultdict(list)
for row in rows:
    if row["stage"] == stage:
        members[row["member"]].append(row)
names = sorted(next(iter(members.values()))[0]["prices"])
scalars = ["hired_hours", "real_output", "price_level", "inventory_value", "rate", "wage", "unmet_need"]
def series_of(years, name):
    if name in scalars:
        return [year.get(name) for year in years]
    return [year["prices"].get(name) for year in years]
def summary(values):
    moves = []
    for before, after in zip(values, values[1:]):
        if before and after and before > 0 and after > 0:
            moves.append(math.log(after / before))
    if len(moves) < 3:
        return None
    mean_abs = sum(abs(move) for move in moves) / len(moves)
    drift = sum(moves) / len(moves)
    centred = [move - drift for move in moves]
    variance = sum(value * value for value in centred)
    lagged = sum(first * second for first, second in zip(centred, centred[1:]))
    correlation = lagged / variance if variance > 0 else 0.0
    return mean_abs, drift, correlation, max(abs(move) for move in moves)
print(f"{'name':18s} {'mean|move|':>10s} {'drift/yr':>9s} {'lag1':>6s} {'max':>7s}  members {len(members)}")
for name in scalars + names:
    found = [summary(series_of(years, name)) for years in members.values()]
    found = [item for item in found if item]
    if not found:
        print(name, "no data"); continue
    count = len(found)
    print(f"{name:18s} {sum(i[0] for i in found)/count:10.4f} {sum(i[1] for i in found)/count:9.4f} {sum(i[2] for i in found)/count:6.2f} {max(i[3] for i in found):7.3f}")
