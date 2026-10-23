"""Complaint 556: who can work and who is hired by whom has one owner, the labour package.

Rule tests (Complaint 640): the founder's book accessors and the reservation arithmetic run on a stub world, and the
wall keeps every write of the founder's book inside the owner."""
import ast
import os
import re
from types import SimpleNamespace

from sim.labour.staff_book import StaffBookMixin

from .harness import *  # noqa: F401,F403

QUICK_TOPIC = True


class _Book(StaffBookMixin):
    """The owner's book over a stub world: a household with a staff map and the other employers' staff."""

    def __init__(self, other_staff, supply):
        self._world = SimpleNamespace(
            state=SimpleNamespace(household=SimpleNamespace(employees={})),
            actors_staff_nationwide=lambda trade: other_staff.get(trade, 0.0),
            HOURS_PER_PERSON_YEAR=2000.0)
        self._supply = supply

    def people_who_exist(self, trade):
        return self._supply.get(trade, 0.0)


# ---- the founder's book is the owner's ----
book = _Book(other_staff={"artisan": 4.0}, supply={"artisan": 10.0, "labourer": 5.0})
household = book._world.state.household
household.employees["artisan"] = 3.0
check("the owner reads the founder's head count", book.employed("artisan") == 3.0)
book.set_employed("artisan", 2.0)
check("set_employed writes the household's book", household.employees["artisan"] == 2.0 and book.employed_total() == 2.0)
book.add_employed("artisan", -2.0)
check("a count of nothing leaves the trade off the book",
      "artisan" not in household.employees and book.employed_by_trade().get("artisan") is None)
book.add_employed("labourer", 3.0)
copy = book.employed_by_trade()
copy["labourer"] = 99.0
check("the staff the owner reports is a copy", household.employees["labourer"] == 3.0)

# ---- a reservation is the founder's staff plus the other employers' ----
book.set_employed("artisan", 2.0)
check("reserved people are the book plus the firms' and states' staff", book.reserved_people("artisan") == 6.0, book.reserved_people("artisan"))
check("reserved hours are people times hours a person-year", book.reserved_hours("artisan") == 6.0 * 2000.0)
check("unreserved people are the supply less every reservation", book.unreserved_people("artisan") == 4.0, book.unreserved_people("artisan"))
book.set_employed("labourer", 9.0)
check("unreserved people are never negative", book.unreserved_people("labourer") == 0.0)

# ---- a hire is taken out of the core's people at the base tile, and the estimate reads the core ----
class _CoreBook(StaffBookMixin):
    def __init__(self, core, staff):
        self._world = SimpleNamespace(state=SimpleNamespace(household=SimpleNamespace(employees=dict(staff))))
        self._core = core

    def core_people_by_tile_and_trade(self):
        return self._core

    def base_tile(self):
        return "home"


core_book = _CoreBook({"home": {"labourer": 5.0}, "away": {"labourer": 2.0}}, {"labourer": 3.0})
check("the founder's hire is taken from the core at the base tile, not counted free for another employer",
      core_book.free_core_people("labourer") == 4.0, core_book.free_core_people("labourer"))
check("hires within the core's people at their tile are not over-reserved", core_book.reservations_over_core() == [])
over_book = _CoreBook({"home": {"labourer": 2.0}}, {"labourer": 3.0})
check("a hire the core's people at its tile do not cover is listed",
      over_book.reservations_over_core() == [("home", "labourer", 3.0, 2.0)], over_book.reservations_over_core())
check("with no core yet nothing is free to count and nothing is over-reserved",
      _CoreBook(None, {}).free_core_people("labourer") is None and _CoreBook(None, {}).reservations_over_core() == [])

from unittest import mock
from sim.labour import labour_population


class _Estimate(labour_population.PopulationMixin):
    def __init__(self, in_core):
        self._world = SimpleNamespace(population=SimpleNamespace(total=1000.0, working_age=600.0),
                                      urban_fraction=lambda: 0.2, trades_absent=())
        self._in_core = in_core

    def trade_available(self, trade):
        return True

    def core_people_by_trade(self):
        return self._in_core


with mock.patch.object(labour_population.trade_data, "drawn_from_unskilled_pool", lambda trade: False), \
        mock.patch.object(labour_population.trade_data, "scholar_trade", lambda: "scholar"), \
        mock.patch.object(labour_population.trade_data, "literate_trades", lambda registry, trades: []), \
        mock.patch.object(labour_population.trade_data, "registry_of", lambda world: {}):
    check("the national estimate of a trade is the core's headcount where the core holds people of it",
          _Estimate({"smith": 42.0}).national_trade_population("smith") == 42.0)
    check("a farm trade the core holds nobody of falls back to the rural share of the working age",
          abs(_Estimate({}).national_trade_population(labour_population.FARM_TRADE) - 600.0 * 0.8) < 1e-9)

# ---- the wall: nothing outside the owner writes the founder's book ----
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WRITE = re.compile(r"\.employees\s*(\[[^\]]*\]\s*(=|\+=|-=)|\.(pop|clear|update|setdefault)\(|\s*=[^=])")
ALLOWED = ("sim/labour/", "sim/agents/household.py", "sim/tests/")
# the dict wrapper that reports changes, and the plague survival roll (owned by the disease work; moves to the owner with it)
EXCEPTIONS = ("sim/engine/core.py", "sim/engine/economy.py", "sim/engine/society_hazards.py")
strays = []
for folder, _subfolders, filenames in os.walk(os.path.join(ROOT_DIR, "sim")):
    for filename in filenames:
        path = os.path.join(folder, filename)
        relative = os.path.relpath(path, ROOT_DIR).replace(os.sep, "/")
        if not filename.endswith(".py") or relative.startswith(ALLOWED[0]) or relative in ALLOWED or relative in EXCEPTIONS or relative.startswith(ALLOWED[2]):
            continue
        with open(path, encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                if WRITE.search(line) and not line.lstrip().startswith("#"):
                    strays.append("%s:%d" % (relative, number))
check("only sim/labour (and the household's own accessor, bar the listed exceptions) writes the founder's book", not strays, strays)
readers = []
for name in sorted(os.listdir(os.path.join(ROOT_DIR, "sim", "labour"))):
    if name.endswith(".py") and name != "staff_book.py":
        with open(os.path.join(ROOT_DIR, "sim", "labour", name), encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        readers += ["%s:%d" % (name, node.lineno) for node in ast.walk(tree)
                    if isinstance(node, ast.Attribute) and node.attr == "employees"]
check("labour code reaches the book only through the owner", not readers, readers)
