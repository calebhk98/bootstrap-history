"""priority: regression checks, run individually with `--only priority`."""
from .harness import *  # noqa: F401,F403

from sim.engine.proto.typed import parse_typed as _parse_typed
from sim.engine.proto import command_registry as _registry

# Complaint 91: a player can say which active project gets founder hours first.

_ids = ["academy_network", "corpus_written", "school_founded"]


def _three_active():
    test_sim = sim(capital=1e7)
    test_sim.order = list(_ids)
    for node_id in _ids:
        test_sim.active[node_id] = dict(ph_left=float(NODES[node_id]["ph"]), yrs=0.0, spent=0.0,
                                        cost_left=0.0, lab_left={})
    return test_sim


def _priority(test_sim, **fields):
    return S._agent_dispatch(test_sim, NODES, dict(cmd="priority", **fields))


def _ranks(test_sim):
    test_sim.step()
    return [test_sim.active[node_id]["pool_rank_this_year"] for node_id in _ids]


check("priority is a registered command, so help lists it",
      _registry.resolve("priority") is not None)

test_sim = _three_active()
reply = _priority(test_sim, id="school_founded", position="first")
check("priority <id> first puts that project ahead of the rest",
      reply.get("ok") and reply.get("order")[0] == "school_founded", reply)
check("...and step() hands out hours in that order",
      _ranks(test_sim) == [2, 3, 1], _ranks(test_sim))

test_sim = _three_active()
reply = _priority(test_sim, id="academy_network", position="last")
check("priority <id> last puts it behind the others",
      reply.get("ok") and reply["order"][-1] == "academy_network", reply)

test_sim = _three_active()
reply = _priority(test_sim, id="school_founded", position=2)
check("priority <id> <rank> places it at that rank",
      reply.get("ok") and reply["order"] == ["academy_network", "school_founded", "corpus_written"], reply)

test_sim = _three_active()
test_sim.order = ["other_node"] + list(_ids)
_priority(test_sim, id="school_founded", position="first")
check("inactive nodes keep their place in the master order",
      test_sim.order[0] == "other_node" and test_sim.order.index("school_founded") == 1, test_sim.order)

reply = _priority(_three_active(), id="not_active_node", position="first")
check("an inactive id is refused with a pointer to start",
      not reply["ok"] and "not active" in reply["error"], reply)

reply = _priority(_three_active())
check("bare priority lists active projects with rank",
      bool(reply.get("projects")) and [row["id"] for row in reply["projects"]] == _ids
      and reply["projects"][0]["rank"] == 1, reply)

test_sim = _three_active()
test_sim.hour_allocations["corpus_written"] = 100.0
reply = _priority(test_sim)
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

portfolio = S._agent_dispatch(_three_active(), NODES, {"cmd": "portfolio"})
check("the portfolio note points at the priority command",
      "priority" in portfolio["note"], portfolio["note"])
