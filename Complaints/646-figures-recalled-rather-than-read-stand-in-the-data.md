# Figures recalled rather than read stand in the data and the constants

**Status:** open

Owner direction (2026-10-20): a figure needs a source someone read; "recalled" is not a source. The data and the
declared constants carry many figures marked as recalled (confidence D), from the herd rows (532) to the savings
constants (606). List them:

    grep -rn "recalled" data sim --include=*.json --include=*.py | wc -l

What it would take: for each, find and read a source and record it (author, work, page or URL, and the passage), or
mark the figure as having none and keep it a labelled heuristic with a `retire`. The rule for new work is in
CLAUDE.md section 6. Research agents follow the same rule: every claim cites a source opened in that session.

## Pass 1

Count of lines containing "recalled" in `data` and `sim` (`.json` and `.py`) after the pass: measure with the
command above (about 102 left, from about 150). Sources were opened as PDFs or pages in the session that wrote
this note; passages are quoted in the files named.

Sourced (opened), with changed values:
- `data/world/living_stock.json` sheep, goat, cattle `dung_and_fodder_source`: USDA NRCS, Agricultural Waste
  Management Field Handbook, Part 651 chapter 4 (rev. July 1996), Table 4-18 lamb 40.00 lb/d/1000 lb (sheep 0.04
  kept); Table 4-8 beef cow 63.00 (cattle `manure_share_of_live_weight_per_day` changed 0.08 to 0.063; the 0.08 was
  the dairy figure of Table 4-5; `manure_kg` of the cattle herd recipe in `data/production/95_herds.json` changed
  from 240900 to 189708.75 to follow). Goat has no row in the handbook: the sheep figure is used, no source found.
- Same rows, winter ration 2 percent of live weight a day: South Australian government fact sheet "Calculating dry
  matter intakes for various classes of stock" ('Animal on dry pasture or poor quality feed: 2%').
- `cattle_kg` source: FAO, Production parameters of ruminants in traditional systems (fao.org/4/Y4176E/y4176e08.htm):
  offtake 9.9 percent mean, mature cow 244 kg mean (median 250), milk 252 kg a lactation. Values kept (10 percent,
  250 kg, 250 kg).
- `sim/geography/soil_nutrients.py`: `MINERALISATION_RATE_PER_YEAR` (Oregon State Extension EM 9281, 1 to 3
  percent, kept 0.02); `HERD_EXCRETA_KG_PER_LIVE_WEIGHT_KG_YEAR` (NRCS Table 4-8 beef cow, changed 29.0 to 23.0, the
  old figure was the dairy cow); `MANURE_NITROGEN_FRACTION` (NRCS Table 4-8, 0.33 / 63.00 = 0.52 percent, kept 0.005).
- `sim/economy/households_orders.py`: `SAVINGS_RATE_RESPONSE_LIMIT` and `SAVINGS_RESPONSE_FLOOR` cite Bernheim,
  Taxation and Saving (NBER Working Paper 7061; the sign of the interest elasticity cannot be given by theory; studies
  put it at or near zero; precautionary saving is insensitive to the return). The sizes remain assumptions.
- `data/world/needs.json`: salt subsistence (National Academies, Dietary Reference Intakes for Water, Potassium,
  Sodium, Chloride, and Sulfate, 2005, Summary: sodium AI 1.5 g a day); water subsistence (Howard and Bartram, WHO
  2003, basic access 20 l/c/d); candle lumen-hours (Wikipedia, Candela: 1 cd, 4 pi lumens).

No source found, now labelled (python ones `kind="temporary_heuristic"` with `retire` naming this complaint or 607):
- `HOUSEHOLD_TIME_PREFERENCE`, `SAVINGS_YEARS_OF_SURPLUS_INCOME`, `SPENDING_CUT_LIMIT`, `WEALTH_DRAWDOWN_LIMIT`
  (retire stays Complaints/607).
- `soil_nutrients.py`: `NATIVE_POOL_KG_PER_HECTARE`, `LOSS_RATE_PER_YEAR`, `GRAIN_NITROGEN_FRACTION`,
  `LEGUME_NET_NITROGEN_KG_PER_HECTARE`, `MANURE_AVAILABLE_FIRST_YEAR`, `MANURE_RETAINED_IN_POOL` (kind changed to
  `temporary_heuristic`, confidence D, retire Complaints/646).
- `living_stock.json`: sheep fleece, salt and stocking rates; goat stocking, milk; cattle dressing, fat, hide, horn,
  salt and stocking; goat excreta share.
- `needs.json`: housing satiation multiple, salt satiation (the WHO 2012 sodium guideline was opened and does not
  give a 9 to 12 g mean), pottery stock (Deal), coin stock (Duncan-Jones), tallow and oil lamp quality factors.

Tests: no test needed a bound changed; the byproduct test followed the species row, which is why the herd recipe
value moved. `currency.py` carried no "recalled" line; the 606 constants are those in `households_orders.py`.

Not touched, still open: `data/production` rows (organics, lighting, herds labour), `trades.json`, `spoilage.json`,
`waste_heaps.json`, disease files, civilisation notes, `agriculture.py`, test docstrings.
