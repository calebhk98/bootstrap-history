# Spinners, weavers, fullers and dyers have no trade, though textiles were the largest non-farm work

**Status:** open

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

Depends on 609.

**What is wrong.** `thread_kg` is `labourer`; `fabric_kg` and `linen_kg` use `artisan`, the generic craft placeholder (`legacy_trade_defaults.GENERIC_CRAFT_TRADE`); `cloth_kg` and `dye_kg` are `labourer` hours. Canvas, felt, sailcloth, twine, cordage and backstrap fabrics are in the same state.

**Evidence.** `data/production/*.json` (filter `labour_hours` for `labourer` and `artisan`); `data/world/trades.json`.

**Why it matters.** Textiles are the largest non-farm employer of the period and the model cannot show it.

**What it would take.** Add spinner and weaver, and fuller and dyer, to `data/world/trades.json` with training, tool basket and fatality sources, and re-book those recipes' hours with a source each. Data only (4.7).

**Test.** `python3 sim/simulator.py validate` passes; a test reads that the listed recipes no longer name `labourer` or `artisan` for their craft hours.
