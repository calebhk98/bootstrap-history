# Change checklist

The mistakes below each came back round after round in the economy and labour cleanup (Complaint 964). Every
agent that edits code reads this before starting and confirms each point that applies in its report. Each point
says what went wrong and what to do instead.

## When you change what a function returns or raises

A function that used to return a number and now returns `None`, a `Refusal`, or raises: every caller that does
arithmetic or comparison on the old value breaks, usually somewhere far away.

- Before committing, grep every caller of the function, in all of `sim/`, `tools/` and `sim/tests/`, including
  calls through an api re-export, a view, a protocol method or a forwarder of the same name.
- For each caller, say what it does with the new value. If it is outside your files, hand the exact edit back.
- A `Refusal` is a `str`: `refusal > 0.0` raises, `if refusal:` is true. Test with `isinstance`.

## When you move or rename a name

- Move every importer too (CLAUDE.md "moving a helper moves its importers"). Grep `sim/`, `tools/`,
  `sim/tests/`, `mods/` and `docs/`.
- Do not leave a re-export or facade behind so old imports keep working; that is a second path to the name.
- Fix every comment, docstring and doc that cites the old location.

## Before you declare a constant or a rule

- Grep for the value and for its meaning first. If another module already holds the same fact (the same
  ceiling, the same separator, the same default), import it from its one owner; do not copy it.
- A new heuristic is `declare(..., kind="temporary_heuristic", retire=...)`. A moved one keeps its `retire`.

## Content ids

- Never write a trade, good, need or civilisation id in engine code (CLAUDE.md 4.7), including as a dataclass
  default or a fallback. Read the trade registry's role (`trade_of_role`) or the labour package's accessors
  (`scholar_trade`, `generic_craft_trade` and the like); if no role fits, add one to the data.
- Labelled transitional defaults live only in `sim/labour/legacy_trade_defaults.py`.

## Making a rule strict

Turning "skip when missing" into "error when missing" exposes every second source of the same fact (a raw data
file read beside the mod-applied registry, a default beside the port's value). Before making it strict, find every
place that supplies the fact and make them one.

## Money

- Setup opening prices and opening wages are in opening-year money. Read them in today's money through
  `opening_price_today` or the memory's `opening_wage_level`.
- A missing price or wage is `None`, never `0.0`.

## Caches

- Key a cache on everything the answer depends on. A setup's `tile_owners` is the live map the land module edits;
  the held tiles change mid-game.
- No process-global cache over state that can change, or whose iteration order depends on history.

## Imports

- `tools/check_imports_alone.py` (in `done_check`) imports every module in its own process; keep it green.
- Break a cycle by moving the shared name to its true owner or a leaf module, not by a call-time import.

## Test stand-ins

Tests build fake records, views and worlds (`type("Record", (), {...})`, `SimpleNamespace`, stub classes). When
code starts reading a new field or method, grep the tests for stand-ins of that object and add it, then run those
test topics.

## Classes and attributes

- Never reuse an existing class name for a new class in another module (`tools/check_class_names.py`).
- No `getattr(obj, "name", default)` probe for a field that always exists; read it.

## Before you report

- `python3 -m pyflakes` on every file you changed, `bash tools/done_check.sh`, `python3 sim/simulator.py validate`.
- Run the quick test tier (`python3 -m sim.tests`); it is fast and catches the callers and stand-ins far from your
  files that a few targeted topics miss. Compare against `origin/main`: a topic that passes there and fails on your
  branch is yours.
- Diff your branch and check every claim in your report is in it.
