# There is no corvée or conscription term: labour levies do not exist

**Status:** open

Part of Complaint 542 (State capacity and tax rates are typed, there is no corvée, and the fiscal crisis is a fixed cascade).

Shares the seasonal slack gap noted in 530.

**What is wrong.** Corvée appears only in civilisation prose; soldiers are a typed `standing_army` share paid at wage, not drafted for a term.

**Evidence.** `sim/agents/country_view.py`; Han prose in `data/civilizations/`.

**Why it matters.** Labour levies were a main revenue form of several states.

**What it would take.** Corvée and conscription as labour levies in days per adult, drawn from household time, with commutation to cash as a state choice.

**Test.** A test: a levy removes days from household time and adds them to state works; commuting turns them into cash.
