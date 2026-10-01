# Staffing closures are reported as gross counts with no cause, and the tools that prevent them (`keep`, `reserve`, `auto_replace_foreman`) are never named

**Status:** partly - the closure and reopening lines name the cause, the net count and the remedies (`keep`, `reserve`, `policy auto_replace_foreman`); `state` carries `staffing_closure_summary` (`Sim.staffing_closure_summary`).

Across 300 years the tester reports the same pattern: a small loss of specialists (two carpenters, three artisans and a smith) produces an annual line closing 10 to 210 concerns; automatic hiring and reopening restore most by the next
prompt, so the closed count at the prompt and the closed count in the event differ and neither is labelled "net". Public-service concerns (clinics, hospitals, museum, research institute) were left offline while profitable shops reopened,
and had to be reopened by hand twelve at a time. Turnover is reported as "to death and to better offers" with no split.

What the game already offers and the tester never found (they read `help commands` and used `policy`):

- `keep <id> staffed` (hire each year for the concerns you name, first claim), `reserve craftsmen N` / `reserve scholars N` with `policy reserve_staff on`, and `policy auto_replace_foreman` (closed 130, partly 180).
  Nothing in the closure line, in `state`, or in `stuck` mentions them.
- Reopening after a staffing closure happens unconditionally ("not a policy"), by design (`sim/engine/projects_staffing.py`, `reopen_restaffed_ventures`). The tester read four concerns reopening "with auto_open off" as a fault.

Not reproduced live (needs a large late game). The closure rule itself is per-resource and minimal (`projects_staffing_shortfall.py`), so the very large counts are plausibly many small shares on one short specialist, not a bug; the reporting is what misleads.

What it would take: one annual recap line "closed N, reopened M, still shut K; cause: lost 2 carpenters"; name `keep`/`reserve`/`auto_replace_foreman` in the closure message and in `state`;
a way to mark public services as protected that `auto_open` and the closure rule respect; split departures by cause. Related: 93 (automation audit trail), 205, 89 and 150 (closed).

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 20, 54, 77, 84, 85, 96, 97, 112, 131, 139, 195, 206, 208, 215). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.

Also reported (final playtests, A; `Complaints/reports/final-playtests-triage.md`): A asks for a consolidated workforce screen: single-employee dependencies, businesses at immediate risk, reserve specialists, expected annual attrition, training pipeline, and a prominent warning before a multi-year advance with a critical business resting on one person (A's destitute mortal run lost its loom to the departure of its only carpenter). A liked `keep`, `reserve`, the academy and delegation;

**Remains:** departures are still one pooled rate with no split between death and better offers (no separate mechanism exists to split by); there is no protected-service marking that `auto_open` and the closure rule respect; the consolidated workforce screen (single-employee dependencies, expected attrition, pre-advance warning) is not built; the step report does not yet print the summary line itself.
