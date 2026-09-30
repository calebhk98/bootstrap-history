# `rush preview` always reports nothing

**Status:** open

At 507 AD, `rush preview` and `rush preview:true` both print "RUSH: 0 started, 0 not". On an identical copy of the save, `rush limit:3` started three projects and refused one.

What it would take: make preview list what `rush` (with the same limit/max_total_cost) would start and refuse, without starting anything.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
