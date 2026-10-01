"""hot_path_caches: the per-year hot paths do not repeat work whose answer cannot have changed.

Complaint 145: a year got slower as more was built because every concern's
output looked up the production catalog through a path-resolving call.
"""
import os

from .harness import *  # noqa: F401,F403


def _count_calls(function_owner, name, work):
    """How many times `work()` calls `function_owner.name`."""
    original = getattr(function_owner, name)
    calls = []

    def counting(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    setattr(function_owner, name, counting)
    try:
        work()
    finally:
        setattr(function_owner, name, original)
    return len(calls)


def _look_up_output_many_times():
    from sim.engine.actors.supply import materials_made_by
    for _ in range(500):
        materials_made_by("iron_smelting")


from sim.engine.actors.supply import materials_made_by as _warm
_warm("iron_smelting")
check("a warm production lookup resolves no filesystem paths",
      _count_calls(os.path, "abspath", _look_up_output_many_times) == 0)
check("a warm production lookup lists no directories",
      _count_calls(os, "listdir", _look_up_output_many_times) == 0)

# A year's wall-clock budget is generous on purpose: it catches a return of the
# per-call catalog scan (tens of times slower), not machine noise.
_budget_sim = sim(capital=200000.0)
_start = time.process_time()
for _ in range(3):
    _budget_sim.step()
_elapsed = time.process_time() - _start
check("three early years of the default run take well under a minute of CPU",
      _elapsed < 60.0, "%.1fs" % _elapsed)
