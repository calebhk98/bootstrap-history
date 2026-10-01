# Employers reach into the wage code instead of asking one labour market, and two employers can pay different wages for the same trade

**Status:** open

The founder's wage is `annual_wage` (`labour_wages.py`): base times cost factors, `price_index`, `wage_index`, the local premium and the pay scale. Firms hire at `SimWorld.hiring_wage_per_hour` (`market_wage_per_hour` times the premium, `actors/world.py`), which omits `price_index`, `wage_index` and the cost factors; a firm's wage bill uses `wage_per_hour` with no premium; the state's budget and the interest groups read `market_wage_per_hour`, `labour_pressure_records` and `labour_price_factor` directly; hiring calls `_add_labour_pressure` from three places. Measured: with `price_index` 1.5 an artisan costs the founder 2.41 an hour and a firm 1.61 in the same market in the same year. The trade-allocation solver in `sim/world/labour_market.py` is not an interface employers use.

What it would take: a `LabourMarket` every employer asks (quote a rate for a trade and hours, hire, release, read the pressure), with the wage formula inside it and nowhere else; employers (founder, firms, state, groups) hold no wage arithmetic; a test that every kind of employer is quoted the same rate for the same trade at the same time. Then the labour market and the employers can be worked on separately (CLAUDE.md, general actors).
