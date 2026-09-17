"""The command table: every accepted command name (and alias) mapped to the small handler that answers it, and the dispatcher that resolves names, guards fog, validates the command, and looks the handler up."""

import collections, hashlib, json, math, os, random, re
from collections import defaultdict

from ..data import *          # the shared tables and loaders
from ..data import (ANNUAL_WAGE, TRADES_ABSENT, TRADE_NOTES, WAGES, closure,
                   critical_path, downstream_count, is_downstream, load, money_word,
                   topo_order, trade_family)
from ..fog import strip_self_play_advice

from ..core import Sim

from .economy import (_agent_capacity, _agent_changes, _agent_economy, _agent_mines, _agent_portfolio, _agent_values, _dashboard_snapshot)
from .help import _agent_help
from .nodes import NODE_NAME_NORM, _did_you_mean, _norm_name, _resolve_by_name
from .saveload import load_state, save_state
from .score import score_report
from .state import (_agent_end_reason, _agent_log, _agent_state, _staff_fraction_note, _waiting_on)
from .techtree import _agent_available, _brief, _node_explain
from .util import (_clean, _flag, _localise_money, _localise_words, _num, _qty, _unsafe_path)
from .ventures import _VENTURE_SUPERVISION_NOTE




# Every command the dispatcher answers to, in the order a player meets them.
# Kept beside the dispatcher so that adding a command and forgetting to
# advertise it is a visible omission rather than a silent one.
KNOWN_COMMANDS = (
    "state", "available", "why", "path", "start", "stop", "rush", "step",
    "money", "risk", "values", "labour", "population", "policy", "help", "log",
    "hire", "fire", "train", "commission", "work", "allocate",
    "buy", "quote", "close", "bounty", "mothball", "restore", "bribe",
    "open", "ventures", "withdraw", "mines", "stuck",
    "capacity", "materials", "sell", "economy", "changes", "score", "portfolio",
    "save", "load", "quit",
)


# Every command that names a technology. Under fog, NONE of them may say
# anything about one you have not heard of - including refusing it for a reason
# that describes it.
_ID_COMMANDS = ("why", "path", "start", "stop", "bounty", "mothball", "restore")

# Every command whose `id` a typed NAME should resolve onto, before anything
# else touches it. `open` is not in _ID_COMMANDS above - it is safe without
# the fog guard, because you can only open something you have already done -
# but a player still types its name, not its id, so it needs the same
# resolution the fog-guarded commands get.
_NAME_COMMANDS = _ID_COMMANDS + ("open",)


def _cmd_state(s, nodes, cmd, ended):
    return dict(ok=True, **_agent_state(s, nodes, cmd))



def _cmd_available(s, nodes, cmd, ended):
    return _agent_available(s, nodes, cmd)



def _cmd_log(s, nodes, cmd, ended):
    return _agent_log(s, cmd)



def _cmd_score(s, nodes, cmd, ended):
    return {"ok": True, **score_report(s, nodes)}



def _cmd_why(s, nodes, cmd, ended):
    k = cmd.get("id")
    # The goal is the one thing you were told the name of on arrival; see
    # the _goal_why note on the fog guard above for why it is `why` alone.
    if (isinstance(k, str) and k in nodes and not s.is_visible(k)
            and k != getattr(s, "goal", None)):
        return {"ok": False,
                "error": "you have never heard of that. You know what you have "
                         "built and what you could begin now; use 'available'."}
    if not isinstance(k, str):
        return {"ok": False,
                "error": 'which one? give an id, for example '
                         '{"cmd":"why","id":"units_standards"}. '
                         'Use {"cmd":"available"} to see what you could begin.'
                if k is None else
                "id must be a name in quotes, not %s" % type(k).__name__}
    if k not in nodes:
        # Only blame the fog when there IS any. With it off a break tester
        # mistyped an id and was told the fog was limiting the suggestions,
        # in a game they had explicitly started with the whole tree visible.
        return {"ok": False, "error": "unknown node %r. did you mean: %s"
                % (k, ", ".join(_did_you_mean(k, nodes, s=s))
                   or ("no idea, and under fog of war I can only suggest "
                       "things you have heard of"
                       if getattr(s, "fog", False)
                       else "no idea - nothing in the tree is spelled much "
                            "like that"))}
    return dict(ok=True, **_node_explain(s, nodes, k))



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
    k = cmd.get("id")
    if k not in nodes:
        return {"ok": False, "error": "unknown node id %r" % k}
    need = closure(nodes, k)
    order = topo_order(nodes, need)
    remaining = [x for x in order if x not in s.done]
    out = {"ok": True, "id": k, "name": nodes[k]["name"], "done": k in s.done,
           "remaining_count": len(remaining), "remaining": remaining}
    # THE JOIN NOBODY HAD: "what the goal still needs" and "what I could
    # start today" were two separate reports - this one, and `available`
    # - and by midgame nearly everything on `available`'s several-hundred
    # row list is irrelevant to any one goal. A Han player wrote their own
    # regex script outside the game to intersect the two; an England
    # player asked for exactly this. Do the intersection here, once,
    # cheapest first, so it never has to be done by eye or by script
    # again.
    _startable = sorted((x for x in remaining if s.can_start(x)),
                        key=lambda x: s.project_cost(x))
    out["startable_today_count"] = len(_startable)
    out["startable_today_toward_this"] = (
        [_brief(s, nodes, x, False) for x in _startable[:30]] or "nothing yet")
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
    if _startable and all(nodes[x]["rev"] <= 0 for x in _startable):
        _combined = sum(s.project_cost(x) for x in _startable)
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
    _shut = sorted(x for x in need
                   if x in getattr(s, "mothballed", set()) and x in s.done)
    if _shut:
        out["on_this_route_but_shut_down"] = _shut[:10]
        out["reopen_them_with"] = ("'restore <id>' - you still know how, so "
                                   "putting the plant back costs a fraction "
                                   "of building it. Nothing downstream is "
                                   "waiting on them; their income is")
    return out



def _cmd_start(s, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s); nothing more can be started. 'state' shows where you finished and how far you got" % ended}
    k = cmd.get("id")
    if k not in nodes:
        return {"ok": False, "error": "unknown node id %r. use {\"cmd\":\"available\"} "
                                      "or {\"cmd\":\"why\",\"id\":...} to find valid ids" % k}
    # SAY UP FRONT WHEN THE SOCIETY CANNOT STAFF IT. A play tester started
    # arithmetic_positional, which wants 2,500 scribe-hours a year against
    # a national ceiling of 1,321, and watched it sit at "81% spent" from
    # 1309 to about 1440 - a hundred and thirty years. Their point is the
    # right one: the engine knows this at `start` time. It is still allowed
    # (you may teach or hire your way to the hours, and the work does
    # crawl) but it must not be a silent trap.
    # THE NUMBER PRINTED HAS TO BE THE NUMBER TESTED. The commit that added
    # commissioned hours to the test above ("Make the stated labour ceiling
    # the real one") changed the comparison to hours_you_can_call_on - which
    # is market_supply PLUS whatever you have already commissioned - and left
    # this line printing market_supply alone. A player who had commissioned
    # any of the trade saw `start` quote one ceiling and `stuck` quote a
    # higher one for the identical project a moment later, which is the exact
    # thing that commit's own message promised could not happen again.
    _impossible = []
    _impossible_trades = set()
    _n0 = nodes[k]
    _frac0 = min(1.0, 1.0 / max(1.0, _n0["yrs"]))
    for _t, _want in (_n0["lab"] or {}).items():
        _need = _want * _frac0
        if _need > 0 and s.hours_you_can_call_on(_t) < _need:
            _impossible.append("%s (wants %.0f hours a year; this society can "
                               "field %.0f at most)"
                               % (_t, _need, max(0.0, s.hours_you_can_call_on(_t))))
            _impossible_trades.add(_t)
    # OVERSUBSCRIBED IS NOT THE SAME AS IMPOSSIBLE. The society may be
    # able to field the trade this wants and STILL not have enough of
    # it left once your own OTHER active work is already drawing on it
    # - "the first workshop/lab sat at 60% until I stopped adding new
    # work for a year", from a player who could not see this coming
    # until it had already happened. trade_demand_vs_supply (projects.py)
    # is the CURRENT portfolio's own demand, before this project is
    # added; trade_draw_plan(k, None) is this project's own full want,
    # since it has not started and so owes the whole thing. Same two
    # calls `portfolio` makes to build the aggregate table - reused
    # here, not re-derived, so `start`'s warning and `portfolio`'s own
    # figures can never tell two different stories about the same year.
    _demand_now = s.trade_demand_vs_supply()
    _oversub = []
    for _t, _p in s.trade_draw_plan(k, None).items():
        if _t in _impossible_trades:
            continue          # already said, and said more plainly
        _supply = s.hours_you_can_call_on(_t)
        if _supply <= 0:
            continue
        _existing = _demand_now.get(_t, {}).get("demand_hours_this_year", 0.0)
        _competitors = len(_demand_now.get(_t, {}).get("projects_drawing_on_it", ()))
        _new_total = _existing + _p["desired"]
        if _new_total > _supply + 1e-6:
            _oversub.append(
                "%s: this portfolio would want %s hours a year against "
                "%s this society can supply (%d other active project%s "
                "already drawing on it); this one competes for what is "
                "left, it does not get %s to itself"
                % (_t, "{:,.0f}".format(_new_total), "{:,.0f}".format(_supply),
                   _competitors, "" if _competitors == 1 else "s",
                   "{:,.0f}".format(_p["desired"])))
    ok, why = s.start_project(k)
    if not ok:
        return {"ok": False, "error": why}
    n = nodes[k]
    # SAY SO, FOR THE PLAYER'S OWN RECORD. start_project itself only logs
    # the RESTART case (see its own self.log.append for "begun again");
    # a fresh start was silent, so a player reading `log` back saw
    # completions and failures appear out of nowhere with no record of
    # having chosen to begin them.
    if s.active.get(k, {}).get("spent", 0.0) <= 0.5:
        s.log.append((s.year, "started: %s" % n["name"]))
    # THE PRICE YOU ACTUALLY COMMITTED TO. A normal-play tester read a cost
    # of 106,567 off `why`, started the thing forty years later, and was
    # billed 207,811 - because project_cost moves with prices, the coinage,
    # material scarcity and what you have since built, and nothing told
    # them the earlier figure was a snapshot. The bill IS fixed at the
    # moment you start; what was missing was any statement of what it was
    # fixed AT.
    bill = round(s.active.get(k, {}).get("cost_left", s.project_cost(k)), 1)
    _warn_staff = ("started, but this society cannot supply the labour it "
                   "wants and it will crawl until you can: %s"
                   % "; ".join(_impossible)) if _impossible else None
    out = {"ok": True, "started": k, "name": n["name"], "founder_hours_needed": n["ph"],
           "calendar_floor_years": round(s.calendar_floor(k), 2),
           "nominal_calendar_floor_before_reputation": n["yrs"],
           # SAID AT THE MOMENT OF COMMITMENT, not only on `why` beforehand
           # or `available` in passing - this is the screen the player is
           # actually looking at when the risk becomes theirs. See
           # expected_calendar_years (projects.py): the true expected
           # total, retries included, computed through the same retry
           # rule _complete applies on every failure, not a plain
           # geometric series on the bare risk field.
           "expected_calendar_years_with_retries": round(
               s.expected_calendar_years(k), 2),
           "the_bill_you_have_taken_on": bill,
           "note": "This is the price as of today, and it is now fixed for "
                   "this project. Quotes move with prices, the coinage and "
                   "what a material costs to get: a figure you read years "
                   "ago is not what you will pay."}
    # SAID AT THE MOMENT OF COMMITMENT, NOT DISCOVERED 60% IN. A player
    # who had already won the game found the first workshop/lab stalled
    # at 60% "until I stopped adding new work for a year", with nothing
    # at `start` time to have told them the trade they needed was
    # already spoken for by their own other projects.
    if _oversub:
        out["this_oversubscribes_a_trade"] = (
            "started - but %s. 'portfolio' shows the full demand-vs-"
            "supply table before your next start"
            % "; ".join(_oversub))
    # TAUGHT ONCE, AT THE MOMENT IT FIRST MATTERS. A blind playthrough
    # spent its whole early game treating one long calendar-floor project
    # as "the active research" and only discovered parallel play - running
    # several things at once while a multi-year project sits in the
    # background - after an outside hint, which their own write-up calls
    # probably the difference between finishing comfortably and risking
    # the horizon. This is the central mechanic of the game and the
    # welcome text never says it. Fired once, on the first project whose
    # calendar floor is long enough that it cannot be the only thing in
    # hand for a while - not every multi-year start, which would be noise
    # by the fifth one.
    if n["yrs"] >= 2 and not getattr(s, "_said_parallelism", False):
        s._said_parallelism = True
        out["a_calendar_floor_is_not_exclusive_research_time"] = (
            "%s will take at least %d year%s, whatever else you do. That "
            "time is not spent watching it: your founder-hours and staff "
            "are free the moment this year's share of the work is paid "
            "for, and nothing stops you spending them on something else "
            "in the meantime. The strongest play is usually to keep "
            "several things running at once - start preparing the next "
            "layer now rather than waiting for this one to finish."
            % (n["name"], n["yrs"], "" if n["yrs"] == 1 else "s"))
    if _warn_staff:
        out["but"] = _warn_staff
    # BUILD STAFF AND OPERATING STAFF ARE DIFFERENT NUMBERS, and a player
    # can clear the first (checked above, and by start_project itself),
    # pay the whole bill, and only discover the second - venture_hands(),
    # what 'open' actually enforces - refuses them once the work is
    # already finished. `why` has shown this for a while (same
    # computation, see staff_to_keep_it_open there); three playtesters
    # missed it anyway in a long page and found out at 'open' instead.
    # Said here too, at the one other moment it can still change
    # anything, with today's free staff - not a promise, since attrition
    # and hiring between now and completion can move either number.
    if s.is_venture(k):
        _sup_sch, _sup_art = s.venture_hands(k)
        _free_sch, _free_art = s.venture_staff_free()
        if _sup_sch > _free_sch + 1e-9 or _sup_art > _free_art + 1e-9:
            out["today_you_could_not_open_this_when_it_is_done"] = (
                "keeping it open will want the equivalent of %.2f "
                "scholars and %.2f artisans of your own watching it "
                "full time, every year it runs - a continuous share of "
                "their time, not a headcount; you have %.2f and %.2f "
                "free right now, with nothing else committed. That "
                "is a different, usually smaller number than the crew "
                "that builds it, and it is checked only when you 'open' "
                "it - not now. Staffing can change before this "
                "finishes, for better or worse; if it has not by then, "
                "hire, teach, or close something first."
                % (_sup_sch, _sup_art, _free_sch, _free_art))
    # AND SAY WHEN THIS WOULD BORROW TO FINISH. `start` financed the gap
    # between what a project costs and what the household has, silently,
    # at up to twelve per cent - three players in a row were carried into
    # debt they had not decided to take on. One went 750 denarii short of
    # affordable on turn one and spent the next twenty-five years digging
    # out while the project sat stalled and the interest compounded.
    #
    # Not a refusal. Borrowing to build is a real and often correct move,
    # and the game already lets you. It is the not-being-told that was
    # wrong, so this names the gap, the rate, and how much room is left
    # before the creditors stop being patient - and what they do then,
    # because both players who found that out found it out by losing a
    # school and a collegium they had built years earlier.
    #
    # A FORECAST, NOT A RECEIPT - the keys have to say so. `start` itself
    # borrows nothing: credit only actually draws down at step resolution,
    # if and when cash genuinely goes negative paying this year's share.
    # The first version of this block said "borrowed_now", in the past
    # tense, on the very command that had not borrowed a denarius yet - a
    # Norse player read "borrowed now: 123.8" here and "(none used)" on
    # `money` in the next breath and rightly called it a ledger
    # contradiction. Same numbers, same warning; they describe what WILL
    # happen if the project runs to completion on today's cash, not what
    # has.
    _gap = bill - max(0.0, s.capital)
    if _gap > 0:
        _lim = s.credit_limit()
        _after = -(min(0.0, s.capital) - _gap)
        out["on_credit"] = {
            "nothing_is_borrowed_yet": (
                "this is a forecast, not a receipt: credit only actually "
                "draws down at step resolution, if cash runs short paying "
                "this year's share. These figures are what happens if it "
                "does, on today's numbers."),
            "you_would_borrow": round(_gap, 1),
            "interest_rate_percent": round(s.debt_interest_rate() * 100, 1),
            "estimated_annual_interest": round(
                _gap * s.debt_interest_rate(), 1),
            "you_would_then_owe": round(_after, 1),
            "no_one_advances_past": round(_lim, 1),
            "what_happens_there":
                "past that limit every project in hand halts unfinished, "
                "nobody funds new work for some years, and your creditors "
                "take and sell what you are running - including things you "
                "built long ago and had no debt against.",
        }
    # THE AGGREGATE ANSWER, NOT A SECOND ONE. `on_credit` just above
    # already answers "can THIS project be financed" - correctly - by
    # comparing THIS project's own bill to cash on hand. What it cannot
    # see is that other active work is drawing on the exact same cash at
    # the exact same time: a Rome opening that started scientific_method
    # (230) and then units_standards (444) read "you would borrow: 44"
    # on the second start, because 444 against 400 capital IS only a
    # 44-denarius gap taken alone - and then watched capital fall past
    # -150 within the year, because scientific_method's own 230 still
    # unpaid was drawing on the identical purse at the identical time.
    # The forecast was not wrong about its own project; it was silent
    # about everyone else already in hand. Every playtest of this
    # opening hit some version of the same thing: two or three
    # foundations, each priced honestly on its own screen, together
    # asking for more than the household currently holds. This is that
    # aggregate: committed_spend() (economy.py) is the exact same sum
    # `money`'s "still_owed_on_work_in_hand" already prints, read here
    # instead of re-totalled, and funding_capacity() is the identical
    # number the un-manual director's own start heuristic already uses
    # to avoid over-committing itself (step(), core.py) - given here as
    # the real ceiling, not a second formula that could drift from it.
    _committed = s.committed_spend()
    _cash = max(0.0, s.capital)
    if _committed > _cash and len(s.active) > 1:
        _capacity = s.funding_capacity()
        out["total_committed_across_active_work"] = {
            "you_have_promised": round(_committed, 1),
            "across_projects_in_hand": len(s.active),
            "you_currently_hold": round(_cash, 1),
            "likely_to_draw_on_credit_between_them": round(
                _committed - _cash, 1),
            "your_real_ceiling_if_it_comes_to_that": round(_capacity, 1),
            "what_this_means": (
                "not what this ONE project costs - the total still owed "
                "across all %d projects in hand at once, including this "
                "one, against what you actually hold right now. Above, "
                "'on_credit' priced only this project against your cash; "
                "your other work in hand draws on the same cash at the "
                "same time, so the real combined draw is bigger than "
                "that figure alone suggests. 'your_real_ceiling' is "
                "what funding_capacity() judges you could service in "
                "total before it stops being safe - cash, half your "
                "credit line, and about five years of what your "
                "standing income can spare - not a hard limit today. "
                "Individually affordable commitments can still be "
                "collectively ruinous; 'money' shows the same "
                "committed total, and 'portfolio' shows which projects "
                "it is spread across. This is a warning, not a "
                "refusal - taking on debt on purpose is a real choice "
                "the game lets you make."
                % len(s.active)),
        }
    # WARN, DO NOT SILENTLY ACCEPT. start_reason() already refuses a trade
    # that does not exist AT ALL (see "THE TRADE HAS TO EXIST" there), but
    # trade_available() goes true the moment you call `train`, two years
    # before anyone graduates - market_supply() is the stricter, honest
    # figure step() actually checks. A tester's `start` came back ok:true
    # for a project needing an engineer while nobody could yet DO engineer
    # work, and years later it was HALTED with everything spent on it
    # lost, with no warning at the point they could still have done
    # something about it. Name it here instead.
    short = sorted(t for t in n["lab"] if s.market_supply(t) <= 0.0)
    if short:
        out["warning"] = (
            "no one can do this work YET: %s. The trade exists here or is "
            "being taught, but nobody is trained and ready, and this "
            "project cannot progress at all until someone is. If that is "
            "still true after four years with no progress, it is halted "
            "and everything spent on it is lost. Check {\"cmd\":\"labour\"}, "
            "and see {\"cmd\":\"train\"} if nobody is being taught yet."
            % ", ".join(short))
    return out



