"""Read-only inspection and status commands: state, available, why, path,
log, score, risk, values, stuck, mines, capacity, portfolio, economy,
changes, population, materials - every command whose job is to explain the
current position rather than to change it.

Split out of dispatch.py (see that file's own docstring for why): dispatch.py
stays the composition point - the command table, the dispatcher, and every
name protocol.py's shim re-exports - and imports these handlers back from
here. Behaviour is unchanged and moved verbatim.
"""

from ..data import closure, topo_order
from .economy import (_agent_capacity, _agent_changes, _agent_economy,
                      _agent_mines, _agent_portfolio, _agent_values)
from .nodes import _did_you_mean
from .score import score_report
from .state import _agent_log, _agent_state, _waiting_on
from .techtree import _agent_available, _brief, _node_explain


def _cmd_state(s, nodes, cmd, ended):
    return dict(ok=True, **_agent_state(s, nodes, cmd))



def _cmd_available(s, nodes, cmd, ended):
    return _agent_available(s, nodes, cmd)



def _cmd_log(s, nodes, cmd, ended):
    return _agent_log(s, cmd)



def _cmd_score(s, nodes, cmd, ended):
    return {"ok": True, **score_report(s, nodes)}



def _cmd_why(s, nodes, cmd, ended):
    node_id = cmd.get("id")
    # The goal is the one thing you were told the name of on arrival; see
    # the _goal_why note on the fog guard above for why it is `why` alone.
    if (isinstance(node_id, str) and node_id in nodes and not s.is_visible(node_id)
            and node_id != getattr(s, "goal", None)):
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
        # Only blame the fog when there IS any. With it off a break tester
        # mistyped an id and was told the fog was limiting the suggestions,
        # in a game they had explicitly started with the whole tree visible.
        return {"ok": False, "error": "unknown node %r. did you mean: %s"
                % (node_id, ", ".join(_did_you_mean(node_id, nodes, s=s))
                   or ("no idea, and under fog of war I can only suggest "
                       "things you have heard of"
                       if getattr(s, "fog", False)
                       else "no idea - nothing in the tree is spelled much "
                            "like that"))}
    return dict(ok=True, **_node_explain(s, nodes, node_id))



