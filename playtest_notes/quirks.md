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
