"""Complaint 340: every change to the founder's cash goes through the household's ledger with a
cause, and the `cash` figure and `money` read their causes from it (Complaint 97)."""
import os
import re

from .harness import *  # noqa: F401,F403

from sim.engine import cash_book

ENGINE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
# The only places allowed to write the purse itself: the ledger's own methods and the opening balance.
PURSE_WRITERS = {"state.py", "core_properties.py", os.path.join("actors", "household.py")}
DIRECT_WRITE = re.compile(r"\.capital\s*[-+*/]?=(?!=)")


def ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


# --- no code path writes the purse around the ledger -------------------------------------------
offenders = []
for folder, _dirs, files in os.walk(ENGINE_DIR):
    for name in files:
        path = os.path.join(folder, name)
        relative = os.path.relpath(path, ENGINE_DIR)
        if not name.endswith(".py") or relative in PURSE_WRITERS:
            continue
        with open(path, encoding="utf-8") as source:
            for number, line in enumerate(source, 1):
                if DIRECT_WRITE.search(line.split("#", 1)[0]):
                    offenders.append("%s:%d" % (relative, number))
check("no engine code changes the founder's cash except through the ledger", not offenders, offenders)


def reconciles(test_sim):
    return abs(cash_book.unaccounted(test_sim)) < 0.01


# --- every kind of activity leaves the book reconciled -----------------------------------------
rich = sim(capital=2_000_000.0, manual=False, events=True)
rich.end_year = rich.cfg["start_year"] + rich.cfg["horizon_years"]
check("a new game's book reconciles", reconciles(rich), cash_book.unaccounted(rich))

for label, action in (
        ("hire", lambda: rich.hire("smith", 1)),
        ("train", lambda: rich.train("smith", 1)),
        ("commission", lambda: rich.commission("smith", 200)),
        ("bribe", lambda: rich.bribe(500.0)),
        ("farm", lambda: rich.invest_farm(5)),
        ("housing", lambda: rich.build_worker_housing(2)),
        ("nitre", lambda: rich.build_nitre(10)),
        ("forest", lambda: rich.buy_forest(5)),
        ("materials bought", lambda: rich.buy_material_stock("iron", 2.0)),
        ("materials sold", lambda: rich.sell_material_stock("iron", 1.0)),
        ("a hazard's loss", lambda: rich.lose_capital(0.1)),
        ("a bounty", lambda: rich.post_bounty("horse_collar")),
        ("a start", lambda: rich.start_project(next(
            node_id for node_id in rich.order if NODES[node_id]["rev"] > 0 and rich.can_start(node_id)))),
):
    try:
        action()
    except Exception as error:  # an action the scenario refuses is not a ledger fault
        label += " (refused: %s)" % type(error).__name__
    check("after %s the book reconciles" % label, reconciles(rich), cash_book.unaccounted(rich))

causes_seen = set()
for _year in range(40):
    ask(rich, cmd="step", years=1)
    causes_seen |= set(rich.state.household.cash_flow)
    check("year %d: the book reconciles" % rich.year, reconciles(rich), cash_book.unaccounted(rich))
    if not rich.state.founder.founder_alive:
        break

poor = sim(capital=2_000.0, manual=False, events=True)
poor.end_year = poor.cfg["start_year"] + poor.cfg["horizon_years"]
for _year in range(40):
    ask(poor, cmd="step", years=1)
    causes_seen |= set(poor.state.household.cash_flow)
    if not reconciles(poor):
        break
check("a household in arrears, with interest and settlements, reconciles",
      reconciles(poor), cash_book.unaccounted(poor))
check("the ledger names the main flows",
      {"venture revenue", "running costs of concerns", "living costs"} <= causes_seen, sorted(causes_seen))

# --- the inspector reads its causes from the ledger --------------------------------------------
cash = ask(rich, cmd="figures", id="cash")
leftover = [cause for cause in cash["causes"] if cause["cause"].startswith("not itemised")]
check("the cash figure has nothing left unitemised", not leftover, cash)
check("the cash causes add up to the change",
      abs(sum(cause["contribution"] for cause in cash["causes"]) - cash["change"]) < 0.5, cash)
check("the cash figure names venture revenue",
      any(cause["cause"] == "venture revenue" for cause in cash["causes"]), cash)

# --- `money` shows the year's cash by cause ----------------------------------------------------
money = ask(rich, cmd="money")
book = money.get("cash_book") or {}
check("money carries the year's cash by cause",
      {"opening", "closing", "causes"} <= set(book)
      and abs(book["opening"] + sum(book["causes"].values()) - book["closing"]) < 1.0, book)
check("the ledger is bounded in a save",
      len(rich.state.household.cash_periods) <= cash_book.PERIODS_KEPT,
      len(rich.state.household.cash_periods))
