# Tin is cheaper than copper because cassiterite has no deposit stock

**Status:** open

Split from 502. The recipe `cassiterite_kg` (`data/production/20_nonferrous.json`) costs a few miner and
labourer hours a tonne and carries nothing for the scarcity of the deposit, while copper's ore recipe carries a
large ore and labour cost. In an aged Rome game tin shows a fraction of copper's price, the reverse of the
historical relation (measure: `python3 sim/simulator.py play --civ rome_100ad --seed real25`, `market` screen, or
`shown_prices_of(economy)` for `tin_kg` and `copper_kg`).

Tin's scarcity is geographic: few deposits, long haul. The recipe cannot express that; a producer anywhere with
a mine recipe can make cassiterite at alluvial cost.

What it would take (data and geography work): cassiterite draws on a limited deposit stock at located tiles
(as other ores draw on `sim/world/deposits`), so tin's price rises as near deposits deplete and the route to
far ones lengthens; no engine special case for tin (CLAUDE.md 4.7). A regression test that tin's shown price
over copper's is not below the ratio of their deposit scarcity in an aged game.
