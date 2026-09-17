# Design: extracting the household out of `Sim`

**Status:** design, pending the field list in `SIM_STATE_INVENTORY.md`.
**Why:** `Sim` is one object holding the world, the scenario, and the founder's
household all together. Nothing else can own money, knowledge or a workshop,
so there can be no government actor, no firm, no rival, and no second player.
This is the change that makes all four possible, and it is the same change for
all four.

---

## 1. What moves, and where it goes

A new package, so this is not more state in the same files:

```text
sim/engine/actors/
    __init__.py       what a caller imports
    household.py      class Household - the founder/family as an economic actor
```

`Sim` keeps a reference:

```python
self.household = Household(...)
```

and the roughly eighty founder-specific attributes move onto it: money and
credit, staff and their hours, the knowledge this household owns, its
inventory and facilities, its standing and reputation.

`SIM_STATE_INVENTORY.md` has the measured field list, each classified
HOUSEHOLD / WORLD / SCENARIO / INTERNAL. Only HOUSEHOLD moves. WORLD state
(the year, population, price indices) stays on `Sim`, because it belongs to
the world whoever is playing.

### One class now, not a class hierarchy

The obvious temptation is an `Actor` base class with `Household`, `Government`
and `Firm` under it. Resist it until there is a second actor to look at. A
base class designed against one example encodes that example's accidents as
the interface. What we do now instead is name the fields so they would make
sense for a government or a firm - `capital` rather than `founders_purse` -
and let the second actor tell us what the base class actually is.

The inventory flags the fields that genuinely cannot generalise, the ones
about one mortal person's lifespan and death. Those are a design question, not
a move, and they stay on `Sim` until we answer it.

---

## 2. How call sites reach it, and why not the elegant way

Roughly eighty attributes are read and written from six mixin files through
`self`. There are three ways to keep `self.capital` working, and the
difference between them is not style.

Measured on this machine, 2,000,000 accesses each:

| How | ns per access | vs today |
|---|---|---|
| `self.capital` (today) | 10.2 | 1.0x |
| `self.household.capital` (rewrite every call site) | 17.4 | **1.7x** |
| `@property` on `Sim` forwarding to the household | 60.3 | 5.9x |
| `__getattr__` on `Sim` forwarding to the household | 519.4 | **51x** |

`__getattr__` is the elegant one: leave every call site alone, forward
anything `Sim` does not have. It is also fifty-one times slower per access,
and it is slow in exactly the wrong place, because `__getattr__` fires only
when normal lookup FAILS, which after the move is the common case for all
eighty fields. The engine's own comments record `revenue()` being called
sixty-one million times in a forty-five-year run. Fifty-one times slower on
the hot path is not a tax, it is a different program.

So:

**Engine-internal call sites are rewritten to `self.household.capital`.**
Mechanical, one extra C-level attribute lookup, 1.7x on a lookup that is not
the dominant cost of anything. This is the bulk of the diff and it is the part
an agent can do with a clear spec.

**Properties on `Sim` exist only for the outside surface** - the JSON
protocol, save/load, the CLI, and the tests. Those are not hot, 5.9x on a cold
path costs nothing, and it means no caller outside the engine has to change at
all.

---

## 3. The trap that has already caught someone here

`sim/ARCHITECTURE.md` records it plainly:

> An "obviously safe" cleanup - promoting `getattr(self, x, default)` calls to
> real `__init__` attributes - passed the entire suite while silently breaking
> save-file semantics, because several of those names are in `SAVE_FIELDS`
> where a *missing* attribute is meaningful.

Many household fields are created lazily, and their **absence means "this has
never happened yet"**. A save file without the field is not a save file with
the field set to zero.

A plain property breaks this, because a property always exists.
`getattr(sim, "bounties_paid", None)` would return the household's default
instead of `None`, and the difference is invisible until a save file from an
old run reads back wrong.

The rule for this extraction: **a property over a lazily-created field must
raise `AttributeError` when the household does not have it.** Then
`getattr(sim, name, default)` returns the default, exactly as today.

```python
@property
def bounties_paid(self):
    # AttributeError on purpose: absence is meaningful here, and
    # getattr(sim, "bounties_paid", default) must still see it.
    return self.household.bounties_paid
```

With one footgun to know about: an AttributeError raised by a bug *inside* a
property body is indistinguishable from the intended one, and gets silently
swallowed by any caller using `getattr` with a default. Keep these property
bodies to a single attribute access and nothing else.

`SAVE_FIELDS` in `sim/engine/proto/saveload.py` is the authoritative list of
which fields this applies to.

---

## 4. Proving it changed nothing

This is a refactor whose entire claim is that behaviour is identical, so the
proof matters more than the diff.

1. `python3 sim/test_regressions.py` - 1608 checks, 0 failures.
2. `python3 sim/perf_fingerprint.py record` before, `check` after, byte
   identical across all nine reference scenarios.
3. Save/load round trip: a save written before the change loads after it, and
   a field absent before is still absent after.
4. Timing from `perf_fingerprint`'s own per-scenario CPU numbers, to confirm
   the 1.7x lookup cost does not show up as a wall-clock regression.

**Step 2 cannot be done yet.** `perf_fingerprint.py` does not currently
reproduce its own recording - see
`Complaints/27-nondeterministic-simulation.md`. The determinism bug is being
fixed first, and this extraction does not land until a clean `check` means
something. The suite alone is explicitly not a substitute; that is what
`sim/ARCHITECTURE.md` says and it is why that warning exists.

---

## 5. What this is not

It is not the decomposition `sim/ARCHITECTURE.md` considered and rejected.
That one meant giving all 157 fields explicit owners and converting ~200
implicit `self.x` couplings into arguments - a rewrite of most of 30,000
lines, for a payoff the note correctly called small.

This moves one coherent group of fields onto one object and changes
`self.capital` to `self.household.capital`. It is textual, it is checkable a
line at a time, and it buys the actor axis, which the rejected refactor did
not.

The coupling between money, labour and projects stays exactly where it is.
That coupling is the domain, not an accident, and moving it around would not
remove it.
