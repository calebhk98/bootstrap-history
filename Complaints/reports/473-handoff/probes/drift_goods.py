"""Which goods carry the slow change of real output, and how their price and their makers' stock move.
Usage: python3 drift_goods.py <series.jsonl> <from row> <to row>"""
import json, sys
lines = [json.loads(line) for line in open(sys.argv[1])]
head, rows = lines[0], lines[1:]
weight = head["weight"]
first, last = int(sys.argv[2]), int(sys.argv[3])
start, end = rows[first], rows[last]
def value(row, good):
    return weight.get(good, 0.0) * row["output"].get(good, 0.0)
goods = sorted(set(start["output"]) | set(end["output"]))
total_start = sum(value(start, good) for good in goods)
total_end = sum(value(end, good) for good in goods)
print("weighted output", "%.4g -> %.4g" % (total_start, total_end), "ratio %.3f" % (total_end / total_start))
print("state real_output %.4g -> %.4g  hours %.4g -> %.4g" % (start["state"]["real_output"], end["state"]["real_output"], start["state"]["hired_hours"], end["state"]["hired_hours"]))
ranked = sorted(goods, key=lambda good: -abs(value(end, good) - value(start, good)))
print(f"{'good':28s} {'share0':>7s} {'out ratio':>9s} {'d share':>8s} {'price ratio':>11s} {'price/open0':>11s} {'held0':>8s} {'held1':>8s}")
for good in ranked[:32]:
    before, after = value(start, good), value(end, good)
    price_before, price_after = start["prices"].get(good), end["prices"].get(good)
    ratio = after / before if before else float("inf")
    price_ratio = (price_after / price_before) if price_before and price_after else float("nan")
    held_before = start["held"].get(good, 0.0) / before if before else 0.0
    held_after = end["held"].get(good, 0.0) / after if after else 0.0
    print(f"{good:28s} {before/total_start:7.4f} {ratio:9.3f} {(after-before)/total_start:8.4f} {price_ratio:11.3f} {(price_before or 0)/weight.get(good,1):11.3f} {held_before:8.2f} {held_after:8.2f}")
