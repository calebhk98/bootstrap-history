# Starved or stuck situations do not name the advanced command that fixes them (first case: `allocate`)

**Status:** partly - a starved project's reason names `priority` and the allocation notice names `allocate`.

Starting the written corpus took all the founder-hours, so several small active projects got none. `portfolio` showed it, but neither `state` nor the starvation message suggested `allocate`. The tester found `allocate` only by reading `help commands` and calls it excellent once found. More generally they found the advanced layer (`materials`, `capacity`, `portfolio`, `bounty`, `commission`, `rush`, `mothball`) well layered but hard to discover: when a portfolio starves for founder-hours, materials, housing or a specialist trade, the normal output should point at the command that solves or diagnoses it. The "DIRECTED HOURS UNUSED" messages do mention `allocate` (for hours wasted), but the starved-project reason in `sim/engine/core_step_phases.py` ("hours before this one's turn came") carries no pointer.

Not replayed (needs several concurrent projects in a late game). What it would take: when a running project receives no founder-hours because higher-priority work took the pool, one line saying that `allocate <project> <hours>` reserves hours for it. More generally, each such shortage message carries one command hint (closed complaint 92 did this for material shortages). Related: 91 (closed), 101, 129.

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 77, 85, 97, 203; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): closure cascades, clinics left offline and oversized `allocate` orders were all handled by commands the tester learned late: `keep`, `reserve`, `policy auto_replace_foreman`, `mothball` (not `close`, see 221) and an `allocate` that wasted 540 hours on a 360-hour rework (they ask for an "up to the useful work" option). None of the closure or shortage messages names them. See 233.

Also reported (Han China 100 AD fog playtest, tester item(s) 33, 46; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): workforce advice also names the wrong size or the wrong person: the atomic-theory message said two scholars were needed and suggested `hire scholar 2` when one more reached two, and `state` repeatedly warned "no spare scholars, hire two" for an immortal founder who is the only scholar (the founder cannot leave; the warning should say the capacity is guaranteed and ask for the actual deficit).

Also reported (final playtests, B; `Complaints/reports/final-playtests-triage.md`): specialists (glassblowers, engineers, machinists) left almost every year 'to death and better offers', closing concerns, before the player had found `auto_hire` and schools; nothing names those as the remedy (see 233 for the closure side).

**Remains:** an `allocate` option that caps at the useful work; the immortal-founder scholar warning and the atomic-theory hire-size advice. Starved-project reasons for trades now name `labour`, `hire`, `train`, `portfolio`, `priority` and `allocate`.
