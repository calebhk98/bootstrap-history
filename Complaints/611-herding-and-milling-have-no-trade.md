# Herders and millers have no trade: herding is not told apart from crop farming

**Status:** open

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

Depends on 609.

**What is wrong.** `wool_kg`, `milk_kg` and `hide_kg` are `labourer` hours; so are herd and draught animals and meat. `flour_kg` and its variants are `labourer` hours and are eaten as is.

**Evidence.** `data/production/*.json`; `data/world/needs.json` (flour as a good).

**Why it matters.** Herding and milling are the by-employment and food processing of the period and are invisible.

**What it would take.** Add herder and miller to `data/world/trades.json` with sourced training, tools and danger, and re-book those recipes' hours. Baking is 614.

**Test.** `validate` passes; a test reads the booked trade for the listed recipes.
