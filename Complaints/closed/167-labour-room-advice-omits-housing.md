# `labour` says household room "is not bought, it is built", but `buy housing` works

**Status:** closed - `labour`, the `hire`/`train` refusals list `buy housing N` with its per-place price (housing_price_per_place, shared with `quote housing`) before the nodes

`labour` when full: "to make room: Room is not bought, it is built: blast_furnace (+15 places); freedman_staff (+10 places); school_founded (+12 places)". The nearest cost ~1.8M. `buy housing 10` worked at once for ~40k (+10 places). The `hire` refusal repeats "Room is not bought".

What it would take: list `buy housing` first in that advice and in the `hire` refusal.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
