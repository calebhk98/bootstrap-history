# The `wage_materials` view lists only the staple, never the trades' tool materials

**Status:** open

`wage_materials` is meant to answer "the materials a wage is set against, in order: the staple, and every trade's tool
materials" (its docstring, `sim/workforce/views.py`; the same text was on the engine bridge entry it replaced). It was
computed as `trade_data.registry_of(sim)` over the `Sim` object, but `registry_of` reads the world's `trade_registry`
attribute and `Sim` has none (`python3 -c "import sys; sys.path.insert(0,'.'); from sim.engine.core import Sim; print(hasattr(Sim, 'trade_registry'))"`
prints `False`), so the registry was always empty and the answer was the staple alone. The workforce module keeps that
answer (the move changed no behaviour) and says so in the view's docstring.

Why it matters: `record_wage_market_ratios` (`sim/reporting/price_ratios.py`) records the real price ratio of each
material the view names at every year's close, and `last_market_price_ratio` falls back to one for a material never
recorded. A tool material is never recorded, so the tools factor of every trade's wage (`wage_cost_factors` in
`sim/labour/labour_wages.py`) reads one however dear the tools have become.

What it would take: build the answer from the trade registry the module already holds (`Workforce.trade_registry`),
which adds every trade's `tool_basket` materials, then re-run the equivalence tiers: the figures that read this view
will change, so the fix is a gameplay change and not part of a move.
