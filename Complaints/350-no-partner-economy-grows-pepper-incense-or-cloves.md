# No partner economy grows pepper, incense or cloves, so they never cross to Rome

**Status:** open

Pepper (`pepper_kg`) is priced and wanted by Roman households (`seasoning`
need), and its production entry names the tropical Koppen classes it grows in
(`data/production/40_organics.json`), so Rome, whose territory has none, does
not make it. The only partner economy is Han, whose territory has one tropical
tile and does not hold `fud_pepper_cultivation`, so nothing offers pepper and
Rome's imports of it are zero. The historical pepper trade ran between Rome and
the Malabar coast, not Han.

## Evidence

`python3 sim/foreign_trade_report.py --years 100 --partner han_china_100ad` (script since removed; recover with `git show 97473f1:sim/foreign_trade_report.py`)
lists silk and cassia among Rome's imports and no pepper.

## What it would take

A civilisation file for an Indian economy (starting techs including
`fud_pepper_cultivation`, home regions `india`, a coin, a population from a
source) and an entry in `data/world/foreign_economies.json`. Entries for
frankincense, myrrh, cinnamon (Ceylon), cloves and nard, with the climate
classes and the technology each needs, are not yet written either. The
partner's capacity opens equal to its own demand
(`FOREIGN_OPENING_IN_BALANCE`), so a tropical partner would offer whatever its
households want, not what its land can bear; a land-limited capacity is
needed before an economy that grows a luxury can be added honestly.

Related: 109, 300, 324, 338, 339, 346, 347, 351, 353.

Owner decision (2026-10-02): can be a mod (an India partner is content); deferred.
