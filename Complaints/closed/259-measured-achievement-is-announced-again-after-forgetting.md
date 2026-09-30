# "achieved: A literate people, not just a literate few" is announced repeatedly (1539, 1546, 1548)

**Status:** closed

Run 2 (C) saw the same achievement announced three times.

Cause: a measured goal node (`win_condition`, e.g. `goal_literacy_common`, `goal_literate_nation`) is put into `projects.done` by `_check_win_conditions` (`sim/engine/core.py`), which logs "achieved: NAME". Dissolution after the founder's death (`_step_founder_mortality`, `sim/engine/core_step_phases.py`, which samples `done` minus `granted` and discards it) and sack and plague technology loss treat that node as losable knowledge; once it has been discarded the yearly check finds the measurement still met and awards it again with a fresh log line. By code reading: the loss lists do not exclude win-condition nodes. Reproducing needs a dissolving run (Mexica mortal, no deputy; achievement via literacy); untested live here.

Why it matters: a measurement is not a thing that can be forgotten, and repeated "achieved" lines devalue the real ones and could double-count in a score.

What it would take: exclude `win_condition` nodes from every forgetting/loss sample, or record `achieved` once; a test that loses technologies and then checks the log for a single achievement line. Related: 223.


Found in the final blind playtests of this branch (three mortal fog Mexica 1500 runs; C bug 8). Reports: `Complaints/reports/playtest-mexica-1500-mortal-three-runs.md`; triage: `Complaints/reports/final-playtests-triage.md`.
