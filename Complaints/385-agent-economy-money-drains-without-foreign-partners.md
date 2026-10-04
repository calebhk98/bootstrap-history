# On the agent economy, a civilisation with no foreign partner slowly loses its money

**Status:** open - needs data (partner economies for other eras) and a decision on how foreign trade is opened

The agent economy loses coin every year through coin wear (`COIN_WEAR_PER_YEAR`, `sim/economy/metal_stock.py`). Money comes back in through the mint (metal mined at home) and through foreign trade (`edge:external`, opened at the port by `AgentEconomy._external_orders`). Foreign trade only opens with the economies `data/world/foreign_economies.json` names for the game year, and that file names one economy, for one era. So every other civilisation has no foreign trade at all, and one whose home mines produce little precious metal sees its money stock shrink and its prices and wages drift down with it.

Why it matters:
- Real economies of these eras gained and lost bullion mainly through trade (wool and tin exports, the Baltic and Islamic silver trades, tribute). Without it, the price level of a civilisation without mines is decided by wear alone, which CLAUDE.md 4.1 forbids as an outcome nobody chose.
- The founder's choices about exports have no effect on the money stock.

Evidence: `python3 sim/economy_validate.py --years 40 --seeds 1 --civs <civilisation>` (script since removed; recover with `git show 97473f1:sim/economy_validate.py`) prints `money_drift`, the mean yearly log change of the money stock. A civilisation the foreign-economies file gives no partner shows a steady negative drift.

What it would take:
- Partner economies (or a generic "rest of the world" seller and buyer at landed prices) for each era a civilisation starts in, as data.
- Later, partners become full economies of their own (Complaint 382).

Related: 382.
