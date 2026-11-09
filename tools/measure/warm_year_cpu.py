"""Process time of one warm year, and how many `Producer` records it builds. Run from the repository root:

    python3 tools/measure/warm_year_cpu.py SAVE.json

Loads the save as `warm_year_profile` does, steps one year, then times a second `game.step()` with `time.process_time()`."""
import gc
import sys
import time

sys.path.insert(0, ".")
from sim.economy.api import Producer   # noqa: E402
from tools.measure.warm_year_profile import warmed_game   # noqa: E402


def main(save_path):
    game = warmed_game(save_path)
    builds = []
    store_class = next(each for each in map(type, gc.get_objects()) if each.__name__ == "ProducerStore")     # not exported by the economy's api
    original_new, original_build = Producer.__new__, store_class._build

    def counting_new(cls, *args, **kwargs):
        builds.append(1)
        return original_new(cls, *args, **kwargs)

    def counting_build(self, row):
        builds.append(1)
        return original_build(self, row)

    Producer.__new__, store_class._build = counting_new, counting_build
    start = time.process_time()
    game.step()
    seconds = time.process_time() - start
    Producer.__new__, store_class._build = original_new, original_build
    print(f"process_seconds {seconds:.3f} producers_built {len(builds)}")


if __name__ == "__main__":
    main(sys.argv[1])
