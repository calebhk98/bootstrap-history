# Request: goal-directed automation (`pursue <goal>`), and smarter policies

**Status:** closed - folded into 421

Mid-game I wrote ~40 lines of shell to do each year what the game could: open concerns that pay, hire when short, follow `stuck`'s route-blocker advice, start what `path` lists within cash, step. `rush` is not a substitute: it picks from hundreds of startable nodes "with no idea what you are building toward".

Requests:
- `pursue <goal>` or `rush path:<goal> max_total_cost:N`.
- A policy that follows `stuck`'s route-blocker advice (train the missing trade, open the named institution, hire scholars).
- `auto_replace_foreman`: rehire a specialist foreman when one dies; and a `state` warning when a concern depends on exactly one person.
- A "keep N spare craftsmen/scholars" reserve policy (done: `policy reserve_staff on`, `reserve craftsmen N`, `reserve scholars N`).
- `allocate` hours per goal, not only per project.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.

Related: 145, 146.

Also reported (Han China 100 AD fog playtest, tester item(s) 113, 190, 85, 171, 172; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): asks for replace-only versus expand modes for `auto_hire`, worker targets, protected minimum staff by trade, a budget cap, a keep-these-services-open priority that `auto_open` respects, and exclusions for `rush` (see 226). The tester did not find `auto_replace_foreman`, `reserve` or `keep`, which already answer part of it (see 229). Reproduces: n/a (request).
