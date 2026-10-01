# The save format carries a version stamp

**Status:** closed - stamp, version check and old-key branch removed

`sim/engine/proto/saveload.py:12` `SAVE_VERSION = 3`; `sim/engine/state.py:412` `_version: int = 3`, written at `:456`, checked at `:619` (`"_version" in blob or "household" in blob`).

CLAUDE.md 4.6: "no shim, no version stamp, no `if \"old_key\" in data`". The check at `state.py:619` is exactly an old-key test.

What it would take: remove the stamp and the old-format branch; keep the in-build round-trip test (and add one for a posted bounty, see 153).

Found by a code inventory made for the new-player playtest (`playtest_notes/code_systems_inventory.md`); each claim below was re-checked by grep.
