"""Complaint 89: a player can say which active project gets founder hours first. The `priority` handler runs on a stub game
(master order, active projects, standing allocations) the test builds; the step takes its ranks from that queue (`hour_priority_queue`)."""
QUICK_TOPIC = True

from sim.tests import workforce_stand_in
from types import SimpleNamespace

from .harness import check

from sim.projects.hour_offer import priority_queue
from sim.ui.proto import command_registry as _registry
from sim.ui.proto.dispatch_priority import _cmd_priority
from sim.ui.proto.typed import parse_typed as _parse_typed

_ids = ["academy_network", "corpus_written", "school_founded"]
_nodes = {node_id: {"name": node_id.replace("_", " ")} for node_id in _ids + ["other_node", "arithmetic_positional"]}


def _three_active(order=None, allocations=None):
    return workforce_stand_in.Game(order=list(order or _ids), active={node_id: {} for node_id in _ids},
                                   hour_allocations=dict(allocations or {}))


def _priority(game, **fields):
    return _cmd_priority(game, _nodes, dict(cmd="priority", **fields), False)


check("priority is a registered command, so help lists it",
      _registry.resolve("priority") is not None)

game = _three_active()
reply = _priority(game, id="school_founded", position="first")
check("priority <id> first puts that project ahead of the rest",
      reply.get("ok") and reply.get("order")[0] == "school_founded", reply)
queue = priority_queue(game.active, game.order, game.hour_allocations)
check("...and the queue the hours are handed out by is in that order",
      queue == reply["order"] and [queue.index(node_id) + 1 for node_id in _ids] == [2, 3, 1], queue)

game = _three_active()
reply = _priority(game, id="academy_network", position="last")
check("priority <id> last puts it behind the others",
      reply.get("ok") and reply["order"][-1] == "academy_network", reply)

game = _three_active()
reply = _priority(game, id="school_founded", position=2)
check("priority <id> <rank> places it at that rank",
      reply.get("ok") and reply["order"] == ["academy_network", "school_founded", "corpus_written"], reply)

game = _three_active(order=["other_node"] + _ids)
_priority(game, id="school_founded", position="first")
check("inactive nodes keep their place in the master order",
      game.order[0] == "other_node" and game.order.index("school_founded") == 1, game.order)

reply = _priority(_three_active(), id="arithmetic_positional", position="first")
check("an inactive id is refused with a pointer to start",
      not reply["ok"] and "not active" in reply["error"], reply)  # presentation: the refusal points at 'start'

reply = _priority(_three_active(), id="school_founded", position=0)
check("a rank below one is refused", not reply["ok"], reply)
reply = _priority(_three_active(), id="no_such_node", position="first")
check("an unknown id is refused", not reply["ok"], reply)

reply = _priority(_three_active())
check("bare priority lists active projects with rank",
      bool(reply.get("projects")) and [row["id"] for row in reply["projects"]] == _ids
      and reply["projects"][0]["rank"] == 1, reply)

reply = _priority(_three_active(allocations={"corpus_written": 100.0}))
check("a project with a standing allocate order is listed first and marked, since allocate outranks priority",
      bool(reply.get("projects")) and reply["projects"][0]["id"] == "corpus_written"
      and reply["projects"][0].get("allocate_hours_a_year") == 100.0, reply)

check("typed 'priority X first' parses",
      _parse_typed("priority school_founded first")[0]
      == {"cmd": "priority", "id": "school_founded", "position": "first"},
      _parse_typed("priority school_founded first"))
check("typed 'priority X 2' parses",
      _parse_typed("priority school_founded 2")[0]
      == {"cmd": "priority", "id": "school_founded", "position": 2},
      _parse_typed("priority school_founded 2"))
