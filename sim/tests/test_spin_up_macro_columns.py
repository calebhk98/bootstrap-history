"""The spin-up trace's four macro columns (`macro_columns`) from a written-out year outcome: the basket level, the
unskilled trade's wage, idle hours over hours offered, and the real output passed in."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.markets.port_trace_columns import macro_columns

outcome = SimpleNamespace(basket_price_level=1.25, wages={"labourer": 3.0, "smith": 9.0}, hired_hours=300.0, idle_hours=100.0)
columns = macro_columns(outcome, "labourer", 42.0)
check("the four columns read from the outcome", columns == {"price_level": 1.25, "wage": 3.0, "unemployment": 0.25, "real_output": 42.0},
      columns)

none_offered = SimpleNamespace(basket_price_level=1.0, wages={}, hired_hours=0.0, idle_hours=0.0)
columns = macro_columns(none_offered, "labourer", 0.0)
check("no hours offered and no wage are None, not zero", columns["unemployment"] is None and columns["wage"] is None, columns)
