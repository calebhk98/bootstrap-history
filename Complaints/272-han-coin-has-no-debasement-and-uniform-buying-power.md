# Han coin keeps uniform buying power across three centuries

**Status:** open

Source: `Complaints/reports/playthrough-review-han-china-100-to-400ad.md`, item 4 (currency debasement).

## What is wrong

Rome's data names debasement events (`grep -il debas data/civilizations/*.json` lists Rome and one other file whose note says its coin was not debased); Han China's has none. In a Han game a coin's buying power never moves, although the period saw severe monetary disorder (melted statues, debased issues in the successor states). The review calls it nothing in the game.

## Why it matters

Coin that never loses value removes a hazard the founder should plan around, and tilts every wealth decision. `184` records that Rome's dated debasement is a stopgap until debasement falls out of the economy.

## What it would take

Do not add a Han debasement date. Let debasement come from a state that mints against its purse (`docs/architecture/ACTORS_NEXT.md`, the state's spending) and from the coin metal's value (see 135, 140: the price solver's numeraire is labour, not the coin, so a coin that moves while labour does not is representable). Related: 180, 105, 109.
