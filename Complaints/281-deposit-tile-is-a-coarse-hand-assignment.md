# A deposit's tile is a hand assignment onto a 150,000 km2 grid

**Status:** partly - a deposit carries a position and the holding tile is found at load; the positions are still the old tile centres, not surveyed mine sites

Each deposit in `data/world/deposits.json` names one tile (Complaints/136). The tile was chosen as the one nearest the mine among the tiles of the region that held the deposit's share, so that a region's total, and with it `mineral_scale` for every civilisation, did not move. The grid is coarse, so some choices are poor: the Noricum iron mine is in Austria, but the Austrian tile belongs to no region, so the deposit sits on a Czech tile; Elba is placed on the Sardinian tile. The generic placeholder deposits sit on a representative tile of their region, not at a place.

## Why it matters

Anything that later asks where a deposit is (distance to a mine, who holds it after a conquest, ore carried by sea) reads the wrong ground for a few of them.

## What it would take

Give deposits a latitude and longitude and resolve the tile by containment, once tiles are what civilisations hold (Complaints/136), so a deposit follows the tile that holds it and the Austrian tile can carry Noricum. Compare each deposit's tile `lat`/`lon` in `data/world/geography.json` with where the mine was to see which choices are far off.

## Done and remaining

Done: `lat`/`lon` on every deposit, resolved by nearest tile centre (`sim/world/tile_lookup.py`). Remaining: enter a surveyed position per named mine. Each move changes a region's metal total, and with it `mineral_scale`, so Noricum (the Austrian tile belongs to no region) needs its region mapping settled first.

Related: 328.

Owner decision (2026-10-02): ignore for now. The tile centre is fine as long as mines and other geographical features stay in their own data file, so a mod or a better map can place them later.
