# There is no war: armies are a headcount with no units, location, quality or supply line

**Status:** open

- An army is one float per government (`record.army`; `budget.army_next_year` in
  `sim/agents/government.py` and `government_foreign.py`). No type, location, equipment, training,
  morale or quality, and so no decay of quality in long peace.
- `sim/world/military_logistics.py` models rations, fodder, water, pack-animal range and foraging, but
  its own docstring says the engine has no army location or campaign; the engine imports only the
  per-soldier iron and ammunition burden (`sim/engine/society_state_pressure.py`).
- No attack, battle, siege, blockade or naval action exists, and no phase for one in `run_year`
  (`sim/engine/year_run.py`). Rome's third-century crisis hazard lists "no neighbouring polity with an army
  is simulated" under `causes_not_modelled` (`data/civilizations/rome_100ad.json`).
- The navy is a wage line sized from coast length (`COAST_KM_PER_SHIP`, a labelled temporary heuristic in
  `sim/agents/tuning_spending.py`), not a fleet of ships (see 492).
- Nothing makes expansion stop at barriers or low-value land: there is no value of a frontier tile against
  the cost of holding it.

Why it matters: the group runs wars (an invasion that fails on terrain, a sea battle, steppe expansion,
an overstretched army months from supply) and needs outcomes to follow from terrain, supply and
logistics rather than be written in.

What it would take: an army record per actor with location, composition and quality; a conflict phase in
the year; supply reach from `military_logistics` over the route graph; terrain and disease modifiers from
the tile layers; ownership change on a won campaign (483). Each a separate step.
