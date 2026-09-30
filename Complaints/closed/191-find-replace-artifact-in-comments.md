# Comments name a non-existent path `sim/world/self._demography.py`

**Status:** closed - replaced incorrect paths in sim/engine/core.py (3 instances)

`sim/engine/core.py:351`, `:701`, `:761` refer to "sim/world/self._demography.py", which looks like a find-and-replace of `_demography` applied to prose. The real module is `sim/world/demography.py`. The inventory reports the same pattern for agriculture.

What it would take: `grep -rn "sim/world/self\._" sim` and restore the paths.

Found by a code inventory made for the new-player playtest (`playtest_notes/code_systems_inventory.md`); each claim below was re-checked by grep.
