"""Complaint 133, played: Rome builds the water works, one closes, and what needs it running lapses.

SLOW SCENARIO (it builds a whole game and steps it): the one played chain. The rules are held on fakes by
test_running_gates (a shut work closes its dependents down the chain, the closure is logged, opening a dependent is refused
while its work is shut), test_held_and_running (a shut venture is not held; a voyage returns its route),
test_failed_voyage_loses_what_it_risked (a failed crossing takes crew and hull) and test_works_register (the register is
saved state as a field), and the buoy lapsing with its harbour is the same gate as the tower with the pumping station.
"""
from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of
from .harness import _LOADTEST_DIR
from .agent_command_helpers import ask_agent, with_end_year

AQUEDUCT, PUMPING, TOWER = "civ_aqueduct_roman", "civ_pumping_station", "civ_water_tower"
CHAIN = (TOWER,)   # the aqueduct is held by the society at the opening, so the pumping station is the gate that can close
OPENING_PURSE_PER_PROJECT_COST = 10.0   # a purse many times the works' project cost covers their opening stock

# --- a chain of works: each needs the one before it running.
game = with_end_year(sim())
run_it(game, PUMPING, *CHAIN)
check("with the pumping station open, the work that needs it is running",
      all(game.running(work) for work in (PUMPING,) + CHAIN), [game.running(work) for work in CHAIN])

game.close_work(PUMPING, "closed_by_the_player")
check("shutting the pumping station shuts the tower on it",
      all(game.closure_of(work) and game.closure_of(work)["reason"] == game.CLOSED_GATE_LAPSED for work in CHAIN),
      {work: game.closure_of(work) for work in CHAIN})
check("...and it is not running", not any(game.running(work) for work in CHAIN), None)
check("...so the geography no longer counts the shut pumping station among the technologies held",
      PUMPING not in game.held_and_running(), None)

ask_agent(game, cmd="step", years=2)
check("two years on, the tower is still shut while the pumping station is",
      not any(game.running(work) for work in CHAIN), [game.running(work) for work in CHAIN])
check("...and the log says why", any(cause_of(line) == "work_closed_gate_lapsed" for _year, line in game.state.household.log), None)

# the gate is what is under test, not the purse: cover both works' costs so what the opening stock costs at the
# prices of the day cannot decide whether the tower may be opened
game.capital = OPENING_PURSE_PER_PROJECT_COST * sum(game.project_cost(work) for work in (PUMPING,) + CHAIN)
reopened, message = game.open_venture(PUMPING)
check("the pumping station can be reopened", reopened, message)
again, why = game.open_venture(TOWER)
check("with the pumping station back, the tower can be opened again", again, why)

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
