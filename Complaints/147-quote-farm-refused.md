# `quote farm` is refused although `buy farm` works and is advertised

**Status:** open

`help economy` lists `buy farm 120`. `quote farm 20` gives "REFUSED: you can quote a mine, a forest or people". `buy farm 1000` does work (late game it cost about 505 den/ha). The same applies to other `buy` targets (housing, school, material, nitre): `quote` covers only mine, forest and slaves.

Why it matters: the help says "ASK THE PRICE FIRST with quote"; for most purchases the player cannot.

What it would take: `quote` for every `buy` target, including `quote material <name> <tonnes>` (there is currently no way to learn a material's market price without buying some; I bought 1 t of charcoal and watched capital change).

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
