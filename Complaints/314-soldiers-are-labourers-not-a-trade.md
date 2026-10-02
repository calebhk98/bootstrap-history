# Soldiers are booked as labourers: there is no soldier trade, and conscription does not move the wage

**Status:** open - found while closing the rest of 286 and 287; next: a soldier trade (wage, trade density, hiring screens), then draw the army from it

The state's army is a `labourer` line in the budget (`sim/engine/actors/budget.py`). Soldiers are now taken out of production: `SimWorld.society_output` counts the working age less the soldiers the state keeps, so the state's own revenue falls with a larger army. Three things remain, each measurable.

1. There is no `soldier` entry in the wage table (`data/` wage schedule, `sim.engine.data.WAGES`), in `TRADE_DENSITY` or in the hiring and training screens, so a soldier cannot be a trade in the founder's labour pool. A trade needs a wage, a national population and a way to be recruited; adding one touches the wage provider, `national_trade_population` and every screen that lists trades, which is not a contained change.
2. Soldiers pulled out of production do not raise the unskilled wage the founder pays: `wage_per_hour("labourer")` comes from the schedule, not from the labour that is left. Check: run `python3 sim/budget_series.py rome_100ad 60 1` and compare `wage_per_hour("labourer")` in a year with a large army and in one with a small one.
3. The state's labourer staff (soldiers, road menders, court servants) enter the founder's pool as a share of the nation's working age (`BudgetView.local_staff`), which is right only while the army is small against the working age.

Related: 315.

Owner decision (2026-10-02): should be fixed.
