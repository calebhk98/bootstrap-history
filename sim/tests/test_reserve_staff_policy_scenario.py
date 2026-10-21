"""reserve_staff through a running game (the rule is test_reserve_staff_policy): the policy is listed and off, a year
of the staff step fills the reserve and logs who was hired, a reserve too big for the household buys housing, and the
setting survives a save and a load."""
from .harness import *  # noqa: F401,F403
from sim.refusal import facts_of
from sim.ui.proto.typed import parse_typed


def _dispatch(test_sim, line):
    cmd, _refusal = parse_typed(line)
    return S._agent_dispatch(test_sim, NODES, cmd)


def _hired_for_reserve(test_sim):
    return any(facts_of(message).get("policy") == "reserve_staff" for _year, message in test_sim.log)


idle = sim(capital=5_000_000)
check("reserve_staff is listed by policy and off by default; a year with it off hires no reserve",
      idle.policy.get("reserve_staff") is False and not (idle._step_staff() or _hired_for_reserve(idle)), sorted(idle.policy))

kept = sim(capital=5_000_000)
_dispatch(kept, "reserve craftsmen 5")
_dispatch(kept, "reserve scholars 1")
_dispatch(kept, "policy reserve_staff on")
check("bare policy explains reserve_staff", "reserve_staff" in (_dispatch(kept, "policy").get("what_each_does") or {}))
kept._step_staff()
scholars_free, craftsmen_free = kept.venture_staff_free()
check("after a year the free craftsmen and scholars cover the reserve and the log says who was hired",
      craftsmen_free >= 5 - 0.01 and scholars_free >= 1 - 0.01 and _hired_for_reserve(kept),
      (craftsmen_free, scholars_free, kept.log[-6:]))

big = sim(capital=5_000_000)
places_before = big.state.household.worker_housing_places or 0.0
_dispatch(big, "reserve craftsmen 40")
_dispatch(big, "policy reserve_staff on")
big._step_staff()
check("a reserve larger than the household has room for buys housing and is then filled",
      (big.state.household.worker_housing_places or 0.0) > places_before and big.venture_staff_free()[1] >= 40 - 0.01,
      (places_before, big.state.household.worker_housing_places, big.venture_staff_free()))

from sim.engine.saveload import save_state, load_state
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "reserve.json")
    save_state(kept, path)
    restored = unopened_sim(capital=1.0)
    load_state(restored, path)
check("the reserve size and switch are saved",
      restored.policy.get("reserve_staff") is True
      and _dispatch(restored, "reserve").get("reserve") == {"craftsmen": 5, "scholars": 1})
