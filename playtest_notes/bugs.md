# Playtest bugs

New-player playtest: Rome 100 AD, poor_scholar kit, seed 1, default goal.
Each entry: what happened, and the command that shows it.

## 1. `available sort earns` does not sort by earnings
`available sort earns limit 25` returns the list in alphabetical order by id, with every row at EARNS/YR 0.
Real earners (tex_hand_ginning 291.8/yr, pwr_peat 303.2/yr, pwr_oil_shale, hom_toothbrush) are not on the first page.
The help text on that screen says `sort` accepts `earns`. The `sort:earns` form in `help commands` may behave differently (untested).

## 2. `quote farm` refused although `help economy` advertises farms
`help economy` lists `buy farm 120`, but `quote farm 20` gives:
`REFUSED: you can quote a mine, a forest or people`.
So a new player cannot find out what farmland costs before buying it.

## 3. `work` is missing from the log, and the money it costs is never itemised
After `work scholar 1500` (reply: earned 1,442, "cost your own practice 1,769"), `log` has no entry for it.
Money went 2,762 -> 203 over the next `step 1`. Project payment (566.6) and the recurring loss (about 340) explain about 900 of that.
The other ~1,650 appears nowhere in `money` or `log`. It is about the size of the practice loss, so that is probably what it is, but the game never says so.
Repro: new Rome game, open two concerns, `work scholar 1500`, `step 1`, then `money` and `log`.

## 4. `why` misstates the staff a concern needs to open
`why tex_horizontal_loom` says `STAFF TO KEEP IT OPEN: 0 scholars, 0.27 artisans`.
After building it, `open tex_horizontal_loom` is refused: "needs 0.25 carpenter FTE to supervise its specialist work ... Generic artisans cannot substitute for this trade."
The `why` screen never mentions a carpenter. It even says "know this number before you spend money", and the number it gives is the wrong one.
Repro: Rome 100 AD, `start tex_horizontal_loom`, `step 1`, `open tex_horizontal_loom` with no carpenter hired.

## 5. Losing a specialist foreman also closes concerns that did not need that specialist
In 105 AD and again in 110 AD: "you lose 1 carpenter ... nobody left to keep an eye on 2 concerns, so pwr_peat, tex_horizontal_loom closed."
The loom needs a carpenter foreman, so its closing makes sense. pwr_peat needs only 0.03 of a generic craftsman, and at that moment I still had myself and a smith, with `state` reporting about 1.4 spare craftsmen.
The following year the log says "you have the people again: pwr_peat reopen on their own", with no hire in between that it could have waited for (in 111 AD, nothing was hired).
So either the closure was wrong, or the reopen condition differs from the close condition.
Repro: seed 1 Rome game, hire carpenter + smith, open loom, peat, horse collar, step until the carpenter attrition event.
**Stronger evidence (118 AD):** staff were me, 2 carpenters, 2 artisans, 1 smith. The smith died. The game closed exp_trade_route_extend, horse_collar, pwr_peat and tex_horizontal_loom.
Right after, with no hire, `open exp_trade_route_extend`, `open tex_horizontal_loom` and `open pwr_peat` all succeed. Only `open horse_collar` is refused, since it needs a smith.
So the attrition check closes every concern whenever any one foreman is lost, while `open` checks correctly.
Each wrongful closure costs a tenth of the upkeep to reopen, and it looks like the 3-year earnings ramp restarts too (the reopen message repeats "reaches that over the first 3 years"). On the trade route that is thousands of denarii a year.

