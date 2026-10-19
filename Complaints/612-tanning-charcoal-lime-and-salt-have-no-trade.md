# Tanners, charcoal burners, lime burners and salt workers have no trade, and leather has no goods

**Status:** open

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

Depends on 609. Forest stock (539), lime fuel (534) and salt demand (535) are closed.

**What is wrong.** `leather_kg` is `labourer` plus `artisan`, with no shoes, harness or scabbard goods; `vellum` and `parchment` likewise. `charcoal_kg` and `firewood_kg` are `labourer` hours; the salt recipes are `miner` and `labourer`; `lime_kg` is `furnaceman` and `labourer` (a glassblower exists).

**Evidence.** `data/production/*.json`; `data/world/trades.json`.

**Why it matters.** These are standing trades of every classical economy.

**What it would take.** Add tanner, charcoal burner, lime burner and salt worker to `data/world/trades.json`, re-book the hours with sources, and add leather goods recipes (shoes, harness, scabbard) that use the tanner's output.

**Test.** `validate` passes; a test reads the booked trades; leather goods exist as goods with recipes.
