# Unskilled wages are low in Rome and Mexica on the agent economy

**Status:** closed - folded into 398

An hour of unskilled work buys markedly less grain in Rome and Mexica on the agent economy than in England and Han. Measure with `python3 sim/economy_validate.py --years 40 --seeds 1,2,3` (script since removed; recover with `git show 97473f1:sim/economy_validate.py`), column `wage_kg_wh`.

Whether this is wrong needs a source: attested day wages against grain prices for the Roman empire and for Tenochtitlan (cacao-bean wages) would bound it. Mechanisms to check: the wage floor (`year_labour.outside_option_by_tile`, family subsistence per hour), households' own-plot hours, and labour demand after households began saving.

Related: 387.
