# A patron's death cuts protection and adds scandal, protection is back the next year with no stated cause, and the scandal forecast treats the one-off jump as a yearly trend

**Status:** closed

Tester, six occurrences (173, 209, 246, 289, 328, 385 AD): protection falls by 30 to 37 points (61 to 37, 87 to 52, 92 to 55) and scandal rises by 4. The following arrival shows protection back at 62, 88 or 92 percent with no heir courted (173, 209) or
after `auto_court_heir` paid 1.5 million and still lost the points (246, 289). `state` then extrapolates the +4 jump into "crosses the scandal line in about six years". At 385 AD a manual `bribe` of 10 million restored scandal to 0 and protection to 92 percent, which the tester found by trying it; the help does not say `bribe` is the manual heir route
(the policy text says each automatic behaviour "can be done by hand instead").

Closed complaint 6 made the forced spend visible; this is the recovery and the forecast. Not replayed (needs a patron and a long game).

What it would take: one event line stating what recovered and why ("the office passed to the heir, protection restored at year end"), or the duration of the dip; do not extrapolate a one-time jump into a trend in `state`; name the manual command for each policy in `help policy`. Related: 198, 91.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 78, 105, 119, 148, 185). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.

Fixed: the death line says the dip lasts until the next year-end recount, when the office passes to the heir, names `bribe <amount>` as the by-hand route, and the policy and `help policy` text name it; the one-off scandal jump moves the year's starting mark so `state` no longer extrapolates it into a yearly trend.
