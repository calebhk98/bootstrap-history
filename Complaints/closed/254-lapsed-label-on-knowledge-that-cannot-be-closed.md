# Epidemic reports say "lapsed: Germ theory of disease is closed" for knowledge that cannot be closed or opened

**Status:** closed

Every epidemic year in all three Mexica runs listed "lapsed: Germ theory of disease is closed" and "lapsed: Silage and the silo is closed"; `open germ_theory` answers "that is knowledge, not a going concern". Closed 178 (merged into 165) and 202 were about naming the concern to reopen; this is a wrong label.

Cause: `hazard_relief` (`sim/engine/society_hazards.py`) labels a counter "lapsed" whenever its strength is between 0 and 1. With `beyond_national=True` (used by `_shock_staff_loss`) the strength is multiplied by `1 - civ_diffusion(node)`, so a counter that is running at full strength but is partly adopted nationally also falls under 1 and gets the lapsed label. Reproduced (harness, Mexica, `germ_theory` done as knowledge, `civ_diffusion` set to 0.4): `hazard_relief("staff_loss")` gives no note, `hazard_relief("staff_loss", beyond_national=True)` gives "knowing what is actually killing them (lapsed: Germ theory of disease is closed)". `running("germ_theory")` is True and `is_venture` is False. Same for `ag2_silage_silo`.

Why it matters: it tells a player to reopen something that cannot be opened, and hides that the real effect is "the nation has adopted part of it".

What it would take: decide the label from `_counter_strength` before the national discount, and say "partly adopted nationally" for the discount; a test that a knowledge node never reads "closed". Related: 198, 165, 200.


Found in the final blind playtests of this branch (three mortal fog Mexica 1500 runs; C bug 4). Reports: `Complaints/reports/playtest-mexica-1500-mortal-three-runs.md`; triage: `Complaints/reports/final-playtests-triage.md`.
