# Playtest quirks and confusing things

Things that are not clearly bugs but confused a new player.

## 1. `play --session FILE` alone does not start a new game
The README shows `python3 sim/simulator.py play --session mygame.json` as the way to start. With no save at that path it refuses:
"no --civ given, so I do not know what game you meant". Either default to the default civ (as `play` without a session does) or say `--civ` is needed in the README.

## 2. Goal naming mismatch
`goals` lists the headline goal as "Grown and alloy junction transistor" (junction_transistor, "the original goal"), but a default `play` sets `Goal: point_contact_transistor`.

## 3. `options` is listed as an alias of `available`
`help commands` lists `options: available` under aliases, but typing `options` opens a separate Options menu (horizon, mortality, save path). The intro screen describes the menu, so the alias entry is stale.

## 4. The Options menu swallows piped commands
Piping `options`, then `help work`, then `labour` makes the menu read the next two lines as menu choices, reprint itself with "-- not a choice right now." each time, and exit without running them. It does not echo what it received, so it is hard to see why the commands vanished.

## 5. `work` commits first and explains the loss afterwards
`work scholar 1500` runs at once, then reports "so you are up: -327.2 ... Wage work is for when you have no practice to lose."
No preview or warning comes before it. It is also surprising that wage work costs the practice but project hours do not.
On top of that, the reply shows capital jumping by the full wage (1,320 -> 2,763), and the practice loss seems to be taken silently at the next `step` (see bugs.md #3). That makes the money shown straight after `work` misleading.

## 6. A new concern charges full upkeep while earning a third of its revenue
`open pwr_peat` earns 303/yr at full takings but charges 270/yr upkeep from day one while revenue starts at 33%. For the first years it loses money, and `available` shows no hint of that.
The reply to `open` does say "expect less at first".

## 7. Some cheap "earners" lose money outright
`hom_toothbrush`: EARNS 202.1 but UPKEEP 269.5. `available` shows both columns but not a net column, so a new player sorting for income may pick a loss-maker.

## 8. `step 2` reports only the first year's events, and `log` has nothing for the second year
From 106 AD, `step 2` printed only "DURING 106" lines and landed on 108 AD. `log limit:12` jumps from 106 AD straight to the 108 state, with no 107 AD entries at all (not even the routine "population below trend" line every other year has).
It may be that nothing happened in 107, but every other year logged at least the population line. Unverified which it is.

## 9. A concern's earnings drop well below its quote with no reason shown
tex_hand_ginning is quoted at 291.8/yr (in `why` and `open`), reached about 302 in 103, and by 108 AD `ventures` shows it earning 126.6.
The `money` screen earlier said market saturation was taking 3% from it, and that "'ventures' says the same thing for each one". `ventures` shows no saturation line or reason, only the lower figure.
Meanwhile horse_collar earns 7,255 against a quoted 6,064, also unexplained.

## 10. lead_metallurgy says Rome already does it, but Rome must rebuild it for 460k
`why lead_metallurgy`: "This is already done, and done well, wherever there is a developed lead-mining and -working tradition (Rome is the best-documented case)."
In a Rome game it is not among the granted technologies, and it costs 460,398 den, of which 532,296 is materials (300 t charcoal + 280 t galena) before the x0.85 civ discount. That is about fifteen years of my whole income at the time, for a node the text says the society already has.
Either the node should be granted to Rome, or the text should say what extra (industrial-scale) step it represents.

## 11. First attempts seem to fail more often than the listed risk (suggestive, not proven)
By 121 AD (seed 1), 7 of 25 projects failed on the first attempt. The FAILURE RISK figures shown at `start` sum to about 3.2 expected failures, and 7 or more has roughly a 4-5% chance under those figures.
In 119 AD, three projects at 20%, 12% and 15% all failed in the same year (about 0.4% chance if independent).
This could just be seed 1. Worth checking with many seeds whether realised first-attempt failure rates match the displayed FAILURE RISK, for example whether reputation or opposition multipliers apply at roll time but not in the displayed figure.

## 12. Three ways to reopen a shut concern, three different prices, none stated up front
- After a staff-loss closure, `open` costs "a tenth of what opening did" (the closure message says so).
- After `mothball`, `open <id>` worked in 135 AD and charged 1x the yearly upkeep (nitre_beds: 10,781).
- After `mothball`, `restore <id>` in 136 AD charged 2x the yearly upkeep (nitre_beds: 21,561; refractory_fireclay: 9,433 vs 4,717 upkeep).
Neither the `mothball` reply, `help mothball` ("Stops its upkeep; restore reopens it") nor `help restore` ("Undoes mothball") mentions a cost. Combined with bugs.md #8, a player who mothballs a concern that looked unprofitable pays double to undo it.

## 13. `labour` says household room "is not bought, it is built", but `buy housing` works
`labour` at 142 AD: "to make room: Room is not bought, it is built: blast_furnace (+15 places); freedman_staff ...; school_founded ...". It points only at tech-tree nodes, the nearest costing 1.8M.
`buy housing 10` succeeded straight away for about 40k and took places from 22 to 32. `help economy` lists it, but the screen a player reads when short of room steers them away from the cheap option.

## 14. Staff fall faster than the log's "you lose N" lines add up to
Artisans: 41 on staff after `hire artisan 20` in 169 AD, 18 by 179 AD (`labour`). The log's "you lose N artisans" lines for 169-178 add up to about 14-16. The rest may be the Antonine plague (`state` shows "HAPPENING NOW: Antonine plague" from 169), but no log line connects the plague to my staff.
`state` also says attrition is "about 3.5%/yr", which would be about 12 over ten years on a staff of ~40.

## 15. Disasters destroy a share of cash
177 AD: "fire in the insula district ... destroyed 1,662,217 denarii" and "banditry or a frontier war disrupts supply: it cost you 757,232 denarii", together about a quarter of the 9.1M I held. In 132 a fire took 77,957 and in 120 one took 10,763, so the loss scales with wealth.
It is unclear what a tenement fire burns when most of the wealth is cash. If it is deliberate (idle money is exposed), `risk` or `help money` should say so.

## 16. The third-century crisis wiped out 150 years of progress in under 20 years
Sackings (from `log find:sacked`): 235 (14.1M taken, 119 people), 242 (8.6M, 114 people, "8 projects back to the beginning"), 246 (3.2M, 88), 250 (1.1M, 48), 252 (0.2M, 15), 253 (111 den, 8).
Result: "technologies: N built by you" fell from 91 to 21, route steps remaining went from 69 back to 135, money from ~17M to -88k, and net from +1.2M/yr to +1.2k/yr. In game terms 256 AD looks like 110 AD.
- Each sack took most of the cash on hand. The first took 14.1M of roughly 17M. There seems to be no way to protect cash: no bank, no deposit elsewhere, no "move base" advice in `risk`.
- Frequency: `risk` at 241 AD said "sack chance after what you have built: 10%" a year (16% base). Six sackings in 19 years is about 4% likely at those rates. It compounds: every sack destroys the defences, so the chance returns to 16%. Suggestive, not proven.
- In fairness, it was signposted. Every `state` from 100 AD printed "N technologies at risk if a hazard lands, hedged by nothing yet", and `risk` listed the crisis window with its odds. I ignored it and filtered it out. The hedge nodes (corpus_dispersed, academy_network) were still several steps away when the crisis began.
