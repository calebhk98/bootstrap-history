"""Which goods carry the year-to-year swing of producers' inventory value (opening prices) over a window of years, and
how the price level and the rate moved beside it. Usage: python3 analyse_inventory.py <series.jsonl> <first row> <last row>"""
import json, sys, collections
path, first, last = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
lines = [json.loads(line) for line in open(path)]
head, rows = lines[0], lines[1:]
weight = head["weight"]
window = rows[first:last + 1]
total = [row["state"]["inventory_value"] for row in window]
mean_total = sum(total) / len(total)
print("inventory value", " ".join("%.4g" % value for value in total))
print("price level    ", " ".join("%.4g" % row["price_level"] for row in window))
print("rate           ", " ".join("%.4g" % row["rate"] for row in window))
print("real output    ", " ".join("%.4g" % row["state"]["real_output"] for row in window))
by_good = collections.defaultdict(lambda: [0.0] * len(window))
for index, row in enumerate(window):
    for good, value in row["held"].items():
        by_good[good][index] = value
ranked = []
for good, series in by_good.items():
    changes = [after - before for before, after in zip(series, series[1:])]
    mean_abs = sum(abs(change) for change in changes) / len(changes)
    alternating = sum(1 for a, b in zip(changes, changes[1:]) if a * b < 0) / max(1, len(changes) - 1)
    ranked.append((mean_abs / mean_total, good, sum(series) / len(series) / mean_total, alternating, series))
ranked.sort(reverse=True)
print("-- producers' holdings by good: mean |change| as share of inventory value, level share, alternation, series")
for share, good, level, alternating, series in ranked[:16]:
    made = [weight.get(good, 0.0) * row["output"].get(good, 0.0) for row in window]
    print("   %.4f  %-26s level %.3f alt %.2f" % (share, good, level, alternating))
    print("          held   " + " ".join("%9.4g" % value for value in series))
    print("          made   " + " ".join("%9.4g" % value for value in made))
    print("          price  " + " ".join("%9.4g" % (row["prices"].get(good) or 0.0) for row in window))
