import random, traceback
from sim.tests.test_in_memory_civilisation import *
from sim.tests.test_in_memory_civilisation import _variant, _SKIP, _agent_dispatch, KNOWN_COMMANDS
sim = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=False, civ=_variant())
try:
    for _ in range(4):
        sim.step()
    for c in sorted(KNOWN_COMMANDS):
        if c in _SKIP:
            continue
        try:
            _agent_dispatch(sim, NODES, {"cmd": c})
        except BaseException:
            print("==", c)
            traceback.print_exc(limit=-6)
except BaseException:
    traceback.print_exc()
