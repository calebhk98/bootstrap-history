# Tiles have no place names and the data holds no towns

**Status:** open

`map` and `move` name a tile by its country and number (`China 10`, `Mexico 6`) because `data/world/geography.json` land tiles carry only `country_majority` and an id. Complaint 243 asked for city names (leaving Tenochtitlan before 1519 was not a real decision); the data has no town list, so the screens say so and show only the one estimated town the household works in.

What it would take: a town table (name, tile, size at the start date, with a source and confidence) in `data/world/`, loaded like `deposits.json`, so `map` can list towns and `move` can name destinations. Sizes must come from the settlement model or a cited start-date figure, not be hardcoded outcomes (CLAUDE.md 4.1). Related: 243, 140.
