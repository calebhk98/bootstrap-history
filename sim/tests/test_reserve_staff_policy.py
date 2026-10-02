"""reserve_staff: the keep-N-spare part of complaint 176."""
from .harness import *  # noqa: F401,F403
from sim.engine.proto.typed import parse_typed


def _dispatch(test_sim, line):
    cmd, refusal = parse_typed(line)
    check("typed %r parses" % line, cmd is not None, refusal)
    return S._agent_dispatch(test_sim, NODES, cmd) if cmd else {}


# Off by default: a year passes and nobody is hired for a reserve.
idle = sim(capital=5_000_000)
check("reserve_staff is listed by policy and off by default",
      idle.policy.get("reserve_staff") is False, sorted(idle.policy))
idle.step()
check("with the policy off no reserve hire is logged",
      not any("reserve_staff" in message for _year, message in idle.log), idle.log[-4:])

# The size of the reserve is set with `reserve`, the switch with `policy`.
kept = sim(capital=5_000_000)
reply = _dispatch(kept, "reserve craftsmen 5")
check("reserve craftsmen 5 is accepted", reply.get("ok") is True, reply)
reply = _dispatch(kept, "reserve scholars 1")
check("reserve scholars 1 is accepted",
      reply.get("ok") is True and reply.get("reserve") == {"craftsmen": 5, "scholars": 1}, reply)
reply = _dispatch(kept, "policy reserve_staff on")
check("policy reserve_staff on is accepted",
      reply.get("ok") is True and kept.policy.get("reserve_staff") is True, reply)
check("bare policy explains reserve_staff",
      "reserve_staff" in (_dispatch(kept, "policy").get("what_each_does") or {}))

kept.step()
scholars_free, craftsmen_free = kept.venture_staff_free()
check("after a year the free craftsmen cover the reserve", craftsmen_free >= 5 - 0.01, craftsmen_free)
check("...and the free scholars do", scholars_free >= 1 - 0.01, scholars_free)
check("...and the log says who was hired",
      any("reserve_staff" in message for _year, message in kept.log), kept.log[-6:])

# Housing is bought when the reserve does not fit.
big = sim(capital=5_000_000)
places_before = big.state.household.worker_housing_places or 0.0
_dispatch(big, "reserve craftsmen 40")
_dispatch(big, "policy reserve_staff on")
big.step()
check("a reserve larger than the household has room for buys housing",
      (big.state.household.worker_housing_places or 0.0) > places_before,
      (places_before, big.state.household.worker_housing_places))
check("...and the reserve is then filled", big.venture_staff_free()[1] >= 40 - 0.01, big.venture_staff_free())

# Within cash: nothing is hired or built when the household is in arrears to its limit.
poor = sim(capital=5_000_000)
poor.state.household.capital = -poor.credit_limit()
_dispatch(poor, "reserve craftsmen 40")
_dispatch(poor, "policy reserve_staff on")
places_before = poor.state.household.worker_housing_places or 0.0
poor.step()
check("no cash, no reserve hire and no housing",
      not any("reserve_staff" in message for _year, message in poor.log)
      and (poor.state.household.worker_housing_places or 0.0) == places_before, poor.log[-4:])

# The setting survives a save and a load.
from sim.engine.proto.saveload import save_state, load_state
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "reserve.json")
    save_state(kept, path)
    restored = sim(capital=1.0)
    load_state(restored, path)
check("the reserve size and switch are saved",
      restored.policy.get("reserve_staff") is True
      and _dispatch(restored, "reserve").get("reserve") == {"craftsmen": 5, "scholars": 1})
