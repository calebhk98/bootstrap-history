"""What `load` refuses (Complaint 640): the validation called on saves built here and a stand-in game that holds only the tree
and civilisation id it reads. A refusal is a clear message, never a crash, and leaves the game untouched. The same refusals
through the protocol command are test_save_command_reply."""
QUICK_TOPIC = True

import json
import os
import random
import tempfile
from types import SimpleNamespace

from .harness import check
from sim.engine.saveload import _validate_save, load_state
from sim.engine.state import (EconomyState, FounderState, HoldingsState, HouseholdState,
                              SimulationState, serialize_state)
from sim.knowledge.api import KnowledgeSeat
from sim.projects.state import ProjectsSeat
from sim.seats.state import SeatsSeat
from sim.ventures.state import VenturesSeat
from sim.refusal import cause_of


def valid_save():
    state = SimulationState(
        household=HouseholdState(), economy=EconomyState(),
        holdings=HoldingsState(), founder=FounderState())
    state.seats[state.acting_seat].modules["knowledge"] = KnowledgeSeat(done={"stone_cutting"})
    state.seats[state.acting_seat].modules["projects"] = ProjectsSeat()
    state.seats[state.acting_seat].modules["ventures"] = VenturesSeat()
    state.seats[state.acting_seat].modules["seats"] = SeatsSeat(goal="aqueduct")
    blob = serialize_state(state)
    blob.update({"_civ": "rome_100ad", "_civ_live": {}, "_weights": {}, "_immortal": True,
                 "_rng": [3, list(random.Random(1).getstate()[1]), None]})
    blob["modules"]["scenario"] = {"year": 115, "fog": False}
    return blob, SimpleNamespace(nodes={"aqueduct": {}, "stone_cutting": {}}, civ={"id": "rome_100ad"})


blob, game = valid_save()
check("a legitimate save is accepted", _validate_save(blob, game) is None, _validate_save(blob, game))

bad_saves = {
    "not an object at all": [1, 2, 3],
    "an unrelated JSON object": {"hello": "world"},
    "missing required fields": {"year": 100, "capital": 400},
}
for label, content in bad_saves.items():
    reply = _validate_save(content, game)
    check("load refuses %s with a short message, not a crash" % label, bool(reply) and len(str(reply)) < 400, reply)

check("a save of another civilisation is refused with its cause",
      cause_of(_validate_save(dict(blob, _civ="norse_900ad"), game)) == "save_wrong_civilisation")
unknown = dict(blob)
unknown["seats"] = json.loads(json.dumps(blob["seats"]))
unknown["seats"][blob["acting_seat"]]["modules"]["knowledge"]["done"]["__set__"].append("this_node_does_not_exist_anymore")
refusal = _validate_save(unknown, game)
check("a save naming a node the tree lacks is refused with the node",
      cause_of(refusal) == "save_unknown_nodes" and refusal.facts["nodes"] == ["this_node_does_not_exist_anymore"], refusal)


def naming(label, edit):
    """The valid save with a node the tree lacks named by `edit` of the acting seat's module slots."""
    named = json.loads(json.dumps(blob))
    edit(named["seats"][named["acting_seat"]]["modules"])
    return label, _validate_save(named, game)


GHOST_WORK = {"ph_left": 1.0, "spent": 0.0, "cost_left": 1.0, "lab_left": {}}
for label, edit, ghost in (
        ("in a project in hand", lambda modules: modules["projects"]["active"].update({"ghost_project": GHOST_WORK}), "ghost_project"),
        ("in a bounty", lambda modules: modules["projects"].update({"bountied": {"__set__": ["ghost_bounty"]}}), "ghost_bounty"),
        ("in a plant it runs", lambda modules: modules["ventures"]["businesses"][0]["plants"].append({"entry_key": "ghost_plant"}), "ghost_plant")):
    _label, refusal = naming(label, edit)
    check("a save naming a node the tree lacks %s is refused with the node" % label,
          cause_of(refusal) == "save_unknown_nodes" and refusal.facts["nodes"] == [ghost], refusal)

# a refused load leaves the game untouched
state = SimpleNamespace(household=SimpleNamespace(capital=1250.0))
live = SimpleNamespace(nodes=game.nodes, civ=game.civ, state=state, fog=False)
with tempfile.TemporaryDirectory() as folder:
    for label, content in bad_saves.items():
        path = os.path.join(folder, "save.json")
        with open(path, "w") as handle:
            json.dump(content, handle)
        raised = None
        try:
            load_state(live, path)
        except ValueError as error:
            raised = error
        check("a refused load (%s) raises and leaves the game untouched" % label,
              raised is not None and live.state is state and state.household.capital == 1250.0, raised)
