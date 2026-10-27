"""The path and materials commands."""

from .route_blockers import route_blockers
from sim.engine.ui_port import money_text
from .command_registry import command
from .guidance import LEVERAGE_NOTE, leverage_points
from sim.engine.ui_port import knowledge_loss_warning
from sim.engine.ui_port import active_years_left, remaining_critical_path_years
from sim.engine.ui_port import closure, topo_order
from .techtree import _brief


def route_money_warnings(startable_count, any_pays_its_way, combined_bill, can_raise, money_words):
    """The money warnings of a route's startable steps, as reply fields.

    A route can be entirely true and entirely unable to pay the rent: early in any tree its critical path is almost
    pure knowledge, so following it with no word of that walks a new player into the opening debt trap. The warning
    is not gated on already being insolvent, which catches the damage and never the cause; it fires whenever nothing
    on the list earns more than it costs to keep running. And it states the COMBINED bill of everything listed,
    because several individually affordable starts are not one affordable start (`can_start` has no memory of its
    earlier answers). `money_words` turns an amount into the player's coin."""
    if not startable_count or any_pays_its_way:
        return {}
    out = {"this_route_pays_for_nothing": (
        "none of the %d things above earns more than it costs to "
        "keep running - they are knowledge or infrastructure, or "
        "trades that do not yet pay their way. This "
        "route will not cover your costs; something off it has to. "
        "{\"cmd\":\"available\",\"sort\":\"earns\",\"reverse\":true} "
        "finds what actually pays today - building one of those "
        "alongside the route is not a detour from it, it is how you "
        "afford to keep walking it." % startable_count)}
    if combined_bill > can_raise:
        out["these_together_cost_more_than_you_can_raise"] = (
            "starting everything listed above would cost %s in "
            "all, against %s you could actually raise today. Each "
            "one passed its OWN affordability check when it was "
            "priced; that is not the same question as whether you "
            "can afford several of them at once. Pick one, or a few, "
            "not all of them - and see what pays before spending "
            "the rest."
            % (money_words(combined_bill), money_words(can_raise)))
    return out


@command("path", shape="tech", group="overview", aliases=("route", "plan"), fog_hidden=True,
         summary="the route to one thing",
         usage=["path <id or name>"], options={"<id>": "the goal or any target"},
         description="Everything still standing between here and there, and which "
                     "of those you could start today. Try it on your goal first.")
def _cmd_path(sim, nodes, cmd, ended):
    if sim.view("legacy_fog")():
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
    node_id = cmd.get("id") or sim.view("goal")()["node"]    # a bare `path` is the route to the goal
    if node_id not in nodes:
        return {"ok": False, "error": "unknown node id %r" % node_id}
    need = closure(nodes, node_id)
    order = topo_order(nodes, need)
    remaining = [node_id for node_id in order if node_id not in sim.view("techniques_held")()]
    out = {"ok": True, "id": node_id, "name": nodes[node_id]["name"], "done": node_id in sim.view("techniques_held")(),
           "remaining_count": len(remaining), "remaining": remaining,
           "years_following_the_chain_alone": round(remaining_critical_path_years(
               nodes, node_id, sim.view("techniques_held")(), active_years_left(nodes, sim.view("active_projects")())), 1),
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
    _startable = sorted((node_id for node_id in remaining if sim.view("start_check")(node_id, False, None, False)[0]),
                        key=lambda x: sim.view("project_cost")(x))
    out["startable_today_count"] = len(_startable)
    out["startable_today_toward_this"] = (
        [_brief(sim, nodes, node_id, False) for node_id in _startable[:30]] or "nothing yet")
    if len(_startable) > 30:
        out["and_more_startable_today"] = len(_startable) - 30
    out["still_waiting_on_something_else"] = len(remaining) - len(_startable)
    if remaining and not _startable:
        out["note"] = "nothing on the route is startable today"
        out["nearest_blockers"] = route_blockers(sim, nodes, remaining, 3)
    # A ROUTE CAN BE ENTIRELY TRUE AND ENTIRELY UNABLE TO PAY THE RENT: say so every time, not only once in debt
    # (see route_money_warnings).
    out.update(route_money_warnings(
        len(_startable),
        any(sim.view("venture_real_earnings")(node_id) > sim.view("venture_upkeep_quote")(node_id)["now"] for node_id in _startable),
        sum(sim.view("project_cost")(node_id) for node_id in _startable),
        sim.view("spending_power")("start"),
        lambda amount: money_text(amount, sim, grouped=True)))
    # A ROUTE THAT DOES NOT SAY "RESTORE" IS A ROUTE YOU CANNOT FOLLOW: a
    # node you know but have SHUT does not appear above (it is done, so it
    # is not remaining, and nothing downstream is blocked by it), yet
    # after a bad century it can be exactly the thing standing between the
    # route and its income, because its plant is gone and its income with
    # it. Only `restore` reopens it, so `path` has to say so explicitly or
    # nothing on this screen points at the right verb.
    _shut = sorted(node_id for node_id in need
                   if node_id in sim.view("mothballed")() and node_id in sim.view("techniques_held")())
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
    return {"ok": True, "materials": sim.view("materials_report")(),
            "units": "stocks are tonnes; production and demand are tonnes/year",
            "how_to_trade": "buy material <name> <tonnes>; sell <name> <tonnes>"}
