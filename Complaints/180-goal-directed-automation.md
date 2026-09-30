# Request: goal-directed automation (`pursue <goal>`), and smarter policies

**Status:** partly - done: auto_replace_foreman policy, the state depends_on_one_person warning, and the reserve part (`policy reserve_staff on` with `reserve craftsmen N` / `reserve scholars N`); still open: pursue-goal, a policy following stuck route-blocker advice, per-goal allocate

Mid-game I wrote ~40 lines of shell to do each year what the game could: open concerns that pay, hire when short, follow `stuck`'s route-blocker advice, start what `path` lists within cash, step. `rush` is not a substitute: it picks from hundreds of startable nodes "with no idea what you are building toward".

Requests:
- `pursue <goal>` or `rush path:<goal> max_total_cost:N`.
- A policy that follows `stuck`'s route-blocker advice (train the missing trade, open the named institution, hire scholars).
- `auto_replace_foreman`: rehire a specialist foreman when one dies; and a `state` warning when a concern depends on exactly one person.
- A "keep N spare craftsmen/scholars" reserve policy (done: `policy reserve_staff on`, `reserve craftsmen N`, `reserve scholars N`).
- `allocate` hours per goal, not only per project.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.

Related: 149, 150.
