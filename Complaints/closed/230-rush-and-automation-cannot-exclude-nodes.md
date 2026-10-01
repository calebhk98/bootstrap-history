# `rush`, `rush preview` and the automatic policies cannot exclude a node or a category the player will not do

**Status:** closed

`rush preview` ranked `freedman_staff` (buy, train, release people) among the best starts more than once; the tester, who never buys people, had to screen the list by hand every time and never
used the automatic `rush`. `help rush` lists `limit:` and `max_total_cost:` and nothing for excluding ids, categories or policies. The same gap applies to `auto_commission` and `auto_open`, which cannot be told
which concerns are off limits or must be kept.

What it would take: a persistent exclusion list (ids, categories, or "anything that buys people") honoured by `rush`, `rush preview` and the automatic policies, with the reason shown in the preview.
Related: 180 (goal-directed automation), closed 77 (rush fiscal controls).

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 113, 190). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.

**Fixed:** `exclude` / `include` keep a saved list of ids, `category:<cat>` and `trait:<trait>`; `rush`, `rush preview` (under `excluded`, with the reason), `auto_open` and `auto_commission` honour it; `policy` shows it. A hand `start` is unaffected.
