# An "imperial edict" is a free starting option in England 1300, and taking it silently raises scandal

**Status:** open

`med_legal_physician` ("Imperial edict: physicians who follow established methods are not liable for death") is offered in England 1300 at zero cost, zero hours, zero risk, no prerequisites. The tester found it contextually wrong for Edward I's England and took it only because it was free.

New finding on reproduction: taking it also raises scandal, and neither `why` nor the start message says so. Starting only `med_ligature_haemostasis` and stepping one year leaves scandal at zero; starting `med_legal_physician` as well gives a scandal of 5.8 the next year (the tester saw the same 5.8 and "did not expect" it). `why med_legal_physician` lists no downside.

Reproduces on the current branch:

    printf 'why med_legal_physician\nstart med_legal_physician\nstart med_ligature_haemostasis\nstep 1\nstate\nquit\n' | python3 sim/simulator.py play --civ england_1300 --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

What it would take: civilisation-specific wording or a per-civilisation variant of generic institutional nodes (the mechanic is a legal privilege for physicians; the flavour text names Rome); and `why` showing standing effects (scandal, reputation) before the player commits, even when the price is zero. Related: 136 (the game assumes Rome exists), 42 (starting state breaks the tree), 132 (descriptions).

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.
