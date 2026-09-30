# Rome data: `mat_copper` is blocked on `blast_furnace`; Rome starts without `mat_pozzolana` (and with `sea_harbours_pozzolana` unstarted)

**Status:** open

Two contradictions in the Rome start, both checked in data:

- `mat_copper` ("Copper (fire refined)") has `pre: ['blast_furnace', 'cap_heat_1100']` in `data/tech_tree.json` while Rome smelted copper for centuries and starts with `mat_bronze` and `mat_brass`. The early copper-iron brine cell in the tree uses copper too, so the tester could not make it before the blast furnace (133 AD in their run).
- Rome's `starting_techs` (`data/civilizations/rome_100ad.json`) contain neither `mat_pozzolana` (prerequisite only `mat_lime`, cost 250 capital, 50 hours) nor the zero-cost `sea_harbours_pozzolana`; the Rome introduction says "Concrete that sets under water". `civ_vault_barrel` and other Roman concrete-age works are held.

Why it matters: the copper chain is gated by a furnace rung the Roman metal trades did not need, and Rome buys back its own signature material as research. Related data problems in the same file: 127 (Rome holds iron, bronze and glass but not the furnace rung), 128 (no check that a start agrees with itself), 42 (pinned starting-tech violations).

What it would take: decide with the validator asked for in 128: either grant `mat_pozzolana` and `sea_harbours_pozzolana` and relax the copper prerequisite (fire refining does not need a blast furnace), or document why not; add a check that a civilisation's briefing claims match `starting_techs`.


Found in the final blind playtests of this branch (Rome 100 AD fog, won 301 AD; tree and history section). Reports: `Complaints/reports/playtest-rome-fog-demo-65pct.md`; triage: `Complaints/reports/final-playtests-triage.md`.
