# The engine cannot yet host several players or an agent economy: one founder is wired in, households are not actors, and most money moves without a counterparty

**Status:** open - steps 1 and 2 are done: every engine, agent and labour money posting goes through `ledger.transfer` and names an actor or a named edge (`sim/agents/edges.py`, held in `ActorsState.edges`), and wages, the state's pay and lenders' interest are paid to the home strata's purses (`sim/agents/payroll.py`); step 3 stages A (seat record, `act_as`, aliases not saved), B (economy, governance and scenario state split into world parts and seat parts: `state.holdings`, `state.governance`, `state.seat_progress` alias the acting seat, `sim/engine/state_holdings.py`) and C (one party id per seat: the goods market, credit, the capital market and the agent economy name the acting seat, no `FOUNDER` constant; unrun in a whole game) are built, and a seat holds patents and shares as an actor (Complaint 103); stage D (a second seat stepping with the year) is blocked as the plan's stage D status says (`_step_money` mixes world work, the end rule for several seats, the labour pool, no whole game to test on); stages E to I (commands addressing a seat, fog between seats) and step 4 remain. The one-sided volume is now zero by construction (`sim/tests/test_every_posting_names_a_counterparty.py` scans for new ones); what crosses each named edge is `state.actors.edge_volume`.

Multiplayer, and other countries as players, need every actor to be able to own money and goods, be somewhere, and pay someone. Today:

- **One founder.** `SimulationState` holds one `household`, one `projects`, one `founder` (`sim/engine/state.py`). The goods market's party was a hard-coded founder id and is now the acting seat's id (`sim/engine/goods_market_api.py`, stage C). A second player needs the household, project and knowledge fields to be per actor (stages A and B).
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

Measure what crosses each named edge as `state.actors.edge_volume` (divide by years played); the scan in the test above lists any posting that names no counterparty.

What it would take, in order:
1. Every engine posting names a counterparty, or a named edge.
2. Households become cohort actors with purses (the new economy's cohorts).
3. Per-actor household, project and knowledge state, so a second player can exist.
4. Partners become economies in the same agent model.

Related: 185, 189, 102, 381.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 401 (`closed/401-no-command-reaches-a-second-player.md`): no command reaches a second player.
- 402 (`closed/402-the-founder-is-not-a-player-actor.md`): the founder is not a player actor.
- 392 (`closed/392-one-money-per-economy-so-mexica-cloth-is-a-good.md`): one money per economy, so Mexica cloth is a good (design report: Complaints/reports/agent-economy-several-moneys.md).
- 270 (`closed/270-request-private-militia-bribery-and-campaign-influence.md`): private militia, bribery and campaign influence (owner: wait for multiplayer).

Owner decision (2026-10-09): high priority: do it as soon as possible.
