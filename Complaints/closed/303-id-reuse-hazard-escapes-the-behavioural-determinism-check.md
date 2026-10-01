# The behavioural determinism check does not see the id()-reuse hazard it was written for

**Status:** closed - pinned by sim/tests/test_identity_cache.py and test_determinism.py (the three address-keyed caches use `IdentityCache`, which confirms every hit with `is`; engine code calls `id()` nowhere else)

`sim/tests/test_determinism.py` has a structural guard (no bare `id()` outside a dict key) and a behavioural one (repeat one scenario in one process and compare per-year digests). On the integration branch the structural guard failed on `market_clearing.py`, where an `id()` of the price table sat inside a cache signature that was compared with `==`, while the behavioural check, run at its old ten repeats of a full-length scenario, passed. So the behavioural check is blind to this class at any length we can afford; only the structural guard catches it (that cache now confirms the table with `is`).

Why it matters: the shortened behavioural check now only promises to catch state that survives from one `Sim` to the next in a process, and the comment says so. Nothing else would notice a different spelling of the hazard (an `id()` hidden behind a helper, or `hash()` of an object used as an identity).

What it would take: (aliases of `id` are now checked in `sim/tests/test_determinism.py`; `key = id(x)` was already rejected as a bare call outside a dict key.) What remains: add a cheap runtime guard, for example a debug mode that wraps the caches' keys and asserts the stored object is the one looked up.


Resolved: `sim/engine/identity_cache.py` is the one place an address keys a dictionary; a recycled address is a miss (tested by planting a stale entry). The structural guard now also fails any other `id()` call in `sim/engine`.
