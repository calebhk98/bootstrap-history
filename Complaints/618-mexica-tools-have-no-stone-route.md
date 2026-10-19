# The implements need lists only metals, and obsidian blades have no recipe, good or knapper

**Status:** open

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

**What is wrong.** `mat_obsidian_blade` is a tree node with no recipe, no obsidian good and no knapper trade. The `implements_and_arms` need lists only metals, so Mexica tools have no stone route. Whether Mexica households can buy the metals was not checked.

**Evidence.** `data/branches/00_core.json`; `data/world/needs.json`.

**Why it matters.** A stone-using society cannot be modelled.

**What it would take.** Check first whether Mexica households can buy the metals. Then add an obsidian and flint good, a knapper trade, a recipe for the node, and a stone route in the implements need.

**Test.** `validate` passes; a test: a Mexica household can meet the implements need from stone.
