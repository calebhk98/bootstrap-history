# The stone tool route's hours, tool life and deposits have no source

**Status:** open - mostly sourced (third pass, see **Sourced figures** below); left: the blade and flint tool service lives against bronze (`data/world/needs.json`, one edge-loss datum found, no life), the mass lost preforming raw obsidian nodules into cores, deposit placement on the map, and the wooden tool's figures (no timed or weighed source found)

Follow-up to Complaint 618. `data/production/96_stone_tools.json`, the `knapper` trade and the `obsidian_blade_kg` and `flint_tool_kg` entries in `data/world/needs.json` carry labelled heuristics (confidence D, `retire` naming this complaint): hours per blade, hours per tonne of obsidian and flint dug, finished flint tool mass per kilogram of flint, knapper training years, the implements effectiveness of a kilogram of blades or flint tools against bronze (blade service life), and the mass lost preforming raw nodules into cores. No source for these was found in a search of Sheets and Muto 1972, Clark's Ojo de Agua workshop estimate and Parry's Aztec city-state study (abstracts only; the full texts are paywalled). Obsidian and flint have no placed deposits, so any civilisation can quarry them.

The wooden-tool hours factor (Complaint 659) is sourced and out of this list (Semyonov 1974 via Shukurov et al., `sim/tests/test_tool_hours_sourced.py`). The wooden tool's other figures (wood per tonne, carpenter hours, stock per worker, the by-hand factor, service life) are still labelled heuristics with `retire` naming 659; the wooden tool's service life is in `data/world/service_lives.json` (a labelled heuristic, searched in the 650 pass; no complaint 701 exists), and the obsidian blade's and flint tool's lives are in `data/world/needs.json`.

**Research needed.** For each figure a source opened in the session (CLAUDE.md section 6): the lithic literature on hours per blade and per core (Clark on Ojo de Agua, Titmus and Woods, the Mesoamerican Lithic Technology volume), experimental replication studies for knapping and quarrying rates, and a use-wear study for blade life.

**What it would take.** Open Clark 1982 or 1989, Titmus and Woods, or the Mesoamerican Lithic Technology volume for hours per blade and per core; a use-wear study for blade life; place obsidian and flint deposits on the map.

**Test.** `sim/tests/test_stone_tools_route.py` keeps the retire fields; replace each heuristic with a quoted figure.


## Sourced figures (third pass)

| Figure | Old | New | Source (opened this pass) |
|---|---|---|---|
| `flint_kg` labour, hours per tonne | 20 | 280 (conf C) | https://en.wikipedia.org/wiki/Grime%27s_Graves : "more than 2,000 tonnes of chalk ... taking 20 men around five months"; "medium-depth shafts yielded as much as 60 tons of flint". 20 x 5 months x 21 days x 8 h = 16,800 h / 60 t. A deep-mine ceiling. |
| `obsidian_kg` labour | 20 | 280 (conf C) | Same figure by analogy; no obsidian-specific rate found (searches on Sierra de las Navajas, Chivay, experimental quarrying). |
| `obsidian_blade_kg` labour | 4600 | 2200 (conf C) | Clark, Ancient Mesoamerica 8, abstract (https://www.cambridge.org/core/journals/ancient-mesoamerica/article/prismatic-blademaking-craftsmanship-and-production/4DE4B3F54E0E94388CDDD6D11FD7AF52): 26,000 blades a year = three months of part-time work; 26,000 / 110 per kg = 236 kg; 520 h / 0.236 t. Floor 1100 h from Clavijero via Clark 1979. |
| `obsidian_blade_kg` mass | 1099 kg per tonne | unchanged | Sheets and Muto 1972 (https://vivo.colorado.edu/display/pubid_69138), 91 percent. |
| `flint_tool_kg` flint per tonne | 3000 | 5000 | Finkel and Gopher 2018, Lithic Technology 43(3), PDF: "a weight ratio of 1:4 between end product and knapping waste (or 80 per cent waste)". Putt et al. (https://pmc.ncbi.nlm.nih.gov/articles/PMC4938430, Table 5): 94.8 percent lost for handaxe cores. |
| `flint_tool_kg` knapper hours | 3000 | 900 (conf C) | https://en.wikipedia.org/wiki/Hand_axe : "less than 15 minutes"; forum quoting David Miles, 20 minutes; 0.33 h / 0.364 kg (Putt et al. Table 5). |
| `knapper` training years | 3 (D) | 3, sourced | https://mayan.org/civilization/obsidian/ : "2-5 years of practice" (secondary page). |
| obsidian blade edge life | D | D, datum added | https://makingflakes.blogspot.com/2013/12/unused-obsidian-knife-hi-all-images.html : one rabbit cost 37.6 percent of the edge. The 0.05 effectiveness is still a judgement. |

Tried and not found: hours to quarry obsidian (no experimental rate), Ramat Tamar experiment (Barkai et al. 2007, not openable), Hansen and Madsen 1983 timings (core.ac.uk returned 403), flint tool life, wooden spade making time (Danish spade abstract has no hours; shop listings give only steel spade weights). Deposit placement skipped: `data/world/resources.json` is national output ceilings, not map deposits.
