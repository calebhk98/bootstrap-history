"""`stuck` checks the road to the goal (`_stuck_road_to_goal`) only without fog: under fog it says outright that it did not, so a
player does not read general advice as goal-directed (and the hidden tree does not leak). Called on a stand-in game with the closure
and blocker lookups replaced by recorders. The reply's field is read in `dispatch_inspection_stuck.stuck`."""

QUICK_TOPIC = True

from types import SimpleNamespace
from unittest import mock

from .harness import check

from sim.ui.proto import dispatch_inspection_stuck as stuck

NODES = {"goal": {}, "road_a": {}, "road_b": {}}


def game(startable=()):
    return SimpleNamespace(goal="goal", done=set(), start_reason=lambda node_id: (node_id in startable, ""))


def road(fog, goal_game=None, nodes=NODES):
    with mock.patch.object(stuck, "closure", return_value={"goal", "road_a", "road_b"}) as closure, \
            mock.patch.object(stuck, "route_blockers", return_value=[{"id": "road_a", "kind": "money", "why": "dear"}]) as blockers:
        return stuck._stuck_road_to_goal(goal_game or game(), nodes, fog), closure, blockers


(reason, goal_routing_off), closure, blockers = road(fog=True)
check("under fog with a goal set, the road is not checked and the reply says so", reason is None and goal_routing_off is True)
check("under fog the tree is not walked at all", closure.call_count == 0 and blockers.call_count == 0)

(reason, goal_routing_off), closure, _blockers = road(fog=False, goal_game=game(startable={"road_b"}))
check("without fog, with something on the road startable, there is no reason and no fog notice",
      reason is None and goal_routing_off is False)
check("without fog the road is the goal's closure less what is done", closure.call_args.args == (NODES, "goal"), closure.call_args)

(reason, goal_routing_off), _closure, blockers = road(fog=False)
check("without fog, a road with nothing startable names the nearest blocker's kind and the nodes nearest it",
      goal_routing_off is False and reason["what"] == "the road to the goal" and reason["kind"] == "money"
      and reason["the_nearest_few"] == ["road_a"], reason)
check("the blockers are asked for the five nearest of the road", blockers.call_args.args[2:] == ({"goal", "road_a", "road_b"}, 5), blockers.call_args)

(reason, goal_routing_off), *_unused = road(fog=True, nodes={"road_a": {}})
check("a goal outside the tree is neither checked nor reported as hidden by fog", reason is None and goal_routing_off is False)
