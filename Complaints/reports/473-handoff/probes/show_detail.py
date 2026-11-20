"""Show the differing leaves of one year's twin detail file, filtered by path prefix."""
import json, sys
path, prefix = sys.argv[1], sys.argv[2]
least = float(sys.argv[3]) if len(sys.argv) > 3 else 1e-6
floor = float(sys.argv[4]) if len(sys.argv) > 4 else 1e-6
limit = int(sys.argv[5]) if len(sys.argv) > 5 else 40
detail = json.load(open(path))
rows = [(d, p, a, b) for d, p, a, b in detail if p.startswith(prefix) and d >= least
        and max(abs(a or 0), abs(b or 0)) > floor]
rows.sort(key=lambda item: (-item[0], item[1]))
print("count", len(rows))
for d, p, a, b in rows[:limit]:
    print("  %.3g  %s  %s  %s" % (d, p[:125], "%.9g" % a if a is not None else None, "%.9g" % b if b is not None else None))