def _cmd_path(s, nodes, cmd, ended):
    if getattr(s, "fog", False):
        # THE REASON HAS TO BE THE REAL ONE. This said "you have not
        # discovered this" for every id, including ones the player had
        # already finished and could see `done: true` on in the same
        # session. A player debugging that would go looking for a corrupt
        # save. The command is switched off wholesale under fog, which is a
        # different fact and the true one.
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
    remaining = [node_id for node_id in order if node_id not in s.done]
    out = {"ok": True, "id": node_id, "name": nodes[node_id]["name"], "done": node_id in s.done,
           "remaining_count": len(remaining), "remaining": remaining}
    # THE JOIN NOBODY HAD: "what the goal still needs" and "what I could
    # start today" were two separate reports - this one, and `available`
    # - and by midgame nearly everything on `available`'s several-hundred
    # row list is irrelevant to any one goal. A Han player wrote their own
    # regex script outside the game to intersect the two; an England
    # player asked for exactly this. Do the intersection here, once,
    # cheapest first, so it never has to be done by eye or by script
    # again.
    _startable = sorted((node_id for node_id in remaining if s.can_start(node_id)),
                        key=lambda x: s.project_cost(x))
    out["startable_today_count"] = len(_startable)
    out["startable_today_toward_this"] = (
        [_brief(s, nodes, node_id, False) for node_id in _startable[:30]] or "nothing yet")
    if len(_startable) > 30:
        out["and_more_startable_today"] = len(_startable) - 30
    out["still_waiting_on_something_else"] = len(remaining) - len(_startable)
    if remaining and not _startable:
        out["note"] = ("nothing on the route is startable today - see "
                       "'stuck' for what the nearest of them are waiting on")
    # A ROUTE CAN BE ENTIRELY TRUE AND ENTIRELY UNABLE TO PAY THE RENT.
    # `path` was promoted into the welcome screen's own starter verbs
    # because an earlier player called it the thing that reorganised
    # their whole run - and a second player, who saw it immediately
    # because of that promotion, reported the half that promotion
    # exposed: early in any tree the critical path is almost pure
    # knowledge, zero revenue, and this screen - now the game's own
    # first suggestion - pointed firmly at it with no word that none of
    # it earns a denarius. They found a profitable concern only by
    # guessing to sort `available` by earnings, which nothing here or in
    # the welcome text mentions. Following the game's own first piece of
    # advice should not be how a new player walks into the opening debt
    # trap this engine otherwise warns about everywhere else.
    #
    # PROMOTING THIS SCREEN MADE THE PROBLEM IT REVEALS MORE DAMAGING, NOT
    # LESS. Three more players hit this once `path` became a starter verb.
    # One read the income gap correctly and recovered by abandoning `path`
    # for `available sort earns reverse`, unprompted by anything in the
    # game. A second started four DIFFERENT path items over five years -
    # each individually affordable on the day it was started - and spent
    # the next 24 years in a debt spiral with two insolvencies and a
    # reputation crash, because each one's own affordability check has no
    # memory of the others: "nothing warns that several individually
    # affordable path items can be collectively unaffordable," in their
    # own words, and they are right - `can_start` asks "could I begin
    # this, today, on its own", which is a different and smaller question
    # than "could I finish several of these together". A third reached
    # the identical trap through `rush` instead.
    #
    # So this is not gated on already being insolvent any more - that
    # caught the damage, never the cause, and by the time recurring
    # income actually goes negative the debt is often already taken.
    # Said plainly, every time the route itself cannot pay for itself,
    # whether or not today's ledger happens to look fine yet; and said
    # with the COMBINED bill of everything listed above, not each item's
    # own affordability, which is the exact number these players were
    # never shown before committing to more than one.
    if _startable and all(nodes[node_id]["rev"] <= 0 for node_id in _startable):
        _combined = sum(s.project_cost(node_id) for node_id in _startable)
        _raise = s.spending_power("start")
        out["this_route_pays_for_nothing"] = (
            "every one of the %d things above is knowledge or "
            "infrastructure - none earns a denarius by itself. This "
            "route will not cover your costs; something off it has to. "
            "{\"cmd\":\"available\",\"sort\":\"earns\",\"reverse\":true} "
            "finds what actually pays today - building one of those "
            "alongside the route is not a detour from it, it is how you "
            "afford to keep walking it." % len(_startable))
        # THE COMBINED BILL, not each item's own affordability. Several
        # individually-affordable starts are not one affordable start;
        # `can_start` has no memory of its own earlier answers, so the
        # first time a player can see the total is here, where several
        # are listed together.
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
    # A ROUTE THAT DOES NOT SAY "RESTORE" IS A ROUTE YOU CANNOT FOLLOW. A
    # break tester drove a run mechanically from `path` after a sack:
    # `path` listed lead_chamber as remaining, `start` answered "you built
    # this once - restore it", and anything downstream said the same node
    # was a missing prerequisite. They sat at 106 technologies and 760,403
    # denarii from 460 AD to the horizon, because `path` never mentioned
    # the one verb that would have moved them.
    # A node you know but have SHUT does not appear above: it is done, so
    # it is not remaining, and nothing downstream is blocked by it. It is
    # still the thing a player driving from `path` most needs to see after
    # a bad century, because its plant is gone and its income with it.
    _shut = sorted(node_id for node_id in need
                   if node_id in getattr(s, "mothballed", set()) and node_id in s.done)
    if _shut:
        out["on_this_route_but_shut_down"] = _shut[:10]
        out["reopen_them_with"] = ("'restore <id>' - you still know how, so "
                                   "putting the plant back costs a fraction "
                                   "of building it. Nothing downstream is "
                                   "waiting on them; their income is")
    return out



def _cmd_materials(s, nodes, cmd, ended):
    return {"ok": True, "materials": s.materials_report(),
            "units": "stocks are tonnes; production and demand are tonnes/year",
            "how_to_trade": "buy material <name> <tonnes>; sell <name> <tonnes>"}



def _cmd_risk(s, nodes, cmd, ended):
    knowledge_risk = s.knowledge_risk()
    return {"ok": True, "knowledge_risk": knowledge_risk, "year": s.year,
            "note": "What history is about to do to you, and what you have "
                    "built that blunts it. Every hazard here is fightable."}



def _cmd_values(s, nodes, cmd, ended):
    return _agent_values(s)



