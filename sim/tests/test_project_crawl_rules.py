"""A project short of a trade, but not of all of it, crawls: each year it draws what the trade can field, works its hours down, and its
bill is scaled by the worst-supplied trade; the last instalment is never more than is left, so the crawl ends instead of freezing.
Rules: `ProgressMixin.lab_year_draw`, `ProgressMixin.active_hours_still_wanted`, `project_funding.year_bill`."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine.project_funding import year_bill
from sim.engine.projects_progress import ProgressMixin

NODE = {"name": "Logarithms", "yrs": 10, "ph": 500, "lab": {"scribe": 1000.0}, "cat": "x"}


def a_game(hours_fielded, node=NODE, active=None):
    """A stub game for `lab_year_draw`: one node, a labour market that can field `hours_fielded` of every trade."""
    class Game(ProgressMixin):
        pass

    game = Game()
    game.nodes = {"p": node}
    game.state = SimpleNamespace(projects=SimpleNamespace(trade_hours_used={}, active=active or {}, active_keys_sorted=lambda: sorted(active or {})))
    game.labour = SimpleNamespace(hours_you_can_call_on=lambda trade: hours_fielded)
    game.lab_max_span = lambda node_id: 40.0
    game.trade_shortage_kind = lambda trade, need, demand=None: "staffing"
    return game


def year_of_draw(game, project_state):
    game.state.projects.trade_hours_used = {}
    return game.lab_year_draw("p", project_state, 0.1, 1.0e9)


# --- a trade that can field less than the project's yearly want: the draw is what it can field, the labour left falls every year
game = a_game(hours_fielded=30.0)
project_state = {"yrs": 0.0, "ph_left": 500.0, "lab_left": {"scribe": 1000.0}}
left_each_year = [project_state["lab_left"]["scribe"]]
hired, worst, frac, abandon = year_of_draw(game, project_state)
left_each_year.append(project_state["lab_left"]["scribe"])
hired_again, _worst, _frac, _abandon = year_of_draw(game, project_state)
left_each_year.append(project_state["lab_left"]["scribe"])
check("a short trade is drawn only as far as it can field, year after year", hired == 30.0 and hired_again == 30.0, (hired, hired_again))
check("...so the labour left works down every year", left_each_year == [1000.0, 970.0, 940.0], left_each_year)
check("...and the year's bill share is cut to the worst-supplied trade's share of its own pace",
      abs(worst - 30.0 / 100.0) < 1e-9 and abs(frac - 0.1 * worst) < 1e-9 and abandon is None, (worst, frac, abandon))
check("...and the project is marked blocked on inputs, naming the trade", project_state["status"] == "BLOCKED_INPUTS"
      and project_state["short_of_trade"] == ["scribe"] and project_state["short_of_trade_staffing"] == ["scribe"], project_state)

# --- a trade that fields the want leaves the project active at full pace
game = a_game(hours_fielded=1.0e9)
project_state = {"yrs": 0.0, "ph_left": 500.0, "lab_left": {"scribe": 1000.0}}
hired, worst, frac, abandon = year_of_draw(game, project_state)
check("a trade that fields the whole want is drawn up to its crew ceiling and leaves the project active",
      hired == 100.0 * ProgressMixin.LAB_CREW_RATE_MULT and worst == 1.0 and frac == 0.1 and project_state["status"] == "ACTIVE", (hired, worst, frac, project_state))

# --- the crawl has an end: a project that has run out of calendar with labour still owed is abandoned
project_state = {"yrs": 40.0, "ph_left": 500.0, "lab_left": {"scribe": 900.0}}
_hired, _worst, _frac, abandon = year_of_draw(a_game(hours_fielded=30.0), project_state)
check("a project that has had its span and still owes a trade hours is abandoned, naming the trade", abandon and "scribe" in abandon, abandon)

# --- the tail: the instalment is never more than is left, so the last one lands
check("the last instalment is what is left, not the year's full share", year_bill(5.0, 1000.0, 0.1) == 5.0)
check("an ordinary instalment is the year's share of the whole cost", year_bill(900.0, 1000.0, 0.1) == 100.0)
check("a crawling year pays the share its trade managed", abs(year_bill(900.0, 1000.0, 0.1 * 0.3) - 30.0) < 1e-9)

# --- what the sale of hours is warned against: each active project's pace
game = a_game(hours_fielded=1.0, active={"slow": {"ph_left": 400.0}, "done": {"ph_left": 0.0}})
game.nodes = {"slow": dict(NODE, ph=500, yrs=2), "done": dict(NODE, ph=0, yrs=1)}
game.state.projects.bountied = set()
check("only a project that still wants a real amount of the founder's time is listed, at its pace",
      game.active_hours_still_wanted() == {"slow": 400.0}, game.active_hours_still_wanted())
