"""Lay perturb_probe.py runs side by side: each total over the last ten years as a share of the first file's, and its mean yearly move.
Usage: python3 perturb_table.py <label>=<file> [...]   (the first is the unchanged run)"""
import json, sys
runs = []
for argument in sys.argv[1:]:
    label, path = argument.split("=", 1)
    rows = [json.loads(line) for line in open(path)]
    runs.append((label, [row for row in rows if row["stage"] == "trimmed"]))
names = ("hired_hours", "real_output", "price_level", "wage")
def level(rows, name):
    tail = [row[name] for row in rows[-10:] if row.get(name)]
    return sum(tail) / len(tail) if tail else float("nan")
def move(rows, name):
    pairs = [(a[name], b[name]) for a, b in zip(rows[1:], rows[2:]) if a.get(name) and b.get(name)]
    return sum(abs(new - old) / old for old, new in pairs) / len(pairs) if pairs else float("nan")
def hunger(rows):
    tail = rows[-10:]
    return sum((row.get("unmet_need") or 0.0) / row["food_need"] for row in tail) / len(tail)
base = runs[0][1]
print("%-28s" % "run" + "".join("%22s" % name for name in names) + "%12s" % "unmet food")
print("%-28s" % "" + "".join("%22s" % "level vs base / move" for _name in names))
for label, rows in runs:
    print("%-28s" % label[:28] + "".join("%14.3f / %5.2f%%" % (level(rows, name) / level(base, name), 100 * move(rows, name)) for name in names)
          + "%11.1f%%" % (100 * hunger(rows)))
