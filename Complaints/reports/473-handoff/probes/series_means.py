"""The ensemble's mean of each quantity by year, as a share of its first year, for each file given, every few years.
Usage: python3 series_means.py <every> label=file.jsonl [...]"""
import json, sys
from collections import defaultdict
every = int(sys.argv[1])
names = ("hired_hours", "real_output", "price_level", "inventory_value", "wage", "unmet_need", "rate")
for argument in sys.argv[2:]:
    label, path = argument.split("=", 1)
    by_year = defaultdict(lambda: defaultdict(list))
    order = []
    for line in open(path):
        row = json.loads(line)
        key = (row["stage"], row["year"])
        if key not in by_year:
            order.append(key)
        for name in names + ("food_need",):
            if row.get(name) is not None:
                by_year[key][name].append(row[name])
    first = {name: sum(by_year[order[0]][name]) / len(by_year[order[0]][name]) for name in names if by_year[order[0]][name]}
    print(label)
    print("  %-12s" % "year" + "".join("%9s" % name[:8] for name in names))
    for index, key in enumerate(order):
        if index % every and index != len(order) - 1:
            continue
        cells = []
        for name in names:
            values = by_year[key][name]
            if not values:
                cells.append("%9s" % "-")
                continue
            mean = sum(values) / len(values)
            if name == "unmet_need":
                need = by_year[key]["food_need"]
                cells.append("%9.3f" % (mean / (sum(need) / len(need)) if need else float("nan")))
            elif name == "rate":
                cells.append("%9.3f" % mean)
            else:
                cells.append("%9.3f" % (mean / first[name] if first.get(name) else float("nan")))
        print("  %-12s" % ("%s %d" % (key[0][:5], key[1])) + "".join(cells))
