# The farm trade and the unskilled fallback trade are one id, so processing and herding hours count as farming

**Status:** open

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

Blocks 610 to 613 (their hours must stop counting as farming).

**What is wrong.** `FARM_TRADE` and the unskilled fallback are both `labourer`. Every `labourer` hour in every recipe is dropped from the non-farm need shares, so spinning, fulling, dyeing, wine, oil, brick and milling labour never appears as a non-farm trade, and the non-farm workforce is sized mostly from furnacemen and miners.

**Evidence.** `sim/labour/legacy_trade_defaults.py`; `sim/labour/workforce_spinup.py` (`total_by_trade.pop(FARM_TRADE, None)`). Measure: `python3 -c "from sim.tests.harness import sim; lab=sim(civ='rome_100ad').labour; print(sorted(((round(v,3),k) for k,v in lab._non_farm_need_shares().items()), reverse=True))"`.

**Why it matters.** The occupational distribution of every run is wrong in kind, not only in size (CLAUDE.md 4.2). Related: 513, 434.

**What it would take.** Give the unskilled fallback its own trade id, distinct from the farm trade, so only crop and farm hours are dropped from the non-farm shares.

**Test.** A test: a recipe booked to the unskilled fallback appears in the non-farm need shares and a farm recipe does not.
