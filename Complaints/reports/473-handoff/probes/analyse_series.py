"""Which series carry the year-to-year swing of hired hours and real output over a window of years."""
import json, sys, collections
path = sys.argv[1]
first, last = int(sys.argv[2]), int(sys.argv[3])      # row indices (0 = first year)
lines = [json.loads(line) for line in open(path)]
head, rows = lines[0], lines[1:]
weight = head["weight"]
window = rows[first:last + 1]
print("years", [(row["stage"][0], row["year"]) for row in window])
total_hours = [row["state"]["hired_hours"] for row in window]
print("hired hours", ["%.4g" % value for value in total_hours])
print("real output", ["%.4g" % row["state"]["real_output"] for row in window])

# labour: by trade, and by (trade, area): mean absolute yearly change as a share of total hired hours
def swing(series_by_key, denominator):
    out = []
    for key, series in series_by_key.items():
        changes = [after - before for before, after in zip(series, series[1:])]
        mean_abs = sum(abs(change) for change in changes) / len(changes)
        alternating = sum(1 for a, b in zip(changes, changes[1:]) if a * b < 0) / max(1, len(changes) - 1)
        out.append((mean_abs / denominator, key, sum(series) / len(series), alternating))
    return sorted(out, reverse=True)

mean_hours = sum(total_hours) / len(total_hours)
by_trade = collections.defaultdict(lambda: [0.0] * len(window))
by_market = collections.defaultdict(lambda: [0.0] * len(window))
by_area = collections.defaultdict(lambda: [0.0] * len(window))
offered_area = collections.defaultdict(lambda: [0.0] * len(window))
for index, row in enumerate(window):
    for key, market in row["labour"].items():
        trade, area = key.split("|", 1)
        by_trade[trade][index] += market["hired"]
        by_market[key][index] += market["hired"]
        by_area[area][index] += market["hired"]
        offered_area[area][index] += market["offered"] or 0.0
print("-- hired hours by trade: mean |change| as share of all hired hours, mean level share, alternation")
for share, key, level, alternating in swing(by_trade, mean_hours)[:8]:
    print("   %.4f  %-22s level %.3f alt %.2f" % (share, key, level / mean_hours, alternating))
print("-- by area")
for share, key, level, alternating in swing(by_area, mean_hours)[:14]:
    print("   %.4f  %-28s level %.3f alt %.2f  hired %s  offered %s" % (share, key, level / mean_hours, alternating,
          " ".join("%.3g" % value for value in by_area[key]), " ".join("%.3g" % value for value in offered_area[key])))
print("-- by (trade, area)")
for share, key, level, alternating in swing(by_market, mean_hours)[:10]:
    market_rows = [row["labour"].get(key, {}) for row in window]
    print("   %.4f  %-36s level %.3f alt %.2f" % (share, key, level / mean_hours, alternating))
    print("          hired   " + " ".join("%9.4g" % (m.get("hired") or 0) for m in market_rows))
    print("          offered " + " ".join("%9.4g" % (m.get("offered") or 0) for m in market_rows))
    print("          wanted  " + " ".join("%9.4g" % (m.get("wanted") or 0) for m in market_rows))
    print("          wage    " + " ".join("%9.4g" % (m.get("wage") or 0) for m in market_rows))

# output by good valued at opening prices
mean_output = sum(row["state"]["real_output"] for row in window) / len(window)
by_good = collections.defaultdict(lambda: [0.0] * len(window))
for index, row in enumerate(window):
    for good, quantity in row["output"].items():
        if good in weight:
            by_good[good][index] += weight[good] * quantity
print("-- output by good (opening value): mean |change| as share of real output")
for share, key, level, alternating in swing(by_good, mean_output)[:14]:
    print("   %.4f  %-26s level %.3f alt %.2f  %s" % (share, key, level / mean_output, alternating, " ".join("%.3g" % value for value in by_good[key])))
