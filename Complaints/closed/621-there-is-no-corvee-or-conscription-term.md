# There is no corvée or conscription term: labour levies do not exist

**Status:** closed. A revenue form on the basis `labour_days` declares days a year per working-age person or per household, for the state's works or its army, with a share commuted to coin (`sim/agents/revenue_labour.py`, `data/civilizations/_SCHEMA.md`). The hours come off the working time of the people it falls on: the state books them (`record.corvee_hours`), the engine hands them to the economy as `labour_levy_hours_per_worker` (`sim/engine/economy_port_levy.py`), and households offer fewer hours at a dearer wage (`sim/economy/year_labour.py`), so their income and the labour market show the loss. Corvee labour takes the place of the wages of roads, buildings and walls, then raises the works the state lacks, unpaid (`sim/agents/government_corvee.py`); conscripts fill the army unpaid and count against the 602 head count (`sim/agents/budget.py`, `government.py`). Han declares a corvee. Tests: `test_state_corvee.py`, `test_economy_labour_levy.py`, `test_state_corvee_game.py`. Not done: a state that chooses to commute at run time (the share is data), and conscripts do not yet leave the labour core's trade counts.

Part of Complaint 542 (State capacity and tax rates are typed, there is no corvée, and the fiscal crisis is a fixed cascade).

Shares the seasonal slack gap noted in 530.

**What is wrong.** Corvée appears only in civilisation prose; soldiers are a typed `standing_army` share paid at wage, not drafted for a term.

**Evidence.** `sim/agents/country_view.py`; Han prose in `data/civilizations/`.

**Why it matters.** Labour levies were a main revenue form of several states.

**What it would take.** Corvée and conscription as labour levies in days per adult, drawn from household time, with commutation to cash as a state choice.

**Test.** A test: a levy removes days from household time and adds them to state works; commuting turns them into cash.
