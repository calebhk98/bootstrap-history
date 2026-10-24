"""Order across a save, where the claim is the identity of serialize-then-deserialize and so each check calls both
(`serialize_state`, `deserialize_state`) on one kind of value: a collection built in two different orders. The saved
text is the same for both, and the loaded collection holds what was saved in the order it was saved."""
QUICK_TOPIC = True

import json

from sim.engine.state import HoldingsState, ProjectsState, deserialize_state, serialize_state
from sim.tests.harness import check

IDS = ["mill", "forge", "loom", "kiln"]


def through_json(value):
	return json.loads(json.dumps(serialize_state(value)))


two_orders = [ProjectsState(done=set(IDS)), ProjectsState(done=set(reversed(IDS)))]
texts = [json.dumps(serialize_state(each), sort_keys=False) for each in two_orders]
check("sets: two sets built in different orders are saved as the same text, sorted", texts[0] == texts[1]
      and through_json(two_orders[0])["done"] == {"__set__": sorted(IDS)}, None)
check("sets: the loaded set is equal to the saved one", deserialize_state(through_json(two_orders[1]), ProjectsState).done == set(IDS))

held = HoldingsState(mine_ready={"zinc": 3, "iron": 1, "tin": 2}, mine_tranches=[["tin", 1, 0.5], ["iron", 3, 2.5]])
loaded = deserialize_state(through_json(held), HoldingsState)
check("dicts and lists: a loaded dict iterates in the order it was saved and a list keeps its order",
      list(loaded.mine_ready) == ["zinc", "iron", "tin"] and loaded.mine_tranches == [["tin", 1, 0.5], ["iron", 3, 2.5]], list(loaded.mine_ready))

active = ProjectsState(active={})
active.failed_attempts.update({"printing": 3, "alloy": 1})
loaded = deserialize_state(through_json(active), ProjectsState)
check("retry counts: the counts and their order survive, and a project never tried still counts from zero",
      list(loaded.failed_attempts) == ["printing", "alloy"] and dict(loaded.failed_attempts) == {"printing": 3, "alloy": 1}
      and loaded.failed_attempts["never_tried"] == 0, loaded.failed_attempts)
