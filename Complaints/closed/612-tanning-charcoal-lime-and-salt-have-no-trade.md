# Tanners, charcoal burners, lime burners and salt workers have no trade, and leather has no goods

**Status:** closed - pinned by sim/tests/test_tanning_burning_and_salt_trades.py

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

Depends on 609. Forest stock (539), lime fuel (534) and salt demand (535) are closed.

**What is wrong.** `leather_kg` is `labourer` plus `artisan`, with no shoes, harness or scabbard goods; `vellum` and `parchment` likewise. `charcoal_kg` and `firewood_kg` are `labourer` hours; the salt recipes are `miner` and `labourer`; `lime_kg` is `furnaceman` and `labourer` (a glassblower exists).

**Evidence.** `data/production/*.json`; `data/world/trades.json`.

**Why it matters.** These are standing trades of every classical economy.

**What it would take.** Add tanner, charcoal burner, lime burner and salt worker to `data/world/trades.json`, re-book the hours with sources, and add leather goods recipes (shoes, harness, scabbard) that use the tanner's output.

**Test.** `validate` passes; a test reads the booked trades; leather goods exist as goods with recipes.

**Resolution.** `tanner`, `leatherworker`, `charcoal_burner`, `lime_burner` and `salt_worker` are trades in `data/world/trades.json` (training times are author estimates, conf D; fatality stated as unsourced). Charcoal, lime (coal and wood), leather, parchment, vellum and the salt recipes book them (rock salt keeps its miner hours). `data/production/95_leather_goods.json` adds shoes, harness and scabbard made from leather; shoes satisfy clothing at the leather factor, harness and scabbard are capital and kit with no household need. Firewood stays with the labourer (forester is not a trade yet). The skilled-trade glut check in `test_complaint_467_trades_open_to_the_jobs` already failed on miller before this change and still does (miller was 225 times the hours bid at the Rome opening before, 84 after; measure with that topic).
