# Project and goods prices still come from `data/prices.json`; the price solver is off by default

**Status:** open

`sim/engine/data.py:320` `def load(use_solved_prices: bool = False, ...)`; the docstring says it "remains off by default for legacy content". No non-test caller passes `use_solved_prices=True` (`grep -rnE "use_solved_prices\s*=\s*True" sim --include=*.py | grep -v tests` is empty). So play and the CLI price nodes from `data/prices.json` (`data.py:107`), with the solver filling only materials the book lacks.

This conflicts with CLAUDE.md 4.5 ("Prices are calculated, not looked up"; `prices.json` "is being deleted"). It is also a likely cause of complaint 151: project material costs disagree with the market prices `materials` shows.

What it would take: switch play onto solved prices behind `perf_fingerprint.py` checks, then remove the book reads.

Found by a code inventory made for the new-player playtest (`playtest_notes/code_systems_inventory.md`); each claim below was re-checked by grep.

Related: `Complaints/123` (the exit checklist for making solved prices the default, per `docs/architecture/STATE_OF_THE_PROJECT.md`); this issue adds the player-visible symptom (151).

Stakeholder decision: yes; delete `data/prices.json` as soon as possible. Sequence with 151 (projects price materials from the market) and the exit checklist in 123.

Also reported (final playtests, A; `Complaints/reports/final-playtests-triage.md`): `python3 sim/simulator.py validate` passes with one warning, reproduced: `el2_inductor_ferrite_core: material ferrite_kg has a production entry but no solved price (cost is a lower bound)`.
