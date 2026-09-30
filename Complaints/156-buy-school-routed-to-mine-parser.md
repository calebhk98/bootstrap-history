# `buy school <trade> <n>` is always refused with the mine error

**Status:** open

`help buy` lists `buy school <trade> <n>`; `help economy` gives the example `buy school smith 2` ("makes two more smiths' worth of annual labour locally available"). At 542 AD, `buy school smith 2`, `buy school scholar 1` and `buy school scholar 5` all return "REFUSED: material must be one of: well-known workings: coal, copper, gold, iron, lead, silver, tin - or any other material key ...", the `buy mine` validation text.

Why it matters: scholars were the binding constraint for the whole late game ("reach ... will not stretch past 14.4 in total", later 67 and 75.7), and `labour scholar` says schools widen that cap. The documented way to raise it does not work.

What it would take: route `school` to its own handler; a test for the exact help example.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
