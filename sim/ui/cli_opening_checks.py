"""`opening-checks`: print the opening checks (sim/engine/opening_checks.py) for each civilisation's full-length opening,
then the concerns that pay their way (sim/engine/concern_scan_run.py; reported, never a failing check)."""
import json

from sim.engine import concern_scan_run, opening_checks_run, opening_checks_table
from sim.engine.ui_port import civilization_ids


def cmd_opening_checks(args):
    civs = [part.strip() for part in (args.civs or "").split(",") if part.strip()] or civilization_ids()
    concerns_only = bool(getattr(args, "concerns_only", False))
    as_json = bool(getattr(args, "json", False))
    results_by_civ, document = {}, {}
    if not as_json and not concerns_only:
        print(opening_checks_table.header(), flush=True)
    for civ_id in civs:
        results, concerns = opening_checks_run.check_civilisation_and_concerns(civ_id, with_checks=not concerns_only)
        results_by_civ[civ_id] = results
        document[civ_id] = {"checks": [result.to_plain() for result in results], "concerns": concerns}
        if not as_json:
            if results:
                print("\n".join(opening_checks_table.table({civ_id: results}, with_header=False)), flush=True)
            print("\n".join(concern_scan_run.lines(civ_id, concerns)), flush=True)
    if as_json:
        print(json.dumps(document, indent=1, sort_keys=True))
    return 1 if any(opening_checks_run.failures(results) for results in results_by_civ.values()) else 0
