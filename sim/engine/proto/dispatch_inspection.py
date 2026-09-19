"""Read-only inspection and status commands: state, available, why, path,
log, score, risk, values, stuck, mines, capacity, portfolio, economy,
changes, population, materials - every command whose job is to explain the
current position rather than to change it.

dispatch.py stays the composition point - the command table, the
dispatcher, and every name protocol.py's shim re-exports - and imports
these handlers back from here (see dispatch.py's own docstring for why
these live in a separate file).
"""

from ..data import closure, topo_order
from .economy import (_agent_capacity, _agent_changes, _agent_economy,
                      _agent_mines, _agent_portfolio, _agent_values)
from .nodes import _did_you_mean
from .score import score_report
from .state import _agent_log, _agent_state, _waiting_on
from .techtree import _agent_available, _brief, _node_explain


def _cmd_state(sim, nodes, cmd, ended):
    return dict(ok=True, **_agent_state(sim, nodes, cmd))



def _cmd_available(sim, nodes, cmd, ended):
    return _agent_available(sim, nodes, cmd)



def _cmd_log(sim, nodes, cmd, ended):
    return _agent_log(sim, cmd)



def _cmd_score(sim, nodes, cmd, ended):
    return {"ok": True, **score_report(sim, nodes)}



def _cmd_why(sim, nodes, cmd, ended):
    node_id = cmd.get("id")
    # The goal is the one thing you were told the name of on arrival; see
    # the _goal_why note on the fog guard above for why it is `why` alone.
    if (isinstance(node_id, str) and node_id in nodes and not sim.is_visible(node_id)
            and node_id != getattr(sim, "goal", None)):
        return {"ok": False,
                "error": "you have never heard of that. You know what you have "
                         "built and what you could begin now; use 'available'."}
    if not isinstance(node_id, str):
        return {"ok": False,
                "error": 'which one? give an id, for example '
                         '{"cmd":"why","id":"units_standards"}. '
                         'Use {"cmd":"available"} to see what you could begin.'
                if node_id is None else
                "id must be a name in quotes, not %s" % type(node_id).__name__}
    if node_id not in nodes:
        # Only blame the fog when there IS any: with fog off, the error must
        # not claim fog is limiting the suggestions, in a game started with
        # the whole tree visible.
        return {"ok": False, "error": "unknown node %r. did you mean: %s"
                % (node_id, ", ".join(_did_you_mean(node_id, nodes, sim=sim))
                   or ("no idea, and under fog of war I can only suggest "
                       "things you have heard of"
                       if getattr(sim, "fog", False)
                       else "no idea - nothing in the tree is spelled much "
                            "like that"))}
    return dict(ok=True, **_node_explain(sim, nodes, node_id))



def _cmd_path(sim, nodes, cmd, ended):
    if getattr(sim, "fog", False):
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
           "remaining_count": len(remaining), "remaining": remaining}
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
        out["note"] = ("nothing on the route is startable today - see "
                       "'stuck' for what the nearest of them are waiting on")
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



def _cmd_materials(sim, nodes, cmd, ended):
    return {"ok": True, "materials": sim.materials_report(),
            "units": "stocks are tonnes; production and demand are tonnes/year",
            "how_to_trade": "buy material <name> <tonnes>; sell <name> <tonnes>"}



def _cmd_risk(sim, nodes, cmd, ended):
    knowledge_risk = sim.knowledge_risk()
    return {"ok": True, "knowledge_risk": knowledge_risk, "year": sim.year,
            "note": "What history is about to do to you, and what you have "
                    "built that blunts it. Every hazard here is fightable."}



def _cmd_values(sim, nodes, cmd, ended):
    return _agent_values(sim)



