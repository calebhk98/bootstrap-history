# `school_founded` requires `freedman_staff`, so a player who declines to buy people has no route to the school

**Status:** closed

`school_founded` has `pre: ['arithmetic_positional', 'collegium_licensed', 'freedman_staff']` (`data/tech_tree.json`); `freedman_staff` is the buy, train and manumit route.
The tester set a personal goal of never owning or buying a person, so the school, and every institution whose hidden prerequisite it is (academy, journal, doctorate), stayed closed for 300 years. They reached the literacy goal
through a lending library and movable type instead, which shows the game has other routes; the school itself has none that is paid labour.
(`buy school <trade> <n>`, a different thing, now works: closed 156.)

    python3 -c "import json;d={n['id']:n for n in json.load(open('data/tech_tree.json'))['nodes']};print(d['school_founded']['pre'])"

What it would take: an alternative prerequisite (paid teachers, stipends, a licensed guild, voluntary apprenticeship) that may cost more or train more slowly, as a `req_any` alternative to `freedman_staff`;
say in `why` what `freedman_staff` means for a player who would rather not. A request, not a defect in the coercion the setting contains. See also 230.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 75, 166, 213). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.

**Fixed:** `school_founded` takes a `technical_staff` group: `freedman_staff` or the new `paid_apprentice_staff` (masters and apprentices at market wages over a longer calendar; no purchase). `freedman_staff` carries the trait `buys_people`, so `exclude trait:buys_people` keeps it out of automation. Test: `sim/tests/test_player_choice_routes.py`.
