"""Scenario for Complaint 420: in a whole game a concern's opening and closures write cause rows, the rows survive a
save and load, and `figures` and the `causes` command show them. The rules are in test_cause_book."""
import os
import tempfile

from .harness import *  # noqa: F401,F403

from sim.engine import cause_book
from sim.engine.saveload import load_state, save_state


def ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


game = unopened_sim(capital=1_000_000.0)
game.end_year = game.cfg["start_year"] + game.cfg["horizon_years"]
# a concern the founder's free hands can staff under the plant-derived crew (the same gate `open` applies)
node_id = next(node for node in game.order if NODES[node]["rev"] > 0 and game.is_venture(node)
               and game.staffing_open_refusal(node) is None)
game.state.projects.done.add(node_id)
game.open_venture(node_id, pay=False)
game.mothball_work(node_id)
game.close_work(node_id, game.CLOSED_FOR_STAFF)
kinds = {(row["kind"], row.get("cause")) for row in cause_book.rows(game) if row["subject"] == node_id}
check("scenario: opening, closing by choice and closing for staff each write their row",
      any(kind == "opening" for kind, _cause in kinds)
      and ("closure", game.CLOSED_BY_CHOICE) in kinds and ("closure", game.CLOSED_FOR_STAFF) in kinds, kinds)

cause_book.close_period(game)   # sets the readings the next period is measured from
game.state.household.capital += 5_000_000.0
game.state.household.eminence += 3.0
cause_book.close_period(game)
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(game, path)
    revived = unopened_sim(civ="rome_100ad")
    load_state(revived, path)
check("scenario: the rows and marks survive a save and load",
      revived.state.household.cause_rows == game.state.household.cause_rows
      and revived.state.household.cause_mark == game.state.household.cause_mark
      and bool(revived.state.household.cause_rows))

notice_figure = ask(game, cmd="figures", id="state_notice")
reply = ask(game, cmd="causes")
check("scenario: the state notice figure and the causes command list the recorded causes",
      notice_figure.get("ok") and bool(notice_figure["causes"])
      and reply.get("ok") and any(row["kind"] == "closure" for row in reply["rows"]), (notice_figure, reply))
