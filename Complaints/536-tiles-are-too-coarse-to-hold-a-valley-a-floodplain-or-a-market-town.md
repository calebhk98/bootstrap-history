# Tiles are too coarse to hold a valley, a floodplain or a market town, and carry one land class

**Status:** open

Reference (an outside design note, not code-aware): an ancient market town drew on the distance a
person or ox-cart covers in a day, roughly twenty kilometres, and a coarse tile with one terrain type
averages a Nile valley a few kilometres wide into the desert around it. Its suggested fix keeps the
tile but gives it a land-use breakdown and edge flags for rivers, ports, roads and elevation.

## What the map does

- Every tile is an equal-area cell of the same large area, clipped at coasts:

      python3 -c "import json,statistics; t=json.load(open('data/world/geography/tile_grid.json')); t=t.get('tiles',t); t=list(t.values()) if isinstance(t,dict) else t; a=[x['land_area_km2'] for x in t]; print(len(a), max(a), statistics.median(a))"

  That is hundreds of times the day's-walk catchment the note assumes.
- A tile has one Koppen class, and its `arable_fraction` and `fertility_quality_multiplier` are read
  from that class. Forest is a separate layer (`layers/forest_fraction.json`), arable is the class
  share limited by forest and slope (`sim/geography/food_land.py`), pasture is the open remainder
  (`food_pasture.py`). There is no waste or settled share and no stored composition per tile.
- Edges are already per tile pair (`sim/geography/routes_graph.py`): land edges carry grade, river
  edges a current, sea edges coast or open sea, and built roads, ports and canals are improvements on
  an edge. So the edge half of the note is in place; the land half is not.
- The Nile is a strip of fixed width each side of a navigable river (`food_crops.py`,
  `food_irrigation_strip_width_km`), inside desert tiles. Egypt is a handful of tiles.

## Why it matters

Every per-tile quantity (harvest, weather, rent, labour market, ownership, control) is an average
over a region the size of a modern province. A floodplain, a mountain pass, a harbour town and its
hinterland cannot differ, and a founder cannot pick one valley over the next.

## What it would take

- A stored land-use composition per tile (arable, pasture, forest, waste, irrigated floodplain)
  built from the map layers, read by food, rent and fuel instead of each deriving shares.
- Sub-tile places (market towns, river strips, ports) with their own catchment, or a finer grid where
  a game needs it; the cost in run time is Complaint 497.
- Related: 483 (tile control), 489 (population is national).
