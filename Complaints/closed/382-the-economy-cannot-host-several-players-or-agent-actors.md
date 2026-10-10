# The engine cannot yet host several players or an agent economy: one founder is wired in, households are not actors, and most money moves without a counterparty

**Status:** closed - several seats step together (stages D to F: the year runs world phases once and seat phases per seat, a seat's end stops that seat only, commands address a seat with `as`, fog and diffusion count every seat), households and money are actors with named counterparties (steps 1 and 2), and partner countries are economies in the same agent model (step 4 and stages G to I: tiles carry a country, producers follow its techniques, its pay, prices and output are read from its own markets, a seat of another country deals in them). The slow proof `test_partner_in_agent_economy.py` has since run on the close-complaints-batch-3 branch (8 checks, 0 failures, about 26 minutes) and the partner switch `agent_economy` in `data/world/foreign_economies.json` is on for Han (Complaint 407).

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

Owner decision (2026-10-09): when one player's founder dies in a run where founders are mortal, the game stops for that player only; every other seat keeps playing. In an immortal-founder run this never arises.


Closed with the owner's end rule built (`sim/engine/seat_run.py`) and the plan's stage statuses in `docs/architecture/MULTI_ACTOR_STATE_PLAN.md`. What each part cannot do yet is listed there, per stage.
