"""The cohort table's columns: one row per cohort, a column for every field of `Cohort`.

`CohortRows` is the namedtuple of numpy columns the store (`cohort_store.py`) holds. A name (tile, need, good) is held as its
number in the store's own `IdTable`; a field that is a small mapping or tuple (the unmet floors, the own plan, the grains bought
milled) is a row of a width column plus a count of the places in use. `share_wealth` is NaN until a close sets it."""
import numpy as np

from sim.compiled_tables.spec import Column, TableSpec

COHORT_ROWS_SPEC = TableSpec("CohortRows", [
    Column("tile", np.int64, "the tile whose people the cohort stands for", "number", ids="tiles"),
    Column("income_class", np.int64, "income class on its tile; 0 is the poorest", "class"),
    Column("people", np.float64, "people the cohort stands for", "people"),
    Column("working_people", np.float64, "of whom working age", "people"),
    Column("ownership_share", np.float64, "share of the tile's rent and profit the class receives", "ratio"),
    Column("expected_inflation", np.float64, "yearly price rise it expects", "ratio per year"),
    Column("cash_target", np.float64, "cash it rests at; zero until the first close", "money"),
    Column("last_basket_price_level", np.float64, "basket price level at the last close", "ratio"),
    Column("last_year_income", np.float64, "income of the year before", "money"),
    Column("share_wealth", np.float64, "what it owned of the firms at the last close; NaN before one", "money"),
    Column("planned_spending", np.float64, "money placed in bids this year", "money"),
    Column("expected_spending", np.float64, "smoothed spending that sizes the stock of durables it wants", "money"),
    Column("expected_floor_cost", np.float64, "smoothed cost of the cohort's need floors", "money"),
    Column("hired_work_per_person", np.float64, "hours of household work a person's share hires this year", "hours per person"),
    Column("numpy_typed", np.int64, "bit of each float field (`FLOAT_FIELDS` order) whose value was written as a numpy float, which a `Cohort` built from the row hands back as one (numpy and Python scalars round some operations differently)", "bit set"),
    Column("unmet_count", np.int64, "places of the unmet-floor columns in use", "count"),
    Column("plan_count", np.int64, "places of the own-plan columns in use", "count"),
    Column("milled_count", np.int64, "places of the milled-grain column in use", "count"),
    Column("unmet_need", np.int64, "the need each unmet figure is for, in the order written", "number", ids="needs", width=0),
    Column("unmet_units", np.float64, "need units short of the floor", "need units", width=0),
    Column("unmet_typed", np.int8, "1 where the figure was written as a numpy float", "flag", width=0),
    Column("plan_need", np.int64, "the need each own-plan figure is for, in the order written", "number", ids="needs", width=0),
    Column("plan_units", np.float64, "need units it grows with hours kept back", "need units", width=0),
    Column("plan_typed", np.int8, "1 where the figure was written as a numpy float", "flag", width=0),
    Column("milled_good", np.int64, "the grains it buys milled, in the order written", "number", ids="goods", width=0),
])

CohortRows = COHORT_ROWS_SPEC.make_type(__name__)

FLOAT_FIELDS = ("people", "working_people", "ownership_share", "expected_inflation", "cash_target", "last_basket_price_level",
                "last_year_income", "share_wealth", "planned_spending", "expected_spending", "expected_floor_cost",
                "hired_work_per_person")
FLOAT_BIT = {name: 1 << place for place, name in enumerate(FLOAT_FIELDS)}
OPTIONAL_FLOATS = ("share_wealth",)
SCALAR_FLOATS = tuple(name for name in FLOAT_FIELDS if name not in OPTIONAL_FLOATS)
# the columns of one wide group grow together
WIDE_GROUPS = {"unmet": ("unmet_need", "unmet_units", "unmet_typed"), "plan": ("plan_need", "plan_units", "plan_typed"),
               "milled": ("milled_good",)}
WIDE_COLUMNS = tuple(name for group in WIDE_GROUPS.values() for name in group)
