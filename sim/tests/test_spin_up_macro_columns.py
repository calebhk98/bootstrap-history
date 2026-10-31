"""The spin-up trace's macro columns (`macro_columns`) from a written-out year outcome and its market rows: the basket
level, the unskilled trade's wage, the unsold-hours share, the people-weighted unemployment, and the real output."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.markets.port_trace_columns import macro_columns

# hired 225 and idle 275 of 500 offered; the people-weighted rate over the two markets is (100 * 0.25 + 300 * 0.625) / 400
outcome = SimpleNamespace(basket_price_level=1.25, wages={"labourer": 3.0, "smith": 9.0}, hired_hours=225.0, idle_hours=275.0)
markets = [(100.0, 100.0, 75.0), (300.0, 400.0, 150.0)]
columns = macro_columns(outcome, "labourer", 42.0, markets)
check("the price level, wage and real output are read from the outcome",
      columns["price_level"] == 1.25 and columns["wage"] == 3.0 and columns["real_output"] == 42.0, columns)
check("the unsold-hours share is hours idle over hours offered", abs(columns["unsold_hours_share"] - 0.55) < 1e-12, columns)
check("the people unemployment rate is weighted by people, not hours",
      abs(columns["people_unemployment"] - 0.53125) < 1e-12, columns)
check("the row carries exactly the five macro figures", set(columns) == {"price_level", "wage", "real_output",
                                                                         "unsold_hours_share", "people_unemployment"}, columns)

none_offered = SimpleNamespace(basket_price_level=1.0, wages={}, hired_hours=0.0, idle_hours=0.0)
columns = macro_columns(none_offered, "labourer", 0.0, [(100.0, 0.0, 0.0)])
check("no hours offered and no wage are None, not zero",
      columns["unsold_hours_share"] is None and columns["people_unemployment"] is None and columns["wage"] is None, columns)
