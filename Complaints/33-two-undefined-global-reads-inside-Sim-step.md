# `Sim.step` reads an undefined global `n` in two places

**Type:** Latent bug, engine
**Priority:** Medium. It cannot be hit by anything we currently run, which is exactly why it has survived.

## What is there

`sim/engine/core.py`, inside `Sim.step`:

```
1971:   if not any(_is_gone(t) for t in n["lab"]):
2438:   blocked = [t for t, want in n["lab"].items()
```

There is no module-level `n` in `core.py` and no builtin `n`. Both compile to
`LOAD_GLOBAL 'n'`. Reaching either line raises `NameError: name 'n' is not
defined`.

Found by disassembly rather than by reading, which is the point:

```python
step = <the code object for Sim.step>
[ins for ins in dis.get_instructions(step)
 if "LOAD_GLOBAL" in ins.opname and ins.argval == "n"]     # two hits
```

The set of `LOAD_GLOBAL` names in `Sim.step` that are neither module-level
nor builtin is exactly `['n']`.

## Why nothing has noticed

The suite is green at 1,670 checks and all nine `perf_fingerprint` scenarios
run to completion. So in every path we exercise, these two lines are dead.
They do not look dead. They sit in the engine's main tick, inside what reads
like ordinary guard logic about a node's labour requirements, and a reader
skimming for the reason a technology is blocked would believe them.

Dead code that looks live is worse than dead code that looks dead, because
the next person to change the surrounding logic will reason about it.

## How it surfaced

The round 3 naming sweep. An agent renaming locals in `core.py` bound these
two references to a real local, which removed `n` from `co_names`.
`prove_rename_safe.py` refused the file:

```
Sim.step: an ATTRIBUTE or GLOBAL changed, not a local - removed ['n'], added nothing
```

That is the prover doing exactly its job. The rename would have turned
"raises NameError" into "reads an actual node dict", which is a behaviour
change wearing a rename's clothes - and it would have gone in under a commit
message about naming, unreviewed. A second effect in the same function:
`year` moved from `co_varnames` to `co_cellvars`, meaning a nested scope
began closing over it, which is the scope-boundary form of NAMING_PLAN A.5's
third hazard.

This is the first time on this branch the bytecode proof has found something
the test suite could not. Worth recording on its own: the suite asserts on
outputs, and an unreachable line produces no output to assert on.

## What NOT to do

Do not fix it inside a naming commit. A locals-only rename sweep is the
wrong place for a behaviour change, and "the rename happens to make the line
work" is not a reason to believe the line is right.

## What to do

Work out what `n` was MEANT to be at each site before binding it to
anything. The two lines want a node record - the surrounding code is about a
node's `lab` requirements - so the likely history is a local that was renamed
or a loop that was restructured, leaving these behind. Establishing which,
and whether the guard they implement is still wanted at all, decides between
three different fixes: bind them correctly, delete them, or restore the loop
they belonged to.

Whichever it is, it needs its own commit, a regression test that reaches the
line, and a `perf_fingerprint` check - because if the guard starts firing,
behaviour changes.

## Related

`Complaints/31` is the other case where a tool refused something correct-
looking and was right. The pattern is the same: a checker that only accepts
what it can prove will sometimes reject a change that a reader is sure about,
and the rejection is worth reading rather than working around.
