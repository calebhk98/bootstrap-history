"""Every nth year of a probe_spin_years output against its first year. Usage: python3 table.py <file> [step]"""
import json, sys
rows = [row for row in (json.loads(line) for line in open(sys.argv[1])) if "stage" in row]
step = int(sys.argv[2]) if len(sys.argv) > 2 else 5
base = rows[0]
goods = sorted(base["prices"])
print("yr hours output wage level inv/out rate idle/hired money | " + " ".join(good[:6] for good in goods))
for index, row in enumerate(rows):
    if index % step == 0 or index == len(rows) - 1:
        prices, first = row["prices"], base["prices"]
        print(f"{index:3d} {row['hired_hours']/base['hired_hours']:5.2f} {row['real_output']/base['real_output']:5.2f} {row['wage']:5.2f} {row['price_level']:5.2f} "
              f"{row['inventory_value']/row['real_output']:5.2f} {row['rate']:5.3f} {row['idle_hours']/row['hired_hours']:5.2f} {row['money_supply']/base['money_supply']:5.2f} | "
              + " ".join(f"{(prices.get(good) or 0)/first[good]:6.2f}" for good in goods))
