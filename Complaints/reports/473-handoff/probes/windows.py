"""A long single run in windows of years: mean absolute yearly move and net drift a year of each watched quantity.
Usage: python3 windows.py <probe_spin_years output> [window years]"""
import json, math, sys
rows = [row for row in (json.loads(line) for line in open(sys.argv[1])) if "stage" in row]
size = int(sys.argv[2]) if len(sys.argv) > 2 else 20
print("keys", [key for key in rows[0] if key not in ("prices",)][:30])
scalars = [name for name in ("hired_hours", "real_output", "price_level", "inventory_value", "rate", "wage", "unskilled_wage", "money_supply", "unmet_need", "idle_hours", "money_households", "money_producers") if name in rows[0]]
price_key = "prices" if "prices" in rows[0] else None
goods = sorted(rows[0][price_key]) if price_key else []
def series(name):
    if name in scalars:
        return [row.get(name) for row in rows]
    return [row[price_key].get(name) for row in rows]
def moves(values):
    out = []
    for before, after in zip(values, values[1:]):
        out.append(math.log(after / before) if before and after and before > 0 and after > 0 else None)
    return out
starts = list(range(0, len(rows) - 1, size))
print(f"{'window':18s}" + "".join(f"{start:>5d}-{min(start+size, len(rows)-1):<4d}" for start in starts))
for name in scalars + goods:
    found = moves(series(name))
    cells = []
    for start in starts:
        part = [move for move in found[start:start + size] if move is not None]
        if not part:
            cells.append("    -    "); continue
        cells.append(f"{100*sum(abs(move) for move in part)/len(part):4.1f}{100*sum(part)/len(part):+5.1f}")
    print(f"{name:18s}" + " ".join(cells))
print("each cell: mean absolute yearly move in percent, then net drift a year in percent")