def _cmd_stop(s, nodes, cmd, ended):
    k = cmd.get("id")
    ok, why = s.stop_project(k)
    if not ok:
        return {"ok": False, "error": why}
    # stop_project ITSELF never touches self.log - see its own docstring,
    # which is entirely about what the hours and money do, not about
    # recording the decision. A deliberate abandonment is exactly the
    # kind of thing a player asked `log` to be able to find again.
    s.log.append((s.year, "stopped: %s (%s)" % (nodes[k]["name"], why)))
    return {"ok": True, "stopped": k, "what_happened": why}



def _cmd_rush(s, nodes, cmd, ended):
    # BULK START, FOG-SAFE. A break tester in the late game had thirty
    # or forty things startable at once and nothing to do but type
    # `start <id>` thirty or forty times - "the late game is pure
    # typing" - and every one of those ids was already something
    # `can_start` had already cleared, the same check `available` uses
    # to decide what to list at all, so acting on all of them at once
    # hands back nothing a player could not already see for themselves.
    if ended:
        return {"ok": False,
                "error": "the run has ended (%s); nothing more can be "
                         "started. 'state' shows where you finished and "
                         "how far you got" % ended}
    try:
        limit = (int(cmd.get("limit")) if cmd.get("limit") is not None
                 else None)
    except (TypeError, ValueError):
        return {"ok": False, "error": "limit must be a whole number"}
    if limit is not None and limit < 1:
        return {"ok": False, "error": "limit must be at least 1"}
    _memo = {}
    _ok = [k for k in s.order if s.can_start(k, _memo=_memo)]
    # HIGHEST-LEVERAGE FIRST, INTERNALLY ONLY. This never shows a player
    # a downstream_count - that is a fog spoiler, see _node_explain's own
    # comment on it - it only uses the number to decide which of several
    # things your money cannot all cover gets it first, the same number
    # `available`'s own "most_rests_on_these" digest already uses to
    # decide what to show you. Ranking by it here leaks nothing, because
    # the ranking itself is never printed, only which ids got started.
    _ok.sort(key=lambda k: (-downstream_count(nodes, k), s.project_cost(k)))
    # Discovery must not mutate dozens of portfolio entries. A numeric limit
    # is an explicit bounded instruction; an unbounded run needs confirmation.
    if limit is None and not cmd.get("force"):
        return {"ok": True, "preview": True,
                "count_would_start": len(_ok),
                "would_start": [{"id": k, "name": nodes[k]["name"],
                                  "cost": round(s.project_cost(k), 1)}
                                 for k in _ok],
                "nothing_changed": True,
                "how_to_confirm": ("Use 'rush force' to begin this unbounded "
                                   "set, or 'rush limit:N' to begin at most N.")}
    # AND STOP WHEN THE YEAR IS FULL. `rush limit:1000` on turn one started
    # 209 things at once - a plantation, a whaling industry, a theatre, a
    # gambling house, nitre beds and lens grinding, all in the same year -
    # owing 90,944 founder-hours against a lifetime the game itself puts at
    # about 72,000. The next step gave hours to exactly ONE of them and the
    # other 208 sat inert for ever, so "RUNNING (209)" was a fiction about
    # 208 of them. A weird-play tester called it out as the worst thing they
    # found, and they were right: the command was doing what it was asked
    # and what it was asked was incoherent.
    #
    # Committing a couple of years of everyone's attention is a decision a
    # player might reasonably make. Committing four centuries of it is not.
    _hours_room = max(0.0, s.director_pool() - s.director_hours_committed())
    _HORIZON_YEARS = 2.0
    _budget = s.director_pool() * _HORIZON_YEARS
    started, not_started = [], []
    _owed = 0.0
    for k in _ok:
        if limit is not None and len(started) >= limit:
            break
        if started and _owed + nodes[k]["ph"] > _budget:
            not_started.append({
                "id": k, "name": nodes[k]["name"],
                "why": "not begun: the %d things already started this turn "
                       "owe %s of your hours, and you have about %s a year. "
                       "Beginning more would not make them go faster, only "
                       "leave them all standing still"
                       % (len(started), "{:,.0f}".format(_owed),
                          "{:,.0f}".format(s.director_pool()))})
            continue
        ok2, why = s.start_project(k)
        if ok2:
            _owed += nodes[k]["ph"]
            n = nodes[k]
            # SAY SO, for the same reason the single-id `start` does: a
            # player reading `log` back should see every begun-work as a
            # choice they made, not a completion that appeared unasked.
            if s.active.get(k, {}).get("spent", 0.0) <= 0.5:
                s.log.append((s.year, "started: %s" % n["name"]))
            started.append({"id": k, "name": n["name"],
                            "cost": round(s.active.get(k, {}).get(
                                "cost_left", s.project_cost(k)), 1)})
        else:
            not_started.append({"id": k, "why": why})
    return {"ok": True, "started": started, "count_started": len(started),
            "not_started": not_started,
            "count_not_started": len(not_started),
            # THE SAME WARNING `policy` CARRIES, for the same reason. This
            # is an automatic behaviour and it reads as the game offering to
            # play your turn well for you. It is not: it begins things in
            # order of how much rests on them, which is a rule of thumb and
            # not a plan. A round-12 tester used it on turn one and watched
            # scandal jump to within a year of the line that ends the run,
            # with the treasury in debt.
            "this_is_an_approximation_not_optimal_play": (
                "`rush` is a rough rule of thumb, not a plan: it begins "
                "things in order of how much rests on them, with no idea "
                "what you are building toward. Beginning a great deal at "
                "once also makes you conspicuous and spends your credit, so "
                "on an early turn it can do real damage. A careful player "
                "beats it; it exists to save typing in a late game where "
                "you would have begun all of these anyway."),
            "note": "tried everything you could begin today, "
                    "highest-leverage first, until your credit ran out "
                    "or the list did. 'why <id>' on anything in "
                    "not_started says exactly why it stopped there."}



def _cmd_bounty(s, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s); nothing more can be bought. 'state' shows where you finished and how far you got" % ended}
    k = cmd.get("id")
    if k not in nodes:
        return {"ok": False, "error": "unknown node id %r" % k}
    if k in s.done:
        return {"ok": False, "error": "%s is already done" % k}
    # ELIGIBILITY FIRST, ALWAYS - a tester was told to stop an active
    # mat_platinum_bulk in order to switch it to a bounty, did so, and
    # then had `bounty mat_platinum_bulk` refused as not bounty-eligible:
    # advice the game itself could have checked before giving. Since an
    # active project's prerequisites are already satisfied (that is what
    # let it start), eligibility here depends only on craft recognition, so
    # checking it before the "already active" branch costs nothing and
    # never sends a player to stop something that could not become a
    # bounty anyway.
    if not s.bounty_eligible(k):
        n = nodes[k]
        missing = [p for p in n["pre"] if p not in s.done]
        if missing:
            # SAME FOG FILTER `why` USES, not a second one. This used to
            # print every missing prerequisite by raw id regardless of
            # whether the player had ever heard of it - industrial zinc
            # leaked power_grid this way, the getter leaked its induction-
            # heating coupling, and the vacuum tube leaked its hidden
            # cathode prerequisite.
            return {"ok": False, "error": s.missing_prereq_message(missing)}
        return {"ok": False,
                "error": "not bounty-eligible (category %s): a craftsman "
                         "in %s could not recognise success at this without "
                         "understanding the theory, so there is nothing to "
                         "award the prize for. A bounty works where the craft "
                         "already exists here and success is visible."
                         % (n["cat"],
                            s.civ.get("name", "this society"))}
    if k in s.active:
        return {"ok": False, "error": "%s is already active; stop it first if you want "
                                      "to switch to a bounty instead" % k}
    price = (nodes[k]["_total_cost"] * 2.5 * s.civ_cost_factor(k)
             * s.material_cost_factor(k) * s.cost_money_factor())
    if not s.post_bounty(k):
        return {"ok": False, "error": "cannot afford the bounty: needs about %.0f denarii, "
                                      "you have %.0f. Earn or wait, then try again" % (price, s.capital)}
    return {"ok": True, "posted": k, "price": round(price, 1), "capital": round(s.capital, 1)}



