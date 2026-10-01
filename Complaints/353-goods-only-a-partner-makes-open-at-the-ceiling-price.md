# A good only a partner makes opens at the ceiling price and takes years to reach a flow

**Status:** open

Rome bought silk before the game starts, but the foreign book opens with no trade:
the flow is built from nothing at the merchants' adjustment share, so Rome's silk
price sits at the market's ceiling ratio for the first years and the flow reaches
its level only after a couple of decades. Goods the home makes open in balance.

## Evidence

Step a Rome game with Han as partner and print `market_price_ratio("silk_kg")`
each year: at the ceiling for the first four years, falling only as imports build
(`sim/tests/test_market_engine.py` pins the opening ratio above one).

## What it would take

An opening trade history for a route that already ran (flows at the level the
route's own freight, lift and merchants' capital allow), derived rather than
stated, so the opening price is cost plus the merchants' terms. The adjustment
speed and capital limits are themselves labelled heuristics (630).
