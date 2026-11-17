"""Print per-year states of twin A (and the relative gap between the twins) from a twin probe file."""
import json, sys
rows = [json.loads(line) for line in open(sys.argv[1])][1:]
names = ("real_output", "hired_hours", "inventory_value", "price_level", "rate", "unmet_need", "wage")
print("%-8s %3s " % ("stage", "yr") + " ".join("%12s" % name[:12] for name in names) + "   | yearly change of each | twin gap: out med, p90")
previous = None
for row in rows:
    state = row["states"][0]
    changes = ""
    if previous is not None:
        changes = " ".join("%+6.1f%%" % (100.0 * (state[name] - previous[name]) / previous[name]) if previous.get(name) else "   n/a " for name in names[:5])
    print("%-8s %3d " % (row["stage"], row["year"]) + " ".join("%12.5g" % (state.get(name) or 0.0) for name in names) + "   | " + changes
          + "  | %.1e %.1e" % (row["outcome"]["median"], row["outcome"]["p90"]))
    previous = state
