# Merchants' margin, wait, adjustment speed and capital, and the ornament limit, are stated not derived

**Status:** open

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
