# An opened Rome game holds almost no smiths, so smith work is refused for want of people

**Status:** closed - an opened Rome game with the full spin-up holds smiths in the thousands and `start horse_collar` succeeds

**What was wrong.** In an opened `rome_100ad` game the labour core's people of the smith trade read about a thousandth of a
person, against tens of thousands in an unopened game, so `start horse_collar` was refused with cause `people_exist` ("no
one left to do the smith work"). Measure: `national_trade_population("smith")` (labour api) on `sim(civ="rome_100ad")`
against `unopened_sim(civ="rome_100ad")`. Why it mattered: a trade the opening empties cannot be hired, so whole branches of
the tree were refused at the start, and 533 stage 2 made farms buy iron tools that smiths make.

**Causes found and fixed.**

1. A missing tool stopped the work. 533 stage 2 made worker tool wear a recipe input, so almost every recipe used iron tools,
   and `limited_goods` held nearly the whole economy to the iron deposits. A trade's `tool_basket`
   (`data/world/trades.json`; `tool_hours_factor`, `tool_hours_factor_by_hand`) is now an ordered list: the first good a
   recipe in the society makes is the tool, each later one is a `ToolFallback` on the recipe (`Recipe.tool_fallbacks`, built
   by `with_tool_wear`), then the work is done by hand (`sim/economy/tool_fallback.py`). A tool is no longer in
   `Recipe.hard_inputs`, so the opening's ceilings, `limited_goods`, `fit_to_supply` and entry sizing do not read it. New good
   `wooden_tools_kg` (`data/production/96_wooden_tools.json`; service life in `data/world/service_lives.json`).
2. `opening._add_producers` skipped a second share of runs on a tile that already held the producer, so the pooled share of the
   areas with no site of their own was dropped and the ore was placed at a tenth of the runs the smelters needed. It now adds
   the share. The sited iron room itself was measured and is right (the data's historical rates, `deposit_history.py`;
   `data/world/resources.json`, Craddock 2008 p. 108 as quoted in Poehler et al. 2019, read), and a test pins it.
3. `labour_state.plot_trade` skipped every land recipe with an input, so with tools as inputs the plot trade became `herder`
   instead of `farmer`. It now ignores inputs that are tool wear, as `households_own.own_production_options` does.

Tests: `sim/tests/test_complaint_659_tool_fallback_and_site_room.py`, `test_complaint_659_makeable_price_without_tool.py`,
`test_opening_workforce_follows_hours.py`. The step-by-step findings and before/after opening volumes are in
`Complaints/reports/659-history.md`.

**Measured.** Measured 2026-10-21 on main 3cb9c9a0, an opened Rome game with the full spin-up: from a checkout root, `from sim.tests import harness; import os; os.environ.pop("ROME_SPIN_UP_YEARS", None); game = harness.sim(capital=1e7)`, then the reads named below. `game.labour.national_trade_population("smith")` reads in the thousands (against about a thousandth before the fix), and `_agent_dispatch(game, NODES, {"cmd": "start", "id": "horse_collar"})` returns ok.

**Left elsewhere.** Sources for the wooden
tool: the by-hand-versus-wooden hours factor is sourced (Semyonov 1974 via Shukurov et al., `sim/tests/test_tool_hours_sourced.py`;
see 650 and `Complaints/reports/research-stone-and-wooden-tools.md`); wood per tonne, carpenter hours, the stock per worker, the
by-hand factor and the service life of a wooden tool are labelled heuristics with `retire` naming this complaint (no source
found). They are tracked with the other service lives in 670 and the tool figures in 650.
