# Tax rates are typed in the civilisation file and are not a state choice

**Status:** closed

Part of Complaint 542 (State capacity and tax rates are typed, there is no corvée, and the fiscal crisis is a fixed cascade).

Depends on 625 (consequences) and 595 (levers).

**What was wrong.** Each civilisation's `state_revenue` list declared form, base and rate, and the file was read every year.

**Evidence.** `data/civilizations/*.json`, `sim/agents/revenue.py`.

## Outcome

- Setup copies the file's forms into the state's record once (`ActorRecord.revenue_forms`, filled by `sim/agents/cast.py`).
  `government_levers.revenue_forms(record)` reads that record, then the state's own rate levers; the file is not read again.
  The lever context (`sim/ui/proto/dispatch_levers.py`) names the record's forms.
- A player state sets a rate with the 595 `lever` command. The rate reaches the economy: `YearInputs.tax_rates`
  (`sim/engine/economy_port_land.py`) hands the economy the rates the state holds, and `taxes.with_rates` applies them to
  the forms the economy collects (coin forms and in-kind forms on economy bases). Before this the economy collected at the
  file's rate frozen in its setup, so a lever moved the state's assessment but not the coin that moved.
- An AI state changes a rate with its fiscal policy: `sim/agents/fiscal_response.py` has a seventh response, `raise_rate`.
  Its capacity is the base of the state's coin forms times `RATE_RAISE_STEP`; its consequence is the burden on that base
  (`income_taken`, valued at `FISCAL_BURDEN_WEIGHT`), plus the carry the other deferring responses count. The raise goes
  through the same `set_lever` a player pulls (`Government.raise_coin_rates`). `LEVY_FIRST_ORDER` includes it.
- Tests: `sim/tests/test_state_rates_are_the_states.py` (the file's rate is read only at setup, a state-set rate changes
  the yield, the economy collects at the state's rates, a save keeps the rates) and `sim/tests/test_state_fiscal_response.py`
  (an AI state under a shortfall raises a coin form's rate).
- Left: no consequence of a higher rate exists beyond the revenue and the burden weight, so no elasticity was invented.
  Complaint 657 files the missing ones (flight from a taxed base, resentment). A form a state starts by lever is assessed
  by the actor layer but the economy collects only the forms it was set up with.
