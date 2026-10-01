# `auto_hire` keeps idle taught specialists on full pay with no warning

**Status:** closed - auto_hire now replaces a taught trade only when a project or open concern draws on it; state lists idle_specialists with their wage bill

Two machinists trained in 179 AD stayed on the payroll at ~7.6k/yr each through decades with no project using them, at one point more than 8x total revenue; later `auto_hire` re-hired a machinist after I fired them. `stuck` pointed at arrears, not the wage bill.

What it would take: flag idle specialists in `state`/`stuck`; let `auto_hire` replace taught trades only when something uses them.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
