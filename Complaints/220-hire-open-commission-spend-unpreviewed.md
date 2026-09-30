# `hire`, `open` and `commission` spend cash that is neither previewed nor itemised in the reply

**Status:** open

Three actions commit money the player was not shown first:

- `hire carpenter 1` charges the year's wage at once as an advance. The reply says "annual wage bill 355,925" and
  shows the new capital; capital fell by more than the balance the tester expected to keep. `quote hire carpenter 1` is
  refused with the mine parser's error ("no such material: 'hire'"), so there is no preview.
- `open <concern>` deducts an opening charge (toys about 20 thousand, bone setting about 1.8 thousand, buttons about 8 thousand in the
  tester's and replayed runs). The reply states revenue and upkeep and the new capital, not the charge; `why` does not show it;
  `ventures` shows "TO OPEN" only after the work is finished.
- `commission carpenter 500` (142,273) says only afterwards "These hours are available to your projects this year only".
  `help commission` says nothing about expiry or that commissioned hours cannot supervise a concern.

    printf 'start hom_toys_dolls\nstep\nlabour carpenter\nquote hire carpenter 1\nhire carpenter 1\nopen hom_toys_dolls\nquit\n' | python3 sim/simulator.py play --civ han_china_100ad --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

reproduces the refused quote, the unitemised advance and the unitemised opening charge (capital 258,428 before `open`, 238,290 after;
the reply never names the difference).

Why it matters: the first hire took the tester from positive cash to a debt they did not intend; the advance is correct
and explained later in `money`, but only after the fact. Complaint 166 (closed) made the three reopening prices consistent;
it did not add a preview or a line in the reply.

What it would take: `quote hire <trade> <n>` and `quote open <id>` (and `quote commission`) that do not mutate; one line in each reply
("paid now: advance X, fee Y; from next year Z a year"); a line in `why` for the opening charge; expiry and eligibility in `help commission`.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 15, 16, 19, 62). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.
