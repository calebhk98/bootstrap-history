# Sea routes have no land mask and few lanes

**Status:** closed - folded into 411

`sim/geography/routes_graph.py` joins coastal tiles by straight chords. It drops a chord that passes near another tile's centre, but there is no coastline mask, so some legs cut across a peninsula (Sinai between `egypt_08` and Saudi tiles). Sea lanes that need a technique are boxes in `data/world/geography/sea_lanes/lanes.json`: only the monsoon crossing and Arctic ice exist, so open-sea legs across the Atlantic and Pacific need nothing beyond a square sail, and a coast-hugging chain round Africa and India reaches China without the monsoon route.

Evidence: `api.route(['italy_03'], ['china_32'], api.usable_modes([['sea_square_sail']]))` sails the whole way.

What it would take: a sea-distance graph over a water mask (the layer build already has the Natural Earth coastline), and lanes for ocean crossings (trade winds, westerlies) as data with their required techniques.
