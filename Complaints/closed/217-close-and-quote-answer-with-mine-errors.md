# `close <concern>` and `quote <not a purchase>` answer with the mine parser's error instead of the right command

**Status:** closed

`close hom_button` answers "REFUSED: no such material: hom_button. well-known workings: coal, copper, ...". The command that
shuts a concern is `mothball`; `close` only shuts mines. The same message appears for `quote hire ...` and `quote open ...`.
The game's own advice says "close something" in several places (closure warnings, `stuck`), so the natural next
command fails with a message about minerals. The tester found `mothball` only by reading the help index.

    printf 'start hom_button\nstep\nopen hom_button\nclose hom_button\nquit\n' | python3 sim/simulator.py play --civ han_china_100ad --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

What it would take: when the argument is an id of a concern you own, `close` answers "that is a concern: use mothball <id>"
(or acts as an alias); `quote` refusals name the commands that do exist (`quote farm|housing|school|forest|nitre|material|mine`) and, for
`hire`/`open`, point at complaint 216's previews once they exist. Related closed complaints in the same class: 143, 152.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 76, 31). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.
