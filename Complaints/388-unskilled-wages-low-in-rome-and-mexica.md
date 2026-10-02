# Unskilled wages are low in Rome and Mexica on the agent economy

**Status:** open

An hour of unskilled work buys markedly less grain in Rome and Mexica on the agent economy than in England and Han. Measure with `python3 sim/economy_validate.py --years 40 --seeds 1,2,3`, column `wage_kg_wh`.

Whether this is wrong needs a source: attested day wages against grain prices for the Roman empire and for Tenochtitlan (cacao-bean wages) would bound it. Mechanisms to check: the wage floor (`year_labour.outside_option_by_tile`, family subsistence per hour), households' own-plot hours, and labour demand after households began saving.

It also makes Rome's goods dear in labour, so a basic concern pays back more slowly in Rome than elsewhere: `test_money_units_one_boundary.py` (`test_han_can_afford_and_earn_from_a_basic_concern`) allows a fourfold band between Han and Rome for this reason; narrow it again when this is fixed.

Related: 387.
