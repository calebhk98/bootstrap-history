# Merchants' margin, wait, adjustment speed and capital, and the ornament limit, are stated not derived

**Status:** partly - merchants' terms now follow from the route's fleet, the labour market and the merchant class's capital (test `merchant_terms`); the ornament limit stays a labelled heuristic; the residue is Complaint 379

Partners are on by default because, with merchants' costs and a partial yearly
response (`Complaints/339`) and a satiating ornament need (`Complaints/325`),
the measured flows are small and stable. The parameters that make them so are
labelled heuristics (`sim/engine/foreign_traders.py`,
`satiation_per_capita_per_year` in `data/world/needs.json`), and the effect is
that almost nothing but a real shortage or a good one side cannot make crosses
the border: freight and a merchant cost of a sixth of the price swallow gaps of
a few percent, so the foreign economy does little in the default game.

## Evidence

`python3 sim/foreign_trade_report.py --years 100 --partner <han civilisation id>`
shows near-zero flows and a constant coin stock; cut a commodity's capacity and
step the game to see a small import build over years and fade as home capacity
recovers. Without a partner the same years run faster.

## What it would take

A merchant labour and credit market that sets margin and capital (and the speed
at which a trade relationship builds), a held-stock model of ornament metal
instead of a per-head yearly limit, goods that differ by origin so a partial gap
moves part of a market, and sourced output for more goods (`Complaints/324`).

Related: 109, 300, 338, 347, 350, 351, 353.

Owner decision (2026-10-02): should be looked at: merchants' terms should be derived from merchants' actual costs.

## Done (merchants)

`sim/world/merchant_terms.py` and `sim/engine/foreign_traders.py`: the wait is the route's round
trip over its carriers (a sailing's wait); agents' pay is agents per carrier times carrier-years
per tonne times the labour market's merchant wage; the markup over cost is the lone merchant's
over the number of carriers (one merchant each); the speed of change is the share of carriers home
to change cargo in a year; the capital is the merchant headcount times the modest-merchant kit,
plus earnings kept, less carriers, plus borrowing against it within lenders' room. Measure with
`python3 sim/foreign_trade_report.py --years 100 --partner han_china_100ad`.

## Ornament limit

Left as it is: `satiation_per_capita_per_year` for ornament is a household need limit with a
stated basis (a held stock of a few tens of grams worn or lost at a few per cent a year), not a
merchant term, and no source for the held stock was found. A held-stock model replaces it.
