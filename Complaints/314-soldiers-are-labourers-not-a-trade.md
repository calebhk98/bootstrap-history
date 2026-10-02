# Soldiers are booked as labourers: there is no soldier trade, and conscription does not move the wage

**Status:** partly - soldier is a trade in the one labour market (wage, state hiring, recruitment pressure, test state_soldier_trade); remaining: withdraw soldiers from the society's labour allocation so the unskilled wage moves by tightness, not only through the pressure curve

The state's army is a `labourer` line in the budget (`sim/engine/actors/budget.py`). Soldiers are now taken out of production: `SimWorld.society_output` counts the working age less the soldiers the state keeps, so the state's own revenue falls with a larger army. Three things remain, each measurable.

1. There is no `soldier` entry in the wage table (`data/` wage schedule, `sim.engine.data.WAGES`), in `TRADE_DENSITY` or in the hiring and training screens, so a soldier cannot be a trade in the founder's labour pool. A trade needs a wage, a national population and a way to be recruited; adding one touches the wage provider, `national_trade_population` and every screen that lists trades, which is not a contained change.
2. Soldiers pulled out of production do not raise the unskilled wage the founder pays: `wage_per_hour("labourer")` comes from the schedule, not from the labour that is left. Check: run `python3 sim/budget_series.py rome_100ad 60 1` and compare `wage_per_hour("labourer")` in a year with a large army and in one with a small one.
3. The state's labourer staff (soldiers, road menders, court servants) enter the founder's pool as a share of the nation's working age (`BudgetView.local_staff`), which is right only while the army is small against the working age.

Related: 315.

Owner decision (2026-10-02): should be fixed.

Built (owner decision 2026-10-02): `soldier` is in `data/world/trades.json`; the army line is people of that trade at the labour market's quote for it; its national pool is the working age; hiring presses the soldier trade, so conscription moves the soldier wage; soldiers under arms are a standing draw on the unskilled pool (`LabourMarket.standing_draw`), which raises the unskilled price factor, and they owe no poll tax. Still open: `society_labour_hours` (labour_allocation.py) takes the whole working age, so soldiers do not leave production or farming, and the unskilled wage rises only through the pressure curve; the effect is small at a real army's share of the working age. Measure with `python3 sim/budget_series.py rome_100ad 100 1` (soldier and unskilled wage columns).
