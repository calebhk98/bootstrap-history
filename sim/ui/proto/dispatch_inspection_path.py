"""The path and materials commands."""

from .route_blockers import route_blockers
from .command_registry import command
from .guidance import LEVERAGE_NOTE, leverage_points
from sim.engine.ui_port import knowledge_loss_warning
from sim.engine.ui_port import active_years_left, remaining_critical_path_years
from sim.engine.ui_port import closure, topo_order
from .techtree import _brief


@command("path", shape="tech", group="overview", aliases=("route", "plan"), fog_hidden=True,
         summary="the route to one thing",
         usage=["path <id or name>"], options={"<id>": "the goal or any target"},
         description="Everything still standing between here and there, and which "
                     "of those you could start today. Try it on your goal first.")
def _cmd_path(sim, nodes, cmd, ended):
    if sim.fog:
        # THE REASON HAS TO BE THE REAL ONE: the command is switched off
        # wholesale under fog, regardless of whether this particular node
        # is already done, and the error must say that rather than implying
        # any one id has not been discovered.
        return {"ok": False,
                "error": "route planning is switched off under fog of war: "
                         "nobody can lay out a road to somewhere they have "
                         "not been, whether or not you have built this "
                         "particular thing already. Use 'available' to see "
                         "what you could begin now."}
    node_id = cmd.get("id")
    if node_id not in nodes:
        return {"ok": False, "error": "unknown node id %r" % node_id}
    need = closure(nodes, node_id)
    order = topo_order(nodes, need)
    remaining = [node_id for node_id in order if node_id not in sim.done]
    out = {"ok": True, "id": node_id, "name": nodes[node_id]["name"], "done": node_id in sim.done,
           "remaining_count": len(remaining), "remaining": remaining,
           "years_following_the_chain_alone": round(remaining_critical_path_years(
               nodes, node_id, sim.done, active_years_left(nodes, sim.active)), 1),
           "years_following_the_chain_alone_means": "the calendar floor of the longest chain, not counting money or hours",
           "leverage_points": leverage_points(sim), "leverage_note": LEVERAGE_NOTE}
    warning = knowledge_loss_warning(sim)
    if warning:
        out["knowledge_loss_warning"] = warning
    # THE JOIN: "what the goal still needs" and "what I could start today"
    # are two separate reports - this one, and `available` - and by
    # midgame nearly everything on `available`'s several-hundred row list
    # is irrelevant to any one goal. Do the intersection here, once,
    # cheapest first, so it never has to be done by eye or by script.
    _startable = sorted((node_id for node_id in remaining if sim.can_start(node_id)),
                        key=lambda x: sim.project_cost(x))
    out["startable_today_count"] = len(_startable)
    out["startable_today_toward_this"] = (
        [_brief(sim, nodes, node_id, False) for node_id in _startable[:30]] or "nothing yet")
    if len(_startable) > 30:
        out["and_more_startable_today"] = len(_startable) - 30
    out["still_waiting_on_something_else"] = len(remaining) - len(_startable)
    if remaining and not _startable:
        out["note"] = "nothing on the route is startable today"
        out["nearest_blockers"] = route_blockers(sim, nodes, remaining, 3)
    # A ROUTE CAN BE ENTIRELY TRUE AND ENTIRELY UNABLE TO PAY THE RENT.
    # Early in any tree the critical path is almost pure knowledge, zero
    # revenue; following `path` with no word of that walks a new player
    # straight into the opening debt trap this engine otherwise warns
    # about everywhere else, unless this screen says so itself.
    #
    # The warning must not be gated on already being insolvent: that
    # catches the damage, never the cause, and by the time recurring
    # income actually goes negative the debt is often already taken. It
    # has to fire every time the route itself cannot pay for itself,
    # whether or not today's ledger happens to look fine yet - and it has
    # to be said with the COMBINED bill of everything listed above, not
    # each item's own affordability, because several individually
    # affordable path items can be collectively unaffordable: `can_start`
    # asks "could I begin this, today, on its own", which is a different
    # and smaller question than "could I finish several of these
    # together".
    if _startable and all(nodes[node_id]["rev"] <= 0 for node_id in _startable):
        _combined = sum(sim.project_cost(node_id) for node_id in _startable)
        _raise = sim.spending_power("start")
        out["this_route_pays_for_nothing"] = (
            "every one of the %d things above is knowledge or "
            "infrastructure - none earns a denarius by itself. This "
            "route will not cover your costs; something off it has to. "
            "{\"cmd\":\"available\",\"sort\":\"earns\",\"reverse\":true} "
            "finds what actually pays today - building one of those "
            "alongside the route is not a detour from it, it is how you "
            "afford to keep walking it." % len(_startable))
        # THE COMBINED BILL, not each item's own affordability: several
        # individually-affordable starts are not one affordable start, and
        # `can_start` has no memory of its own earlier answers, so this is
        # where the total has to be added up.
        if _combined > _raise:
            out["these_together_cost_more_than_you_can_raise"] = (
                "starting everything listed above would cost %s in "
                "all, against %s you could actually raise today. Each "
                "one passed its OWN affordability check when it was "
                "priced; that is not the same question as whether you "
                "can afford several of them at once. Pick one, or a few, "
                "not all of them - and see what pays before spending "
                "the rest."
                % ("{:,.0f}".format(_combined), "{:,.0f}".format(_raise)))
    # A ROUTE THAT DOES NOT SAY "RESTORE" IS A ROUTE YOU CANNOT FOLLOW: a
    # node you know but have SHUT does not appear above (it is done, so it
    # is not remaining, and nothing downstream is blocked by it), yet
    # after a bad century it can be exactly the thing standing between the
    # route and its income, because its plant is gone and its income with
    # it. Only `restore` reopens it, so `path` has to say so explicitly or
    # nothing on this screen points at the right verb.
    _shut = sorted(node_id for node_id in need
                   if node_id in getattr(sim, "mothballed", set()) and node_id in sim.done)
    if _shut:
        out["on_this_route_but_shut_down"] = _shut[:10]
        out["reopen_them_with"] = ("'restore <id>' - you still know how, so "
                                   "putting the plant back costs a fraction "
                                   "of building it. Nothing downstream is "
                                   "waiting on them; their income is")
    return out



@command("materials", shape="bare", group="overview",
         summary="material stocks, production and demand",
         usage=["materials"], options={},
         description="Stocks on hand, annual production and demand, and current "
                     "buy and sell values for every tracked material.")
def _cmd_materials(sim, nodes, cmd, ended):
    return {"ok": True, "materials": sim.materials_report(),
            "units": "stocks are tonnes; production and demand are tonnes/year",
            "how_to_trade": "buy material <name> <tonnes>; sell <name> <tonnes>"}
