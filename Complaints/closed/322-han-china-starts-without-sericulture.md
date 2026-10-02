# Han China starts without sericulture, so it cannot make silk

**Status:** closed - Han starts with `sea_monsoon_route`, `tx2_silkworm_stock`, `tx2_silk_fibre` and `tx2_sericulture`; silk is solved for Han and crosses to Rome (`sim/tests/test_luxuries_cross_borders.py`); yields remain unchecked against sources (351)

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

## Resolution

The four nodes are in Han's `starting_techs` as initial conditions (Han held
sericulture at its start date). The sericulture chain is now three entries in
`data/production/` (`mulberry_leaves_kg`, `silk_cocoon_kg`, `silk_kg`) with the
land on the leaf. Han as a player civilisation changes (its starting techs
grew); `sea_monsoon_route` is a prerequisite the tree imposes on
`tx2_silkworm_stock`, which is odd for the country that kept the secret (see 352, now fixed).
