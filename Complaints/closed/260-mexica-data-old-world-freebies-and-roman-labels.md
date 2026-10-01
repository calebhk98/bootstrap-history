# Mexica data: 96 zero-cost Old World nodes are startable at 1500 (draught power, coin, brass, olive oil, silk, wheels, sleeping car) and Roman labels remain

**Status:** closed

The civilisation text says the Mexica have "no draught animals, no iron, no wheel in practical use". The data disagree. The tree holds 144 nodes with no cost at all (`cap`, `ph`, `lab`, `mat` and `yrs` all zero); Rome starts with most of them as inherited techs, every other civilisation gets the ones it does not list as instant free starts. Measured (prerequisites met by the start or by another free node; script below):

    python3 - <<'EOF'
    import json
    t = json.load(open("data/tech_tree.json")); nodes = {n["id"]: n for n in t["nodes"]}
    free = [i for i, n in nodes.items() if not (n["cap"] or n["ph"] or n["lab"] or n["mat"] or n["yrs"])]
    st = set(json.load(open("data/civilizations/mexica_1500.json"))["starting_techs"])
    print(len([i for i in free if i not in st and all(p in st or p in free for p in nodes[i]["pre"])]))
    EOF

prints 96 for `mexica_1500` (28 for Han, 16 for England, 37 for Norse, 3 for Rome). In a Mexica game `available all` lists at cost 0: `cap_power_muscle` (draught-animal power), `fin_coined_money`, `mat_brass`, `mat_olive_oil`, `mat_silk`, `clock_mechanical_escapement` (see 262), and the same script lists the other Old World items (`lnd_four_wheel_cart`, `lnd_two_wheel_cart`, `lnd_wheel_spoked`, `lnd_tyre_iron`, `lnd_ox_transport`, `lnd_mule_transport`, `mat_wrought_iron`, `mat_bronze`, `hom_public_bath`, `prn_codex_bound` and more). `tr_sleeping_car` has no prerequisites at all (`pre` empty) and needs only two artisans, so a railway car is startable in a society without the wheel. `med_vaccination_progression` is gated on `germ_theory` only and is named for cowpox vaccination although the civilisation has no cattle (variolation is the plausible Mexica route; the name may only need changing).

Roman labels: `school_founded` is named "Found the school (the Museum)" in `data/branches/00_core.json` and shown unchanged in a Mexica game (`why school_founded`); the civilisation's `local_words` table (`data/civilizations/mexica_1500.json`) rewrites only a handful of phrases. A reported "denarii" in invasion-hedge costs did not reproduce in `risk` or the step log (the reply layer rewrites "denarii" to "beans"); hard-coded "denarii" strings remain in `sim/engine/proto/dispatch_inspection.py`, `dispatch_money.py` and `dispatch_ventures.py` and show only if some path bypasses that rewrite.

Why it matters: a good deal of the Mexica scenario's texture (the tester's favourite part) is undone by free wheels, brass and coin; it also removes the scenario's constraint (no draught animals) that the civilisation data otherwise set up.

What it would take: per civilisation, mark which free nodes are inherited by the start and which are not obtainable at all (a "not available here" list), or make the free nodes cost what they cost from scratch outside the region that has them; rename the school and localise the remaining Roman words. Related: 231 (same for Han), 128, 42 (pinned), 136, 235.


Found in the final blind playtests of this branch (three mortal fog Mexica 1500 runs; C civ data problems and bug 6; counts measured by script). Reports: `Complaints/reports/playtest-mexica-1500-mortal-three-runs.md`; triage: `Complaints/reports/final-playtests-triage.md`.


**Resolution:** the words for a civilisation's money are the `currency_words` field of its own file (`sim/engine/data.py` holds no per-currency table); the reply layer rewrites the book unit with them. The vaccination node is already named neutrally (variolation to attenuated vaccines). Offline analysis tables (`cli.py`, `cli_analysis.py`) still print the book unit, which they do not convert.
