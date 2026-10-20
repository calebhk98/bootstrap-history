# The Mexica start has no domestic animals or game, so meat, fat, hides and their goods cannot be made

**Status:** open

Found closing 652. With the basket check walking whole input chains, Mexica 1500 cannot make cheese, felt, leather,
tallow candles, salted meat or any lamp: every chain ends at a herd good (`meat_kg`, `milk_kg`, `fat_kg`, `hide_kg`,
`wool_kg`) whose herd nodes Mexica does not hold, or at `olive_oil_kg`. They are declared in the civilisation's
`unsupplied_basket_goods`. Historically the Mexica kept turkeys and dogs, hunted deer and other game, and fished;
none of these is modelled, so the society's animal protein, fat and hides are missing rather than scarce.

What it would take: turkey and dog as living stock (`data/world/living_stock.json`, the herd recipes of 532) and game
and fowling as land-bound recipes, each with read sources; Mexica's held nodes for them; then remove the declared
entries that these supply. Test: `validate` passes with the Mexica entries removed for goods the new chains make.
