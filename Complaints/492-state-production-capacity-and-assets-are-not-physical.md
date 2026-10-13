# State building is not physical: no fleets, no state-held asset stock with service life, no monopoly or mine revenue

**Status:** open

Private producers in the agent economy are capacity-limited by plant, inputs and labour
(`sim/economy/producers*.py`, `entry_sizing.py`), and recipes carry hard chemical inputs
(`data/production/`, `data/material_gating.json`). The state does not use that machinery:

- **No ships.** The navy is a wage line from coast length (`sim/agents/budget_lines.py`,
  `COAST_KM_PER_SHIP`). A state cannot commission warships, so funding cannot be refused for lack of
  timber, shipwrights or a yard, and there are no wrecks or replacements.
- **State works are masonry.** `sim/agents/state_works.py` keeps square metres of walls and buildings with
  labour-only upkeep. Schools, telegraphs and machinery are not stocks with a service life and the staff
  they need each year.
- **Monopolies and mines yield nothing to the treasury.** `state_monopolies` only blocks exports
  (`sim/agents/policy.py`); no base in `sim/agents/revenue_bases.py` charges a monopoly margin or a
  royalty. Mine workings are the founder's (`household.mines`; `sim/engine/mine_deposits.py`).
- **Recovery technology is a flat multiplier.** Cyanidation is an `output_multiplier` on the gold commodity
  (`data/world/commodities.json`, node `mt2_cyanidation`, read by `sim/engine/commodities.py`) rather than a recovery fraction applied to a deposit's grade
  (`sim/world/deposits.py`, `ore_dressing.py`).
- **Alternative recipes have no performance or failure.** `data/production/_SCHEMA.md` says margin, risk
  and failed batches are not modelled, so a weaker or riskier engine cannot be a worse good.

Why it matters: the group's test case is a navy funded far beyond what yards can build each year. The
limit must come from yards, timber and skilled hands, not a number.

What it would take: state commissions placed through the same recipe and plant path as private
producers (a hull is a good, a yard is plant); state-held assets with service life, wear and staff;
revenue bases for monopoly margin and mine royalty; recovery and failure fields on recipes.
