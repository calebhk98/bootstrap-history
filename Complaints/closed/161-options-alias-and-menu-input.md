# `options` is listed as an alias of `available`, and the Options menu swallows piped input

**Status:** closed - alias removed; the Options menu echoes a rejected line and hands it back to the game prompt (and returns at end of input)

`help commands` lists "options: available" under aliases; typing `options` opens the Options menu (horizon, mortality, save path), as the intro describes. When commands are piped (`options`, `help work`, `labour`), the menu consumes the next lines as menu choices, prints "-- not a choice right now." for each without echoing what it read, and exits; the commands never run.

What it would take: drop the stale alias; have the menu echo the rejected input and return to the game prompt on a non-choice (or on end of input).

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
