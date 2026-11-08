"""Profile the second (warm) year of a saved game: load it, step one year unprofiled (caches, compiled kernels), then
step one more under cProfile and write the profile. Run from the repository root:

    python3 tools/measure/warm_year_profile.py SAVE.json OUT.prof
    python3 -c "import pstats; pstats.Stats('OUT.prof').sort_stats('cumulative').print_stats(40)"

The save is read, never written. cProfile inflates times (about two to three times); compare profiles with each other,
and wall time with `simulator.py year-time`."""
import cProfile
import random
import sys

sys.path.insert(0, ".")
from sim.engine.ui_port import Sim, load, load_civ   # noqa: E402
from sim.ui.protocol import civ_of_save, load_state   # noqa: E402


def warmed_game(save_path):
    """The saved game loaded and stepped one year (caches and compiled kernels warm)."""
    _tree, _prices, nodes, _wages, _goods = load()
    game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ_of_save(save_path)),
               defer_economy=True)
    load_state(game, save_path)
    game.step()
    return game


def main(save_path, profile_path):
    game = warmed_game(save_path)
    profile = cProfile.Profile()
    profile.enable()
    game.step()
    profile.disable()
    profile.dump_stats(profile_path)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
