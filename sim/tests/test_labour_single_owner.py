"""Complaint 556: who can work and who is hired by whom has one owner, the labour package.

Rule tests (Complaint 640): the founder's book accessors and the reservation arithmetic run on a stub world, and the
wall keeps every write of the founder's book inside the owner. The whole-game agreement of the estimate with the
labour core is test_labour_single_owner_scenario."""
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
