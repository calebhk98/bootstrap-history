# `ventures` says machinists are scholars and cannot watch a workshop; `labour` says a machinist is craft

**Status:** open

In a new Han game, `ventures` prints "Engineers, chemists and machinists are scholars here, and a scholar cannot watch a workshop. 'labour <trade>' says which of the two a trade is."
`labour machinist` answers "TRADE: machinist (craft)"; `labour engineer` and `labour chemist` answer "(scholar)". After the tester trained two machinists the craft count rose, as `labour` said, and
the machinists could supervise workshops, so the `ventures` sentence is wrong for one of the three trades it names. The tester also found that trained and hired staff are counted differently by the prompt's scholar number (scribes and engineers missing) and by `labour`.

    printf 'ventures\nlabour machinist\nlabour engineer\nquit\n' | python3 sim/simulator.py play --civ han_china_100ad --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

What it would take: generate the sentence from the trade table (list only the trades whose type is scholar); say once whether the prompt's `sch`/`art` counts include hired specialists. Replayed: yes (the contradiction is visible in the first two replies).

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 56). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.
