"""Scenarios: the per-year hot paths on a whole game (Complaint 141). The rules are in test_hot_path_caches."""
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


# --- the material stock moves capacity keys to the pool once, not on every read.
_probe = unopened_sim(capital=2000.0)
_ledger = _probe._material_stock()
_ledger["scholar_hours"] += 5.0
_probe._material_stock()
check("a capacity key written to the stock lands in the pool and leaves the stock",
      "scholar_hours" not in _probe._material_stock() and _probe.state.economy.capacity_pool.get("scholar_hours", 0.0) >= 5.0)

# --- the works effects of mining techniques are read once until what is built or operating changes.
_probe.mine_works_effects()
_asked = _count_calls(_probe, "running", lambda: [_probe.mine_works_effects() for _ in range(20)])
check("the mining works effects are not recomputed while nothing built or operating changes", _asked == 0, _asked)