def _stuck_work_in_hand(sim, nodes):
    if not sim.active:
        return None
    _waits = {}
    _why_underfunded = {}
    for node_id, progress in sorted(sim.active.items()):
        bill = progress.get("cost_left")
        if bill is None:
            bill = max(0.0, sim.project_cost(node_id) - progress["spent"])
        _waits[node_id] = _waiting_on(sim, nodes, node_id, progress, bill)
        # SAME GAP AS `why` AND `state`: arrears gives unspendable
        # founder hours back, so this can say "waiting on your hours"
        # for a project that is really stuck on money, on the exact
        # screen a player checks first when something is stalled.
        # why_underfunded, already computed onto st by core.py, is
        # the real reason - carry it per project, not just the string
        # above.
        if progress.get("why_underfunded"):
            _why_underfunded[node_id] = progress["why_underfunded"]
    return {"what": "work in hand",
            "how_many": len(sim.active),
            "each_waiting_on": _waits,
            **({"each_why_underfunded": _why_underfunded}
               if _why_underfunded else {})}


def _stuck_road_to_goal(sim, nodes, _fog):
    # THE ROAD TO THE GOAL, not the tree at large: a report that leans on
    # whether ANYTHING in the tree is startable is useless when hundreds
    # of unrelated things are startable but none of them serves the goal.
    # Nobody is stuck for want of a bottling shed.
    #
    # Returns (reason_or_None, goal_routing_off_under_fog) - the caller needs
    # the flag even on the years this has no reason to report, to explain at
    # the end why nothing here spoke about the goal at all.
    _goal = getattr(sim, "goal", None)
    _goal_routing_off_under_fog = False
    if _goal in nodes and not _fog:
        _road = closure(nodes, _goal) - sim.done
        _road_open = [node_id for node_id in _road if sim.start_reason(node_id)[0]]
        if _road and not _road_open:
            _near = sorted(_road, key=lambda k: len(closure(nodes, k) - sim.done))
            return ({
                "what": "the road to the goal",
                "why": "%d of its nodes are still to build and NONE of them "
                       "is startable today. The nearest is %s: %s"
                       % (len(_road), _near[0],
                          sim.start_reason(_near[0])[1]),
                "the_nearest_few": _near[:5]}, _goal_routing_off_under_fog)
    elif _goal in nodes and _fog:
        # SAY SO, THE WAY `rush` DOES: the road-to-the-goal branch above is
        # switched off under fog of war for exactly the reason `path`
        # gives for doing the same - naming what is left on a route to
        # something not fully discovered would hand over the hidden tree.
        # Silence here would read as "everything below is the real answer"
        # when it is really "the one analysis that could answer this did
        # not run", so the caller is handed _goal_routing_off_under_fog and
        # must say so rather than leaving a player to infer it from an
        # unhelpful reply.
        _goal_routing_off_under_fog = True
    return (None, _goal_routing_off_under_fog)


def _stuck_started_nothing(sim, _startable, _afford):
    # STARTING NOTHING IS THE COMMONEST WAY TO GET NOWHERE, and this
    # command - whose whole job is "why you are not getting on" - must not
    # report "you have work in hand, money to pay for it and people to do
    # it" when no project is actually active.
    if sim.active:
        return None
    _cheap = (min(_afford or _startable, key=lambda k: sim.project_cost(k))
              if (_afford or _startable) else None)
    return {"what": "you have started nothing",
            "why": ("no project is in hand, so no year of yours "
                    "is being spent on one. %s"
                    % ("'start %s' would begin the cheapest "
                       "thing you can pay for today." % _cheap
                       if _cheap else
                       "and nothing in front of you can be "
                       "begun, which the rows below explain."))}