def _cmd_buy(s, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s); nothing more can be bought. 'state' shows where you finished and how far you got" % ended}
    what = cmd.get("what")
    # THE SAME READER AS EVERY OTHER QUANTITY. This had its own float()
    # and so missed the guards _qty carries: a break tester bought
    # 1e30 hectares of coppice and read the refusal in binary rounding
    # error.
    n, _err_n = _qty(cmd, "n", 0)
    if _err_n:
        return {"ok": False, "error": _err_n + ". Nothing was changed."}
    # A playtester passed n:-5 and got money from nothing. buy_forest(-5)
    # computed a NEGATIVE cost, passed the affordability test because
    # -1250 > 400 is false, then credited the capital and set forest_ha to
    # -5, while the reply said ok:false. The refusal was reported AFTER the
    # mutation had already happened. Validate before touching anything.
    if not (n > 0):
        return {"ok": False,
                "error": "n must be greater than zero, got %g. Nothing was changed." % n}
    if what == "forest":
        got = s.buy_forest(n)
        if got <= 0:
            return {"ok": False, "error": "cannot afford %.0f ha of coppice woodland "
                                          "(you have %.0f denarii)" % (n, s.capital)}
        return {"ok": True, "bought_ha": got, "forest_ha": round(s.forest_ha, 1),
                "capital": round(s.capital, 1)}
    if what in ("nitre", "nitre_bed", "saltpetre", "nitre beds"):
        got = s.build_nitre(n)
        if got <= 0:
            return {"ok": False,
                    "error": "cannot afford %.0f square metres of nitre bed "
                             "(that is %s denarii and you have %s). Nothing "
                             "was changed."
                             % (n, "{:,.0f}".format(n * s.NITRE_COST_PER_M2
                                                    * s.price_index),
                                "{:,.0f}".format(s.capital))}
        return {"ok": True, "laid_m2": got,
                "nitre_bed_m2": round(s.nitre_bed_m2, 1),
                "saltpetre_it_yields_per_year_tonnes":
                    round(s.nitre_bed_m2 * s.NITRE_YIELD_T_PER_M2, 3),
                "capital": round(s.capital, 1)}
    if what in ("farm", "food"):
        got = s.invest_farm(n)
        if got <= 0:
            return {"ok": False, "error": "cannot afford that farmland"}
        return {"ok": True, "bought_farm_hectares": got,
                "farm_hectares": round(s.farm_hectares, 1),
                "food_cost_factor": round(s.essential_price_ratio(), 3),
                "capital": round(s.capital, 1)}
    if what in ("housing", "houses"):
        got = s.build_worker_housing(n)
        if got <= 0:
            return {"ok": False, "error": "cannot afford that worker housing"}
        return {"ok": True, "built_worker_housing_places": got,
                "worker_housing_places": round(s.worker_housing_places, 1),
                "capital": round(s.capital, 1)}
    if what in ("school", "trade_school", "trade school"):
        trade = str(cmd.get("trade") or cmd.get("material") or "").lower()
        ok, why = s.found_trade_school(trade, n)
        if not ok:
            return {"ok": False, "error": why}
        return {"ok": True, "trade": trade, "new_training_seats": n,
                "trade_school_seats": s.trade_schools[trade],
                "market_supply_hours_per_year": round(s.market_supply(trade), 1),
                "capital": round(s.capital, 1)}
    if what in ("material", "stock"):
        material = cmd.get("material")
        got = s.buy_material_stock(material, n)
        if got <= 0:
            return {"ok": False, "error": "cannot buy that quantity at the current material quote"}
        return {"ok": True, "material": material, "bought_tonnes": got,
                "stock_on_hand_tonnes": s.material_stock_t(material),
                "capital": round(s.capital, 1)}
    if what == "mine":
        mat = cmd.get("material")
        # GENERALISED beyond the seven hand-named metals (see
        # economy.py's mineable()/mine_catalog_hint(), and
        # COMMODITY_DYNAMISM.md for why the closed list was the actual
        # bug: "no mine, no supply lever" for anything else the tree
        # ever asks a node to buy). This is the one gate that used to
        # make that literally true at the command surface, even though
        # the seven-name dict membership check lived here, not in
        # economy.py, which is why the fix has to touch this file.
        if not s.mineable(mat):
            return {"ok": False, "error": "material must be one of: "
                                          + s.mine_catalog_hint()}
        # partial=False: a mine you asked for by name is bought in full or
        # not at all. It used to spend every denarius you had and hand back
        # a fraction, without asking.
        price = s.mine_quote(mat, n).get("to_sink_it") if hasattr(s, "mine_quote") else None
        got = s.open_mine(mat, n, partial=False)
        if got <= 0:
            if price is not None and price > s.capital:
                return {"ok": False,
                        "error": "%.0f tonnes a year of %s costs %s denarii to "
                                 "sink and you have %s. Nothing was changed - ask "
                                 "for what you can pay for, or check the price "
                                 'first with {"cmd":"quote","what":"mine",'
                                 '"material":"%s","n":%g}.'
                                 % (float(n), mat, "{:,.0f}".format(price),
                                    "{:,.0f}".format(s.capital), mat, float(n))}
            return {"ok": False, "error": "could not commission any %s capacity right now "
                                          "(ceiling reached, or standing too low for a "
                                          "concession that size)" % mat}
        # Say what was actually commissioned and WHEN it arrives. A tester
        # asked for 999,999,999 tonnes a year, silently got 59, and found
        # ready_year was always null so there was no way to know whether the
        # workings would appear in four years or ninety-five. Both of those
        # are the model being coy about its own arithmetic.
        tranche = [t for t in getattr(s, "mine_tranches", []) if t[0] == mat]
        ready = min((t[2] for t in tranche), default=None)
        asked = float(n)
        reply = {"ok": True, "material": mat,
                 "you_asked_for_t_per_yr": asked,
                 "commissioned_t_per_yr": round(got, 2),
                 "ready_year": ready,
                 "years_until_producing": (None if ready is None
                                           else round(ready - s.year, 1)),
                 "already_producing_t_per_yr": round(s.mine_capacity.get(mat, 0.0), 2),
                 "capital": round(s.capital, 1)}
        if got < asked * 0.999:
            reply["note"] = ("less than you asked for: limited by capital, by the "
                             "ceiling your standing supports, or both. Nothing was "
                             "wasted, you paid only for what was sunk.")
        return reply
    if what == "slaves":
        s._last_buy_refusal = None
        got = s.buy_slaves(int(n))
        if got <= 0 and getattr(s, "_last_buy_refusal", None):
            return {"ok": False, "error": s._last_buy_refusal}
        if got <= 0:
            # Quote the price actually asked. It is no longer 300 flat: a
            # large purchase bids the local market up, and saying "300 each"
            # while charging far more is the model lying to the player.
            q = s.slave_quote(int(n))
            return {"ok": False,
                    "error": "cannot afford %d slaves: %.0f denarii "
                             "(%.0f each after the market moves against a purchase "
                             "this size) and you have %.0f"
                             % (int(n), q, q / max(1, int(n)), s.capital)}
        return {"ok": True, "bought": got, "slaves": s.slaves, "capital": round(s.capital, 1)}
    if what == "manumit":
        got = s.manumit(int(n))
        if got <= 0:
            return {"ok": False, "error": "you have no slaves to free"}
        return {"ok": True, "manumitted": got, "freedmen": s.freedmen, "slaves": s.slaves}
    return {"ok": False, "error": "what must be one of: forest, farm, housing, school, material, mine, slaves, manumit"}


def _cmd_materials(s, nodes, cmd, ended):
    return {"ok": True, "materials": s.materials_report(),
            "units": "stocks are tonnes; production and demand are tonnes/year",
            "how_to_trade": "buy material <name> <tonnes>; sell <name> <tonnes>"}


def _cmd_sell(s, nodes, cmd, ended):
    material = str(cmd.get("material") or cmd.get("what") or "").lower()
    n, err = _qty(cmd, "n", 0)
    if err or n <= 0:
        return {"ok": False, "error": err or "n must be greater than zero"}
    sold = s.sell_material_stock(material, n)
    if sold <= 0:
        return {"ok": False, "error": "you have none of that material stock to sell"}
    return {"ok": True, "material": material, "sold_tonnes": sold,
            "stock_on_hand_tonnes": s.material_stock_t(material),
            "capital": round(s.capital, 1)}



