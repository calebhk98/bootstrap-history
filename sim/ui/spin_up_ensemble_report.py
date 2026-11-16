"""The text and CSV of a spin-up ensemble (sim/ui/spin_up_ensemble_run.py)."""
import csv

from sim.markets import api as markets_api


def _short(value):
    return "-" if value is None else "%.4g" % value


def format_ensemble(civilisation_id, results):
    """Per quantity: each member's end gap, their median and spread, then each member's trend (second-half mean against
    first-half mean of the trimmed stage, as a share of the second half's mean) and their median."""
    gaps = markets_api.spin_up_summary([result["gaps"] or {} for result in results])
    trends = markets_api.spin_up_summary([result["trends"] for result in results])
    members = [result["member"] for result in results]
    lines = ["%s: %d spin-up replays; member k starts with every household cohort's cash multiplied by 1 + k * %g "
             "(a measurement perturbation, not part of the game); member 0 is unperturbed"
             % (civilisation_id, len(results), markets_api.spin_up_cash_factor(1) - 1.0),
             "end gap = largest change between consecutive years over the last trimmed years; trend = change from the first "
             "to the second half of the trimmed stage over the second half's mean (rate against SPIN_UP_RATE_FLOOR, unmet "
             "need against the food need)",
             "%-16s %s | %9s %9s | %s | %9s" % ("quantity", " ".join("%9s" % ("gap m%d" % member) for member in members),
                                                "median", "spread",
                                                " ".join("%9s" % ("trend m%d" % member) for member in members),
                                                "trend med")]
    for name in gaps:
        trend = trends.get(name)
        lines.append("%-16s %s | %9s %9s | %s | %9s" % (
            name, " ".join("%9s" % _short((each["gaps"] or {}).get(name)) for each in results),
            _short(gaps[name]["median"]), _short(gaps[name]["spread"]),
            " ".join("%9s" % _short(each["trends"].get(name)) for each in results),
            _short(trend["median"] if trend else None)))
    return "\n".join(lines)


def write_ensemble_csv(results, path):
    """One row per member and quantity: member, quantity, end gap, trend; empty where none."""
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("member", "quantity", "end_gap", "trend"))
        for result in results:
            gaps = result["gaps"] or {}
            for name in sorted(set(gaps) | set(result["trends"])):
                writer.writerow([result["member"], name] + ["" if value is None else value
                                                            for value in (gaps.get(name), result["trends"].get(name))])