def _stuck_shut_ventures(sim, nodes):
    # AND WHAT YOU HAVE BUILT AND NEVER SWITCHED ON: a report of "nothing
    # you could begin" is incomplete while a finished, closed concern with
    # revenue above upkeep sits unopened - reopening it needs no new
    # building at all.
    _shut = sorted(node_id for node_id in sim.done
                   if sim.is_venture(node_id) and node_id not in sim.operating
                   and nodes[node_id]["rev"] > nodes[node_id]["up"])
    if not _shut:
        return None
    # DO NOT RECOMMEND A COMMAND THAT WILL FAIL: picking the best-margin
    # shut concern by revenue minus upkeep alone and telling the player to
    # 'open' it is not enough, because a household deep in the
    # credit-exhaustion/named-trade trap (see PATH_SEARCH.md) can have too
    # little free staff capacity for open_venture to actually succeed.
    # The recommendation has to check that it would work, not just that
    # it would pay.
    _sch_free, _art_free = sim.venture_staff_free()
    _shut_for_staff = getattr(sim, "shut_for_staff", {})
    def _capex_now(_k):
        _fee = sim.venture_capex(_k)
        if (_k in _shut_for_staff
                and sim.year - _shut_for_staff[_k] <= sim.STAFF_CLOSURE_GRACE):
            _fee *= 0.1
        return _fee
    def _openable(_k):
        _need_sch, _need_art = sim.venture_hands(_k)
        return (_need_sch <= _sch_free + 0.01
                and _need_art <= _art_free + 0.01
                and _capex_now(_k) <= sim.spending_power("buy"))
    _really_openable = [node_id for node_id in _shut if _openable(node_id)]
    if _really_openable:
        _best = max(_really_openable,
                   key=lambda k: nodes[k]["rev"] - nodes[k]["up"])
        return {"what": "things you built and never opened",
                "why": "%d finished concern(s) are shut and "
                       "earning nothing. The best you could "
                       "actually open right now is %s, which "
                       "would earn %s a year against %s of "
                       "upkeep: 'open %s'"
                       % (len(_shut), _best,
                          "{:,.0f}".format(nodes[_best]["rev"]),
                          "{:,.0f}".format(nodes[_best]["up"]),
                          _best)}
    _best = max(_shut, key=lambda k: nodes[k]["rev"] - nodes[k]["up"])
    _need_sch, _need_art = sim.venture_hands(_best)
    if _need_sch > _sch_free + 0.01 or _need_art > _art_free + 0.01:
        _why = ("it needs the full-time equivalent of %.2f "
                "scholars and %.2f craftsmen to supervise it "
                "(a continuous share of their year, not a "
                "headcount), and you have %.2f and %.2f not "
                "already watching something else"
                % (_need_sch, _need_art, _sch_free, _art_free))
    else:
        _why = ("opening it costs %s denarii, and between cash "
                "and what anyone will advance you can raise %s"
                % ("{:,.0f}".format(_capex_now(_best)),
                   "{:,.0f}".format(sim.spending_power("buy"))))
    return {"what": "things you built and cannot open yet",
            "why": "%d finished concern(s) are shut and "
                   "earning nothing, and none of them can "
                   "be opened right now. The best is %s, "
                   "which would earn %s a year against "
                   "%s of upkeep, but %s. Hire, teach, or "
                   "close something to free the hands, "
                   "or raise the money, and try again"
                   % (len(_shut), _best,
                      "{:,.0f}".format(nodes[_best]["rev"]),
                      "{:,.0f}".format(nodes[_best]["up"]),
                      _why)}


def _stuck_nothing_or_money(sim, _startable, _afford):
    if not _startable:
        return {"what": "nothing you could begin",
                "why": "everything in front of you is either built, "
                       "already running, or waiting on something. "
                       "'available' says which."}
    if not _afford:
        return {"what": "money",
                "why": "%d things are startable and the cheapest of "
                       "them costs %s, against the %s you could "
                       "raise"
                       % (len(_startable),
                          "{:,.0f}".format(min(sim.project_cost(node_id)
                                               for node_id in _startable)),
                          "{:,.0f}".format(sim.spending_power("start")))}
    return None


def _stuck_raw_material(sim):
    if sim.binding and sim.resource_throttle() < 0.95:
        return {"what": "a raw material",
                "why": "%s: work is running at %d%% of plan. %s"
                       % (sim.binding, sim.resource_throttle() * 100,
                          sim.shortage_remedy(sim.binding))}
    return None


def _stuck_room_for_people(sim):
    _room = sim.household_room()
    if _room < 1.0:
        return {"what": "room for people",
                "why": "you can take %.2f more people. %s"
                       % (max(0.0, _room), sim._room_advice())}
    return None


def _stuck_arrears(sim):
    if sim.capital < 0:
        return {"what": "arrears",
                "why": "you owe %s of the %s anyone will advance "
                       "you, and the interest is %s a year"
                       % ("{:,.0f}".format(-sim.capital),
                          "{:,.0f}".format(sim.credit_limit()),
                          "{:,.0f}".format(-sim.capital
                                           * sim.debt_interest_rate()))}
    return None


