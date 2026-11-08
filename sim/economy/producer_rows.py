"""The producer table's columns: one row per producer, a column for every field of `Producer`.

`ProducerRows` is the namedtuple of numpy columns the store (`producer_store.py`) holds; its spec below says what each column
means. A name (owner, recipe, tile, good, trade) is held as its number in the store's own `IdTable`; a field that is a short
list or a small mapping (the histories, the expected prices, the crew's practice) is a row of a width column plus a count of
the places in use. A field that may be absent (`land_run_cap`, `staffed_runs`) is NaN when absent."""
import numpy as np

from sim.compiled_tables.spec import Column, TableSpec

PRODUCER_ROWS_SPEC = TableSpec("ProducerRows", [
    Column("owner", np.int64, "the cohort or agent that owns the producer", "number", ids="owners"),
    Column("recipe", np.int64, "the recipe the producer works", "number", ids="recipes"),
    Column("tile", np.int64, "the tile it works on", "number", ids="tiles"),
    Column("capacity_runs", np.float64, "runs a year the plant and site allow", "runs per year"),
    Column("yield_factor", np.float64, "weather, depletion and site quality, set yearly", "ratio"),
    Column("years_of_loss", np.int64, "years running at a loss", "years"),
    Column("cash_target", np.float64, "cash it keeps; the rest is paid out as dividends", "money"),
    Column("expected_sales", np.float64, "runs' worth of output it expects to sell a year; zero is unknown", "runs per year"),
    Column("last_runs", np.float64, "runs it worked last year; below zero before its first year", "runs"),
    Column("land_rent_per_run", np.float64, "rent on the land a run works, set yearly by the land market", "money per run"),
    Column("land_run_cap", np.float64, "runs the land it was granted allows; NaN for no limit", "runs per year"),
    Column("workshops", np.int64, "independent workshops it stands for", "count"),
    Column("idle_years", np.int64, "years it stays idle after a bankruptcy", "years"),
    Column("staffed_runs", np.float64, "runs the hands it hired last year could have worked; NaN when unknown", "runs"),
    Column("numpy_typed", np.int64, "bit of each float field (`FLOAT_FIELDS` order) whose value was written as a numpy float, which a `Producer` built from the row hands back as one (numpy and Python scalars round some operations differently)", "bit set"),
    Column("earnings_count", np.int64, "places of `earnings_history` in use", "count"),
    Column("revenue_count", np.int64, "places of `revenue_history` in use", "count"),
    Column("price_count", np.int64, "places of the expected-price columns in use", "count"),
    Column("crew_count", np.int64, "places of the crew columns in use", "count"),
    Column("earnings_history", np.float64, "its last years' net earnings, oldest first", "money", width=0),
    Column("revenue_history", np.float64, "its last years' revenue, oldest first", "money", width=0),
    Column("price_good", np.int64, "the good each expected price is for, in the order the expectations were written", "number",
           ids="goods", width=0),
    Column("price_value", np.float64, "the expected price of `price_good`", "money per unit", width=0),
    Column("crew_trade", np.int64, "the trade each crew practice figure is for, in the order written", "number", ids="trades", width=0),
    Column("crew_units", np.float64, "the runs the crew has made at `crew_trade`", "runs", width=0),
])

ProducerRows = PRODUCER_ROWS_SPEC.make_type(__name__)

SCALAR_FLOATS = ("capacity_runs", "yield_factor", "cash_target", "expected_sales", "last_runs", "land_rent_per_run")
SCALAR_INTS = ("years_of_loss", "workshops", "idle_years")
OPTIONAL_FLOATS = ("land_run_cap", "staffed_runs")
FLOAT_FIELDS = SCALAR_FLOATS + OPTIONAL_FLOATS
FLOAT_BIT = {name: 1 << place for place, name in enumerate(FLOAT_FIELDS)}
WIDE_COLUMNS = ("earnings_history", "revenue_history", "price_good", "price_value", "crew_trade", "crew_units")
NAME_COLUMNS = ("owner", "recipe", "tile")
