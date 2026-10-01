# The founder's payroll and every labour cost the price solver sets stay at the opening wage while firms now pay what an hour earns

**Status:** open - found while making what a firm carries follow the economy (Complaints 620, 600). Measure with `_fp`-style drivers: Rome seed 1, recommended strategy, `Sim.wage_per_hour("labourer")` against `Sim.market_wage_per_hour("labourer")` per decade.

`Sim.market_wage_per_hour` is the wage table times `labour_pay_scale()` (the volume a concern sells over the authored volume, `output_volume_scale()`, to the power `LABOUR_PAY_SHARE_OF_OUTPUT_GAIN`). Firms (`SimWorld.concern_wage_bill`, `hiring_wage_per_hour`), the household and group budgets and `society_output` read it. Three things still read the bare table:

- **The founder's own payroll** (`annual_wage`, `wage_bill`, `living_cost`). It is left bare on purpose: scaling it made the founder's research staff cost as much more as the economy index rose while nothing paid for them, and the Rome seed-1 run (seeds 1 to 3) then never left debt, so the economy index stayed near three for 150 years. The founder therefore hires an hour cheaper than a firm does; a firm that matches the founder's staffing pays more. Fix when the economy index is replaced by diffusion that actually earns (Complaint 104), or when the founder's non-earning staff have a revenue of their own.
- **Labour inside project costs, freight, mining and the price solver** (`wage_document`, `project_cost`, `economy_freight`, `economy_mining`). A richer economy makes the same project no dearer in labour. Making the solver follow the pay scale moves every solved price and every derived `rev`, which `output_volume_scale` already multiplies, so it would count the gain twice; it needs the generic index gone first.
- **Firms' wages carry neither `price_index` nor the demographic `wage_index`**, where the founder's `annual_wage` carries both.

Related: `104`, `287`, `600`, `620`.
