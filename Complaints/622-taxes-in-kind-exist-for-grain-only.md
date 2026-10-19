# Taxes in kind exist for grain only

**Status:** open

Part of Complaint 542 (State capacity and tax rates are typed, there is no corvée, and the fiscal crisis is a fixed cascade).

**What is wrong.** `paid_in` is grain-only.

**Evidence.** `sim/agents/government_stores.py`.

**Why it matters.** States demanded goods in kind when short of money.

**What it would take.** A kind levy on any good the base names, stored and used by the state like grain.

**Test.** A test: a levy on a non-grain good moves stock from households to the state's store.
