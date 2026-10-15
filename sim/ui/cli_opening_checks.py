"""`opening-checks`: print the opening checks (sim/engine/opening_checks.py) for each civilisation's full-length opening."""
from sim.engine import opening_checks_run, opening_checks_table
from sim.engine.ui_port import civilization_ids


def cmd_opening_checks(args):
    civs = [part.strip() for part in (args.civs or "").split(",") if part.strip()] or civilization_ids()
    results_by_civ = {}
    print(opening_checks_table.header(), flush=True)
    for civ_id in civs:
        results_by_civ[civ_id] = opening_checks_run.check_civilisation(civ_id)
        print("\n".join(opening_checks_table.table({civ_id: results_by_civ[civ_id]}, with_header=False)), flush=True)
    return 1 if any(opening_checks_run.failures(results) for results in results_by_civ.values()) else 0
