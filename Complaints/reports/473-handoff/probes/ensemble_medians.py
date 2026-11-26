"""Each settle quantity's median and worst gap over the members of saved ensemble outputs, with the members passing and the mean of the
members' worst gaps, one line a file. A count of members passing is a coarse reading where the gaps sit near the tolerance; these say
whether a rule moved anything.
usage: ensemble_medians.py <output of `spin-up-trace --stages --ensemble N`> [more outputs]"""
import statistics
import sys

QUANTITIES = ["price_level", "rate", "real_output", "hired_hours", "inventory_value", "unmet_need", "prices"]


def gaps_of(lines):
    """{quantity: its gap in each member} from the ensemble's table (a quantity's row holds the members' gaps first)."""
    members = next((int(line.split()[2]) for line in lines if "members pass" in line and "of" in line), None)
    found = {}
    for line in lines:
        parts = line.split()
        if parts and parts[0] in QUANTITIES and members and len(parts) > members and parts[0] not in found:
            try:
                found[parts[0]] = [float(value) for value in parts[1:1 + members]]
            except ValueError:
                pass
    return found, members


for path in sys.argv[1:]:
    lines = open(path).read().splitlines()
    gaps, members = gaps_of(lines)
    passing = next((line.strip() for line in lines if "members pass" in line), "no verdict line")
    print("%s: %s" % (path, passing))
    if not gaps:
        continue
    for quantity in QUANTITIES:
        if quantity in gaps:
            print("    %-16s median %.4f  worst %.4f" % (quantity, statistics.median(gaps[quantity]), max(gaps[quantity])))
    worst = [max(values[member] for values in gaps.values()) for member in range(members)]
    print("    members' worst gaps: mean %.4f  largest %.4f" % (statistics.mean(worst), max(worst)))
