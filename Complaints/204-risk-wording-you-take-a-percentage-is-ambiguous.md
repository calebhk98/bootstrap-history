# `risk` says "you take 80% of it" and "staff loss: you take 100% of it"; the reading is ambiguous

**Status:** open

Hazard lines read "output factor: you take 80% of it (softened by ...)" and "staff loss: you take 100% of it". The tester could not tell whether the percentage is the output retained, the share of the penalty suffered, or something else; the war event text "trade and output fall to 88% of normal" was clear by contrast. (In the tester's run the line said 58 percent.)

Reproduces on the current branch:

    printf 'step 10\nrisk\nquit\n' | python3 sim/simulator.py play --civ england_1300 --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

The text comes from `sim/engine/proto/render_screens_status.py` (`"%s%s: you take %s of it"`). What it would take: say "output falls to 80% of normal" for the output factor and "you lose N% of your staff in a wave" for staff loss, using the wording the event message already uses.

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 45; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): "Output factor: you take 100% of it" (Han, regency crisis) was read as a report of exposure; the event later said output fell to 94 percent. The tester wants severity and mitigation shown together before the event. Reproduces: untested (needs the dated event).

Also reported (final playtests, C; `Complaints/reports/final-playtests-triage.md`): the Mexica invasion risk text should say what the design intent is ("you cannot stop the conquest, only protect what you know"), if that is the design, and show how much each hedge moves the chance (the tester's best reached 66% a year); see 270.
