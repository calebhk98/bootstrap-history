# Silk and spices never cross between Rome and Han

**Status:** closed - silk and cassia cross from Han (test luxuries_cross_borders); pepper and the other spices need a partner that grows them, which is 350 (a mod by owner decision)

With the partner on, the measured flows between the default civilisation and
Han are near zero. That is credible for bulk goods (freight plus merchants'
cost swallow gaps of a few percent) but not for goods that historically
crossed. Silk is priced on both sides yet neither side's techniques make it,
so `_foreign_trade_key` in `sim/engine/foreign_economies.py` finds no maker
and does not trade it, although Han's sericulture is what the route existed
for. Pepper, cinnamon, incense and other spices have no production entries at
all, so no price exists to compare.

## Evidence

Step a Rome game with Han as partner and ask `_foreign_trade_key("silk", facts)`
(None), or list `facts["solved_materials"]` for silk and spice keys (absent).
`python3 sim/foreign_trade_report.py --years 100 --partner <han civilisation id>`
shows no silk flow.

## What it would take

Han's starting techniques (or a stated regional output) that make silk, and
production entries for the spices and aromatics the route carried, so the
price gap and the partner's capacity exist before the trade rule runs.

## Done so far

Silk (322) and cassia cross from Han to Rome through the ordinary trade rule.
A crop that grows only in some climates carries `grown_in_climate_classes` in
its production entry, read against the Koppen classes of the territory's tiles
(`sim/engine/crop_climate.py`); a home that lacks the climate does not "solve"
the good, so a partner that has it offers it. Households want spices through
the `seasoning` need. Pepper has an entry and a technology node
(`fud_pepper_cultivation`), but no economy in
`data/world/foreign_economies.json` grows it, so nothing carries it to Rome:
the remaining work is 350.

Related: 109, 300, 324, 338, 339, 346, 351, 353.
