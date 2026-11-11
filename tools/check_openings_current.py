"""List the civilisations whose shipped opening (openings/) was not built from the code and data as they are now: a fresh
environment spins those up from scratch, minutes for the large ones. Exit status 1 when any is stale. Rebuild with
`python3 sim/simulator.py openings --prune` as the last step before a pull request. Run from the repository root."""
import sys

sys.path.insert(0, ".")
from sim.engine.ui_port import civilization_ids   # noqa: E402
from sim.ui.openings_manifest import stale_civs   # noqa: E402


def main():
    stale = stale_civs([civ_id for civ_id in civilization_ids() if ":" not in civ_id])    # a mod's civilisations ship none
    for civ_id in stale:
        print("stale shipped opening: %s" % civ_id)
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