def _stuck_credit_freeze(sim):
    if sim.year < getattr(sim, "credit_frozen_until", 0):
        return {"what": "a credit freeze",
                "why": "nobody will fund new work until %d"
                       % int(sim.credit_frozen_until)}
    return None


def _stuck_startable_and_afford(sim, nodes, _fog):
    _startable = [node_id for node_id in nodes
                  if node_id not in sim.done and node_id not in sim.active
                  and (not _fog or sim.is_visible(node_id))
                  and sim.start_reason(node_id)[0]]
    _afford = [node_id for node_id in _startable
               if sim.project_cost(node_id) <= sim.spending_power("start")]
    return _startable, _afford


def _cmd_stuck(sim, nodes, cmd, ended):
    # WHY AM I STUCK: several independent kinds of stall - work blocked, no
    # road to the goal, nothing started, a shut venture, a binding raw
    # material, no room for people, arrears, a credit freeze - can each
    # keep a run motionless for decades, and stall_diagnosis alone only
    # speaks once insolvency has already set in. This command gathers
    # every check into one place instead of making a player find each
    # cause by guessing at `why`.
    _fog = getattr(sim, "fog", False)
    _startable, _afford = _stuck_startable_and_afford(sim, nodes, _fog)
    _goal_reason, _goal_routing_off_under_fog = _stuck_road_to_goal(sim, nodes, _fog)
    # Every check below is independent, and GATHERS into `reasons`: each one
    # that has something to say is kept, none of them stop the others from
    # running. More than one usually applies at once, and a player deciding
    # what to fix first needs to see all of them, not just whichever is
    # checked first - see _compact_stuck in dispatch.py, which already
    # assumes this list can hold several entries. The order below is the
    # fixed order a player reads them in: work in hand, the road to the
    # goal, having started nothing, shut ventures, nothing startable or
    # unaffordable, a binding raw material, no room for people, arrears, a
    # credit freeze.
    _checks = (
        _stuck_work_in_hand(sim, nodes),
        _goal_reason,
        _stuck_started_nothing(sim, _startable, _afford),
        _stuck_shut_ventures(sim, nodes),
        _stuck_nothing_or_money(sim, _startable, _afford),
        _stuck_raw_material(sim),
        _stuck_room_for_people(sim),
        _stuck_arrears(sim),
        _stuck_credit_freeze(sim),
    )
    reasons = [reason for reason in _checks if reason]
    _stall = sim.stall_diagnosis()
    out = {"ok": True,
           "you_could_begin": len(_startable),
           "and_could_pay_for": len(_afford),
           "what_is_holding_you_up": reasons or (
               "nothing: %d project(s) in hand, money to pay for them and "
               "people to do them" % len(sim.active)),
           "and_the_cheapest_thing_you_could_start_now": (
               min(_startable, key=lambda k: sim.project_cost(k))
               if _startable else None)}
    if _stall:
        out["and_you_are_in_a_hole"] = _stall
    if _goal_routing_off_under_fog:
        out["this_does_not_know_your_goal"] = (
            "fog of war is on, so this cannot check whether anything "
            "below is actually on the route to your goal, or name the "
            "one thing blocking it - that would leak the hidden tree, "
            "the same reason 'path' refuses outright under fog. "
            "Everything above is general advice, not goal-directed; "
            "'why <id>' on anything you have heard of is still the way "
            "to reason toward the goal by hand.")
    return out



def _cmd_mines(sim, nodes, cmd, ended):
    # See _agent_mines above: the one place this arithmetic is written,
    # shared with `capacity`, so the two screens cannot drift apart.
    return _agent_mines(sim)



def _cmd_capacity(sim, nodes, cmd, ended):
    return _agent_capacity(sim, nodes, cmd)



def _cmd_portfolio(sim, nodes, cmd, ended):
    return _agent_portfolio(sim, nodes, cmd)



def _cmd_economy(sim, nodes, cmd, ended):
    return _agent_economy(sim, cmd)



def _cmd_changes(sim, nodes, cmd, ended):
    return _agent_changes(sim, nodes, cmd)



def _cmd_population(sim, nodes, cmd, ended):
    return {"ok": True, **sim.population_report()}
