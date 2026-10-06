"""Complaint 420: the engine keeps (cause, amount) rows for wage changes, concern closures and state
notice, bounded to a few years, saved, and shown by `figures` and the `causes` command."""
import os
import tempfile

from .harness import *  # noqa: F401,F403

from sim.engine import cause_book
from sim.engine.saveload import load_state, save_state


def ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


def fresh():
    test_sim = sim(capital=1_000_000.0)
    test_sim.end_year = test_sim.cfg["start_year"] + test_sim.cfg["horizon_years"]
    return test_sim


game = fresh()
node_id = next(node for node in game.order if NODES[node]["rev"] > 0 and game.is_venture(node))
game.state.projects.done.add(node_id)
opened = game.open_venture(node_id, pay=False)
check("opening a concern leaves an opening row with its revenue and upkeep",
      any(row["kind"] == "opening" and row["subject"] == node_id and "revenue" in row
          for row in cause_book.rows(game)), (opened, game.state.household.cause_rows))

game.mothball_work(node_id)
closed = [row for row in cause_book.rows(game) if row["kind"] == "closure" and row["subject"] == node_id]
check("a closure by choice records its cause and what it stops earning",
      len(closed) == 1 and closed[0]["cause"] == game.CLOSED_BY_CHOICE
      and closed[0]["revenue"] == NODES[node_id]["rev"], closed)

game.close_work(node_id, game.CLOSED_FOR_STAFF)
check("a staffing closure is a separate row with its own cause",
      {row["cause"] for row in cause_book.rows(game) if row["kind"] == "closure"}
      == {game.CLOSED_BY_CHOICE, game.CLOSED_FOR_STAFF})

pressure = fresh()
cause_book.close_period(pressure)
index_start = pressure.wage_index
notice_start = pressure.state_notice()
pressure._apply_population_mortality_shock(0.3)
cause_book.record_wage_shock(pressure, "a plague", index_start)
pressure.state.household.capital += 5_000_000.0
pressure.state.household.eminence += 3.0
cause_book.close_period(pressure)
wage = cause_book.causes_since(pressure, "wage", None)
check("a mortality shock is named in the wage causes", wage.get("a plague", 0) > 0, wage)
check("wage causes sum to the index change",
      abs(sum(wage.values()) - (pressure.wage_index - index_start)) < 1e-9, (wage, index_start))
notice = cause_book.causes_since(pressure, "notice", None)
check("notice causes sum to the notice change",
      abs(sum(notice.values()) - (pressure.state_notice() - notice_start)) < 1e-9, (notice, notice_start))
check("wealth is named as a notice cause", notice.get("wealth", 0) > 0, notice)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(pressure, path)
    revived = sim(civ="rome_100ad")
    load_state(revived, path)
check("the rows and marks survive a save and load",
      revived.state.household.cause_rows == pressure.state.household.cause_rows
      and revived.state.household.cause_mark == pressure.state.household.cause_mark
      and bool(revived.state.household.cause_rows))

wages_figure = ask(pressure, cmd="figures", id="wages")
check("the wages figure lists its recorded causes",
      wages_figure.get("ok") and any(cause["cause"] == "a plague" for cause in wages_figure["causes"]), wages_figure)
notice_figure = ask(pressure, cmd="figures", id="state_notice")
check("the state notice figure lists its recorded causes",
      notice_figure.get("ok") and any(cause["cause"] == "wealth" for cause in notice_figure["causes"]), notice_figure)

for _ in range(cause_book.YEARS_KEPT + 3):
    pressure.state.scenario.year += 1
    cause_book.record(pressure, "closure", "x", "manual", 1.0)
    cause_book.close_period(pressure)
check("rows older than the window are dropped",
      min(row["year"] for row in pressure.state.household.cause_rows)
      > pressure.state.scenario.year - cause_book.YEARS_KEPT - 1, len(pressure.state.household.cause_rows))

reply = ask(game, cmd="causes")
check("the causes command lists closures with their reason",
      reply.get("ok") and any(row["kind"] == "closure" for row in reply["rows"]), reply)
