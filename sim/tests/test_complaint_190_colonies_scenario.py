"""SCENARIO (Complaint 190): settled colonies (owned territory with a people of its own on the tile map) in a whole game:
founding, its people over the years, save and load, and the `settle` and `colonies` commands. Wiring only: the refusals and the yearly step are in test_colony_rules. The
light and amusement needs and the typed lines are in test_complaint_190_colonies."""
from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of

from sim.geography.api import tiles_held

CHARTER = "ben_settlement_charter"


def chartered(capital=1.0e12):
    """A game that holds the charter and has money, the economy unopened."""
    game = unopened_sim(capital=capital)
    game.done.update(NODES[CHARTER]["pre"])
    game.done.add(CHARTER)
    game._done_changed()
    game.spending_power = lambda kind: game.state.household.capital   # what is raised is the cash in hand
    return game


def people(colony):
    return colony["children"] + colony["working_age"] + colony["elderly"]


game = chartered()
spec = NODES[CHARTER]["mechanics"]["settlement"]
held = tiles_held(game.civ)
reachable = game.settlement_candidates(False)
check("settlers can reach tiles that border what the country holds", bool(reachable) and not set(reachable) & set(held), reachable[:3])

# ---- founding a colony --------------------------------------------------------------------------------------
tile = reachable[0]
working_before, capital_before = game.population.working_age, game.state.household.capital
ok, text = game.found_colony(tile)
colony = game.state.holdings.colonies[0] if game.state.holdings.colonies else {}
check("a colony is founded on a reachable tile", ok and colony.get("tile") == tile, (ok, text))
check("the settlers are the colony's working-age people at the start", people(colony) == spec["settlers"]
      and colony["working_age"] == spec["settlers"], colony)
check("the settlers leave the home country's working age", abs(working_before - game.population.working_age - spec["settlers"]) < 1e-6,
      (working_before, game.population.working_age))
check("the outfit is paid", abs(capital_before - game.state.household.capital - game.settlement_outfit_cost(spec)) < 1e-3,
      (capital_before - game.state.household.capital, game.settlement_outfit_cost(spec)))
check("the tile is held now and cannot be settled twice", tile in game.claimed_tiles() and not game.found_colony(tile)[0])
check("a tile settlers cannot reach is refused", not game.found_colony("zz_not_a_tile")[0])
check("the log says where", any(tile in line for _year, line in game.state.household.log))
check("the colonies listing shows its people and what its land could feed",
      game.colony_rows()[0]["people"] == spec["settlers"] and game.colony_rows()[0]["most_the_land_feeds"] > 0, game.colony_rows())

# ---- the people of a colony ---------------------------------------------------------------------------------------
growing = chartered()
growing.found_colony(reachable[0])
for year in range(2):
    growing.advance_colonies(growing.state.scenario.year + year)

dying = chartered()
dying.found_colony(reachable[0])
colony = dying.state.holdings.colonies[0]
colony.update(children=0.2, working_age=0.2, elderly=0.2)
dying.advance_colonies(dying.state.scenario.year)
check("a colony whose people die out is lost and the log says so",
      dying.state.holdings.colonies == [] and any(cause_of(line) == "colony_died_out" for _year, line in dying.state.household.log))

# a colony that is saved and loaded is the same colony
from sim.engine.saveload import load_state, save_state
path = os.path.join(tempfile.mkdtemp(), "colony_roundtrip.json")
save_state(growing, path)
reloaded = unopened_sim()
load_state(reloaded, path)
check("colonies survive a save and a load", reloaded.state.holdings.colonies == growing.state.holdings.colonies,
      (reloaded.state.holdings.colonies, growing.state.holdings.colonies))

# ---- the commands ------------------------------------------------------------------------------------------------
listing = S._agent_dispatch(chartered(), NODES, {"cmd": "settle"})
check("`settle` lists the tiles, the settlers and the outfit cost",
      listing.get("ok") and listing["settlers"] == spec["settlers"] and listing["outfit_cost"] > 0 and listing["tiles"], listing)
check("`settle` with nothing known is refused", S._agent_dispatch(unopened_sim(), NODES, {"cmd": "settle"})["ok"] is False)
commanded = chartered()
reply = S._agent_dispatch(commanded, NODES, {"cmd": "settle", "tile": reachable[0]})
check("`settle <tile>` founds the colony", reply.get("ok") and commanded.state.holdings.colonies, reply)
check("`colonies` lists those held", S._agent_dispatch(commanded, NODES, {"cmd": "colonies"})["colonies"][0]["tile"] == reachable[0])
