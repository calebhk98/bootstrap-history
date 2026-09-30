# A failed bounty stays flagged as a bounty, is never worked by anyone, and nothing tells the player it became their job

**Status:** open

The tester bountied `master_screw` in 127 AD; it failed in 128; it then sat 13 years at "0 offered, 0 effective" with priority 1 or 2 while 7,000 or more hours went unused. `allocate master_screw 700` said "its own pace this year - at most 0 hours". `stop` then `start` fixed it.

Mechanism (reproduced with the harness):

- `post_bounty` (`sim/engine/projects_starting.py`) pays the prize, sets `ph_left = 0`, `lab_left = {}` and adds the id to `projects.bountied`.
- `project_hour_pace` (`sim/engine/projects_progress.py`) returns 0 for any id in `projects.bountied` ("a bounty is worked by whoever claims the prize").
- On a failed roll `_complete` (`projects_completion.py`) sets `ph_left = ph * 0.4`, banks part of the calendar and charges the poster the failure loss in cash, but leaves the id in `bountied`. `ph_left` is now above zero, yet the pace stays 0 forever and `lab_left` is empty. Only `stop`/`start` clears the flag (`projects_starting.py`, `bountied.discard`).

Measured: post a bounty on `horse_collar` with 50 million in hand, force the roll to fail: `bountied` True, `ph_left` 80, `pace` 0.0, `lab_left` {}, cash lost 1,918. So the poster pays twice (prize, then the failure charge) and the project never progresses.

Why it matters: a prize that pays twice and stalls silently costs years; no screen says that the bounty has become the poster's own project (`portfolio` shows it as running).

What it would take: on failure either leave the bounty with the claimant (and say "the claimant failed, the prize holds, they try again") or release the flag and log "bounty failed; this is now your own project"; do not charge the poster a failure loss for someone else's attempt; a test that a failed bountied project either progresses or is released. Related: 248 (bounty has no preview), 157 closed.


Found in the final blind playtests of this branch (Rome 100 AD fog, won 301 AD; tester bug 2; reproduced with the harness). Reports: `Complaints/reports/playtest-rome-fog-demo-65pct.md`; triage: `Complaints/reports/final-playtests-triage.md`.
