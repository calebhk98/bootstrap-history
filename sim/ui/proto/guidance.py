"""Guidance figures for the goal and idle screens (Complaints/98, 99).

Every figure is read from the engine function that computes it; nothing here
names a content id, and nothing reads the hidden tree.
"""

import math

from .portfolio_bottlenecks import blocker_kind_of
from .economy import _portfolio_constraint
from .state import _agent_state

LEVERAGE_NOTE = ("A broad approach can make a hard goal cheaper, faster and more robust than "
                 "walking its prerequisite chain alone; these are the levers that work for any "
                 "goal. This does not prescribe a route.")


def leverage_points(sim):
    """The system levers behind every goal, each with the engine's own figures."""
    risk = sim.knowledge_risk()
    return [
        {"lever": "literacy", "why_it_matters": "more people who can read and be taught makes research and trades faster",
         "figures": {"literacy_general": round(float(sim.civ.get("literacy_general", 0.0)), 3),
                     "general_ceiling": round(sim.literacy_ceiling_general(), 3),
                     "schooling_flow": round(sim.effective_schooling_flow(), 3)}},
        {"lever": "labour", "why_it_matters": "directed hours and people let several projects run in parallel",
         "figures": {"directed_hours_this_year": round(sim.labour.director_pool(), 1),
                     "committed_hours": round(sim.labour.director_hours_committed(), 1),
                     "people_you_can_oversee": round(sim.labour.supervision_room(), 1)}},
        {"lever": "finance", "why_it_matters": "money removes the cost bottleneck for everything else",
         "figures": {"recurring_net_per_year": round(sim.recurring_net(), 1),
                     "credit_limit": round(sim.credit_limit(), 1),
                     "you_could_raise_now": round(sim.spending_power("start"), 1)}},
        {"lever": "institutions", "why_it_matters": "schools, guilds and standing concerns spread skill and specialisation",
         "figures": {"concerns_running": len(sim.operating), "people_you_can_oversee": round(sim.labour.supervision_room(), 1)}},
        {"lever": "knowledge", "why_it_matters": "what is known can be lost to sackings; preserving it protects every goal",
         "figures": {"technologies_at_risk": risk.get("technologies_at_risk"),
                     "expected_lost_per_sacking": risk.get("expected_technologies_lost_per_sacking")}},
        {"lever": "materials", "why_it_matters": "supply chains cap how fast anything physical can be built",
         "figures": {"work_runs_at_share_of_plan": round(sim.throttle, 3), "binding_material": sim.binding}},
    ]


def delay_kinds(sim, nodes):
    """Active project ids grouped by the shared blocker kind each waits on."""
    kinds = {}
    for node_id, entry in sorted((_agent_state(sim, nodes).get("active") or {}).items()):
        kind = blocker_kind_of(_portfolio_constraint(entry.get("waiting_on")))
        kinds.setdefault(kind, []).append(node_id)
    return kinds


def wait_explanation(kinds):
    if not kinds:
        return "nothing is running, so nothing is being waited on: every directed hour is free to start something."
    if set(kinds) == {"calendar"}:
        return ("every running project is only waiting on its calendar floor. A calendar floor is not "
                "exclusive research time and cannot be bought down: start something else alongside it, "
                "teach, or sell hours; hours do not carry into next year.")
    return ("the delay is not only the calendar: %s. 'portfolio' shows each group's pool."
            % delay_phrase(kinds))


def delay_phrase(kinds):
    """The kinds of delay running projects wait on, as a short phrase."""
    return ", ".join("%s (%d)" % (kind, len(ids)) for kind, ids in sorted(kinds.items())) or "nothing running"


def training_suggestions(sim, trade_rows):
    """One sized teaching suggestion per oversubscribed trade: the people its shortfall needs and the
    founder-hours teaching them takes. Nothing is spent."""
    rows = []
    for row in trade_rows:
        if not row["oversubscribed"]:
            continue
        short = row["demand_hours_this_year"] - row["supply_hours_this_year"]
        people = max(1, math.ceil(short / sim.HOURS_PER_PERSON_YEAR))
        rows.append({"trade": row["trade"], "people_short": people,
                     "teaching_hours": people * sim.TEACHING_HOURS_PER_PERSON,
                     "command": "train %s %d" % (row["trade"], people)})
    return rows


def development_program(sim, nodes, startable):
    """The startable project that costs least cash, sized by what it would draw: its own labour hours
    spread over its years. None when nothing can start."""
    if not startable:
        return None
    node_id = min(startable, key=lambda candidate: (sim.project_cost(candidate), candidate))
    node = nodes[node_id]
    years = max(float(node.get("yrs") or 1.0), 1.0)
    return {"id": node_id, "name": node["name"], "cash_cost": round(sim.project_cost(node_id), 1),
            "years": years,
            "directed_hours_per_year": round(sum((node.get("lab") or {}).values()) / years, 1),
            "command": "start %s" % node_id}
