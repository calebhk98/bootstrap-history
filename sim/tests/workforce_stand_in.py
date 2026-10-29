"""A stand-in for the workforce module's views over a plain object that holds a seat's fields (a test fake of a game)."""
from types import SimpleNamespace

from sim.tests.ui_stand_in import FactViews

STAFF_FIELDS = ("employees", "scholars", "artisans", "directors_extra", "slaves", "freedmen", "manumitted_total",
                "reserve_craftsmen", "reserve_scholars")
HOURS = {"allocations": "hour_allocations", "work_trade": "work_trade", "wage_hours": "wage_hours_this_year",
         "wage_income": "wage_income_this_year", "teaching_hours": "teaching_hours_this_year",
         "relocation_hours": "relocation_hours_this_year", "supervision_hours": "supervision_hours_this_year",
         "contract_hours": "contract_hours", "commissioned": "commissioned", "last_year": "hours_this_year",
         "wage_work_last_year": "wage_work_last_year", "trade_hours_used": "trade_hours_used",
         "unused_reported": "unused_hours_reported", "last_taught": "last_taught",
         "director_hours_spent": "director_hours_spent_founder"}
EMPTY = {"employees": {}, "hour_allocations": {}, "contract_hours": {}, "commissioned": {}, "trade_hours_used": {},
         "unused_hours_reported": {}, "last_taught": {}, "trades_created": set(), "trades_endemic": set(), "trade_introduced_year": {},
         "training": [], "staff_pay_held": {}}


def _get(seat, name, default=0):
    return getattr(seat, name, EMPTY.get(name, default))


def views_over(seat):
    """{view name: the function that answers it} read off the fields of `seat`."""
    return {
        "staff": lambda: {key: _get(seat, key) for key in STAFF_FIELDS},
        "hour_commitments": lambda: {key: _get(seat, field, None if key in ("work_trade", "last_year", "wage_work_last_year") else 0)
                                     for key, field in HOURS.items()},
        "pay_book": lambda: {"prepaid": _get(seat, "wages_prepaid"), "earned": _get(seat, "wages_earned", None),
                             "paid": _get(seat, "wages_paid"), "pay_held": _get(seat, "staff_pay_held"),
                             "living_cost_paid": _get(seat, "living_cost_paid")},
        "training_queue": lambda: _get(seat, "training"),
        "trade_schools": lambda: _get(seat, "trade_schools", None) or {},
        "worker_housing_places": lambda: _get(seat, "worker_housing_places", None) or 0.0,
        "trade_spread": lambda: {"absent": [], "created": _get(seat, "trades_created"), "endemic": _get(seat, "trades_endemic"),
                                 "introduced_year": _get(seat, "trade_introduced_year")},
        "staff_version": lambda: 0,
    }


def view_of(seat, **more):
    """A `view(name)` function for a fake game: the workforce views over `seat`, and any `more` (name=callable)."""
    table = dict(views_over(seat), **more)

    def view(name):
        return table[name] if name in table else FactViews.view(seat, name)   # the facts the screens read, held as attributes
    return view


class World(SimpleNamespace):
    """A fake labour world whose purse is the `capital` of its `workforce` object (read live, put back by `restore_purse`)."""

    @property
    def balance(self):
        return self.workforce.capital

    def restore_purse(self, balance):
        self.workforce.capital = balance


def seat_of(**fields):
    """A seat holding the given fields."""
    return SimpleNamespace(**fields)


class Game(SimpleNamespace):
    """A fake game whose fields are one seat's workforce fields: it answers the workforce views over them and applies the
    workforce commands to them with the module's own handlers."""

    def __init__(self, **fields):
        super().__init__(**fields)
        self.view = view_of(self)
        self._sent = []

    def send(self, command):
        from sim.tests import module_harness
        from sim.workforce.module import Workforce
        from sim.workforce.module_spec import MODULE_SPECS
        self._sent.append(command)
        handlers = dict(MODULE_SPECS[0].applies)
        module = module_harness.build(Workforce, seat=self, world=getattr(self, "society", None))
        return getattr(module, handlers[type(command)])(command)
