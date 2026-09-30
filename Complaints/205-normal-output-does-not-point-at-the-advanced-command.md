# Starved or stuck situations do not name the advanced command that fixes them (first case: `allocate`)

**Status:** open

Starting the written corpus took all the founder-hours, so several small active projects got none. `portfolio` showed it, but neither `state` nor the starvation message suggested `allocate`. The tester found `allocate` only by reading `help commands` and calls it excellent once found. More generally they found the advanced layer (`materials`, `capacity`, `portfolio`, `bounty`, `commission`, `rush`, `mothball`) well layered but hard to discover: when a portfolio starves for founder-hours, materials, housing or a specialist trade, the normal output should point at the command that solves or diagnoses it. The "DIRECTED HOURS UNUSED" messages do mention `allocate` (for hours wasted), but the starved-project reason in `sim/engine/core_step_phases.py` ("hours before this one's turn came") carries no pointer.

Not replayed (needs several concurrent projects in a late game). What it would take: when a running project receives no founder-hours because higher-priority work took the pool, one line saying that `allocate <project> <hours>` reserves hours for it. More generally, each such shortage message carries one command hint (closed complaint 92 did this for material shortages). Related: 91 (closed), 101, 129.

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.
