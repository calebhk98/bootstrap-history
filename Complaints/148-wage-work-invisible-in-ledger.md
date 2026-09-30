# Wage work (`work` and `allocate work`) is missing from `money` and `log`

**Status:** open

One-off: `work scholar 1500` replied "earned: 1,442 ... it cost your own practice: 1,769". `log` has no entry for it. Over the next `step 1` money fell by about 1,650 more than projects and running costs explain; neither `money` nor `log` itemises it.

Standing: with `allocate work machinist 2000`, one `step 1` raised cash by ~6.7k while `money` gave "Net/yr before the work in hand: -967.1" and listed only the medical practice under revenue, with "(these add up to the revenue above)".

Also: the `work` reply shows capital jumping by the full wage at once, while the practice loss lands silently at the next step, so the money shown right after `work` is misleading; and `work` commits before telling the player it is a net loss ("so you are up: -327.2 ... Wage work is for when you have no practice to lose").

What it would take: a ledger row and a log line for wage income and for the practice income it displaces; a preview (or `work ... preview`) before committing.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
