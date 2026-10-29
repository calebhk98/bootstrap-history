"""The part of the equivalence tool that builds and steps a game. Imports `sim` from whichever checkout is first on
sys.path, so `equiv_dump.py` can run it against a base checkout."""
import gzip, json, os, sys

from sim.tests import equiv_core, equiv_fields

SPIN_UP_DEFAULT = "3,2"   # the quick tier's short hidden spin-up: a full one costs many minutes per start


def prepare_environment(spin_up=None):
    """Short spin-up and a scratch home, before any game is built. Returns the spin-up setting in force."""
    if spin_up:
        os.environ["ROME_SPIN_UP_YEARS"] = spin_up
    os.environ.setdefault("ROME_SPIN_UP_YEARS", SPIN_UP_DEFAULT)
    from sim.tests.isolation import isolate_home
    isolate_home()
    return os.environ["ROME_SPIN_UP_YEARS"]


def state_leaves(sim, current=True):
    """(leaves, hash of the random generator) of the whole saved state. `current` applies this checkout's
    relocations and ignored prefixes; the base side is read raw."""
    from sim.engine.saveload import state_text
    data = json.loads(state_text(sim))
    rng_record = data.pop("_rng", None)
    leaves = equiv_core.flatten(data)
    if current:
        leaves = equiv_core.drop_ignored(equiv_core.relocate(leaves, equiv_fields.RELOCATIONS), equiv_fields.IGNORED)
        leaves = equiv_core.drop_empty(leaves, equiv_fields.ABSENT_WHEN_EMPTY)
    return leaves, equiv_core.rng_hash(rng_record)


def _founder_dead(sim):
    """The founder's death, read on either build: the base checkout runs this file too, and its `Sim` has no views."""
    return sim.view("founder")()["dead_reason"] if hasattr(sim, "view") else sim.dead_reason


def run_years(scenario, on_year, current=True, stop_after=None):
    """Step the scenario; call `on_year(index, leaves, rng_hash)` after each year; a False return stops the run."""
    from sim.tests import equiv_stress, fingerprint
    sim = equiv_stress.build(scenario) if scenario.get("stress") else fingerprint.build(scenario)
    years = scenario["years"] if stop_after is None else stop_after + 1
    for index in range(years):
        if _founder_dead(sim):
            break
        sim.step()
        leaves, rng = state_leaves(sim, current)
        if on_year(index, leaves, rng) is False:
            break


def leaves_at_year(scenario, year_index, current=True):
    """(leaves, rng hash) after year `year_index` of the scenario."""
    held = []
    run_years(scenario, lambda index, leaves, rng: held.append((leaves, rng)) if index == year_index else None,
              current, stop_after=year_index)
    return held[0] if held else ({}, None)


def write_dump(path, leaves, rng):
    with gzip.open(path, "wt") as handle:
        json.dump({"leaves": leaves, "rng": rng}, handle)


def read_dump(path):
    with gzip.open(path, "rt") as handle:
        data = json.load(handle)
    return data["leaves"], data["rng"]


def main_dump(argv):
    """`equiv_dump.py` entry: scenario json, year index, output path, 'raw' or 'current'."""
    scenario, year_index, out_path, mode = json.loads(argv[0]), int(argv[1]), argv[2], argv[3]
    prepare_environment(argv[4] if len(argv) > 4 else None)
    leaves, rng = leaves_at_year(scenario, year_index, current=(mode == "current"))
    write_dump(out_path, leaves, rng)
    return 0


if __name__ == "__main__":
    sys.exit(main_dump(sys.argv[1:]))
