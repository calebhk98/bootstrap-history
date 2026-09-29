"""mine build cost: shafts, hoist capacity, technology, and the amortised share."""
import math

from .harness import *  # noqa: F401,F403
from sim.constants import REGISTRY
from sim.engine.data import WAGES
from sim.world import deposits


def _deposit(grade=10.0, depth_class="shallow_vein", hardness="medium",
             quantity=100.0, name="probe"):
    return deposits.Deposit(
        name=name, metal="probe_metal", region="nowhere", material_moved="ore",
        ore_grade_kg_per_tonne=grade, depth_class=depth_class,
        hardness_class=hardness, quantity_tonnes_per_year=quantity, note="")


# --- a shaft costs what the rock and depth make it cost, not what is in it.
_poor = _deposit(grade=0.001, quantity=1.0)
_rich = _deposit(grade=900.0, quantity=50000.0)
check("shaft cost ignores ore grade and quantity",
      deposits.shaft_cost_labour_hours(_poor) == deposits.shaft_cost_labour_hours(_rich),
      (deposits.shaft_cost_labour_hours(_poor), deposits.shaft_cost_labour_hours(_rich)))
check("a shaft costs something", deposits.shaft_cost_labour_hours(_poor) > 0)

_shallow = _deposit(depth_class="shallow_vein")
_deep = _deposit(depth_class="deep_vein")
check("a deeper shaft costs more in total",
      deposits.shaft_cost_labour_hours(_deep) > deposits.shaft_cost_labour_hours(_shallow))
check("a deeper shaft costs more per metre",
      deposits.shaft_cost_labour_hours(_deep) / deposits.shaft_depth_metres(_deep)
      > deposits.shaft_cost_labour_hours(_shallow) / deposits.shaft_depth_metres(_shallow))
check("harder rock costs more to sink through",
      deposits.shaft_cost_labour_hours(_deposit(hardness="hard"))
      > deposits.shaft_cost_labour_hours(_deposit(hardness="soft")))
check("a deeper shaft raises less per year",
      deposits.shaft_rock_capacity_tonnes_per_year(_deep)
      < deposits.shaft_rock_capacity_tonnes_per_year(_shallow))
check("surface ground needs no shaft",
      deposits.shafts_needed(_deposit(depth_class="surface"), 500.0) == 0)

# --- capacity N needs ceil(rock to raise / what one shaft raises) shafts.
_per_shaft_metal = (deposits.shaft_rock_capacity_tonnes_per_year(_shallow)
                    / (_shallow.ore_grade_kg_per_tonne ** -1 * 1000.0))
for _tonnes in (0.5 * _per_shaft_metal, 1.0 * _per_shaft_metal,
                1.01 * _per_shaft_metal, 7.3 * _per_shaft_metal):
    check("shafts_needed is ceil(N / per-shaft) for N=%.3f" % _tonnes,
          deposits.shafts_needed(_shallow, _tonnes) == math.ceil(_tonnes / _per_shaft_metal - 1e-9),
          (deposits.shafts_needed(_shallow, _tonnes), _tonnes / _per_shaft_metal))
check("build cost is shafts times the per-shaft cost",
      deposits.build_cost_labour_hours(_shallow, 7.3 * _per_shaft_metal)
      == 8 * deposits.shaft_cost_labour_hours(_shallow))
check("a richer ore needs fewer shafts for the same metal output",
      deposits.shafts_needed(_deposit(grade=100.0), 50.0)
      < deposits.shafts_needed(_deposit(grade=1.0), 50.0))

# --- the solver's amortised share is that same per-shaft cost, spread.
_district = _deposit(quantity=400.0, depth_class="deep_vein", grade=5.0)
_reserve_kg = (_district.quantity_tonnes_per_year
               * deposits.DEPOSIT_ASSUMED_WORKING_LIFE_YEARS * 1000.0)
check("amortised sinking share times reserve is shafts_needed x shaft cost",
      abs(deposits.amortized_sinking_cost_labour_hours_per_kg(_district) * _reserve_kg
          - deposits.shafts_needed(_district, 400.0) * deposits.shaft_cost_labour_hours(_district))
      < 1e-6 * deposits.build_cost_labour_hours(_district, 400.0))
check("a district of many shafts is charged for all of them",
      deposits.shafts_needed(_district, 400.0) > 1, deposits.shafts_needed(_district, 400.0))

# --- the engine derives capex from the same physics, and technology cuts it.
_engine = sim(capital=1e9)
_pool = deposits.load_deposits("silver")
_expected = (WAGES["miner"]
             * sum(dep.quantity_tonnes_per_year
                   * deposits.build_cost_labour_hours_per_tonne_year(dep) for dep in _pool)
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
check("a quote is paid in full by open_mine",
      abs(_engine.open_mine("gold", 10.0, partial=False) - 10.0) < 1e-9)
check("paying the build cost takes what the quote said",
      abs((1e9 - _engine.state.household.capital) - _dear) < 1e-6 * _dear + 1e-6,
      (1e9 - _engine.state.household.capital, _dear))

# --- the hardcoded outcomes it replaces are gone.
_gone = [name for name in REGISTRY
         if name.startswith("MINE_CAPEX_PER_T_YR") or name == "GENERIC_MINE_CAPEX_MULTIPLE"]
check("the capex hardcoded outcomes are no longer declared", not _gone, _gone)
_left = [name for name, entry in REGISTRY.items() if entry["kind"] == "hardcoded_outcome"]
check("the hardcoded-outcome count fell below the eleven it began at",
      len(_left) <= 5, _left)
