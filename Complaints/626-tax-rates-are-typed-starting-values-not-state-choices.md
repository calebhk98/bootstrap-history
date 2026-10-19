# Tax rates are typed in the civilisation file and are not a state choice

**Status:** open

Part of Complaint 542 (State capacity and tax rates are typed, there is no corvée, and the fiscal crisis is a fixed cascade).

Depends on 625 (consequences) and 595 (levers).

**What is wrong.** Each civilisation's `state_revenue` list declares form, base and rate.

**Evidence.** `data/civilizations/*.json`, `sim/agents/revenue.py`.

**Why it matters.** A rate without consequences is an input, not an outcome.

**What it would take.** Rates become a state choice once the consequences exist; the civilisation file keeps only the starting rates.

**Test.** A test: the file's rate is read only at setup; a state-set rate changes revenue and its consequences.
