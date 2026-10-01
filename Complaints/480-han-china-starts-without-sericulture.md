# Han China starts without sericulture, so it cannot make silk

**Status:** open

`data/civilizations/han_china_100ad.json` lists `starting_techs` without
`tx2_sericulture`, so `silk_kg` is not solved for Han and Han cannot supply it
in foreign trade. The tree gates it behind `tx2_silk_fibre`,
`tx2_silkworm_stock` and `sea_monsoon_route`, none of which Han holds either.

## Evidence

`python3 sim/foreign_trade_report.py` lists no silk among Rome's imports. Run
the same report with those four nodes added to Han's techs (a scratch patch of
`load_civ`) and silk becomes the largest import by tonnage, carried by sea.

## What it would take

A historian's decision on Han's opening techs. Adding them changes Han as a
player civilisation (the Han scenario in `sim/perf_fingerprint.py`) and may
move the pins in `sim/tests/test_civilisation_prerequisites.py`, so it was not
done under the foreign-trade work.
