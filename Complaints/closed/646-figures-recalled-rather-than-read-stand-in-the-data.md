# Figures recalled rather than read stand in the data and the constants

**Status:** closed - an umbrella whose passes sourced what could be found; the rest is split by domain into 650, 656, 669, 670 and 671 (and 619, 607)

Owner direction (2026-10-20): a figure needs a source someone read; "recalled" is not a source. The data and the declared
constants carried many figures marked as recalled (confidence D), from the herd rows (532) to the savings constants (606). The
rule for new work is in CLAUDE.md section 6; research agents follow it too: every claim cites a source opened in that session.

**Why it closes.** The word "recalled" is nearly gone from the data (`grep -rn "recalled" data sim --include=*.json --include=*.py`
lists what is left, mostly deposit and civilisation notes and test docstrings), and what stays is not a recall problem but a list of
figures with no source found, each a labelled heuristic or a confidence-D entry. An audit with no end is not an issue; each
domain has its own list and its own research question.

**Where the remainder lives.**

| Remaining work | Complaint |
|---|---|
| Stone tool figures (hours per blade, knapper years, blade life) and the wooden tool's other figures | 650 |
| Wine, oil and jar figures (press, jar, stand years, yields) | 656 |
| Disease figures, civilisation starting figures (grade D), three deposit entries | 669 |
| Service lives, livestock, spoilage, household needs, soil nitrogen, the three-field legume share | 670 |
| Production recipe rows at `"conf": "D"` | 671 |
| Plausibility bands of the occupational distribution (`data/world/occupation_groups.json`, "Recalled" entries) | 619 |
| Savings and time-preference constants (`households_orders.py`) | 607 |
| Land-concentration bands in `sim/tests/test_economy_land_concentration.py` (recalled, not looked up) | 538 |

Some `retire` fields still read `Complaints/646` (`sim/geography/soil_nutrients.py`, `data/world/service_lives.json`); they
mean the lists above.

**What the passes did** (full text, with the passages and file:line of each change, in `Complaints/reports/646-history.md`).

1. Herds, soil and savings constants, needs: NRCS Agricultural Waste Management Field Handbook, FAO traditional-systems
   ruminant parameters, Oregon State Extension, Bernheim on saving, National Academies and WHO for salt and water.
2. Production rows, spoilage, waste heaps, trades: Varro (one shepherd to a hundred sheep), Frontinus, Cato, Rose et al. 2015,
   Clemson on bread.
3. Needs and soil: Powles et al. 2013 for salt, Clay and Carlson for grain nitrogen, Nelson on vessel life.
4. Disease files and civilisation starts: WHO plague fact sheet, Mordecai et al. 2013 for malaria, CDC for smallpox.
5. Shelter satiation (Naroll 1962; Brown 1987), ox service life (Langdon via Medievalists.net), and the finding that wheat
   labour was far below the sources.
6. Wheat labour built from sub-tasks in `data/world/farm_labour.json` (`sim/world/farm_labour.py`), first from White 1965 as
   quoted in Shukurov et al. (secondary).
7. Columella 2.12.1 and 2.9.1 read in the primary: wheat labour and the hectare conversion now follow his days per iugerum
   (`python3 -c "from sim.world import farm_labour; print(farm_labour.WHEAT_HOURS_PER_HECTARE, farm_labour.WHEAT_HOE_HOURS_PER_HECTARE)"`).
   The earlier passes' wheat figures were superseded by this one.

Tests: `sim/tests/test_recalled_figures_sourced.py`, `sim/tests/test_farm_labour.py`.
