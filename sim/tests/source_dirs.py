"""Where the simulator's source lives, for tests that check a rule by scanning directories.

The engine side is `sim/engine/` plus the packages split out of it (geography, labour, agents, ui),
so a rule that once scanned `sim/engine/` scans all of them. Packages are found, and only the ones
that are not engine-side are named here.
"""
import os

SIM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOT_ENGINE_SIDE = {"tests", "economy", "world"}


def engine_side_dirs():
    """Absolute paths of sim/engine/ and every package split out of it."""
    return [os.path.join(SIM_DIR, name) for name in sorted(os.listdir(SIM_DIR))
            if name not in NOT_ENGINE_SIDE and os.path.isfile(os.path.join(SIM_DIR, name, "__init__.py"))]


def engine_and_world_dirs():
    """The engine side plus sim/world/."""
    return engine_side_dirs() + [os.path.join(SIM_DIR, "world")]
