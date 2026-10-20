# Tax rates are typed in the civilisation file and are not a state choice

**Status:** open - partly done: a state-set rate is read ahead of the file's rate (595 levers) and the state's demand in kind raises the rates of its in-kind forms (`Government.demand_in_kind`, test `state_fiscal_response`). Still open: a coin form's rate is not yet a state choice, and the file's rate is still read each year when no lever is set rather than copied once at setup.

Part of Complaint 542 (State capacity and tax rates are typed, there is no corvée, and the fiscal crisis is a fixed cascade).

Depends on 625 (consequences) and 595 (levers).

**What is wrong.** Each civilisation's `state_revenue` list declares form, base and rate.

**Evidence.** `data/civilizations/*.json`, `sim/agents/revenue.py`.

**Why it matters.** A rate without consequences is an input, not an outcome.

**What it would take.** Rates become a state choice once the consequences exist; the civilisation file keeps only the starting rates.

**Test.** A test: the file's rate is read only at setup; a state-set rate changes revenue and its consequences.
