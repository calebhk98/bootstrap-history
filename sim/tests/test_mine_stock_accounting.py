"""mine_stock_accounting: complaint 148, banked stock is the mine's yearly flow, once per year."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.economy import _mine_rows_for_material

_MATERIAL = "galena"
_KEY = "galena_kg"
_RATED = 280.0


def _mine_fixture():
    test_sim = sim(capital=500000.0)
    test_sim.open_mine(_MATERIAL, _RATED, partial=False)
    return test_sim


# A working with nothing consuming it banks exactly its yearly yield for each year it has run.
mine_sim = _mine_fixture()
yearly_yield = None
years_producing = 0
for _ in range(5):
    mine_sim.step()
    if mine_sim.mine_capacity.get(_KEY):
        years_producing += 1
        yearly_yield = sum(mine_sim.mine_yield_t_for(working) for working in mine_sim._workings_of(_KEY))
banked = mine_sim.material_stock_t(_KEY)
check("set-up: the working came ready and produced for several years", years_producing >= 2, years_producing)
check("stock on hand equals the yearly yield times the years it has run (nothing consumes it)",
      abs(banked - yearly_yield * years_producing) < 0.02 * yearly_yield * years_producing,
      (banked, yearly_yield, years_producing))

# Anything that recomputes the year's materials mid-year must not bank the year again.
mine_sim.resource_throttle()   # the new year's output is banked by the first recompute
stock_before = mine_sim.material_stock_t(_KEY)
for _ in range(25):
    mine_sim.sell_material_stock(_KEY, 1.0)
    mine_sim.resource_throttle()
check("selling 1 t twenty-five times in one year removes 25 t and banks nothing new",
      abs(mine_sim.material_stock_t(_KEY) - (stock_before - 25.0)) < 1e-6,
      (stock_before, mine_sim.material_stock_t(_KEY)))

# A saved and reloaded game keeps the same stock through the same recomputation.
from sim.engine.saveload import save_state, load_state
save_path = os.path.join(tempfile.mkdtemp(), "mine_stock.json")
save_state(mine_sim, save_path)
reloaded = sim(capital=1.0)
load_state(reloaded, save_path)
stock_saved = reloaded.material_stock_t(_KEY)
reloaded.resource_throttle()
check("a reload followed by a recompute in the same year leaves the stock unchanged",
      abs(reloaded.material_stock_t(_KEY) - stock_saved) < 1e-6,
      (stock_saved, reloaded.material_stock_t(_KEY)))

# The mines screen columns: RATED is tonnes sunk, ACTUAL what it raises now, UTIL the share of ACTUAL drawn.
mine_sim.mine_yield_t_for = lambda working: 2.0 * working["capacity"]   # technology doubles the yield
row = _mine_rows_for_material(mine_sim, _KEY, mine_sim._workings_of(_KEY), 100.0)[0]
check("ACTUAL can exceed RATED once technology raises the yield",
      row["actual_output_t_per_yr"] == 2 * row["rated_capacity_t_per_yr"], row)
check("UTIL is the share of ACTUAL that demand draws (100 t of 560 t is 18%), never above 100%",
      row["utilization"] == "18%", row["utilization"])
