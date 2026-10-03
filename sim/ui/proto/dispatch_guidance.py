"""`leverage` and `idle`: guidance screens (Complaints/98, 99)."""

from .command_registry import command
from .economy import _trade_demand_rows
from .guidance import (LEVERAGE_NOTE, delay_kinds, development_program, leverage_points,
                       training_suggestions, wait_explanation)


@command("leverage", group="overview", aliases=("levers",),
         summary="the system levers that make any goal cheaper",
         usage=["leverage"], options={},
         description="Literacy, labour, finance, institutions, knowledge and materials, each "
                     "with the figures the engine holds now. A broad approach can make a hard "
                     "goal cheaper than following its prerequisites alone.")
def _cmd_leverage(sim, nodes, cmd, ended):
    return {"ok": True, "leverage_points": leverage_points(sim), "note": LEVERAGE_NOTE}


@command("idle", group="overview", aliases=("spare_hours", "unused"),
         summary="directed hours not committed, and what they could do",
         usage=["idle"], options={},
         description="This year's directed capacity, what active projects commit, the idle "
                     "remainder, why running work is waiting, and what could use the hours. "
                     "It never spends them.")
def _cmd_idle(sim, nodes, cmd, ended):
    pool = sim.labour.director_pool()
    committed = sim.labour.director_hours_committed()
    startable = [node_id for node_id in nodes
                 if node_id not in sim.done and node_id not in sim.active
                 and (not sim.fog or sim.is_visible(node_id)) and sim.can_start(node_id)]
    kinds = delay_kinds(sim, nodes)
    sized_training = training_suggestions(sim, _trade_demand_rows(sim))
    return {
        "ok": True,
        "directed_hours_this_year": round(pool, 1),
        "committed_hours": round(committed, 1),
        "idle_hours": round(max(0.0, pool - committed), 1),
        "delay_kinds": kinds,
        "what_the_wait_is": wait_explanation(kinds),
        "potential_uses": {
            "startable_today": len(startable),
            "startable_at_no_cash_cost": sum(1 for node_id in startable if sim.project_cost(node_id) <= 0),
            "train_oversubscribed_trades": sized_training or "none",
            "development_program": development_program(sim, nodes, startable),
            "wage_work": "'work <trade> <hours>' sells idle hours for wages; 'allocate' points hours at a project",
        },
        "note": "Hours do not carry into the next year. Nothing here spends them: 'available' lists what could begin.",
    }