## 6. Projects charge for materials at many times the market price, and ignore stock you already own
The biggest problem I hit. It turns the mid-game into a wall of 330k-470k nodes.
- Market price (by buying 1 t and watching capital, 129 AD): charcoal_kg 101 den/t, firewood_kg ~24 den/t, wood_kg 23 den/t. `materials` lists galena_kg at 73.5 den/t.
- `why lead_metallurgy`: MATERIALS charcoal_kg 300,000 + galena_kg 280,000 (kg, i.e. 300 t + 280 t). At those market prices that is ~30.5k + ~20.6k = ~51k. The quote charges 532,296 for materials (before x0.85).
- I then bought 300 t of charcoal (30,553 den) and held 6,993 t of galena from my own mine, and `start lead_metallurgy`. The bill was unchanged at 463,925. After `step 1`, `money` shows "spent on projects last step: 463,920", and `materials` still shows charcoal 301 t and galena 6,992 t on hand. Nothing was drawn from stock.
- Same with charcoal_industrial: buying its 400 t of firewood left the quote at 333,018. That node also needs 200 iugera of land, which may legitimately be most of its cost, so lead_metallurgy is the clean repro.
So: (a) the project material price disagrees with the market by about 10x, and (b) owned stock and mine output are never used by projects. Mines and `buy material` are therefore useless for building anything.
Repro: load a mid-game save with 480k+ den, `why lead_metallurgy`, `buy material charcoal_kg 300`, `start lead_metallurgy` (bill unchanged), `step 1`, `materials` (stock untouched), `money` (full amount spent).

## 7. Mine stock accumulates faster than its stated flow, then stops
`mines` reports my galena mine as 280 t/yr, ready in 123. `materials` in 129 showed 6,993 t on hand with YOUR FLOW 279.5. About 6 years of output would be ~1,700 t; 6,993 is exactly 25 times the yearly flow. A year later, after `step 1`, it read 6,992, so it did not grow at all, although flow still said 279.4 and nothing consumed it (see #6).

## 8. `open` and `mothball` quote a concern's base earnings, and `ventures`/`money` show the real (much higher) figure
At 136 AD: `mothball nitre_beds` says "stop earning the 9,433 a year it brought in" against upkeep 10,781, which reads as a loss-maker. `ventures` in the same session lists nitre_beds at EARNS 17,214 / COSTS 10,781.
refractory_fireclay is the same: 4,043 in `open`/`mothball`, 7,377 in `ventures`. Both ratios are exactly 1.825, so some multiplier (probably the trade-route revenue bonus) is left out of the `open`/`mothball`/`why`/`available` figures.
Earlier: horse_collar quoted 6,064, and `ventures` showed 8,137.
Effect: a player (and my own open-if-profitable routine) mothballs profitable concerns because the decision screens understate earnings. Every screen that quotes earnings should use the same number.
**Worst case (145 AD):** with 3 scholars, 27 artisans, and smiths and carpenters on staff, losing one carpenter printed "nobody left to keep an eye on 19 concerns, so case_hardening, cementation_steel, charcoal_industrial, coal_coke and others closed". Net income fell from +332k to +163k/yr. The next year every one reopened with `open` and no new generic hires (one carpenter was re-hired for the loom's foreman slot); three even "reopen on their own". My guess at the cause (unverified): `state` shows staff are fractional FTEs trimmed about 3.5%/yr, so "lose 1 carpenter" is a rounded decay, not one whole person leaving. The yearly check may close every concern at once when total craftsman FTE dips below the total needed, where it should close only the marginal one. Either way, the yearly closure check and the `open` check disagree.

## 9. A credit freeze refuses cash-funded starts, although its own message says they are allowed
301 AD, holding 47,301 den in cash, frozen until 303 after a credit exhaustion in 291.
`start scientific_method` (cost 1,106) -> "REFUSED: nobody here will fund new work: your creditors were left unpaid ... They will deal with you again in 303, and until then you may finish what is running, and pay for something out of money you actually hold."
`stuck` also says "0 things you could begin, 0 of them you could pay for". Either the rule should let a start the player can fully pay from cash go ahead (which the message promises), or the message should say plainly that nothing can be started.
Repro: exhaust credit so a freeze starts, step until cash is positive, `start` any cheap node.

## 10. `rush preview` always reports nothing
At 507 AD, `rush preview` and `rush preview:true` both print "RUSH: 0 started, 0 not". On an identical copy of the save, `rush limit:3` starts 3 things and refuses 1. The preview should list what `rush` would do.
