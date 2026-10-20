# The implements need lists only metals, and obsidian blades have no recipe, good or knapper

**Status:** closed - stone route added; unsourced figures are labelled heuristics in 650

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

**What is wrong.** `mat_obsidian_blade` is a tree node with no recipe, no obsidian good and no knapper trade. The `implements_and_arms` need lists only metals, so Mexica tools have no stone route. Whether Mexica households can buy the metals was not checked.

**Evidence.** `data/branches/00_core.json`; `data/world/needs.json`.

**Why it matters.** A stone-using society cannot be modelled.

**What it would take.** Check first whether Mexica households can buy the metals. Then add an obsidian and flint good, a knapper trade, a recipe for the node, and a stone route in the implements need.

**Test.** `validate` passes; a test: a Mexica household can meet the implements need from stone.

## Resolution

Metals check (Mexica 1500): iron, steel, cast iron and brass are gated on nodes it does not hold. `bronze_kg` is gated on `mat_bronze` (held) but needs `tin_kg`, gated on `mat_tin`, which sits under the "Old World goods" `needs_first` block, and no enabled partner trades in 1500. So no implement metal can be made: the old basket check passed because it reads only a recipe's own gate, not its inputs's gates.

Added: `obsidian_kg`, `flint_kg`, `obsidian_blade_kg` (gated on `mat_obsidian_blade`) and `flint_tool_kg` in `data/production/96_stone_tools.json`; the `knapper` trade; both tool goods in the implements need; a declared unsupplied reason for blades in the Han file (the only start without the node). Sourced: 91 percent of a preformed core leaves as blades, 83 blades from 820 g (Sheets and Muto 1972, read at https://vivo.colorado.edu/display/pubid_69138). Hours, tool life and training: no source found, labelled heuristics, Complaint 650. Test: `sim/tests/test_stone_tools_route.py` (calls the basket pricing and reads the recipe; no Mexica game).