def _cmd_stuck(s, nodes, cmd, ended):
    # THE QUESTION EVERY TESTER ASKED, in different words. "There's no 'why
    # am I stuck?' view - three separate 90-250-year stalls, each caused by
    # one node blocked on one thing, each found by typing `why` at a
    # guess." The pieces were all here; nothing put them in one place, and
    # stall_diagnosis only spoke after eight years of insolvency.
    _fog = getattr(s, "fog", False)
    reasons = []
    _startable = [node_id for node_id in nodes
                  if node_id not in s.done and node_id not in s.active
                  and (not _fog or s.is_visible(node_id))
                  and s.start_reason(node_id)[0]]
    _afford = [node_id for node_id in _startable
               if s.project_cost(node_id) <= s.spending_power("start")]
    if s.active:
        _waits = {}
        _why_underfunded = {}
        for node_id, progress in sorted(s.active.items()):
            bill = progress.get("cost_left")
            if bill is None:
                bill = max(0.0, s.project_cost(node_id) - progress["spent"])
            _waits[node_id] = _waiting_on(s, nodes, node_id, progress, bill)
            # SAME GAP AS `why` AND `state`: arrears gives unspendable
            # founder hours back, so this can say "waiting on your hours"
            # for a project that is really stuck on money, on the exact
            # screen a player checks first when something is stalled.
            # why_underfunded, already computed onto st by core.py, is
            # the real reason - carry it per project, not just the string
            # above.
            if progress.get("why_underfunded"):
                _why_underfunded[node_id] = progress["why_underfunded"]
        reasons.append({"what": "work in hand",
                        "how_many": len(s.active),
                        "each_waiting_on": _waits,
                        **({"each_why_underfunded": _why_underfunded}
                           if _why_underfunded else {})})
    # THE ROAD TO THE GOAL, not the tree at large. A play tester with fifty
    # nodes left and nothing startable was told "you have work in hand,
    # money to pay for it and people to do it", because two hundred
    # unrelated things elsewhere in the tree were startable. Nobody is
    # stuck for want of a bottling shed.
    _goal = getattr(s, "goal", None)
    _goal_routing_off_under_fog = False
    if _goal in nodes and not _fog:
        _road = closure(nodes, _goal) - s.done
        _road_open = [node_id for node_id in _road if s.start_reason(node_id)[0]]
        if _road and not _road_open:
            _near = sorted(_road, key=lambda k: len(closure(nodes, k) - s.done))
            reasons.append({
                "what": "the road to the goal",
                "why": "%d of its nodes are still to build and NONE of them "
                       "is startable today. The nearest is %s: %s"
                       % (len(_road), _near[0],
                          s.start_reason(_near[0])[1]),
                "the_nearest_few": _near[:5]})
    elif _goal in nodes and _fog:
        # SAY SO, THE WAY `rush` DOES. A blind Han run with the goal set
        # to the junction transistor hit hundreds of affordable things
        # late in the game and was told to open a profitable concern
        # instead of being pointed at the one real blocker - not because
        # this command was broken, but because the road-to-the-goal
        # branch above is switched off under fog of war for exactly the
        # reason 'path' gives for doing the same: naming what is left on
        # a route to something not fully discovered would hand over the
        # hidden tree. The silence read as "everything below is the real
        # answer" when it was really "the one analysis that could answer
        # this did not run". A player should be told that, not left to
        # infer it from an unhelpful reply.
        _goal_routing_off_under_fog = True
    # STARTING NOTHING IS THE COMMONEST WAY TO GET NOWHERE, and this
    # command - whose whole job is "why you are not getting on" - said
    # "nothing: you have work in hand, money to pay for it and people to do
    # it" to a play tester on turn one, with no project running at all. It
    # was the first thing they typed and it was false.
    if not s.active:
        _cheap = (min(_afford or _startable, key=lambda k: s.project_cost(k))
                  if (_afford or _startable) else None)
        reasons.append({"what": "you have started nothing",
                        "why": ("no project is in hand, so no year of yours "
                                "is being spent on one. %s"
                                % ("'start %s' would begin the cheapest "
                                   "thing you can pay for today." % _cheap
                                   if _cheap else
                                   "and nothing in front of you can be "
                                   "begun, which the rows below explain."))})
    # AND WHAT YOU HAVE BUILT AND NEVER SWITCHED ON. A break tester read
    # "NOTHING YOU COULD BEGIN" while two concerns sat finished and closed
    # that between them raised their revenue by 71%.
    _shut = sorted(node_id for node_id in s.done
                   if s.is_venture(node_id) and node_id not in s.operating
                   and nodes[node_id]["rev"] > nodes[node_id]["up"])
    if _shut:
        # DO NOT RECOMMEND A COMMAND THAT WILL FAIL. This used to pick
        # the best-margin shut concern by revenue minus upkeep alone and
        # tell the player to 'open' it, without ever checking whether
        # open_venture would actually let them. A household deep in the
        # credit-exhaustion/named-trade trap (see PATH_SEARCH.md) sits
        # with free_art at 0.00-0.03 for centuries: this command was
        # measured telling such a household "open lens_grinding", which
        # needs 2.13 craftsmen to supervise and fails outright - advice
        # that spends a turn on a refusal and reads as the game having
        # lied about what it just told you to do.
        _sch_free, _art_free = s.venture_staff_free()
        _shut_for_staff = getattr(s, "shut_for_staff", {})
        def _capex_now(_k):
            _fee = s.venture_capex(_k)
            if (_k in _shut_for_staff
                    and s.year - _shut_for_staff[_k] <= s.STAFF_CLOSURE_GRACE):
                _fee *= 0.1
            return _fee
        def _openable(_k):
            _need_sch, _need_art = s.venture_hands(_k)
            return (_need_sch <= _sch_free + 0.01
                    and _need_art <= _art_free + 0.01
                    and _capex_now(_k) <= s.spending_power("buy"))
        _really_openable = [node_id for node_id in _shut if _openable(node_id)]
        if _really_openable:
            _best = max(_really_openable,
                       key=lambda k: nodes[k]["rev"] - nodes[k]["up"])
            reasons.append({"what": "things you built and never opened",
                            "why": "%d finished concern(s) are shut and "
                                   "earning nothing. The best you could "
                                   "actually open right now is %s, which "
                                   "would earn %s a year against %s of "
                                   "upkeep: 'open %s'"
                                   % (len(_shut), _best,
                                      "{:,.0f}".format(nodes[_best]["rev"]),
                                      "{:,.0f}".format(nodes[_best]["up"]),
                                      _best)})
        else:
            _best = max(_shut, key=lambda k: nodes[k]["rev"] - nodes[k]["up"])
            _need_sch, _need_art = s.venture_hands(_best)
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
                           "{:,.0f}".format(s.spending_power("buy"))))
            reasons.append({"what": "things you built and cannot open yet",
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
                                      _why)})
    if not _startable:
        reasons.append({"what": "nothing you could begin",
                        "why": "everything in front of you is either built, "
                               "already running, or waiting on something. "
                               "'available' says which."})
    elif not _afford:
        reasons.append({"what": "money",
                        "why": "%d things are startable and the cheapest of "
                               "them costs %s, against the %s you could "
                               "raise"
                               % (len(_startable),
                                  "{:,.0f}".format(min(s.project_cost(node_id)
                                                       for node_id in _startable)),
                                  "{:,.0f}".format(s.spending_power("start")))})
    if s.binding and s.resource_throttle() < 0.95:
        reasons.append({"what": "a raw material",
                        "why": "%s: work is running at %d%% of plan. %s"
                               % (s.binding, s.resource_throttle() * 100,
                                  s.shortage_remedy(s.binding))})
    _room = s.household_room()
    if _room < 1.0:
        reasons.append({"what": "room for people",
                        "why": "you can take %.2f more people. %s"
                               % (max(0.0, _room), s._room_advice())})
    if s.capital < 0:
        reasons.append({"what": "arrears",
                        "why": "you owe %s of the %s anyone will advance "
                               "you, and the interest is %s a year"
                               % ("{:,.0f}".format(-s.capital),
                                  "{:,.0f}".format(s.credit_limit()),
                                  "{:,.0f}".format(-s.capital
                                                   * s.debt_interest_rate()))})
    if s.year < getattr(s, "credit_frozen_until", 0):
        reasons.append({"what": "a credit freeze",
                        "why": "nobody will fund new work until %d"
                               % int(s.credit_frozen_until)})
    _stall = s.stall_diagnosis()
    out = {"ok": True,
           "you_could_begin": len(_startable),
           "and_could_pay_for": len(_afford),
           "what_is_holding_you_up": reasons or (
               "nothing: %d project(s) in hand, money to pay for them and "
               "people to do them" % len(s.active)),
           "and_the_cheapest_thing_you_could_start_now": (
               min(_startable, key=lambda k: s.project_cost(k))
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



def _cmd_mines(s, nodes, cmd, ended):
    # See _agent_mines above: the one place this arithmetic is written,
    # shared with `capacity`, so the two screens cannot drift apart.
    return _agent_mines(s)



def _cmd_capacity(s, nodes, cmd, ended):
    return _agent_capacity(s, nodes, cmd)



def _cmd_portfolio(s, nodes, cmd, ended):
    return _agent_portfolio(s, nodes, cmd)



def _cmd_economy(s, nodes, cmd, ended):
    return _agent_economy(s, cmd)



def _cmd_changes(s, nodes, cmd, ended):
    return _agent_changes(s, nodes, cmd)



def _cmd_population(s, nodes, cmd, ended):
    return {"ok": True, **s.population_report()}
