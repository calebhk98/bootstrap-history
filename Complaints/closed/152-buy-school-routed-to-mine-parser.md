# `buy school <trade> <n>` is always refused with the mine error

**Status:** closed - buy school, buy trade school and buy trade_school all reach the school handler; buy, quote and help read one target table, buy_targets.py (tests: player_command_fixes)

`help buy` lists `buy school <trade> <n>`; `help economy` gives the example `buy school smith 2` ("makes two more smiths' worth of annual labour locally available"). At 542 AD, `buy school smith 2`, `buy school scholar 1` and `buy school scholar 5` all return "REFUSED: material must be one of: well-known workings: coal, copper, gold, iron, lead, silver, tin - or any other material key ...", the `buy mine` validation text.

Why it matters: scholars were the binding constraint for the whole late game ("reach ... will not stretch past 14.4 in total", later 67 and 75.7), and `labour scholar` says schools widen that cap. The documented way to raise it does not work.

What it would take: route `school` to its own handler; a test for the exact help example.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.

Code evidence: `sim/engine/proto/dispatch_money.py` registers only `"trade_school"` and `"trade school"` as keys for `_buy_school`, while the `help buy` usage in the same file and `sim/engine/proto/help.py` ("buy school smith 2 makes two more smiths' worth ...") advertise `buy school <trade> <n>`. In play, `buy trade school smith 2` was also refused with the mine error. A duplicate review flags this as a possible regression of `Complaints/closed/85-*` and `closed/26-*`, which it says contradict each other (one says the command was removed, one that it exists).
