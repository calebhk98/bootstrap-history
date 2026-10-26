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
                              ProjectsState, ScenarioState, SimulationState, serialize_state)
from sim.refusal import cause_of


def valid_save():
    state = SimulationState(
        household=HouseholdState(capital=1250.0), projects=ProjectsState(done={"stone_cutting"}), economy=EconomyState(),
        holdings=HoldingsState(), founder=FounderState(), scenario=ScenarioState(year=115))
    state._goal = "aqueduct"
    blob = serialize_state(state)
    blob.update({"_civ": "rome_100ad", "_civ_live": {}, "_weights": {}, "_fog": False, "_immortal": True,
                 "_rng": [3, list(random.Random(1).getstate()[1]), None]})
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
unknown["seats"][blob["acting_seat"]]["projects"]["done"]["__set__"].append("this_node_does_not_exist_anymore")
refusal = _validate_save(unknown, game)
check("a save naming a node the tree lacks is refused with the node",
      cause_of(refusal) == "save_unknown_nodes" and refusal.facts["nodes"] == ["this_node_does_not_exist_anymore"], refusal)

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
