"""Complaint 420: the engine keeps (cause, amount) rows for wage changes, concern closures and state
notice, bounded to a few years. The rules are tested on a stub game built here."""
QUICK_TOPIC = True

from sim.tests.purse_stand_in import PurseHousehold
import types

from .harness import *  # noqa: F401,F403

from sim.engine import cause_book


class StubGame:
    """The readings the cause book takes from a game; notice is capacity times a scale that rises with each reading."""

    def __init__(self):
        self.year = 100
        self.standing = {"concealed": 0.0, "eminence": 0.0, "defiance": 0.0}
        self.state = types.SimpleNamespace(household=PurseHousehold(capital=1000.0))
        self.nodes = {"mill": {"rev": 40.0, "up": 15.0}}
        self.reach = 2.0
        self.wage_index_now = 1.0
        self.headcount_now = 100
        self.labour = types.SimpleNamespace(
            headcount=lambda: self.headcount_now,
            market=types.SimpleNamespace(wage_index=lambda: self.wage_index_now,
                                         wage_index_change=lambda before: self.wage_index_now - before))

    def state_reach(self):
        return self.reach

    def view(self, name):   # the polity module's standing, reach and visible scale
        if name in ("visible_scale", "state_reach"):
            return getattr(self, name)
        if name == "acting_balance":
            return lambda: self.state.household.capital
        return lambda: self.standing

    def visible_scale(self, headcount, wealth, eminence, defiance):
        return 1.0 + headcount / 1000.0 + wealth / 100000.0 + eminence / 10.0 + defiance

    def notice(self):
        household = self.state.household
        return self.reach * self.visible_scale(self.headcount_now, household.capital, self.standing["eminence"],
                                                        self.standing["defiance"])


game = StubGame()
cause_book.close_period(game)   # sets the readings the next period is measured from

# --- rows written where things happen --------------------------------------------------------
cause_book.record_concern(game, "opening", "mill", "manual")
check("a concern row carries what the node earns and costs a year",
      cause_book.rows(game, "opening")[0]["revenue"] == 40.0 and cause_book.rows(game, "opening")[0]["upkeep"] == 15.0,
      cause_book.rows(game))
check("an open period's rows count as this year", cause_book.rows(game)[0]["year"] == 100, cause_book.rows(game))

index_start, notice_start = game.wage_index_now, game.notice()
game.wage_index_now = 0.7
cause_book.record_wage_shock(game, "a plague", index_start)
check("a wage shock row names its cause with the signed index change",
      abs(cause_book.causes_since(game, "wage", None)["a plague"] - (-0.3)) < 1e-12, cause_book.rows(game, "wage"))

# --- closing a period adds the unnamed remainder, so the causes sum to the change ----------------
game.wage_index_now = 0.8   # 0.1 more than the shock named
game.state.household.capital += 500000.0
game.standing["eminence"] += 3.0
game.headcount_now = 80
game.reach = 2.5
game.year = 101
cause_book.close_period(game)
wage = cause_book.causes_since(game, "wage", None)
check("wage causes sum to the index change and the unnamed part is its own cause",
      abs(sum(wage.values()) - (game.wage_index_now - index_start)) < 1e-9
      and abs(wage[cause_book.UNSHOCKED_WAGE_CAUSE] - 0.1) < 1e-9, wage)
notice = cause_book.causes_since(game, "notice", None)
check("notice causes sum to the notice change", abs(sum(notice.values()) - (game.notice() - notice_start)) < 1e-9,
      (notice, notice_start, game.notice()))
check("each reading that moved is named: capacity, headcount, wealth and eminence",
      {cause_book.STATE_CAUSE, "headcount", "wealth", "eminence"} <= set(notice) and "defiance" not in notice, notice)
check("wealth is a positive notice cause when the purse grew", notice["wealth"] > 0.0, notice)
check("closing a period stamps the open rows with its year", all(row["year"] is not None for row in
      game.state.household.cause_rows) and cause_book.rows(game, "opening")[0]["year"] == 101, game.state.household.cause_rows)

# --- selecting rows ---------------------------------------------------------------------------
check("causes since a year leave out the rows stamped up to it",
      cause_book.causes_since(game, "wage", 100).get("a plague", 0.0) < -0.29 and cause_book.causes_since(game, "wage", 101) == {},
      (cause_book.causes_since(game, "wage", 100), cause_book.causes_since(game, "wage", 101)))
game.year = 103
cause_book.record(game, "closure", "mill", "by choice", 1.0)
check("rows of a kind in the latest years only", [row["kind"] for row in cause_book.rows(game, "closure", years=1)] == ["closure"]
      and cause_book.rows(game, "opening", years=1) == [], cause_book.rows(game))

# --- bounded ----------------------------------------------------------------------------------
for _ in range(cause_book.YEARS_KEPT + 3):
    game.year += 1
    cause_book.record(game, "closure", "x", "manual", 1.0)
    cause_book.close_period(game)
check("rows older than the window are dropped",
      min(row["year"] for row in game.state.household.cause_rows) > game.year - cause_book.YEARS_KEPT,
      sorted({row["year"] for row in game.state.household.cause_rows}))

for _ in range(cause_book.ROWS_KEPT + 50):
    cause_book.record(game, "closure", "y", "manual", 1.0)
check("a run that never closes a period keeps only a capped number of rows",
      len(game.state.household.cause_rows) == cause_book.ROWS_KEPT, len(game.state.household.cause_rows))
