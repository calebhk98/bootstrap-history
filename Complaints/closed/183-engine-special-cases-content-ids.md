# The engine special-cases content ids

**Status:** closed - node ids moved onto each node's `mechanics` field (data/branches/MECHANICS.md); pinned by sim/tests/test_engine_content_ids.py

Examples: `sim/engine/core_step_phases.py:1754` `if self.running("sanitation_antisepsis")`; `sim/engine/projects_capability.py:54,70` keyed text for `corpus_dispersed`, `sanitation_antisepsis`; `sim/engine/fog.py:335` `hedge == "corpus_dispersed"`; `sim/engine/cli.py:1144-1148` a list of ids (`corpus_written`, `patron_imperial`, `citizenship`, `telegraph_electric`, ...). The code inventory also reports a hardcoded list of disease-burden tech ids in `engine/core.py`.

This conflicts with CLAUDE.md 4.7 ("No `if civ == \"rome\"`, no `if node == \"steam_engine\"`"), and means a mod renaming or replacing those nodes silently loses the effect.

What it would take: move each effect onto a data field on the node (e.g. an `effects`/`capability` block), and read that in the engine.

Found by a code inventory made for the new-player playtest (`playtest_notes/code_systems_inventory.md`); each claim below was re-checked by grep.

Related: `Complaints/131`, `132` (engine names civilisation ids); this issue is the same pattern for technology node ids.
