# A saved and resumed run diverges from an unbroken one

**Status:** open

Rome 100 AD seed 1, events on, fog off, stepped year by year with a digest of the simulation state after each year (the digest in `sim/perf_fingerprint.py`). A run that is saved and loaded at some year (`save_state` then `load_state` into a freshly built `Sim`) has a different digest from the unbroken run from the first year after the load, in the late game (found around AD 217). Two resumed runs that stop and resume at the same years agree with each other, so the difference is the round trip, not nondeterminism. Rule 4.6 of CLAUDE.md requires a save to round-trip within a build; a `--session` game does this every command.

Why it matters: every `--session` game is a chain of save and load, so it plays a different game from the one a single process would; any measurement made across a resume is not comparable with one made without.

What it would take: stop an unbroken run and a saved-and-reloaded copy at the same year, step both once, and diff the state field by field to find which field is not carried (a cache that decides a result, or a field outside the save's field list). Reproduce with any script that builds `perf_fingerprint.build(dict(civ="rome_100ad", seed=1, years=300, events=True, fog=False))`, steps to the late 100s, saves, loads and compares. Related: 396 (the determinism guard cannot see hidden carried state).
