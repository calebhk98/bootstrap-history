# Silk and spices never cross between Rome and Han

**Status:** open

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
