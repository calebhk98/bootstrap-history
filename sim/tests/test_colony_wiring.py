"""Complaint 190, the colony wiring (the refusal and yearly rules are test_colony_rules): founding a colony pays the outfit, takes the
settlers from the home working age, gives the tile to the seat and records the colony; a colony whose people die out is lost; colonies
survive a save; and the `settle` and `colonies` commands answer from those methods. Each method runs on a stand-in `self`."""

QUICK_TOPIC = True

from types import SimpleNamespace
from unittest import mock

from .harness import check

import sim.engine.colonies as colonies_module
from sim.engine.colonies import ColoniesMixin
from sim.engine.state import SimulationState, deserialize_state, serialize_state
from sim.engine.state_seat import seat_from_template
from sim.refusal import cause_of
from sim.ui.proto import command_registry
import sim.ui.proto.dispatch  # noqa: F401  (registers every command)
from sim.tests import event_stand_in

CHARTER = "ben_settlement_charter"
SPEC = {"settlers": 20, "outfit_hours_per_settler": 50.0}


class Founding:
    """A stand-in game that holds the charter, with the tile market, the purse and the people written out."""
    send = event_stand_in.send

    def __init__(self, held_by=None, by_land=("t1",), by_sea=("t1", "t2"), spendable=1.0e9, working_age=1000.0, chosen=(CHARTER, SPEC), cost=5000.0):
        self.state = SimpleNamespace(household=SimpleNamespace(log=[]), scenario=SimpleNamespace(year=100), acting_seat="founder",
                                     holdings=SimpleNamespace(colonies=[]), seats={})
        self.population = SimpleNamespace(working_age=working_age)
        self.civ = {"id": "rome_100ad"}
        self.held_by, self.land, self.sea, self.spendable, self.chosen, self.cost = held_by, list(by_land), list(by_sea), spendable, chosen, cost
        self.paid, self.transfers = [], []

    def settlement_candidates(self, by_sea=False):
        return self.sea if by_sea else self.land

    def settlement_spec(self, by_sea=False):
        return self.chosen

    def settlement_outfit_cost(self, spec, tile_id=None):
        return self.cost

    def tile_owner(self, tile_id):
        return self.held_by

    def spending_power(self, kind):
        return self.spendable

    def pay_edge(self, edge, money, text):
        self.paid.append((money, text))

    def transfer_tile(self, tile_id, owner, level=None, cause=None):
        self.transfers.append((tile_id, owner, cause))


def found(game, tile):
    return ColoniesMixin.found_colony(game, tile)


game = Founding()
ok, text = found(game, "t1")
colony = game.state.holdings.colonies[0] if game.state.holdings.colonies else {}
check("a colony is founded on a reachable tile with the settlers as its working-age people",
      ok and colony.get("tile") == "t1" and colony["working_age"] == 20.0 and colony["children"] == 0.0 and colony["elderly"] == 0.0 and colony["by"] == CHARTER, (ok, text, colony))
check("the settlers leave the home country's working age", game.population.working_age == 980.0, game.population.working_age)
check("the outfit is paid", [money for money, _text in game.paid] == [5000.0], game.paid)
check("the tile passes to the acting seat", game.transfers and game.transfers[0][:2] == ("t1", "founder"), game.transfers)
check("the log says where, by kind", cause_of(game.state.household.log[-1][1]) == "colony_founded", game.state.household.log)

for label, game in (("a tile already held", Founding(held_by="someone")), ("a tile settlers cannot reach", Founding(by_land=(), by_sea=())),
                    ("no known work", Founding(chosen=None)), ("too few working people", Founding(working_age=10.0)),
                    ("an outfit past what can be raised", Founding(spendable=10.0))):
    ok, text = found(game, "t1")
    check("%s is refused and nothing is paid, moved or recorded" % label,
          not ok and game.paid == [] and game.transfers == [] and game.state.holdings.colonies == [] and game.population.working_age in (1000.0, 10.0), text)

game = Founding(by_land=(), by_sea=("t2",))
asked = []
game.settlement_spec = lambda by_sea=False: asked.append(by_sea) or game.chosen
found(game, "t2")
check("a tile reachable only by sea asks for a work that crosses the sea", asked == [True], asked)

# ---- the people of a colony
class Advancing:
    def __init__(self, colonies):
        seat = SimpleNamespace(holdings=SimpleNamespace(colonies=colonies))
        self.state = SimpleNamespace(seats={"founder": seat}, acting_seat="founder", household=SimpleNamespace(log=[]))
        self._demography = SimpleNamespace(Population=None)
        self.send = event_stand_in.bound(self)
        self.transfers = []
        self.seat = seat

    def _disease_burden(self):
        return 0.5

    def transfer_tile(self, tile_id, owner, level=None, cause=None):
        self.transfers.append((tile_id, owner, cause))


game = Advancing([{"tile": "t1", "children": 0.2, "working_age": 0.2, "elderly": 0.2}])
with mock.patch.object(colonies_module, "advance_colony", lambda colony, food, population, burden: True):
    ColoniesMixin.advance_colonies(game, 120)
check("a colony whose people die out is lost, its tile freed", game.seat.holdings.colonies == [] and game.transfers == [("t1", None, "colony died out")], game.transfers)
check("the log says so by kind and names the tile", cause_of(game.state.household.log[-1][1]) == "colony_died_out", game.state.household.log)
game = Advancing([{"tile": "t1", "children": 5.0, "working_age": 20.0, "elderly": 1.0}])
seen = []
with mock.patch.object(colonies_module, "advance_colony", lambda colony, food, population, burden: seen.append(burden) or False):
    ColoniesMixin.advance_colonies(game, 120)
check("a colony that lives on is kept, stepped at the nation's disease burden", len(game.seat.holdings.colonies) == 1 and seen == [0.5] and game.transfers == [], seen)

# ---- a colony survives a save
seat = seat_from_template({}, 10.0, {})
state = SimulationState(household=seat.household, projects=seat.projects, founder=seat.founder)
state.holdings.colonies.append({"tile": "t1", "founded_year": 100, "by": CHARTER, "children": 3.0, "working_age": 18.0, "elderly": 1.0})
loaded = deserialize_state(serialize_state(state))
check("colonies survive a save and a load", loaded.holdings.colonies == state.holdings.colonies, loaded.holdings.colonies)

# ---- the commands
class Commanded(Founding):
    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.founded = []

    def found_colony(self, tile_id):
        self.founded.append(tile_id)
        return (True, "founded") if self.chosen else (False, "you know no way to send settlers")

    def colony_rows(self):
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
