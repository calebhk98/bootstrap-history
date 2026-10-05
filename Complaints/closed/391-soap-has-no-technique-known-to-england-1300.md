# Soap has no technique England in 1300 knows

**Status:** closed - soap is gated on `hom_soap_soft` (`sim/tests/test_soap_known_to_england.py`); every basket good a civilisation cannot supply is checked by `civ_basket_check` in `simulator.py validate` and `sim/tests/test_basket_goods_supplied.py`, and each remaining one is declared with a reason in the civilisation's `unsupplied_basket_goods`

On the agent economy, England's households bid for soap every year and nobody sells it: no production recipe for soap is among the techniques England 1300 starts with, though soap was made and traded in medieval England. Demand-driven entry (sim/economy/entry.py) only uses recipes the society knows, so the market stays empty.

Evidence: `python3 sim/economy_untraded.py --years 15 --civs england_1300 --list` (script since removed; recover with `git show 97473f1:sim/economy_untraded.py`) shows `soap_kg` as buyers_only.

What it would take: a soap recipe (fat or tallow with wood-ash lye) gated by a node England starts with, sourced in `data/production/`. Other buyers-only goods in that list deserve the same check.
