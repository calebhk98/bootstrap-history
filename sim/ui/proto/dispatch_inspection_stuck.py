"""The stuck command and the goal-route blocker helpers behind it."""

from .command_registry import command
from .route_blockers import route_blockers
from sim.engine.ui_port import money_text
from .saving_plan import saving_reason
from sim.engine.ui_port import closure
from .state_waiting import _waiting_on
from .stuck_advice import calendar_bound_advice, filler_note, lever_line


def _stuck_work_in_hand(sim, nodes):
    if not sim.active:
        return None
    _waits = {}
    _kinds = {}
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
            _kinds[node_id] = "money"
        elif progress.get("ph_left", 0.0) <= 0 and progress.get("yrs", 0.0) < sim.calendar_floor(node_id):
            _kinds[node_id] = "calendar"
        else:
            _kinds[node_id] = "active"
    return {"what": "work in hand", "kind": "active",
            "how_many": len(sim.active),
            "each_waiting_on": _waits,
            "each_kind": _kinds,
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
    _goal = sim.goal
    _goal_routing_off_under_fog = False
    if _goal in nodes and not _fog:
        _road = closure(nodes, _goal) - sim.done
        _road_open = [node_id for node_id in _road if sim.start_reason(node_id)[0]]
        if _road and not _road_open:
            _near = route_blockers(sim, nodes, _road, 5)
            return ({
                "what": "the road to the goal", "kind": _near[0]["kind"] or "knowledge",
                "why": "%d of its nodes are still to build and NONE of them "
                       "is startable today. The nearest is %s: %s"
                       % (len(_road), _near[0]["id"], _near[0]["why"]),
                "the_nearest_few": [row["id"] for row in _near]},
                _goal_routing_off_under_fog)
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


def _stuck_started_nothing(sim, _startable, _afford, saving=False):
    # STARTING NOTHING IS THE COMMONEST WAY TO GET NOWHERE, and this
    # command - whose whole job is "why you are not getting on" - must not
    # report "you have work in hand, money to pay for it and people to do
    # it" when no project is actually active.
    if sim.active:
        return None
    _cheap = (min(_afford or _startable, key=lambda k: sim.project_cost(k))
              if (_afford or _startable) and not saving else None)
    if saving:
        return {"what": "you have started nothing", "kind": "idle",
                "why": "no project is in hand, which is what the savings plan below intends."}
    return {"what": "you have started nothing", "kind": "idle",
            "why": ("no project is in hand, so no year of yours "
                    "is being spent on one. %s"
                    % ("'start %s' would begin the cheapest "
                       "thing you can pay for today (filler: cheapest, not a step toward the goal)." % _cheap
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
                   and sim.venture_real_earnings(node_id) > sim.venture_real_upkeep(node_id))
    if not _shut:
        return None
    # DO NOT RECOMMEND A COMMAND THAT WILL FAIL: picking the best-margin
    # shut concern by revenue minus upkeep alone and telling the player to
    # 'open' it is not enough, because a household deep in the
    # credit-exhaustion/named-trade trap (see PATH_SEARCH.md) can have too
    # little free staff capacity for open_venture to actually succeed.
    # The recommendation has to check that it would work, not just that
    # it would pay.
    _shut_for_staff = getattr(sim, "shut_for_staff", {})
    def _capex_now(_node_id):
        _fee = sim.venture_capex(_node_id)
        if (_node_id in _shut_for_staff
                and sim.year - _shut_for_staff[_node_id] <= sim.STAFF_CLOSURE_GRACE):
            _fee *= 0.1
        return _fee
    def _openable(_node_id):
        return (sim.staffing_open_refusal(_node_id, sim.opening_fee(_node_id)[1]) is None
                and _capex_now(_node_id) <= sim.spending_power("buy"))
    _really_openable = [node_id for node_id in _shut if _openable(node_id)]
    if _really_openable:
        _best = max(_really_openable,
                   key=lambda k: sim.venture_real_earnings(k) - sim.venture_real_upkeep(k))
        return {"what": "things you built and never opened", "kind": "closed",
                "why": "%d finished concern(s) are shut and "
                       "earning nothing. The best you could "
                       "actually open right now is %s, which "
                       "would earn %s a year against %s of "
                       "upkeep: 'open %s'"
                       % (len(_shut), _best,
                          money_text(sim.venture_real_earnings(_best), sim, grouped=True),
                          money_text(sim.venture_real_upkeep(_best), sim, grouped=True),
                          _best)}
    _best = max(_shut, key=lambda k: sim.venture_real_earnings(k) - sim.venture_real_upkeep(k))
    _staff_refusal = sim.staffing_open_refusal(_best, sim.opening_fee(_best)[1], with_advice=False)
    if _staff_refusal:
        _why = _staff_refusal.rstrip(".")
    else:
        _why = ("opening it costs %s, and between cash "
                "and what anyone will advance you can raise %s"
                % (money_text(_capex_now(_best), sim, grouped=True),
                   money_text(sim.spending_power("buy"), sim, grouped=True)))
    return {"what": "things you built and cannot open yet", "kind": "closed",
            "why": "%d finished concern(s) are shut and "
                   "earning nothing, and none of them can "
                   "be opened right now. The best is %s, "
                   "which would earn %s a year against "
                   "%s of upkeep, but %s. Hire, teach, or "
                   "close something to free the hands, "
                   "or raise the money, and try again"
                   % (len(_shut), _best,
                      money_text(sim.venture_real_earnings(_best), sim, grouped=True),
                      money_text(sim.venture_real_upkeep(_best), sim, grouped=True),
                      _why)}


def _stuck_nothing_or_money(sim, _startable, _afford):
    if not _startable:
        return {"what": "nothing you could begin", "kind": "unavailable",
                "why": "everything in front of you is either built, "
                       "already running, or waiting on something. "
                       "'available' says which."}
    if not _afford:
        return {"what": "money", "kind": "money",
                "why": "%d things are startable and the cheapest of "
                       "them costs %s, against the %s you could "
                       "raise"
                       % (len(_startable),
                          money_text(min(sim.project_cost(node_id)
                                               for node_id in _startable), sim, grouped=True),
                          money_text(sim.spending_power("start"), sim, grouped=True))}
    return None


def _stuck_raw_material(sim):
    if sim.binding and sim.resource_throttle() < 0.95:
        return {"what": "a raw material", "kind": "supply",
                "why": "%s: work is running at %d%% of plan. %s"
                       % (sim.binding, sim.resource_throttle() * 100,
                          sim.shortage_remedy(sim.binding))}
    return None


def _stuck_room_for_people(sim):
    _room = sim.labour.household_room()
    if _room < 1.0:
        return {"what": "room for people", "kind": "specialists",
                "why": "you can take %.2f more people. %s"
                       % (max(0.0, _room), sim.labour.room_advice())}
    return None


def _stuck_arrears(sim):
    if sim.capital < 0:
        return {"what": "arrears", "kind": "money",
                "why": "you owe %s of the %s anyone will advance "
                       "you, and the interest is %s a year"
                       % (money_text(-sim.capital, sim, grouped=True),
                          money_text(sim.credit_limit(), sim, grouped=True),
                          money_text(-sim.capital
                                           * sim.debt_interest_rate(), sim, grouped=True))}
    return None


def _stuck_credit_freeze(sim):
    if sim.year < sim.credit_frozen_until:
        return {"what": "a credit freeze", "kind": "money",
                "why": "nobody will fund new work until %d"
                       % int(sim.credit_frozen_until)}
    return None


def _stuck_startable_and_afford(sim, nodes, _fog):
    _startable = [node_id for node_id in nodes
                  if node_id not in sim.done and node_id not in sim.active
                  and (not _fog or sim.is_visible(node_id))
                  and sim.start_reason(node_id)[0]]
    _afford = [node_id for node_id in _startable
               if sim.start_refusal(node_id) is None]
    return _startable, _afford


@command("stuck", shape="bare", group="overview", aliases=("blocked", "help_me", "why_stuck"),
         summary="why you are not getting on",
         usage=["stuck", "stuck compact"], options={"compact": "short reply: a blockers list"},
         description="Gathers every kind of stall in one place: work blocked, no road "
                     "to the goal, nothing started, a shut venture, a binding raw "
                     "material, no room for people, arrears, a credit freeze.")
def _cmd_stuck(sim, nodes, cmd, ended):
    # WHY AM I STUCK: several independent kinds of stall - work blocked, no
    # road to the goal, nothing started, a shut venture, a binding raw
    # material, no room for people, arrears, a credit freeze - can each
    # keep a run motionless for decades, and stall_diagnosis alone only
    # speaks once insolvency has already set in. This command gathers
    # every check into one place instead of making a player find each
    # cause by guessing at `why`.
    _fog = sim.fog
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
    _saving = saving_reason(sim)
    _checks = (
        _stuck_work_in_hand(sim, nodes),
        _goal_reason,
        _stuck_started_nothing(sim, _startable, _afford, saving=bool(_saving)),
        _saving,
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
               if _startable and not _saving else None)}
    _calendar = calendar_bound_advice(sim, nodes)
    if _calendar:
        out["goal_path_is_calendar_bound"] = _calendar
    else:
        out["lever_figures"] = lever_line(sim)
    _filler = filler_note(sim, out["and_the_cheapest_thing_you_could_start_now"], nodes)
    if _filler:
        out["the_cheapest_start_is_filler"] = _filler
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
