"""Cash against income through one spin-up, from a series_probe.py output: the cohorts' cash over their year's income, the
producers' cash over the year's output at the year's prices, and all of it over that output (the inverse of velocity).
Usage: python3 money_ratios.py <series.jsonl> [<row> ...]"""
import json, sys
rows = [json.loads(line) for line in open(sys.argv[1])][1:]
picked = [int(each) for each in sys.argv[2:]] or [0, len(rows) // 2, len(rows) - 1]
for index in picked:
    row = rows[index]
    cohort_cash = sum(cohort["cash"] for cohort in row["cohorts"].values())
    income = sum(cohort["income"] or 0.0 for cohort in row["cohorts"].values())
    producer_cash = sum(producer["cash"] for producer in row["producers"].values())
    nominal_output = sum((row["prices"].get(good) or 0.0) * quantity for good, quantity in row["output"].items())
    print("%s %d: cohorts' cash over income %.2f, producers' cash over output %.2f, all cash over output %.2f" % (
        row["stage"], row["year"], cohort_cash / income, producer_cash / nominal_output, (cohort_cash + producer_cash) / nominal_output))
