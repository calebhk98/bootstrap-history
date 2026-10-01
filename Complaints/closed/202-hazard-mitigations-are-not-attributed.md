# Hazard relief is not attributed: national public health, each mitigation's share, and why one lapsed

**Status:** closed

Three faces of one gap, all from the plague and famine screens:

- The event says "the country's own public health has spread far enough to hold this below the 12% this would otherwise have been - 20% softer" (and 45 percent for the Black Death) without saying whether that is the English baseline, the player's discoveries diffusing, or passive drift. A player cannot tell whether their actions mattered.
- `risk` gives one total ("40 percent staff loss per wave") with no per-mitigation breakdown. After vector control, sanitation and a silo the tester could not tell whether vector control helped by 0, 2 or 20 percent before deciding whether to spend six figures on the next mitigation. Asked for: "silo -1.0 pp, vector control -X pp, sanitation -Y pp", or at least rough qualitative shares, plus the national-diffusion contribution and which discoveries feed it.
- In the 1349 event, "fields that do not fail together" and "fodder that keeps through a bad winter" were reported as lapsed. The current build names the closed concern ("lapsed: X is closed", `hazard_relief` in `sim/engine/society_hazards.py`, from closed complaint 182), but not why it closed (lost supervision after attrition, mothballed, loss-making, seized), so the player cannot tell what to fix. A closed concern also keeps a residual share of its relief, which the screen does not distinguish from full effect.

Reproduces by code reading (the messages are built in `society_hazards.py`); the per-mitigation breakdown is absent from `risk`, which shows one number per hazard:

    printf 'step 10\nrisk\nquit\n' | python3 sim/simulator.py play --civ england_1300 --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

What it would take: a per-hazard table of active mitigations with their share and status (in force, lapsed and why, residual), and an attribution clause for the national part. Related: 94 (timing), 97 (why did a number change), 182 (closed), 201, 203.

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 163; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): the tester read "(lapsed: X is closed)" on a risk line and tried to `open` the labelled hedge (smallpox vaccine, asepsis), which is knowledge and refuses ("that is knowledge, not a going concern"); the closed concern named in the parentheses is the one to reopen. The wording should say "reopen <id>" and name the hedge and the concern separately.
