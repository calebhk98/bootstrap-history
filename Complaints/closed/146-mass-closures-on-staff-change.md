# Yearly staff check closes many concerns at once that `open` then accepts immediately

**Status:** closed - the yearly check now closes only the concerns drawing on a short resource, lowest net value first, and none that `open` would accept; a reopen keeps its original ramp start (opened_year is never reset) and no longer repeats the ramp promise

Evidence, in order of severity:
- 118 AD: staff were founder, 2 carpenters, 2 artisans, 1 smith. The smith died; the step closed exp_trade_route_extend, horse_collar, pwr_peat and tex_horizontal_loom. Straight after, with no hire, `open exp_trade_route_extend`, `open tex_horizontal_loom` and `open pwr_peat` all succeeded; only horse_collar (needs a smith) was refused.
- 145 AD: with 3 scholars, 27 artisans, smiths and carpenters, losing one carpenter printed "nobody left to keep an eye on 19 concerns ... closed"; net fell from about +332k to +163k/yr; all reopened next year without new generic staff.
- 584-599 AD, ~500-960 concerns running, scholars at the town cap, ~690 craftsmen idle: closures alternated year by year (464 closed in 586, 461 reopened in 587, 482 closed in 588, 708 in 589, 832 in 598), including concerns needing no scholars (ag2_baler, ag2_bone_meal).
- Early game: "pwr_peat reopen on their own" the year after a closure with no hire in between.

`state` shows staff as fractional FTEs trimmed ~3.5%/yr. A guess (not verified in code): when total FTE for some trade dips below the total claimed, the check closes every concern at once rather than the marginal ones, while `open` checks one concern against what is free.

Why it matters: this was the single largest drain on income in the run. Each closure costs a reopening fee and the reopen message repeats "reaches that over the first 3 years", so the revenue ramp appears to restart. With `policy auto_open on` the damage was contained (closed concerns reopened within the year); my own reopen loop was worse.

What it would take: make the yearly check close only enough concerns to cover the shortfall, lowest-value first, using the same test `open` uses; a regression test with one foreman lost among several concerns.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.

Related: 145 (foreman not shown on `why`), 176 (auto-replace foreman request).

Verified on the original playtest save (599 AD, 820 concerns running): the same `step 1` that closed 408 concerns before the fix now closes 8 (el2_capacitor_variable_air, el2_rheostat, hom_doll_fashion, hom_jigsaw_puzzle and others), leaving 939 running.
