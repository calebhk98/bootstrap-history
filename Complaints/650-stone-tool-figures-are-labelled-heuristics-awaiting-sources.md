# The stone tool route's hours, tool life and deposits have no source

**Status:** open (partly researched: see Complaints/reports/research-stone-and-wooden-tools.md. No stone figure gained a source; the wooden-tool hours factor of Complaint 659 did. Leads for the rest are listed there.)

Follow-up to Complaint 618. `data/production/96_stone_tools.json`, the `knapper` trade and the `obsidian_blade_kg` and `flint_tool_kg` entries in `data/world/needs.json` carry labelled heuristics (confidence D, `retire` naming this complaint): hours per blade, hours per tonne of obsidian and flint dug, finished flint tool mass per kilogram of flint, knapper training years, the implements effectiveness of a kilogram of blades or flint tools against bronze (blade service life), and the mass lost preforming raw nodules into cores. No source for these was found in a search of Sheets and Muto 1972, Clark's Ojo de Agua workshop estimate and Parry's Aztec city-state study (abstracts only; the full texts are paywalled). Obsidian and flint have no placed deposits, so any civilisation can quarry them.

**What it would take.** Open Clark 1982 or 1989, Titmus and Woods, or the Mesoamerican Lithic Technology volume for hours per blade and per core; a use-wear study for blade life; place obsidian and flint deposits on the map.

**Test.** `sim/tests/test_stone_tools_route.py` keeps the retire fields; replace each heuristic with a quoted figure.
