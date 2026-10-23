"""Scenarios: the founder's cash book stays reconciled through the actions a player takes and through a year of play
(Complaint 292), and the `cash` figure and `money` read their causes from it (Complaint 95). The rules are in
test_cash_ledger."""
from .harness import *  # noqa: F401,F403

from sim.engine import cash_book


def ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


def reconciles(test_sim):
    return abs(cash_book.unaccounted(test_sim)) < 0.01


rich = sim(capital=300_000.0, manual=False, events=True)
rich.end_year = rich.cfg["start_year"] + rich.cfg["horizon_years"]
unreconciled = []
for label, action in (
        ("hire", lambda: rich.labour.hire("smith", 1)),
        ("train", lambda: rich.labour.train("smith", 1)),
        ("commission", lambda: rich.labour.commission("smith", 200)),
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
    action()    # a refusal is returned, not raised; anything raised is a fault the run must show
    if not reconciles(rich):
        unreconciled.append(label)
check("scenario: a new game's book reconciles after each kind of player action", not unreconciled, unreconciled)

ask(rich, cmd="step", years=1)
causes_seen = {cause for period in rich.state.household.cash_periods for cause in period["causes"]}
check("scenario: a year of play leaves the book reconciled", reconciles(rich), cash_book.unaccounted(rich))
check("scenario: the ledger is bounded in a save",
      len(rich.state.household.cash_periods) <= cash_book.PERIODS_KEPT, len(rich.state.household.cash_periods))

poor = sim(capital=2_000.0, manual=False, events=True)
poor.end_year = poor.cfg["start_year"] + poor.cfg["horizon_years"]
ask(poor, cmd="step", years=1)
causes_seen |= {cause for period in poor.state.household.cash_periods for cause in period["causes"]}
check("scenario: a household in arrears, with interest and settlements, reconciles",
      reconciles(poor), cash_book.unaccounted(poor))
check("scenario: the ledger names the main flows",
      {"venture revenue", "running costs of concerns", "living costs"} <= causes_seen, sorted(causes_seen))

# The inspector and `money` read their causes from the ledger.
cash = ask(rich, cmd="figures", id="cash")
leftover = [cause for cause in cash["causes"] if cause["cause"].startswith("not itemised")]
check("scenario: the cash figure has nothing unitemised, adds up to the change and names venture revenue",
      not leftover and abs(sum(cause["contribution"] for cause in cash["causes"]) - cash["change"]) < 0.5
      and any(cause["cause"] == "venture revenue" for cause in cash["causes"]), cash)
book = ask(rich, cmd="money").get("cash_book") or {}
check("scenario: money carries the year's cash by cause",
      {"opening", "closing", "causes"} <= set(book)
      and abs(book["opening"] + sum(book["causes"].values()) - book["closing"]) < 1.0, book)