def _cmd_work(s, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    # WHAT THE PRACTICE WAS EARNING BEFORE YOU TOOK THE JOB. Selling your
    # hours takes them out of your own surgery, which is where most of your
    # income comes from at the start - so a play tester earned 80.1 for 500
    # hours as a scribe and lost 58.3 of practice income the same instant,
    # netting 22 for a quarter of their year. Nothing anywhere said founder
    # hours drove revenue, and they only found it by diffing the ledger.
    _rev_before = s.revenue()
    pay, err = s.work_for_wages(cmd.get("trade"), cmd.get("hours", 0))
    # A message WITH pay is a warning about a bad trade, not a refusal:
    # the work happened and the player should be told what it cost them.
    if err and pay <= 0:
        return {"ok": False, "error": err}
    _rev_after = s.revenue()
    _cost = _rev_before - _rev_after
    out = {"ok": True, "trade": cmd.get("trade"), "hours": cmd.get("hours"),
           "earned": round(pay, 1), "capital": round(s.capital, 1),
           "your_hours_left_this_year": round(
               max(0.0, s.director_pool() - s.wage_hours_this_year), 1)}
    if _cost > 0.5:
        # Same rule: round the parts, then take the difference from the
        # rounded parts, so the three figures on the screen subtract.
        out["earned"] = round(pay, 1)
        out["it_cost_your_own_practice"] = round(_cost, 1)
        out["so_you_are_up"] = round(round(pay, 1) - round(_cost, 1), 1)
        # "THE PRACTICE" THROUGHOUT, not "the surgery" halfway through.
        # A Roman founder selling a year of smith's work does not have a
        # surgery, and the sentence named the same thing two ways inside
        # fourteen words.
        out["why"] = ("You cannot be in two places. Hours sold for wages "
                      "come out of your own practice, so what you really "
                      "made this year is the wage less what the practice "
                      "did not earn while you were gone. Hours you put "
                      "into your OWN projects do not cost you this.")
    if err:
        out["but"] = err
    return out



def _cmd_allocate(s, nodes, cmd, ended):
    # A STANDING INSTRUCTION, NOT A ONE-TURN COMMAND. "Divide your own
    # year's hours yourself": `start` and `work` already let a player
    # act for one year at a time, and a player who wants a fixed split
    # - 100 hours a year of manual work, 500 to one project, 1400 to
    # another - had no way to say so once and have it stand, in a game
    # played over hundreds of turns. This writes s.hour_allocations,
    # which core.py's step() - and nowhere else - reads; `portfolio`
    # below reads the same numbers step() actually applied, never a
    # second guess at them. See core.py's own long comment on exactly
    # how a directive changes the allocator (order, not ceiling) and
    # what happens when it cannot be honoured.
    k = cmd.get("id")
    if k is None:
        _rows = [{"id": kk, "hours_a_year": hh}
                 for kk, hh in sorted(s.hour_allocations.items()) if kk != "work"]
        _out = {"ok": True, "allocations": _rows or "none"}
        if s.hour_allocations.get("work"):
            _out["work"] = {"trade": s.work_trade,
                            "hours_a_year": s.hour_allocations["work"]}
        _out["note"] = (
            "hours you have NOT directed keep being shared out by "
            "priority, exactly as before - this only affects what you "
            "have explicitly put here. {\"cmd\":\"allocate\",\"id\":X,"
            "\"hours\":N} sets or replaces one; hours 0 (or leaving "
            "hours out) clears it. id \"work\" sells hours for wages "
            "every year instead of a project - it also needs \"trade\".")
        return _out
    hours = cmd.get("hours")
    hours = 0.0 if hours is None else _num(hours, -1.0)
    if hours < 0:
        return {"ok": False, "error": "hours must be a number, 0 or "
                                      "more. 0 clears the standing order."}
    if k == "work":
        if hours <= 0:
            had = s.hour_allocations.pop("work", None)
            s.work_trade = None
            return {"ok": True, "cleared": "work",
                    "had_been": had} if had else {"ok": True, "cleared": "work"}
        trade = cmd.get("trade") or s.work_trade
        if not trade:
            return {"ok": False,
                    "error": "say which trade to sell hours as, e.g. "
                             "{\"cmd\":\"allocate\",\"id\":\"work\","
                             "\"trade\":\"labourer\",\"hours\":100}"}
        if trade not in WAGES:
            here = sorted(t for t in WAGES if s.trade_available(t))
            return {"ok": False, "error": "no such trade. you could work "
                                          "as: " + ", ".join(here)}
        if not s.trade_available(trade):
            return {"ok": False,
                    "error": "nobody here will pay you to be a %s yet: "
                             "the trade does not exist in this society. "
                             "Teach it first with train." % trade}
        s.hour_allocations["work"] = float(hours)
        s.work_trade = trade
        return {"ok": True, "set": "work", "trade": trade,
                "hours_a_year": float(hours),
                "note": "this much of your own pool is sold for wages as "
                        "a %s every year from now on, topping up anything "
                        "you sell by hand the same year, before your "
                        "projects see what is left. 'allocate' with "
                        "hours 0 clears it" % trade}
    if k not in nodes:
        return {"ok": False, "error": "unknown node id %r. 'state' lists "
                                      "what is active" % k}
    if k not in s.active:
        return {"ok": False,
                "error": "%s is not active, so there is nothing for a "
                         "directive to apply to yet. 'start' it first, "
                         "then 'allocate' it hours" % k}
    if hours <= 0:
        had = s.hour_allocations.pop(k, None)
        return ({"ok": True, "cleared": k, "had_been_a_year": had}
                if had else {"ok": True, "cleared": k})
    s.hour_allocations[k] = float(hours)
    return {"ok": True, "set": k, "name": nodes[k]["name"],
            "hours_a_year": float(hours),
            "note": "this many of your own hours go to %s every year "
                    "from now on, ahead of anything you have not "
                    "directed - it can still never exceed what the pool "
                    "has or what this project's own pace can use; "
                    "'portfolio' shows what it actually gets each year "
                    "and why. 'allocate' with hours 0 clears it"
                    % nodes[k]["name"]}



def _cmd_risk(s, nodes, cmd, ended):
    kr = s.knowledge_risk()
    return {"ok": True, "knowledge_risk": kr, "year": s.year,
            "note": "What history is about to do to you, and what you have "
                    "built that blunts it. Every hazard here is fightable."}



def _cmd_values(s, nodes, cmd, ended):
    return _agent_values(s)



def _cmd_money(s, nodes, cmd, ended):
    # LESS THE YEAR YOU HAVE ALREADY PAID FOR. `hire` takes a finder's fee
    # and the first year's wages up front, and step() nets that advance off
    # the living cost it charges - so counting the whole payroll here bills
    # the same year twice. A break tester hired four artisans, read
    # "Net/yr after it: -1,097" on this very screen, stepped once and lost
    # 61. From the second year on the figure was right, which is what made
    # it so hard to see.
    _prepaid = min(s.living_cost(), getattr(s, "wages_prepaid", 0.0))
    fixed = (s.upkeep() + s.living_cost() - _prepaid
             + s.mine_operating_cost())
    _standing_revenue = s.revenue_capacity()
    _standing_upkeep = s.upkeep()
    _standing_living = s.living_cost(
        _rev=_standing_revenue, _upkeep=_standing_upkeep)
    _standing_prepaid = min(
        _standing_living, getattr(s, "wages_prepaid", 0.0))
    _standing_fixed = (_standing_upkeep + _standing_living
                       - _standing_prepaid + s.mine_operating_cost())
    _ramp, _prac = s.still_ramping(), s.practice_note()
    _mkt = s.goods_market_summary()
    # A PLAYER MUST SEE IT (data/review/COMMODITY_DYNAMISM.md):
    # material_price_factor() now responds for every material a node
    # buys, not just the 9 originally tracked commodities, so what it
    # is doing to costs needs a line here too, not only inside one
    # project's own `why`. See economy.py's material_market_summary().
    _mat_mkt = s.material_market_summary()
    return {"ok": True,
            "capital": round(s.capital, 1),
            "revenue": round(s.revenue(), 1),
            "where_the_money_comes_from": s.revenue_sources(),
            **({"still_building_up_custom": _ramp} if _ramp else {}),
            **({"about_your_own_practice": _prac} if _prac else {}),
            **({"materials_costing_you_a_premium": _mat_mkt} if _mat_mkt else {}),
            **({"the_market_you_sell_into": _mkt} if _mkt else {}),
            "what_it_costs_you": {
                "upkeep_of_what_you_built": round(s.upkeep(), 1),
                "living_and_appearances": round(s.living_cost() - s.wage_bill(), 1),
                # NAME THE PART THAT IS THERE BECAUSE YOU ARE RICH. A break
                # tester started with a million, built nothing, hired
                # nobody, and read "living and appearances ~14,990, Net/yr
                # -14,990" with no explanation anywhere of why an idle
                # fortune bleeds. It is not a fee: it is that a man visibly
                # richer than he lives is suspected in a patronage society.
                "_of_which_because_you_are_rich":
                    round(max(0.0, s.capital) * 0.015, 1) or None,
                "wages": round(s.wage_bill(), 1),
                "of_which_already_paid_as_hiring_advances":
                    round(_prepaid, 1) or None,
                "mines_standing": round(s.mine_operating_cost(), 1),
                # A COST LIKE ANY OTHER. It was printed two lines below the
                # net that ignored it, so a tester in a debt spiral read
                # "+9.5 a year" while capital fell 105 and then 117.
                "interest_on_arrears": round(
                    max(0.0, -s.capital) * s.debt_interest_rate(), 1)},
            # revenue_capacity(), not revenue() - this is the STANDING
            # figure (see the comment two lines below, and state's own
            # net_per_year, protocol.py: same fix, same reason). A
            # player who sold founder-hours with `work` watched this
            # swing to -193/yr for exactly one year and back, which is
            # not what "recurring" means.
            "net_per_year": round(
                _standing_revenue - _standing_fixed
                - max(0.0, -s.capital) * s.debt_interest_rate(), 1),
            "spent_on_projects_last_year": round(getattr(s, "spend_last_year", 0.0), 1),
            # THE SAME FIGURE `state` PRINTS. A break tester read `state`
            # "net -70.8 den/yr (after 75.5 den into projects)" against
            # `money` "Net/yr: 4.6" and called it a contradiction. Both were
            # right and only one was labelled: net_per_year is the standing
            # flows, before anything goes into the work in hand.
            "net_after_project_spend": round(
                s.revenue() - fixed
                - max(0.0, -s.capital) * s.debt_interest_rate()
                - getattr(s, "spend_last_year", 0.0), 1),
            "credit_limit": round(s.credit_limit(), 1),
            "interest_rate_on_arrears": round(s.debt_interest_rate(), 4),
            "interest_paid_in_total": round(getattr(s, "interest_paid", 0.0), 1),
            # HOW CLOSE, not just how far it goes. See warn_near_the_limit.
            "of_that_limit_you_have_used": (
                "%d%%" % (100.0 * -s.capital / max(1e-9, s.credit_limit()))
                if s.capital < 0 and s.credit_limit() > 0 else "none"),
            # committed_spend(), NOT A SECOND SUM OF THE SAME FIELD - this
            # used to total st["cost_left"] itself, inline, and 'start'
            # needed the identical total for its own aggregate warning
            # (see committed_spend()'s docstring, economy.py). One call,
            # read from both places.
            "still_owed_on_work_in_hand": round(s.committed_spend(), 1),
            # THE OTHER HALF OF THE SAME QUESTION 'start' NOW WARNS ABOUT:
            # what you have promised (just above) against what you can
            # actually expect to have. See funding_capacity()'s own
            # docstring for why this is the same number the un-manual
            # director's own start heuristic already used to avoid
            # over-committing itself.
            "you_could_actually_fund_up_to": round(s.funding_capacity(), 1)}



def _cmd_stuck(s, nodes, cmd, ended):
    # THE QUESTION EVERY TESTER ASKED, in different words. "There's no 'why
    # am I stuck?' view - three separate 90-250-year stalls, each caused by
    # one node blocked on one thing, each found by typing `why` at a
    # guess." The pieces were all here; nothing put them in one place, and
    # stall_diagnosis only spoke after eight years of insolvency.
    _fog = getattr(s, "fog", False)
    reasons = []
    _startable = [k for k in nodes
                  if k not in s.done and k not in s.active
                  and (not _fog or s.is_visible(k))
                  and s.start_reason(k)[0]]
    _afford = [k for k in _startable
               if s.project_cost(k) <= s.spending_power("start")]
    if s.active:
        _waits = {}
        _why_underfunded = {}
        for k, st in sorted(s.active.items()):
            bill = st.get("cost_left")
            if bill is None:
                bill = max(0.0, s.project_cost(k) - st["spent"])
            _waits[k] = _waiting_on(s, nodes, k, st, bill)
            # SAME GAP AS `why` AND `state`: arrears gives unspendable
            # founder hours back, so this can say "waiting on your hours"
            # for a project that is really stuck on money, on the exact
            # screen a player checks first when something is stalled.
            # why_underfunded, already computed onto st by core.py, is
            # the real reason - carry it per project, not just the string
            # above.
            if st.get("why_underfunded"):
                _why_underfunded[k] = st["why_underfunded"]
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
        _road_open = [k for k in _road if s.start_reason(k)[0]]
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
    _shut = sorted(k for k in s.done
                   if s.is_venture(k) and k not in s.operating
                   and nodes[k]["rev"] > nodes[k]["up"])
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
        _really_openable = [k for k in _shut if _openable(k)]
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
                                  "{:,.0f}".format(min(s.project_cost(k)
                                                       for k in _startable)),
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



def _cmd_labour(s, nodes, cmd, ended):
    one = (cmd.get("trade") or "").strip().lower()
    if one and one not in WAGES:
        return {"ok": False, "error": "no such trade: %s. They are: %s"
                % (one, ", ".join(sorted(WAGES)))}
    def row(t, long=False):
        # THE PRICE YOU ACTUALLY PAY, not the table price. A play tester
        # watched engineers go from 781 a year to 1,094 and budgeted wrong
        # for decades: leaning on a trade's local supply bids it up, and
        # the premium appeared in the bill and nowhere else.
        _lpf = s.labour_price_factor(t)
        r = {"trade": t,
             "a_year_of_one": round(s.annual_wage(t), 0),
             "you_employ": round(s.employees.get(t, 0.0), 2)}
        if long:
            r["wage_foundation"] = {
                "base_for_skill_and_difficulty": ANNUAL_WAGE.get(t, 375.0),
                **{k: round(v, 3) for k, v in s.wage_cost_factors(t).items()},
                "demographic_scarcity": round(s.wage_index, 3),
                "local_trade_scarcity": round(_lpf, 3),
                "society_price_level": round(s.price_index, 3),
            }
        # SAME EXPLANATION AS THE FULL LIST'S, for whoever asks about
        # one trade without ever asking for all of them - see
        # _staff_fraction_note. Checked on this one trade alone, not
        # the whole household, so a whole-number trade gets no
        # footnote even while another trade is mid-attrition.
        if abs(r["you_employ"] - round(r["you_employ"])) >= 0.02:
            r["you_employ_is_fractional_because"] = (
                "a continuous full-time-equivalent, not a count of "
                "whole people: hiring phases in, training takes years, "
                "and attrition trims a little every year rather than "
                "dismissing one named person at a time.")
        # THE CEILING, ON THE SCREEN. "This society's literacy will not
        # supply more than 6.4 scholars in total, ever" gates the goal
        # itself - which wants twenty-five - and appeared in no screen at
        # all: a play tester found it in a refusal message in year 463 of a
        # 500-year game. A wall you can only discover by walking into it is
        # not a wall, it is a trap.
        if t in s.LITERATE_TRADES:
            r["most_this_society_can_ever_supply"] = round(
                s.literate_capacity(t), 1)
            r["you_have_or_are_teaching"] = round(
                s._trade_headcount_pending(t), 2)
            r["what_widens_it"] = ("printing, paper, schools and academies - "
                                   "they raise how many people here can "
                                   "read, and this ceiling rises with it")
        if _lpf > 1.005:
            r["dearer_than_usual_by"] = "%d%%" % ((_lpf - 1.0) * 100)
            # "HERE" IS ONE TOWN, NOT THE COUNTRY. A player who reads
            # this as a claim about the whole of Rome or Han China
            # concludes the game is absurd - that is the demographics
            # complaint this line exists to head off. See the
            # population command for the country-wide figure this
            # household's own reach is being measured against.
            r["because"] = ("you have taken on a large share of the %ss "
                            "within this household's reach - one town's "
                            "labour market, not the whole country; the "
                            "population command shows how the two "
                            "compare. Teaching more of the trade, or "
                            "anything that widens the supply, brings it "
                            "back down" % t)
        if long:
            r.update({"kind": trade_family(t),
                      "wage_per_hour": round(WAGES[t] * s.wage_index
                                             * s.price_index, 3),
                      # SPLIT, because the total includes your own people
                      # and calling all of it "the market" made hiring look
                      # like it created smiths out of nothing.
                      "hours_the_market_can_supply": round(s.market_supply_split(t)[0], 0),
                      "hours_your_own_people_add": round(s.market_supply_split(t)[1], 0),
                      # AND THE SECOND CHANNEL. A break tester read one
                      # ceiling in three places and then commissioned past
                      # it. There are two: who you can HIRE here, and what
                      # an outside shop will take on, at a premium.
                      "hours_you_have_commissioned": round(s.hours_reserved(t), 0),
                      "hours_you_could_still_commission": round(
                          max(0.0, s.market_supply(t) - s.hours_reserved(t)), 0),
                      "hours_available_to_you_in_all": round(
                          s.hours_you_can_call_on(t), 0),
                      # THE NOTE IS STATIC AND THE WORLD IS NOT. A break
                      # tester read "exists here: True" and "does not exist
                      # yet; you must create this trade" three lines apart,
                      # because the note is a fixed string about the
                      # society as it started and they had since taught the
                      # trade into existence. Teaching one is the whole
                      # point of `train`; the reply has to notice it
                      # happened.
                      "note": (("you taught this trade into existence here; "
                                "the only %ss in this society are yours and "
                                "the ones they have taught since" % t)
                               if t in s.trades_created
                               else TRADE_NOTES.get(t, ""))})
            # THE HIRE YOU ARE CONTEMPLATING, NOT THE MARKET AS IT STANDS.
            # a_year_of_one above is true the instant it is quoted and can
            # be false one command later: hiring is what moves
            # labour_price_factor, and wage_bill charges the NEW factor
            # to every head of the trade you then have, not only the one
            # you added. A Norse player was quoted "a year of one: 525"
            # for a scholar, hired one, and the standing wage bill came to
            # 847.92 - 61% more - from exactly this. See
            # labour_price_factor_after_hiring's own docstring for the
            # full account; this is that forecast, priced and put on the
            # one screen a player actually reads before committing.
            if s.trade_available(t):
                _lpf_after = s.labour_price_factor_after_hiring(t, 1.0)
                _rate_after = round(
                    s.annual_wage(t, include_local_scarcity=False) * _lpf_after, 0)
                # ALWAYS SHOWN, QUIETLY: this is the number the task is
                # actually about, and it belongs on the screen whether or
                # not the move is large enough to also earn the banner
                # below.
                r["a_year_of_one_after_you_hire_one"] = _rate_after
                # THE BANNER IS FOR SCARCITY, NOT ARITHMETIC. One more
                # hire measurably moves the price of almost any trade in
                # a town this size - labourer's base pool is roughly a
                # dozen person-years, so even it crosses a 0.5% move from
                # a single hire. Flagging that every time would be a
                # warning nobody reads by the tenth trade. 5% (the same
                # bound `labour_pressure` itself treats as worth a name,
                # see labour_price_factor's own note on what "roughly
                # doubles the price at the whole of it" means) is where a
                # single hire stops being noise and starts being the
                # reason your wage bill actually moved - which is what
                # the Norse scholar case (1.0 to 1.615) plainly was and a
                # common trade like labourer or smith (~1.01) plainly
                # is not.
                if _lpf_after > 1.05:
                    _have = s.employees.get(t, 0.0)
                    r["hiring_moves_the_price"] = True
                    # NOT JUST THE NEW HIRE. The whole point is that this
                    # rate applies to everyone you already have too, the
                    # instant you take one more on - so the bill, not
                    # only the per-head rate, is what has to be shown.
                    r["wage_bill_for_this_trade_now"] = round(
                        _have * r["a_year_of_one"], 0)
                    r["wage_bill_for_this_trade_after_hiring_one_more"] = round(
                        (_have + 1.0) * _rate_after, 0)
        return r
    if one:
        r = row(one, long=True)
        r["exists_here"] = s.trade_available(one)
        return {"ok": True, "trade": r}
    have = sorted(t for t in WAGES if s.employees.get(t, 0.0) > 0.005)
    # NOT "TRADES YOU DO NOT YET EMPLOY", and not "trades that exist"
    # either. Excluding the ones you have reads as "no more smiths
    # available" the moment you hire your first smith, which `hire smith 1`
    # then contradicts; including every available trade put machinist on
    # the list while `labour machinist` said "the town can supply: 0
    # hours", which a play tester read side by side. It is every trade
    # there is actually somebody here to hire.
    hirable = sorted(t for t in WAGES
                     if s.trade_available(t) and s.market_supply_split(t)[0] > 0)
    taught_only = sorted(t for t in WAGES
                         if s.trade_available(t) and t not in hirable)
    absent = sorted(t for t in WAGES if not s.trade_available(t))
    return {"ok": True,
            "on_your_staff": [row(t) for t in have] or "nobody",
            "you_could_hire_here": hirable,
            "only_the_ones_you_taught": taught_only,
            "do_not_exist_here": absent,
            "you_employ_in_total": round(sum(s.employees.values()), 2),
            # THE CAP, WHERE A PLAYER CAN SEE IT. This number decided a
            # play tester's entire mid-game and appeared NOWHERE: not in
            # state, not in state full, not here. The only way to learn it
            # was to try to hire and be refused, and the only way to learn
            # what RAISED it was to read the refusal, which changed as the
            # tree opened. They sat on 285,000 denarii unable to take on a
            # sixth person and had no idea why.
            "household_places_used": round(s.headcount(), 2),
            "household_places_in_all":
                round(s.headcount() + max(0.0, s.household_room()), 2),
            "room_for_more_people": round(max(0.0, s.household_room()), 2),
            # _room_advice, NOT _staff_advice. This is `labour`, and
            # `state` sends a player here with the words "'labour' says
            # what raises it" - meaning the CEILING on people. It answered
            # with _staff_advice, which names hiring, commissioning and
            # buying, every one of which needs the room you have not got.
            # Two play testers followed it in a circle; one found the real
            # answer only by guessing the word "workshop" in a search.
            # _room_advice exists for exactly this and was written after
            # the same complaint about the hire refusal.
            "what_raises_that_room": s._room_advice(),
            # NOT "NEVER", AND NOT "HOWEVER RICH". This sentence is mine
            # and it went stale the same day I wrote it. It said the
            # ceiling could never move, which was true of the old model and
            # is now false: the ceiling grows with the institutions that
            # train scholars and carry their keep. The user caught it by
            # reading the sentence literally, which is the right way to
            # read a sentence, and noticing it implies no research you do
            # can ever help. The `hire` refusal had already been corrected
            # and this screen had not, so the game was saying both things.
            "and_how_many_of_the_lettered_trades_this_society_supplies": (
                "%s: right now your household can hold at most %.1f of them "
                "in total, hired and taught together. That is your reach "
                "into the labour market, not a fact about how many people "
                "here can read. It RISES: a school, an academy and an "
                "imperial patron train and pay scholars on their own "
                "budget and lift this ceiling with them, which is the large "
                "effect; printing, paper and libraries widen literacy "
                "itself, which is the smaller one."
                % (", ".join(sorted(s.LITERATE_TRADES)),
                   s.literate_capacity("scholar"))),
            "slaves": s.slaves, "freedmen": s.freedmen,
            "annual_wage_bill": round(s.wage_bill(), 1),
            "craftsmen_on_your_staff": round(s.artisans, 2),
            "scholars_including_you": round(s.effective_scholars(), 2),
            # SAME EXPLANATION AS `state`'s - see _staff_fraction_note.
            # A player who asks `labour` without ever asking `state`
            # deserves the same answer to "why is this not a whole
            # number", not silence on this screen and a footnote only
            # on the other one.
            "staff_are_fractional_because": _staff_fraction_note(s),
            # A ROW WITH NO TRADE IS PEOPLE YOU BOUGHT, and printing that
            # as the literal string "None" - "None x3.3", "None x0.55" -
            # is how two separate testers concluded the game had lost track
            # of their household. It knows exactly what they are.
            "in_training": [
                {"trade": (r_[2] if len(r_) > 2
                           else "people you bought, learning the work"),
                 "people": (r_[3] if len(r_) > 3
                            else round(r_[0] / 0.55, 2)),
                 "ready_year": r_[1]}
                for r_ in getattr(s, "training", [])],
            "one_trade_in_full": '{"cmd":"labour","trade":"smith"}',
            "how_to_grow_staff": {"scholars": s._staff_advice("scholars"),
                                  "artisans": s._staff_advice("artisans")},
            "note": "A trade that does not exist here cannot be hired at any "
                    "price; teach one with train. Trades are not "
                    "interchangeable. Buying a job instead of a person is "
                    "commission. Every figure above is this household's "
                    "own reach into ONE town's labour market, not the "
                    "whole country - the population command shows both, "
                    "side by side, for every trade."}



def _cmd_hire(s, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    if not s.founder_alive and s.directors_extra < 0.5:
        return {"ok": False,
                "error": "there is nobody left to take anyone on: the "
                         "founder is dead and no deputy remains to direct "
                         "the work"}
    n, err = _qty(cmd, "n", 1)
    if err:
        return {"ok": False, "error": err + ". Nothing was changed."}
    ok, err = s.hire(cmd.get("trade"), n)
    if not ok:
        return {"ok": False, "error": err}
    # HIRING AND LETTING GO ARE DECISIONS, not standing facts the way
    # payroll is - neither labour.py nor core.py logs either one, so a
    # player reading `log` back saw the wage bill change with nothing
    # saying they were the one who changed it. `hire` already composed a
    # precise sentence for this ("2 smiths taken on for 750 denarii...");
    # using it here rather than rebuilding one from cmd["n"] keeps the log
    # honest about what actually happened, not just what was asked for.
    s.log.append((s.year, err or ("hired %s %s" % (cmd.get("n"), cmd.get("trade")))))
    return {"ok": True, "hired": cmd.get("trade"), "n": cmd.get("n"),
            "you_now_employ": round(s.employees.get(str(cmd.get("trade")).lower(), 0.0), 2),
            "annual_wage_bill": round(s.wage_bill(), 1),
            "capital": round(s.capital, 1)}



def _cmd_fire(s, nodes, cmd, ended):
    n, err = _qty(cmd, "n", 1)
    if err:
        return {"ok": False, "error": err + ". Nothing was changed."}
    ok, err = s.fire(cmd.get("trade"), n)
    if not ok:
        return {"ok": False, "error": err}
    # Same reasoning as `hire` above: `err` here is fire()'s own success
    # message, which says exactly what happened - staff let go, an
    # apprenticeship cancelled, or both - and cmd["n"] alone would not.
    s.log.append((s.year, err or ("let go %s %s" % (cmd.get("n"), cmd.get("trade")))))
    out = {"ok": True, "let_go": cmd.get("trade"),
           "annual_wage_bill": round(s.wage_bill(), 1)}
    if err:
        out["what_happened"] = err
    return out



def _cmd_train(s, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    n, err = _qty(cmd, "n", 1)
    if err:
        return {"ok": False, "error": err + ". Nothing was changed."}
    ok, msg = s.train(cmd.get("trade"), n, cmd.get("from"))
    if not ok:
        return {"ok": False, "error": msg}
    out = {"ok": True, "training": msg, "capital": round(s.capital, 1),
           "your_hours_left_this_year": round(
               max(0.0, s.director_pool() - s.director_hours_committed()), 1)}
    # TRAIN AND HIRE ARE TWO SEPARATE STEPS, and this message was the only
    # one a player saw at the moment they took the first of them. This
    # trade did not exist here before, and a project's hired_labour for it
    # draws only on people you have trained or hired INTO it - there is no
    # open market to fall back on the way there is for a smith or a
    # scribe. Nobody can do that work until the people above finish
    # learning, and 'hire' is how you add more without that wait, now that
    # the trade exists to hire into at all. A Rome player found this out
    # only when `start` refused a project outright, having read nothing on
    # this screen or on `why` that named the gap in advance.
    _trade = str(cmd.get("trade") or "").strip().lower()
    if _trade in TRADES_ABSENT:
        out["means"] = (
            "%s now exists here, but nobody can do that work yet: a "
            "project needing it draws only on people trained or hired "
            "into this exact trade, never a general market. "
            "'hire %s <n>' adds more right away, without waiting; "
            "otherwise the people above are it until they finish."
            % (_trade, _trade))
    return out



def _cmd_commission(s, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    hours, err = _qty(cmd, "hours")
    if err:
        return {"ok": False, "error": err + ". Nothing was changed."}
    ok, msg = s.commission(cmd.get("trade"), hours)
    if not ok:
        return {"ok": False, "error": msg}
    return {"ok": True, "commissioned": msg, "capital": round(s.capital, 1),
            "note": "These hours are available to your projects this year only."}



def _cmd_mothball(s, nodes, cmd, ended):
    _mb_id = cmd.get("id")
    ok, msg = s.mothball_work(_mb_id)
    if not ok:
        return {"ok": False, "error": msg}
    # mothball_work does not log either - a deliberate shutdown reads no
    # differently from one the creditors forced on you (see economy.py's
    # own, separate log lines for THAT case) unless the player's own
    # choice gets a line of its own too.
    s.log.append((s.year, "mothballed: %s (%s)"
                 % (nodes[_mb_id]["name"] if _mb_id in nodes else _mb_id, msg)))
    out = {"ok": True, "mothballed": msg, "upkeep": round(s.upkeep(), 1)}
    # SAY WHAT ELSE CLOSES WITH IT. A Mexica player shut capability
    # institutions for the capital back and lost two multi-year
    # stretches to it silently - the upkeep saving was the only thing
    # this reply ever mentioned. `mothball` takes effect before this
    # runs, so `s.CAPABILITY_INSTITUTIONS` already tells the truth about
    # what just stopped.
    if _mb_id in s.CAPABILITY_INSTITUTIONS:
        out["but"] = (
            "this was a capability, not only an expense: scholars it "
            "supported, household places it added, credit or standing "
            "it lent you, or a future start it cleared have ALL stopped "
            "too, the same as its upkeep. 'restore %s' brings it back "
            "for a fraction of the original cost." % _mb_id)
    return out



def _cmd_restore(s, nodes, cmd, ended):
    _rs_id = cmd.get("id")
    ok, msg = s.restore_work(_rs_id)
    if not ok:
        return {"ok": False, "error": msg}
    s.log.append((s.year, "restored: %s (%s)"
                 % (nodes[_rs_id]["name"] if _rs_id in nodes else _rs_id, msg)))
    return {"ok": True, "restored": msg, "capital": round(s.capital, 1)}



def _cmd_quote(s, nodes, cmd, ended):
    what = (cmd.get("what") or "mine").strip().lower()
    # EVERYTHING YOU CAN BUY, NOT JUST MINES. `quote` exists because a
    # tester went from 38,151 denarii to zero on one unpriced mine command.
    # A break tester then spent 27,500 - 68% of their capital - on `buy
    # forest 100`, with no price shown anywhere, no way to ask for one, and
    # no market to sell it back into. Same lesson, same command, different
    # counter.
    if what in ("forest", "coppice", "woodland"):
        n_f, err_f = _qty(cmd, "n", 100)
        if err_f:
            return {"ok": False, "error": err_f}
        per = s.FOREST_COST_PER_HA * s.price_index
        return {"ok": True, "what": "forest", "hectares": n_f,
                "to_buy_it": round(per * n_f, 1),
                "per_hectare": round(per, 2),
                "you_have": round(s.capital, 1),
                "you_could_raise": round(s.spending_power("buy"), 1),
                "you_can_afford_about": round(s.spending_power("buy") / max(per, 1e-9), 1),
                "afford_means": "cash plus half the credit line",
                "it_yields_per_hectare_per_year":
                    "%.2f tonnes of charcoal, sustainably" % s.CHARCOAL_PER_HA,
                "note": "Coppice is bought once and yields every year after. "
                        "There is no market to sell it back into."}
    if what in ("nitre", "nitre_bed", "saltpetre"):
        n_n, err_n = _qty(cmd, "n", 10000)
        if err_n:
            return {"ok": False, "error": err_n}
        per_n = s.NITRE_COST_PER_M2 * s.price_index
        return {"ok": True, "what": "nitre bed", "square_metres": n_n,
                "to_lay_it": round(per_n * n_n, 1),
                "per_square_metre": round(per_n, 2),
                "you_have": round(s.capital, 1),
                "you_could_raise": round(s.spending_power("buy"), 1),
                "you_can_afford_about": round(s.spending_power("buy") / max(per_n, 1e-9), 0),
                "afford_means": "cash plus half the credit line",
                "it_yields_per_square_metre_per_year":
                    "%.4f tonnes of saltpetre" % s.NITRE_YIELD_T_PER_M2,
                "note": "Saltpetre is made, not mined: dung, straw and ash "
                        "turned for a couple of years. Cheap by the metre "
                        "and thin by the metre, so beds are laid in "
                        "thousands of square metres, not hundreds."}
    if what in ("slaves", "people"):
        n_s, err_s = _qty(cmd, "n", 1)
        if err_s:
            return {"ok": False, "error": err_s}
        return {"ok": True, "what": "slaves", "people": n_s,
                "to_buy_them": round(s.slave_quote(n_s), 1),
                "you_have": round(s.capital, 1),
                "note": "The price rises with how many you take at once, and "
                        "they are worth nothing to you for the first few "
                        "years while they learn the work. Freeing them "
                        "afterwards makes them worth more, not less."}
    if what != "mine":
        return {"ok": False,
                "error": "you can quote a mine, a forest or people: "
                         "quote mine coal 500, quote forest 100, quote slaves 5"}
    n, err = _qty(cmd, "n", 1)
    if err:
        return {"ok": False, "error": err}
    q = s.mine_quote(cmd.get("material"), n)
    if q is None:
        return {"ok": False, "error": "no such material: %r. %s"
                % (cmd.get("material"), s.mine_catalog_hint())}
    return dict(ok=True, **q)



def _cmd_close(s, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    ok, msg = s.close_mine(cmd.get("material") or cmd.get("what"))
    if not ok:
        return {"ok": False, "error": msg}
    return {"ok": True, "closed": msg,
            "mine_operating_cost": round(s.mine_operating_cost(), 1)}



def _cmd_withdraw(s, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    ok, msg = s.withdraw_from_public_life()
    if not ok:
        return {"ok": False, "error": msg}
    return {"ok": True, "withdrew": msg,
            "eminence": round(s.eminence, 2),
            "reputation": round(s.reputation, 1),
            "protection": round(s.protection, 3)}



def _cmd_bribe(s, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    amount, err = _qty(cmd, "amount")
    if err:
        return {"ok": False, "error": err + ". Nothing was changed."}
    ok, msg = s.bribe(amount)
    if not ok:
        return {"ok": False, "error": msg}
    return {"ok": True, "bribed": msg, "capital": round(s.capital, 1)}



def _cmd_open(s, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    k = cmd.get("id")
    if not isinstance(k, str):
        return {"ok": False, "error": 'give an id, e.g. {"cmd":"open","id":"fin_pawnshop"}'}
    if k not in nodes:
        # `why` on a mistyped id suggests; `open` answered "no such node"
        # and stopped. Same typo, same player, two different games.
        near = _did_you_mean(k, nodes, s=s)
        return {"ok": False,
                "error": "no such thing as %r%s"
                         % (k, (". did you mean: " + ", ".join(near))
                            if near else "")}
    # UNITS: HOW A PLAYER FOUNDS A SECOND SCHOOL. See
    # ProjectsMixin.open_venture / _expand_institution (projects.py). A
    # call with no "units" field behaves exactly as it always has.
    _units = cmd.get("units")
    if _units is not None and not isinstance(_units, (int, float)):
        return {"ok": False, "error": "units must be a number"}
    ok, msg = s.open_venture(k, units=_units)
    if not ok:
        return {"ok": False, "error": msg}
    # The single rule `help` calls out as the one that catches everybody -
    # finishing something earns nothing until you open it - deserves a
    # line in the player's own history, not just in the reply to this one
    # command. open_venture itself stays silent; see its docstring.
    s.log.append((s.year, "opened: %s (%s)" % (nodes[k]["name"], msg)))
    return {"ok": True, "opened": msg, "capital": round(s.capital, 1),
            "revenue": round(s.revenue(), 1), "upkeep": round(s.upkeep(), 1)}



def _cmd_ventures(s, nodes, cmd, ended):
    sch_free, art_free = s.venture_staff_free()
    running = sorted(s.operating)
    idle = sorted(k for k in s.done
                  if s.is_venture(k) and k not in s.operating)

    def _vrow(k):
        n = nodes[k]
        # AT THE FIGURE THE LEDGER USES. This printed the tree's raw
        # revenue, and the ledger applies the economy, the output factor,
        # this society's prices and the ramp - so a break tester measured
        # `ventures` understating every concern by a uniform 2.234x against
        # `money` (11,000 against 24,571). And NEEDS printed the BUILD crew
        # while the engine charges supervision, which is a quarter of it
        # and never the number the refusal quotes.
        _scale = (s.economy ** 0.75) * s.output_factor * s.price_index
        _sup_s, _sup_a = s.venture_hands(k)
        _foreman_trade, _foreman_fte = s.venture_foreman(k)
        # AT THE SAME MARKET PRICE `money` credits, for a goods-producing
        # concern: goods_market_factor() is 1.0 for anything not in
        # GOODS_CATEGORIES and for anything not yet open, so this changes
        # nothing for every other row. See that method's own comment.
        _mkt = s.goods_market_factor(k) if k in s.operating else 1.0
        row = {"id": k, "name": n["name"],
                "earns_a_year": round(n["rev"] * _scale
                                      * (s.venture_ramp(k) if k in s.operating
                                         else 1.0) * _mkt, 1),
                "costs_a_year": round(n["up"] * s.price_index, 1),
                "needs": {"scholars": round(_sup_s, 2),
                          "craftsmen": round(_sup_a, 2)},
                "specialist_foreman": (
                    {"trade": _foreman_trade, "fte": round(_foreman_fte, 2)}
                    if _foreman_trade else None)}
        _note = s.goods_market_note(k)
        if _note:
            row["market"] = _note
        # A CAPABILITY, NOT ONLY A BUSINESS. Every other row here is a
        # straightforward earn-vs-cost decision; these are not, because
        # closing one loses scholars it supports, household places it
        # adds, credit or standing it lends, or a future start it clears
        # - none of which show up in earns/costs at all. A Rome player
        # could not tell `identity_cover` and `workshop_first` (real
        # capabilities) apart from an ordinary shuttered business by
        # looking at this exact table; a Mexica player closed some of
        # these for the capital back and lost the capability along with
        # it, twice, having no way to see the difference here either.
        if k in s.CAPABILITY_INSTITUTIONS:
            row["capability"] = ("yes - more than income; see 'why %s'" % k)
        return row

    # CAPABILITY INSTITUTIONS GET THEIR OWN LIST. Sorting them into the
    # ordinary earn/cost table invited exactly the misreading above; a
    # separate heading says outright that these are not evaluated the
    # same way.
    _idle_ordinary = [k for k in idle if k not in s.CAPABILITY_INSTITUTIONS]
    _idle_capability = [k for k in idle if k in s.CAPABILITY_INSTITUTIONS]
    out = {"ok": True,
           "running": [_vrow(k) for k in running] or "nothing",
           "you_know_how_but_have_not_opened":
               [dict(_vrow(k), to_open_it=round(s.venture_capex(k), 1))
                for k in _idle_ordinary[:20]] or "nothing",
           "capabilities_you_know_how_to_run_but_have_not_opened":
               [dict(_vrow(k), to_open_it=round(s.venture_capex(k), 1))
                for k in _idle_capability] or "nothing",
           "people_free_to_run_something_new": {
               "scholars": round(sch_free, 2), "craftsmen": round(art_free, 2)},
           # YOU ARE IN THAT COUNT. `ventures` said "1 scholars, 1
           # craftsmen" on the same screen as `labour`'s "ON YOUR STAFF:
           # nobody" and `why`'s "(you have 1, 0)" - three screens, three
           # different counts, and a break tester listed all three side by
           # side. One person can keep an eye on one small shop, which is
           # how every one of these fortunes started; it just has to say
           # that the person is you.
           "one_of_each_of_those_is_you": bool(s.founder_alive),
           # WHERE THE REST OF THEM ARE. See venture_staff_who_is_watching_what.
           "and_these_concerns_are_holding_the_rest":
               s.venture_staff_who_is_watching_what()[:12] or "none",
           "held_in_all": {
               "scholars": round(s.venture_staff_used()[0], 2),
               "craftsmen": round(s.venture_staff_used()[1], 2)},
           "staffing_rule": (
               "Needs and held totals are full-time-equivalents. Free is "
               "clamped at zero, so a small deficit never appears negative. "
               "Concerns remain open until held staff exceeds effective "
               "capacity by more than the 0.50-FTE anti-churn margin."),
           "you_have_in_all": {
               "scholars": round(s.effective_scholars(), 2),
               "craftsmen": round(s.artisans
                                  + (s.FOUNDER_IS_WORTH if s.founder_alive
                                     else 0.0), 2)},
           # SCHOLARS AND CRAFTSMEN ARE NOT INTERCHANGEABLE, and nothing
           # said so. A play tester spent thirty years poor because
           # auto_train had bought them engineers - who count as scholars
           # and cannot keep an eye on a workshop - and the turn they
           # swapped three engineers for three artisans their net went from
           # -155 a year to +4,164. `labour <trade>` shows the wage and not
           # which of the two columns the trade lands in.
           "these_are_not_interchangeable": (
               "Most concerns want CRAFTSMEN to keep an eye on them. "
               "Engineers, chemists and machinists are scholars here, and "
               "a scholar cannot watch a workshop. 'labour <trade>' says "
               "which of the two a trade is."),
           # "needs", "held_in_all" and "people_free_to_run_something_new"
           # above are venture_hands()/venture_staff_free()'s own numbers
           # - a continuous SHARE of a person's year, never a headcount -
           # see _VENTURE_SUPERVISION_NOTE's own comment for the exact
           # complaint this answers.
           "these_are_a_share_of_their_year_not_a_headcount":
               _VENTURE_SUPERVISION_NOTE,
           "note": "Knowing how to do a thing and running it are different. "
                   "Of the things in the TREE, only what you are RUNNING "
                   "earns anything or costs anything. 'open <id>' starts "
                   "one, 'mothball <id>' stops it, and you keep the "
                   "knowledge either way. The capability list below is "
                   "not judged on money the way the ordinary one is - see "
                   "each one's own 'why' before deciding whether to open "
                   "or close it."}
    # THE PRACTICE IS NOT A VENTURE, AND IT IS WHERE YOUR MONEY COMES FROM.
    # A break tester read "RUNNING: nothing" and "only what you are RUNNING
    # earns anything" on the same screen as a ledger paying 233.5 a year
    # from two named nodes, and filed it as the two screens flatly
    # contradicting each other. They do not, but nothing said which side
    # the practice falls on.
    _prac_note = s.practice_note()
    if _prac_note:
        out["your_practice_is_not_a_venture"] = (
            "%s You did not open it and you cannot close it; it is not "
            "listed here, and it is most of your income until you build "
            "something. See 'money'." % _prac_note)
    if len(_idle_ordinary) > 20:
        out["and_more_you_could_open"] = len(_idle_ordinary) - 20
    return out



def _cmd_policy(s, nodes, cmd, ended):
    want = cmd.get("set")
    changed = {}
    if want is not None:
        if not isinstance(want, dict):
            return {"ok": False,
                    "error": 'set must be an object, e.g. '
                             '{"cmd":"policy","set":{"auto_hire":true}}'}
        for key, val in want.items():
            if key not in s.policy:
                return {"ok": False, "error": "no such policy: %s. They are: %s"
                        % (key, ", ".join(sorted(s.policy)))}
            s.policy[key] = _flag(val)
            changed[key] = s.policy[key]
    # WHICH OF THESE CAN ACTUALLY ACT TODAY. A play tester spent about eight
    # years and 5,952 denarii working out that negative capital silently
    # disables both hiring and opening: the switches read ON, the engine
    # did nothing, and the only clue was one refusal string. A switch that
    # says ON while nothing happens is worse than one that says OFF.
    _stopped = {}
    if s.capital <= 0:
        if s.policy.get("auto_hire"):
            _stopped["auto_hire"] = ("nothing to hire with: hiring is paid "
                                     "in advance and you are in arrears")
        if s.policy.get("auto_open"):
            _stopped["auto_open"] = ("nothing to open with: opening a "
                                     "concern costs stock and premises")
    if s.year < getattr(s, "credit_frozen_until", 0):
        _stopped["credit"] = ("nobody will fund new work until %d"
                              % int(s.credit_frozen_until))
    _pol = {"ok": True, "policy": dict(s.policy), "changed": changed,
            # WHAT THESE ARE FOR, BEFORE WHAT EACH ONE DOES. Play testers
            # keep switching them on in the belief that the engine knows
            # the best line and is offering to walk it for them, and then
            # reporting the result as a bug: "policy auto_hire true
            # destroyed my run in eight years", "auto_train quietly
            # bankrupted me", "policy auto_hire on quietly destroyed my
            # economy". They are none of them wrong about what happened.
            # They are wrong about what these are, and nothing on this
            # screen has ever told them.
            #
            # These are a rough hand on the tiller so a player who does not
            # want to manage a payroll every turn does not have to. They
            # follow simple rules on the information of a single year. They
            # do not look ahead, they do not know your plan, and they will
            # sometimes take a line you would not have taken. That is the
            # deal, and it is worth taking for the tedium it saves; it is
            # not an optimizer and playing by hand will beat it.
            "these_are_approximations_not_optimal_play": (
                "Each of these is a rough rule of thumb applied once a "
                "year on that year's figures. None of them looks ahead, "
                "knows what you are building towards, or is trying to win. "
                "They exist to save you typing, and a careful player beats "
                "them. Turn one on when the tedium is worse than the "
                "mistakes; turn it off the moment it does something you "
                "would not have done. If one of them ever ruins you rather "
                "than merely costing you a little, that is a defect worth "
                "reporting, not the intended cost of convenience."),
            "what_each_does": {
                # SAY WHAT MIX. "Grow the staff" was the whole
                # description, and a play tester turned it on and watched
                # scholars take all 22 of their household places while
                # artisans fell to 0.03 - which shut 22 concerns, because
                # artisans are what supervise them, and took their net from
                # +8,010 a year to -3,027. The mix is now defended in
                # code; a player deciding whether to switch this on should
                # be able to read what it will do before it does it.
                "auto_hire": "grow the staff toward what you can house and "
                             "pay. Mostly craftsmen, because craftsmen are "
                             "what keep concerns open; some scholars; and "
                             "it replaces any trade you taught as its "
                             "people die off. It spends only a share of "
                             "your surplus, so with no surplus it hires "
                             "nobody",
                "auto_buy_people": "buy slaves when the workshop is short-handed",
                "auto_manumit": "free people you hold, over time",
                "auto_train": "teach trades this society does not have when a "
                              "project needs them",
                "auto_mine": "sink a mine when a mineral is holding work up",
                "auto_forest": "buy coppice when charcoal is holding work up",
                "auto_mothball": "stop working mines you cannot pay for",
                # THE ONE SWITCH WITH NO DESCRIPTION AT ALL, on a screen
                # whose entire purpose is saying what each of these does.
                "auto_commission": "buy a job from an outside shop when a "
                                   "few pairs of hands are the only thing "
                                   "between you and something you need. "
                                   "Cheaper than employing somebody you "
                                   "will not need next year, and it leaves "
                                   "no standing obligation either way",
                "auto_bribe": "pay your way out of a scandal before it kills you",
                "auto_court_heir": "spend 800 denarii (price-adjusted) when a "
                                   "patron dies to court the successor. Off by "
                                   "default in manual play; on unattended",
                "auto_shed": "let go of WORKS that cost more than they return "
                             "(this is about buildings and practices, not people)",
                # SAY WHAT IT WILL NOT DO - AND SAY THE EXCEPTION, which
                # this did not, so two players on different civilisations
                # each watched it open a loss-making concern, checked the
                # help, and reported the automation as broken. It is not:
                # auto_open_ventures deliberately opens a capability
                # institution at a loss, because a school takes 2,500 a
                # year and hands back 800 and is where twelve of your
                # scholars come from, and the margin test would otherwise
                # shut it for ever. An ordinary shop that earns less than
                # it costs is still left shut, which is the case the
                # original sentence was written for - a play tester whose
                # nitre beds and glassware stayed closed. Both halves are
                # true and only one of them was written down.
                "auto_open": "open concerns that plainly pay for themselves, "
                             "and the institutions that train and house "
                             "people even when those run at a loss - a "
                             "school costs more than it takes and is where "
                             "your scholars come from. An ordinary shop that "
                             "earns less than it costs is left shut however "
                             "much you need it; open those yourself with "
                             "'open <id>'",
            },
            "note": "Anything switched off here you can still do by hand: hire, "
                    "train, buy, commission, mothball, restore, bribe.",
            # A break tester read the note above as covering everything the
            # game ever does without being asked, switched auto_shed off,
            # and lost their whole staff anyway. The note was too broad and
            # they were entitled to read it that way. A policy is something
            # the game DECIDES for you; a consequence is the world answering
            # a decision you already made, and no switch turns those off.
            "not_policies": "Some things are consequences, not automation, "
                            "and there is no switch for them: people you "
                            "cannot pay leave, mines you cannot pay for stop "
                            "being worked once your credit is gone, and "
                            "creditors take what they are owed. Those follow "
                            "from having no money, not from a setting."}
    if _stopped:
        _pol["switched_on_but_cannot_act_right_now"] = _stopped
    return _pol



def _cmd_save(s, nodes, cmd, ended):
    op = cmd.get("cmd")  # this handler serves both "save" and "load"; see below
    path = cmd.get("file") or cmd.get("path")
    if not isinstance(path, str) or not path:
        return {"ok": False, "error": 'give a filename, e.g. {"cmd":"save","file":"mygame.json"}'}
    # A SAVE FILE IS A SAVE FILE, not a way to write anywhere on the disk.
    # A tester confirmed this would write into /etc/, and that a relative
    # path scattered files through the repository root. The game is played
    # by pointing agents and scripts at it; "name a path and I will write
    # there" is not a thing it should offer.
    bad = _unsafe_path(path)
    if bad:
        return {"ok": False, "error": bad}
    try:
        if op == "save":
            save_state(s, path)
            return {"ok": True, "saved": path, "year": s.year}
        load_state(s, path)
        return {"ok": True, "loaded": path, "year": s.year}
    except Exception as e:
        return {"ok": False, "error": "could not %s %r: %s" % (op, path, e)}



def _cmd_step(s, nodes, cmd, ended):
    # It used to advance the clock silently after the run was over, which
    # looks identical to a working game that has simply stopped progressing.
    if ended:
        return {"ok": False, "error": "the run has ended (%s); time cannot advance. "
                                      "Use {\"cmd\":\"state\"} to see the final position."
                                      % ended}
    raw_years = cmd.get("years", 1)
    # `True` is an int in Python and stepped one year silently. A player who
    # sends true meant something, and it was not that.
    if isinstance(raw_years, bool):
        return {"ok": False, "error": "years must be a number, not true or false"}
    try:
        years = int(raw_years)
    except (TypeError, ValueError):
        return {"ok": False, "error": "years must be an integer"}
    # 0.999 was rejected and 1.99 was silently floored to one year, which is
    # the worst pair of answers to give: the boundary is invisible and the
    # accepted side quietly does something other than what was asked. A
    # calendar advances in years; say so, rather than rounding on the
    # player's behalf and calling it "accepted".
    if float(raw_years) != years:
        return {"ok": False,
                "error": "years must be a whole number of years; %r is not. "
                         "Nothing was changed." % raw_years}
    if years < 1:
        return {"ok": False, "error": "years must be >= 1"}
    # A tester sent 100000 and the run silently ended. Nothing is gained by
    # accepting a number larger than the game can contain, and a typo that
    # ends your run without saying so is the worst kind of accepted input.
    left = max(0, s.end_year - s.year)
    if years > left:
        return {"ok": False,
                "error": "there are only %d years left before the horizon at "
                         "%d. Ask for %d or fewer, or fewer still if you want "
                         "to see what happens on the way."
                         % (left, s.end_year, left)}
    # WARN BEFORE, NOT AFTER, A MULTI-YEAR STEP WASTES HOURS. "Founder-
    # hours do not bank. A player can have long calendar-floor projects
    # running, use `step 5`, and unintentionally throw away thousands of
    # usable founder-hours if they did not fill the portfolio first" -
    # from a player who had already won the game. Checked against THIS
    # year only, before any of the requested years run: free_hours_
    # going_unused is the exact same test `state` already uses (every
    # active project already calendar-locked, or nothing active at all,
    # with a real pool still free) - read here, not recomputed, so this
    # warning and that field can never disagree about what "idle" means.
    # Non-blocking: it says so and proceeds, it does not refuse the step.
    multi_year_hours_warning = None
    if years > 1:
        _pre_state = _agent_state(s, nodes)
        _idle_note = _pre_state.get("free_hours_going_unused")
        if _idle_note:
            # A STARTABLE PROJECT HAS TO EXIST, or the warning would be
            # telling a player to do something they cannot do. Early
            # exit on the first hit - see `stuck`'s own _startable for
            # the same full-tree scan, accepted there for the same
            # reason: nothing cheaper tells you whether ANYTHING at all
            # is startable right now.
            _could_start = next(
                (x for x in nodes if x not in s.done and x not in s.active
                 and s.can_start(x)), None)
            if _could_start:
                # DOES IT ACTUALLY BANK? Checked against step()'s own
                # code, not assumed: core.py's step() computes `pool`
                # fresh every year from director_pool() minus this
                # year's commitments, and whatever of it 5b's wage-work
                # branch does not spend either is simply never written
                # anywhere - no field on `self` carries a "leftover
                # hours" balance into the next call. It does not partly
                # bank; it does not bank at all.
                multi_year_hours_warning = (
                    "before stepping %d years: %s founder-hours this "
                    "year are already going to waste, and '%s' is one "
                    "thing you could start today that would use some of "
                    "them. Founder-hours do not bank at all: step() "
                    "draws a fresh pool every year, and what goes "
                    "unused this year is simply gone, never carried "
                    "into the next one - so 'step %d' spends this "
                    "year's slack exactly as idle as it is right now, "
                    "%d more times over, unless you start something "
                    "first. Proceeding anyway."
                    % (years, "{:,.0f}".format(
                           _pre_state.get("founder_hours_available") or 0.0),
                       nodes[_could_start]["name"], years, years))
    # LOST, not only completed. A normal-play tester lost fourteen finished
    # works inside a single `step 12` - among them corpus_written and
    # school_founded, which they called the pivot of the entire game - and
    # wrote that "completions get EVENT lines; losses get nothing". The
    # engine does log the shedding, but nothing in the reply put a name
    # against what left, while every arrival got one. A game whose only
    # score is what you have built has to report subtraction at least as
    # loudly as addition.
    # STOP WHEN SOMETHING IT WARNED ABOUT ACTUALLY HAPPENS, rather than
    # running the rest of the years you asked for on top of it. A break
    # tester watched a `step 12` carry "CLOSE TO THE LIMIT ... while it is
    # still your choice" (see economy.warn_near_the_limit) straight
    # through to CREDIT EXHAUSTED, and then spend the REMAINING years of
    # the same call compounding arrears with nobody able to react - the
    # choice the warning promised was still theirs had already gone by
    # before the reply came back. A request for N years is not a promise
    # to hide what happens in year 1 until year N has also gone by. So
    # this breaks the loop, not only the request, the moment it fires.
    # A normal-play tester in mortal mode hit the equivalent fault for
    # the founder's own death: it landed inside a `step 60` and the call
    # ran eleven more years past it - far enough to also trip the
    # no-successor catastrophe - before the player got a turn to react.
    # MATCHED CASE-INSENSITIVELY BELOW, because this is prose and prose
    # gets rewritten: the death line was recapitalised to say what the
    # death MEANS and silently stopped matching here, which cost the step
    # its stop and the reply its death field.
    # CLOSE TO THE LIMIT BELONGS HERE TOO, and did not: the comment above
    # describes exactly this warning being cut short so the choice it
    # offers is still real, but the tuple itself never named it, so a
    # batched step ran straight past "stop a project... while it is
    # still your choice" and only broke four years later on the fatal
    # CREDIT EXHAUSTED that warning exists to prevent. The one event that
    # still leaves you options is the one this most needed to interrupt
    # for; the fatal one needs it least, since there is nothing left to
    # choose by the time it fires.
    _STEP_STOP_MARKERS = ("CREDIT EXHAUSTED", "FOUNDER DIES",
                          "CLOSE TO THE LIMIT")
    completed, lost, events = [], [], []
    founder_died_this_step = None
    stopped_early = None
    end_year = s.end_year
    ran = 0
    for _ in range(years):
        if s.dead_reason or s.year >= end_year:
            break
        before_done, before_log = set(s.done), len(s.log)
        # FOR `changes`: what a bare node-or-concern-set diff cannot tell
        # you on its own - WHEN it changed. revealed/operating only ever
        # grow or lose members silently; snapshotting the sets either
        # side of this one year's step() is the one place that year's
        # own diff can still be taken, cheaply, before it is gone.
        before_revealed = set(getattr(s, "revealed", set()))
        before_operating = set(s.operating)
        s.step()
        ran += 1
        hist = getattr(s, "_dashboard_history", None)
        if hist is None:
            hist = s._dashboard_history = []
        _snap = _dashboard_snapshot(s)
        _snap["revealed_added"] = sorted(
            set(getattr(s, "revealed", set())) - before_revealed)
        _snap["concerns_opened"] = sorted(s.operating - before_operating)
        _snap["concerns_closed"] = sorted(before_operating - s.operating)
        _snap["completed"] = sorted(s.done - before_done)
        hist.append(_snap)
        # sorted(), because this is a set difference and a set of strings
        # iterates in an order that depends on PYTHONHASHSEED. Two runs of
        # the same game with the same seed reported the same completions in
        # different orders, which is a small thing that makes the protocol's
        # own output impossible to diff. Caught by fingerprinting the
        # engine before and after being split into modules: every number
        # matched and this list did not.
        for k in sorted(s.done - before_done):
            # YOURS OR THE SOCIETY'S. Anything in `granted` is this
            # civilisation's own work, credited free; printing it in the
            # same "COMPLETED" line as a project the player paid for and
            # waited three years on had a tester reading their first turn
            # as two finished buildings they had never started.
            completed.append({"id": k, "name": nodes[k]["name"],
                              "year": s.done_year.get(k),
                              "granted": k in s.granted})
        for k in sorted(before_done - s.done):
            lost.append({"id": k, "name": nodes[k]["name"], "year": s.year,
                         "can_be_restored": k in getattr(s, "mothballed", set())})
        _this_year = s.log[before_log:]
        for y, m in _this_year:
            events.append({"year": y, "message": m})
            if "founder dies" in m.lower():
                _age = re.search(r"aged about (\d+)", m)
                _age_n = int(_age.group(1)) if _age else None
                founder_died_this_step = {"year": y, "aged_about": _age_n}
                # SAVED, NOT ONLY LOGGED - see _founder_death_info's own
                # comment on why the log alone cannot be trusted to
                # survive a save and a resume.
                s._founder_death_aged, s._founder_death_year = _age_n, y
        # AND STOP THE YEAR YOU WIN. Reaching the goal is no longer an
        # ending, so without this a `step 50` that crosses the finish line
        # would run on for another forty-nine years and mention it in
        # passing. It is the one moment in a run most worth handing back.
        if ran < years and s.goal_year == s.year:
            stopped_early = ("stopped after %d of the %d years you asked "
                             "for: you reached it. Step again when you "
                             "have had a look around."
                             % (ran, years))
            break
        if ran < years and any(mk.lower() in m.lower() for _, m in _this_year
                               for mk in _STEP_STOP_MARKERS):
            stopped_early = ("stopped after %d of the %d years you asked "
                             "for: something happened that you warned "
                             "yourself about and should see before more "
                             "time passes. Step again when you are ready."
                             % (ran, years))
            break
    out = dict(ok=True, completed=completed, lost=lost, events=events)
    if founder_died_this_step:
        out["the_founder_died_this_step"] = founder_died_this_step
    if stopped_early:
        out["stopped_early"] = stopped_early
    if multi_year_hours_warning:
        out["multi_year_hours_warning"] = multi_year_hours_warning
    out.update(_agent_state(s, nodes))
    return out



def _cmd_quit(s, nodes, cmd, ended):
    return {"ok": True, "bye": True}




_AGENT_DISPATCH_TABLE = {
    'state': _cmd_state,
    'available': _cmd_available,
    'log': _cmd_log,
    'score': _cmd_score,
    'why': _cmd_why,
    'path': _cmd_path,
    'start': _cmd_start,
    'stop': _cmd_stop,
    'rush': _cmd_rush,
    'bounty': _cmd_bounty,
    'buy': _cmd_buy,
    'work': _cmd_work,
    'allocate': _cmd_allocate,
    'risk': _cmd_risk,
    'hazards': _cmd_risk,
    'values': _cmd_values,
    'money': _cmd_money,
    'ledger': _cmd_money,
    'accounts': _cmd_money,
    'stuck': _cmd_stuck,
    'why_stuck': _cmd_stuck,
    'blocked': _cmd_stuck,
    'mines': _cmd_mines,
    'workings': _cmd_mines,
    'capacity': _cmd_capacity,
    'materials': _cmd_materials,
    'sell': _cmd_sell,
    'industry': _cmd_capacity,
    'dashboard': _cmd_capacity,
    'portfolio': _cmd_portfolio,
    'economy': _cmd_economy,
    'changes': _cmd_changes,
    'population': _cmd_population,
    'labour': _cmd_labour,
    'hire': _cmd_hire,
    'fire': _cmd_fire,
    'dismiss': _cmd_fire,
    'train': _cmd_train,
    'commission': _cmd_commission,
    'job': _cmd_commission,
    'mothball': _cmd_mothball,
    'restore': _cmd_restore,
    'quote': _cmd_quote,
    'price': _cmd_quote,
    'close': _cmd_close,
    'close_mine': _cmd_close,
    'withdraw': _cmd_withdraw,
    'bribe': _cmd_bribe,
    'open': _cmd_open,
    'ventures': _cmd_ventures,
    'policy': _cmd_policy,
    'save': _cmd_save,
    'load': _cmd_save,
    'step': _cmd_step,
    'quit': _cmd_quit,
}

# KNOWN_COMMANDS must never name a command the table cannot run - see
# KNOWN_COMMANDS' own definition. Checked once at import time so the two
# cannot silently drift apart again.
assert set(KNOWN_COMMANDS) - {"help"} <= set(_AGENT_DISPATCH_TABLE), (
    "KNOWN_COMMANDS names a command absent from _AGENT_DISPATCH_TABLE: %r"
    % sorted(set(KNOWN_COMMANDS) - {"help"} - set(_AGENT_DISPATCH_TABLE)))


def _agent_dispatch(s, nodes, cmd):
    """Every reply, in the money of the place you are standing in."""
    _out = _localise_money(_agent_dispatch_inner(s, nodes, cmd), money_word(s.civ))
    return _localise_words(_out, ((s.civ.get("local_words") or {}).get("pairs")))


def _agent_dispatch_inner(s, nodes, cmd):
    if not isinstance(cmd, dict) or "cmd" not in cmd:
        return {"ok": False, "error": "each line must be a JSON object with a 'cmd' field, "
                                      "e.g. {\"cmd\":\"state\"}"}
    # A NAME RESOLVES TO AN ID, BEFORE ANYTHING ELSE READS IT. Every screen in
    # this game prints the human NAME - "Horizontal loom" - and every command
    # that acts on a technology took only the machine id - "tex_horizontal_
    # loom" - until now; testers called that jarring often enough, in close
    # to the same words, that it stopped being a style choice. This has to run
    # before the fog guard just below: that guard reads cmd["id"] straight off
    # the command, so a name that resolves to exactly one id must already BE
    # that id by the time the guard looks at it, or a perfectly good name
    # would be refused as something the player had never heard of. `id` still
    # takes a raw id unchanged - this only fires when what was given is NOT
    # already one, so scripts and the `agent` protocol lose nothing.
    if (isinstance(cmd.get("cmd"), str) and isinstance(cmd.get("id"), str)
            and cmd["cmd"].strip().lower() in _NAME_COMMANDS
            and cmd["id"] not in nodes):
        _name_cands = _resolve_by_name(cmd["id"])
        if getattr(s, "fog", False):
            # ONLY WHAT THE PLAYER HAS ACTUALLY HEARD OF. Two nodes can share
            # a name where one is built and the other is still beyond the
            # fog; handing back the hidden one as a candidate to disambiguate
            # between is exactly the leak the fog guard below exists to close,
            # so the filter runs before a player ever sees the list, not after.
            _name_memo = {}
            _goal = getattr(s, "goal", None)
            # THE GOAL'S NAME GETS THE SAME NARROW EXCEPTION ITS ID ALREADY
            # HAS, on `why` alone - see the fog guard's own comment on
            # _goal_why just below. Without this, a player who only ever
            # learned the goal's NAME (under fog its id is never shown; see
            # _agent_state's "goal" field) typed it into `why` and was told
            # "you have never heard of any such thing" about the one thing
            # they were told by name on arrival. It is gated on an EXACT match
            # of the goal's own name, not the prefix/substring tiers: a vague
            # guess like "transistor" must stay refused, the same way
            # `_did_you_mean` already refuses to suggest the goal for one.
            _exact_here = NODE_NAME_NORM.get(_norm_name(cmd["id"]), ())
            _op_lc = cmd["cmd"].strip().lower()
            _name_cands = [
                k for k in _name_cands
                if s.is_visible(k, _memo=_name_memo)
                or (k == _goal and _op_lc == "why" and k in _exact_here)]
        if len(_name_cands) == 1:
            cmd = dict(cmd, id=_name_cands[0])
        elif len(_name_cands) > 1:
            _name_cands = sorted(_name_cands, key=lambda k: (nodes[k]["name"], k))
            return {"ok": False,
                    "error": ("more than one thing is called that; say which "
                              "by id: %s%s"
                              % (", ".join("%s (%s)" % (k, nodes[k]["name"])
                                           for k in _name_cands[:10]),
                                 " and %d more" % (len(_name_cands) - 10)
                                 if len(_name_cands) > 10 else ""))}
        # Otherwise: no match by name either. Fall through with cmd["id"]
        # untouched, so the ordinary unknown-id handling further down - and
        # the fog guard immediately below it - answer it exactly as they
        # already do for a mistyped id, did-you-mean included.
    # ONE GUARD, FOR EVERY COMMAND THAT TAKES AN ID. `why` checked visibility
    # and `bounty` did not: it checked prerequisites first, so refusing a
    # bounty on the goal node printed the goal's seven missing prerequisites by
    # name. A break tester crawled that error recursively and recovered 134
    # hidden technology ids and the entire dependency graph to the transistor
    # in six rounds, with fog on the whole time. Patching bounty alone would
    # leave the next command that grows an id to make the same mistake, so the
    # check lives here, once, before any handler sees the id.
    if getattr(s, "fog", False) and isinstance(cmd.get("cmd"), str):
        _op = cmd["cmd"].strip().lower()
        _k = cmd.get("id")
        # THE SAME ANSWER WHETHER OR NOT IT EXISTS. Refusing an unheard-of node
        # with "you have never heard of that" and a nonexistent one with
        # "unknown node 'X'" makes the two distinguishable, and that difference
        # IS the tree: a break tester classified ten real technologies and five
        # invented ones from sixteen plain-English guesses, on a fogged save,
        # in one pass. `help fog` promises there is no way to view the whole
        # tree, and a question you can ask about any name at all, and get a
        # true answer to, is a way to view the whole tree.
        # THE ONE EXCEPTION IS `why` ON THE GOAL. The status line names the goal
        # every single turn - "Aiming at: Point-contact transistor" - and this
        # answered `why point_contact_transistor` with "you have never heard of
        # any such thing", then offered fin_contract_law as what the player
        # might have meant, for the first 187 years of a play tester's run.
        # Being told what you are for and then told you have never heard of it
        # is a contradiction, not fog. It is `why` alone, and not is_visible
        # itself, because making the goal visible reopened the exact exploit
        # this guard exists to close: `bounty` on the goal then printed its
        # seven missing prerequisites by name, and a break tester once crawled
        # that error recursively to recover 134 hidden ids. `why` under fog
        # already says only "this needs 7 other things you have not heard of
        # yet", which is the honest answer.
        _goal_why = (_op == "why" and _k == getattr(s, "goal", None))
        if _op in _ID_COMMANDS and isinstance(_k, str) and not _goal_why and (
                _k not in nodes or not s.is_visible(_k)):
            if _k == getattr(s, "goal", None):
                # You know its name; you were handed it on arrival. Telling you
                # that you have never heard of the thing you are aiming at, and
                # then guessing you meant fin_contract_law, is absurd on its
                # face. Saying nothing MORE than "not yet" leaks nothing.
                return {"ok": False,
                        "error": "that is what you are aiming at, and you cannot "
                                 "act on it yet: everything it rests on is still "
                                 "beyond what you have heard of. 'why %s' is all "
                                 "of it you can see from here." % _k}
            near = _did_you_mean(_k, nodes, s=s)
            # SAY WHERE THE SUGGESTIONS COME FROM. The suggestions are already
            # filtered through is_visible, so nothing hidden is ever named -
            # but this said "you have never heard of any such thing... nothing
            # tells you what lies beyond that" and then listed three ids, and a
            # break tester reasonably read that as the fog leaking and filed it
            # as their second most serious finding. It was a false alarm: the
            # three they saw were two of Rome's own granted crafts and one
            # thing standing startable in front of them. A refusal that
            # manufactures false bug reports is costing real work, so the
            # sentence now says which of the two the suggestions are.
            return {"ok": False,
                    "error": "you have never heard of any such thing. You know "
                             "what you have built and what you could begin next; "
                             "nothing tells you what lies beyond that.%s"
                             % ((" Among the things you DO know, did you mean: "
                                 + ", ".join(near)) if near else "")}
    op = cmd.get("cmd")
    ended = _agent_end_reason(s)

    if op in ("help", "?", "commands"):
        return {"ok": True, "help": _agent_help(s, cmd.get("topic"))}

    # One central guard rather than five. A playtester sent {"id": {"a": 1}} and
    # the process died on `k not in nodes` with an unhashable-type TypeError,
    # losing the whole session. A malformed command must cost you the command,
    # never the game.
    if "id" in cmd and not isinstance(cmd["id"], str):
        return {"ok": False,
                "error": "id must be a name in quotes, not %s. Nothing was changed."
                         % type(cmd["id"]).__name__}

    # NaN and Infinity, anywhere in the command, before anything is touched.
    bad = sorted(k for k, v in cmd.items() if not _clean(v))
    if bad:
        return {"ok": False,
                "error": "%s must be a real number; NaN and Infinity are not "
                         "quantities. Nothing was changed." % ", ".join(bad)}

    _handler = _AGENT_DISPATCH_TABLE.get(op)
    if _handler is not None:
        return _handler(s, nodes, cmd, ended)

    # THE LIST MUST NOT GO STALE. This was ten commands hard-coded into a
    # string while the game had grown to twenty-four, so a player who mistyped
    # was handed a list that silently omitted labour, hire, train, commission,
    # money, risk, policy, quote, close, mothball, restore, work and bribe.
    # A help message that is wrong is worse than none, because it is believed.
    return {"ok": False,
            "error": "unknown cmd %r. Use one of: %s. %s"
                     % (op, ", ".join(KNOWN_COMMANDS),
                        'Or {"cmd":"help"} for what each one does.')}
