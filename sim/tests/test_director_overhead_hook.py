"""Mod code can charge overhead against the directed-hours pool (Complaints/561): the hours count as committed."""
from .harness import *  # noqa: F401,F403

from sim.engine import mod_code

test_sim = sim(capital=1_000_000.0)
pool = test_sim.labour.director_pool()
committed_before = test_sim.labour.director_hours_committed()
free_before = pool - committed_before

api = mod_code.ModCodeApi("test_overhead_k3f9")
registrations_before = len(mod_code.DIRECTOR_OVERHEADS)
try:
    api.director_overhead(lambda world: 120.0)
    api.director_overhead(lambda world: -50.0)
    committed_after = test_sim.labour.director_hours_committed()
    check("a registered overhead counts as committed hours, a negative one as zero",
          abs(committed_after - committed_before - 120.0) < 1e-6, (committed_before, committed_after))
    check("the pool itself is unchanged", test_sim.labour.director_pool() == pool)
    check("free hours fall by exactly the overhead",
          abs((pool - committed_after) - (free_before - 120.0)) < 1e-6, (free_before, pool - committed_after))
finally:
    del mod_code.DIRECTOR_OVERHEADS[registrations_before:]
check("with nothing registered the committed hours are what they were",
      test_sim.labour.director_hours_committed() == committed_before)
