"""Scenario (Complaint 640 audit): the engine derives a mine's capex from the deposit physics tested in test_mine_build_cost,
and technology cuts it."""
from .harness import *  # noqa: F401,F403
from sim.world import deposits

# --- the engine derives capex from the same physics, and technology cuts it.
_engine = sim(capital=1e9)
_pool = deposits.load_deposits("silver")
_effects = _engine.mine_works_effects()   # the running techniques change the works
_expected = (_engine.labour.wage_per_hour(_engine.MINE_TRADE)
             * sum(dep.quantity_tonnes_per_year
                   * deposits.build_cost_labour_hours_per_tonne_year(dep, _effects) for dep in _pool)
             / sum(dep.quantity_tonnes_per_year for dep in _pool))
check("engine silver capex is the quantity-weighted deposit build cost at the miner wage",
      abs(_engine._mine_capex("silver") - _expected) < 1e-6 * _expected,
      (_engine._mine_capex("silver"), _expected))
check("no curated per-material capex table remains",
      not hasattr(_engine, "MINE_CAPEX_PER_T_YR"))
_before = _engine.mine_quote("silver", 10.0)["to_sink_it"]
run_it(_engine, "met_mine_pumping")
_after = _engine.mine_quote("silver", 10.0)["to_sink_it"]
check("mine pumping lowers the cost to sink the same silver mine",
      _after < _before, (_before, _after))
_dear = _engine.mine_quote("gold", 10.0)["to_sink_it"]
_capital_before_sinking = _engine.state.household.capital
check("a quote is paid in full by open_mine",
      abs(_engine.open_mine("gold", 10.0, partial=False) - 10.0) < 1e-9)
check("paying the build cost takes what the quote said",
      abs((_capital_before_sinking - _engine.state.household.capital) - _dear) < 1e-6 * _dear + 1e-6,
      (_capital_before_sinking - _engine.state.household.capital, _dear))

