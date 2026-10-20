"""Complaint 556: who can work and who is hired by whom has one owner, the labour package.

Measures the copies (the labour core's people, the town-supply estimate, the founder's book, the
firms' staff), holds every reservation under the supply the owner reports, and walls the founder's
book to the owner."""
import os
import re

from .harness import *  # noqa: F401,F403

game = sim(capital=5_000_000.0)
labour = game.labour
household = game.state.household
core = labour.core_people_by_trade()

# ---- two copies of "people by trade" disagree: the core's headcount and the town-supply estimate ----
ratios = {}
for trade in ("labourer", "farmer", "smith", "mason", "miner"):
    estimate = labour.national_trade_population(trade)
    ratios[trade] = (core.get(trade, 0.0), estimate)
check("the core and the estimate differ by more than a factor of two for labourer (copy not yet a view of the core)",
      max(ratios["labourer"]) > 2.0 * min(ratios["labourer"]), ratios["labourer"])
check("the core and the estimate differ by more than a factor of two in most sampled trades",
      sum(1 for value, estimate in ratios.values() if max(value, estimate) > 2.0 * max(1.0, min(value, estimate))) >= 3, ratios)

# ---- the founder's book is the owner's ----
check("the owner reads the founder's head count", labour.employed("artisan") == household.employees.get("artisan", 0.0))
labour.set_employed("artisan", 2.0)
check("set_employed writes the household's book", household.employees["artisan"] == 2.0 and labour.employed_total() >= 2.0)
labour.add_employed("artisan", -2.0)
check("a count of nothing leaves the trade off the book", "artisan" not in household.employees and labour.employed_by_trade().get("artisan") is None)

# ---- a hire is a reservation under the supply, and the core does not see it yet ----
core_before = dict(core)
hired, reply = labour.hire("labourer", 3)
check("the hire went through", hired, reply)
check("the founder's book holds the hired people", labour.employed("labourer") == 3.0, labour.employed("labourer"))
check("reserved people include the book", labour.reserved_people("labourer") >= 3.0)
check("reserved hours are people times hours a person-year",
      abs(labour.reserved_hours("labourer") - labour.reserved_people("labourer") * game.HOURS_PER_PERSON_YEAR) < 1e-6)
check("the hire is invisible to the core's people (known gap: reservations are not yet taken from the core)",
      labour.core_people_by_trade().get("labourer") == core_before.get("labourer"))
for trade in sorted(labour.employed_by_trade()):
    check("reservations of %s never exceed the supply the owner reports" % trade,
          labour.reserved_people(trade) <= labour.supplied_people(trade) + 1e-9,
          (labour.reserved_people(trade), labour.supplied_people(trade)))
    check("unreserved people of %s are never negative" % trade, labour.unreserved_people(trade) >= 0.0)

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
import ast
readers = []
for name in sorted(os.listdir(os.path.join(ROOT_DIR, "sim", "labour"))):
    if name.endswith(".py") and name != "staff_book.py":
        with open(os.path.join(ROOT_DIR, "sim", "labour", name), encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        readers += ["%s:%d" % (name, node.lineno) for node in ast.walk(tree)
                    if isinstance(node, ast.Attribute) and node.attr == "employees"]
check("labour code reaches the book only through the owner", not readers, readers)
