# State building is not physical: no fleets, no state-held asset stock with service life, no mine revenue

**Status:** partly - monopolies and declared enterprises are plants in the state's business; mine royalty, recovery and failure fields, state-works masonry, crew pay sized to the target fleet and the corvee, salt and silkworm plants remain

Detail from the earlier status line: partly done. A state's monopolies and declared enterprises are plants in its `business` (`sim/agents/state_enterprises.py`, `government_enterprises.py`): staffed from the labour pool, drawing inputs from its stores then its purse, wearing and paying upkeep like a firm's plant, with takings that are its monopoly revenue (`record.enterprise_takings`) and output kept for its standing lines before any is sold (an arsenal's goods are goods the army draws). Han's iron monopoly is a blast furnace it owns. Tests: `test_complaint_492_state_enterprises.py`, `test_complaint_492_han_iron_monopoly.py`. Still open: the navy line, fleets and the masonry works (`state_works.py`) remain budget figures; salt and silkworm eggs open no plant because their entries have no takings model yet (514 stage 5b); firms are not yet barred from a monopolised good; corvee does not yet staff plants; mine royalties; recovery and failure fields on recipes.

Private producers in the agent economy are capacity-limited by plant, inputs and labour
(`sim/economy/producers*.py`, `entry_sizing.py`), and recipes carry hard chemical inputs
(`data/production/`, `data/material_gating.json`). The state does not use that machinery:

- **Ships (built since):** the navy line buys counted warships through the goods market from shipwright producers
  (`sim/agents/budget_lines.navy_line`, `data/production/99_ships.json`, `sim/agents/NAVY.md`, PR #59); delivered hulls wear
  through the durable stock. Left: crew pay is sized to the target fleet, not to the hulls held, so sailors are paid for ships
  not yet built; merchant fleets and route ownership are 629's.
- **State works are masonry.** `sim/agents/state_works.py` keeps square metres of walls and buildings with
  labour-only upkeep. Schools, telegraphs and machinery are not stocks with a service life and the staff
  they need each year.
- **Mines yield nothing to the treasury.** Monopolies are now plants with takings (see Status); no base in
  `sim/agents/revenue_bases.py` charges a mine royalty (`grep -n "royalt" sim/agents/revenue_bases.py` is empty), and mine
  workings are the founder's (`household.mines`; `sim/engine/mine_deposits.py`).
- **Recovery technology is a flat multiplier.** Cyanidation is an `output_multiplier` on the gold commodity
  (`data/world/commodities.json`, node `mt2_cyanidation`, read by `sim/engine/commodities.py`) rather than a recovery fraction applied to a deposit's grade
  (`sim/world/deposits.py`, `ore_dressing.py`).
- **Alternative recipes have no performance or failure.** `data/production/_SCHEMA.md` says margin, risk
  and failed batches are not modelled, so a weaker or riskier engine cannot be a worse good.

Why it matters: the group's test case is a navy funded far beyond what yards can build each year. The
limit must come from yards, timber and skilled hands, not a number.

What it would take: state commissions placed through the same recipe and plant path as private
producers (a hull is a good, a yard is plant); state-held assets with service life, wear and staff;
a revenue base for mine royalty; recovery and failure fields on recipes.
