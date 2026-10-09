"""Complaint 133, played: Rome builds the water works, one closes, and what needs it running lapses.

SLOW TOPIC (it builds whole games and steps them). It is written to be run by the orchestrator after
merging, not on a small fixture; the quick tiers cover the same rules with fakes
(test_running_gates, test_held_and_running, test_works_register, test_failed_voyage_loses_what_it_risked).
"""
from .harness import *  # noqa: F401,F403
from .harness import _LOADTEST_DIR
from .agent_command_helpers import ask_agent, with_end_year

AQUEDUCT, PUMPING, TOWER, TREATMENT = "civ_aqueduct_roman", "civ_pumping_station", "civ_water_tower", "civ_water_treatment"
CHAIN = (PUMPING, TOWER, TREATMENT)
VOYAGE = "exp_atlantic_crossing"
HARBOUR, BUOY = "sea_harbours_pozzolana", "sea_buoy"

# --- a chain of works: each needs the one before it running.
game = with_end_year(sim())
run_it(game, AQUEDUCT, *CHAIN)
check("with the aqueduct open, the works that need it are running",
      all(game.running(work) for work in (AQUEDUCT,) + CHAIN), [game.running(work) for work in CHAIN])

game.close_work(AQUEDUCT, "closed_by_the_player")
check("shutting the aqueduct shuts the pumping station, the tower on it and the treatment works",
      all(game.closure_of(work) and game.closure_of(work)["reason"] == game.CLOSED_GATE_LAPSED for work in CHAIN),
      {work: game.closure_of(work) for work in CHAIN})
check("...and none of them is running", not any(game.running(work) for work in CHAIN), None)
check("...so the geography no longer counts the shut aqueduct among the technologies held",
      AQUEDUCT not in game.held_and_running(), None)

ask_agent(game, cmd="step", years=2)
check("two years on, the dependents are still shut while the aqueduct is",
      not any(game.running(work) for work in CHAIN), [game.running(work) for work in CHAIN])
check("...and the log says why", any("has stopped" in line for _year, line in game.state.household.log), None)

reopened, message = game.open_venture(AQUEDUCT)
check("the aqueduct can be reopened", reopened or "cash" in message or "afford" in message, message)
if reopened:
    again, why = game.open_venture(PUMPING)
    check("with the aqueduct back, the pumping station can be opened again", again, why)

# --- a harbour and its buoy.
harbour_game = with_end_year(sim())
run_it(harbour_game, HARBOUR, BUOY)
check("a buoy runs while the harbour that tends it runs", harbour_game.running(BUOY), None)
harbour_game.close_work(HARBOUR, "closed_by_the_player")
check("a buoy lapses when the harbour that tends it is shut", not harbour_game.running(BUOY), None)
check("the harbour and the buoy now carry an upkeep to gate on",
      harbour_game.nodes[HARBOUR]["up"] > 0 and harbour_game.nodes[BUOY]["up"] > 0, None)

# --- what an expedition returns stands while it is held.
voyage_game = with_end_year(sim())
check("before the crossing, the open Atlantic is not a route the people hold",
      "route:open_atlantic" not in voyage_game.held_and_running(), None)
run_it(voyage_game, VOYAGE)
check("after it, the route is held", "route:open_atlantic" in voyage_game.held_and_running(), None)

# --- a failed voyage takes what it risked.
loss_game = with_end_year(sim())
loss_game.grant_stock("timber_m3", 100.0)
loss_game.state.household.employees["sailor"] = 400.0
before_timber = loss_game.stock_held("timber_m3")
lines = loss_game.lose_what_was_risked(VOYAGE)
check("a failed crossing loses crew and hull", loss_game.state.household.employees.get("sailor", 0.0) < 400.0
      and loss_game.stock_held("timber_m3") < before_timber, lines)

# --- a work built on a tile is kept in the saved register and survives a save and a load.
works_game = with_end_year(sim())
tile = sorted(works_game.labour.settlement_tiles())[0]
works_game.state.economy.works = {tile: {AQUEDUCT: 1.5}}
os.makedirs(os.path.join(ROOT, _LOADTEST_DIR), exist_ok=True)
_register_file = "%s/works_register_save.json" % _LOADTEST_DIR
ask_agent(works_game, cmd="save", file=_register_file)
check("a works register on a tile is saved with the game",
      ask_agent(works_game, cmd="load", file=_register_file).get("ok") is True
      and works_game.state.economy.works == {tile: {AQUEDUCT: 1.5}}, works_game.state.economy.works)
