# The engine cannot yet host several players or an agent economy: one founder is wired in, households are not actors, and most money moves without a counterparty

**Status:** open - the new agent economy (`sim/economy/`, docs/architecture/ECONOMY_AGENTS.md) is built as if these were fixed; engine postings without a counterparty are booked against `edge:legacy` so their volume is measured

Multiplayer, and other countries as players, need every actor to be able to own money and goods, be somewhere, and pay someone. Today:

- **One founder.** `SimulationState` holds one `household`, one `projects`, one `founder` (`sim/engine/state.py`). The goods market names its only party `FOUNDER = "founder"` (`sim/engine/goods_market_api.py:23`). A second player needs the household, project and knowledge fields to be per actor.
- **Households are not actors.** Population is three national floats (`sim/world/demography.py`, `Population`). Wages, taxes and interest owed to households have no purse to land in.
- **Nothing is located.** `ActorRecord.location` exists (`sim/engine/state.py:453`) and is never set; the founder's base tile is a household field.
- **Money has no currency.** Purses are bare floats in the home coin; foreign amounts are converted by a scalar at the point of use (`sim/engine/foreign_payments.py`).
- **Money moves one-sided.** `ledger.transfer` (`sim/agents/ledger.py`) is the only two-sided posting and few call sites use it. Examples of one-sided postings:
  - Firm takings come from a formula, and wages and upkeep go to nobody (`sim/agents/firm.py:70-72`).
  - State tax revenue is credited from a modelled base, not paid by anyone (`sim/agents/government_stores.py:31`).
  - State budget lines are debited to nobody, and purchases only note tonnes (`sim/agents/government.py:91-93`).
  - The founder's yearly revenue, upkeep and living cost post as one net amount.
  - About forty other founder postings name a purpose but no payee.

  `lose_capital` (`sim/engine/society_hazards.py:390`) destroys money; one confiscation path pays the taken money to the treasury (`sim/engine/society_state_pressure.py`), and others do not.
- **Partners are records, not actors.** Foreign economies are dict ledgers (`economy.foreign_ledger`).
- **Prices are global to one civilisation.** `price_index` is a static float set from the civilisation file (`sim/engine/core.py:344`). The tree's money fields (`rev`, `up`, `cap`) are priced once at load for one coin (`sim/engine/money_units.py:price_nodes`).

Measure the one-sided volume, once the port books it, as the yearly volume of `edge:legacy`. Until then, `grep -rn "\.credit(\|\.debit(" sim/engine` lists the postings.

What it would take, in order:
1. Every engine posting names a counterparty, or a named edge.
2. Households become cohort actors with purses (the new economy's cohorts).
3. Per-actor household, project and knowledge state, so a second player can exist.
4. Partners become economies in the same agent model.

Related: 185, 189, 102, 381.
