"""Complaint 190, the colony wiring (the refusal and yearly rules are test_colony_rules, the module's founding and yearly step are
test_land_module): the colonies survive a save, and the `settle` and `colonies` commands answer from the game's settlement methods."""

QUICK_TOPIC = True


from .harness import check

from sim.engine.state import deserialize_state, serialize_state
from sim.land.state import LandSeat
from sim.ui.proto import command_registry
import sim.ui.proto.dispatch  # noqa: F401  (registers every command)

CHARTER = "ben_settlement_charter"
SPEC = {"settlers": 20, "outfit_hours_per_settler": 50.0}

# ---- a colony survives a save
colonies = [{"tile": "t1", "founded_year": 100, "by": CHARTER, "children": 3.0, "working_age": 18.0, "elderly": 1.0}]
loaded = deserialize_state(serialize_state(LandSeat(colonies=colonies)), LandSeat)
check("colonies survive a save and a load", loaded.colonies == colonies, loaded.colonies)

from sim.refusal import Refusal
from sim.tests.ui_stand_in import FactViews

# ---- the commands
class Commanded(FactViews):
    """A stand-in game that holds the charter (or none), with the settlement methods written out."""
    def __init__(self, chosen=(CHARTER, SPEC), by_land=("t1",), by_sea=("t1", "t2"), cost=5000.0):
        self.chosen, self.land, self.sea, self.cost = chosen, list(by_land), list(by_sea), cost
        self.founded = []

    def settlement_candidates(self, by_sea=False):
        return self.sea if by_sea else self.land

    def settlement_spec(self, by_sea=False):
        return self.chosen

    def settlement_outfit_cost(self, spec, tile_id=None):
        return self.cost

    def send(self, command):
        self.founded.append(command.tile)
        return {"text": "founded"} if self.chosen else Refusal("no_way", "you know no way to send settlers")

    def colonies(self):
        return [{"tile": "t1"}]


handlers = command_registry.handlers()
game = Commanded()
reply = handlers["settle"](game, {}, {"cmd": "settle"}, None)
check("`settle` lists the settlers, the outfit cost and the tiles", reply["ok"] and reply["settlers"] == 20 and reply["outfit_cost"] == 5000.0 and reply["tiles"] == ["t1", "t2"], reply)
reply = handlers["settle"](Commanded(chosen=None), {}, {"cmd": "settle"}, None)
check("`settle` with no known way is refused", reply["ok"] is False, reply)
reply = handlers["settle"](game, {}, {"cmd": "settle", "tile": "t1"}, None)
check("`settle <tile>` founds the colony and lists those held", reply["ok"] and game.founded == ["t1"] and reply["colonies"] == [{"tile": "t1"}], reply)
reply = handlers["settle"](Commanded(chosen=None), {}, {"cmd": "settle", "tile": "t1"}, None)
check("`settle <tile>` passes a refusal on", reply["ok"] is False, reply)
reply = handlers["settle"](game, {}, {"cmd": "settle", "tile": "t1"}, "the run is over")
check("a run that has ended founds nothing", reply["ok"] is False and game.founded == ["t1"], reply)
