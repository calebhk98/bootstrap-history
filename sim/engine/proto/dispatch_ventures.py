"""Projects and ventures commands: start, stop, rush, mothball, restore,
open, ventures, policy - everything whose job is beginning, stopping or
running what the tech tree names, as opposed to labour or money on their
own.

Split out of dispatch.py (see that file's own docstring for why): dispatch.py
stays the composition point - the command table, the dispatcher, and every
name protocol.py's shim re-exports - and imports these handlers back from
here. Behaviour is unchanged and moved verbatim.
"""

from ..data import downstream_count
from .nodes import _did_you_mean
from .util import _flag
from .ventures import _VENTURE_SUPERVISION_NOTE


def _cmd_start(sim, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s); nothing more can be started. 'state' shows where you finished and how far you got" % ended}
    node_id = cmd.get("id")
    if node_id not in nodes:
        return {"ok": False, "error": "unknown node id %r. use {\"cmd\":\"available\"} "
                                      "or {\"cmd\":\"why\",\"id\":...} to find valid ids" % node_id}
    # SAY UP FRONT WHEN THE SOCIETY CANNOT STAFF IT: a project wanting more
    # of a trade's hours than this society's own ceiling can ever supply
    # can otherwise sit crawling at some small percentage for a very long
    # time with nothing said about why. The engine knows this at `start`
    # time. It is still allowed (you may teach or hire your way to the
    # hours, and the work does crawl) but it must not be a silent trap.
    # THE NUMBER PRINTED HAS TO BE THE NUMBER TESTED: the comparison above
    # uses hours_you_can_call_on, which is market_supply PLUS whatever you
    # have already commissioned, so the line that prints the ceiling has
    # to use the same figure - printing market_supply alone would let
    # `start` and `stuck` quote two different ceilings for the identical
    # project a moment apart.
    _impossible = []
    _impossible_trades = set()
    _n0 = nodes[node_id]
    _frac0 = min(1.0, 1.0 / max(1.0, _n0["yrs"]))
    for _trade, _want in (_n0["lab"] or {}).items():
        _need = _want * _frac0
        if _need > 0 and sim.hours_you_can_call_on(_trade) < _need:
            _impossible.append("%s (wants %.0f hours a year; this society can "
                               "field %.0f at most)"
                               % (_trade, _need, max(0.0, sim.hours_you_can_call_on(_trade))))
            _impossible_trades.add(_trade)
    # OVERSUBSCRIBED IS NOT THE SAME AS IMPOSSIBLE. The society may be
    # able to field the trade this wants and STILL not have enough of
    # it left once your own OTHER active work is already drawing on it
    # - "the first workshop/lab sat at 60% until I stopped adding new
    # work for a year", from a player who could not see this coming
    # until it had already happened. trade_demand_vs_supply (projects.py)
    # is the CURRENT portfolio's own demand, before this project is
    # added; trade_draw_plan(node_id, None) is this project's own full want,
    # since it has not started and so owes the whole thing. Same two
    # calls `portfolio` makes to build the aggregate table - reused
    # here, not re-derived, so `start`'s warning and `portfolio`'s own
    # figures can never tell two different stories about the same year.
    _demand_now = sim.trade_demand_vs_supply()
    _oversub = []
    for _trade, _plan in sim.trade_draw_plan(node_id, None).items():
        if _trade in _impossible_trades:
            continue          # already said, and said more plainly
        _supply = sim.hours_you_can_call_on(_trade)
        if _supply <= 0:
            continue
        _existing = _demand_now.get(_trade, {}).get("demand_hours_this_year", 0.0)
        _competitors = len(_demand_now.get(_trade, {}).get("projects_drawing_on_it", ()))
        _new_total = _existing + _plan["desired"]
        if _new_total > _supply + 1e-6:
            _oversub.append(
                "%s: this portfolio would want %s hours a year against "
                "%s this society can supply (%d other active project%s "
                "already drawing on it); this one competes for what is "
                "left, it does not get %s to itself"
                % (_trade, "{:,.0f}".format(_new_total), "{:,.0f}".format(_supply),
                   _competitors, "" if _competitors == 1 else "s",
                   "{:,.0f}".format(_plan["desired"])))
    started, why = sim.start_project(node_id)
    if not started:
        return {"ok": False, "error": why}
    node = nodes[node_id]
    # SAY SO, FOR THE PLAYER'S OWN RECORD: start_project itself only logs
    # the RESTART case (see its own self.log.append for "begun again"), so
    # a fresh start must be logged here too, or a player reading `log`
    # back sees completions and failures appear out of nowhere with no
    # record of having chosen to begin them.
    if sim.active.get(node_id, {}).get("spent", 0.0) <= 0.5:
        sim.log.append((sim.year, "started: %s" % node["name"]))
    # THE PRICE YOU ACTUALLY COMMITTED TO: project_cost moves with prices,
    # the coinage, material scarcity and what has been built since, so an
    # earlier `why` figure is only a snapshot. The bill IS fixed at the
    # moment you start; this must state plainly what it was fixed AT.
    bill = round(sim.active.get(node_id, {}).get("cost_left", sim.project_cost(node_id)), 1)
    _warn_staff = ("started, but this society cannot supply the labour it "
                   "wants and it will crawl until you can: %s"
                   % "; ".join(_impossible)) if _impossible else None
    out = {"ok": True, "started": node_id, "name": node["name"], "founder_hours_needed": node["ph"],
           "calendar_floor_years": round(sim.calendar_floor(node_id), 2),
           "nominal_calendar_floor_before_reputation": node["yrs"],
           # SAID AT THE MOMENT OF COMMITMENT, not only on `why` beforehand
           # or `available` in passing - this is the screen the player is
           # actually looking at when the risk becomes theirs. See
           # expected_calendar_years (projects.py): the true expected
           # total, retries included, computed through the same retry
           # rule _complete applies on every failure, not a plain
           # geometric series on the bare risk field.
           "expected_calendar_years_with_retries": round(
               sim.expected_calendar_years(node_id), 2),
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
    if node["yrs"] >= 2 and not getattr(sim, "_said_parallelism", False):
        sim._said_parallelism = True
        out["a_calendar_floor_is_not_exclusive_research_time"] = (
            "%s will take at least %d year%s, whatever else you do. That "
            "time is not spent watching it: your founder-hours and staff "
            "are free the moment this year's share of the work is paid "
            "for, and nothing stops you spending them on something else "
            "in the meantime. The strongest play is usually to keep "
            "several things running at once - start preparing the next "
            "layer now rather than waiting for this one to finish."
            % (node["name"], node["yrs"], "" if node["yrs"] == 1 else "s"))
    if _warn_staff:
        out["but"] = _warn_staff
    # BUILD STAFF AND OPERATING STAFF ARE DIFFERENT NUMBERS, and a player
    # can clear the first (checked above, and by start_project itself),
    # pay the whole bill, and only discover the second - venture_hands(),
    # what 'open' actually enforces - refuses them once the work is
    # already finished. `why` shows this too (same computation, see
    # staff_to_keep_it_open there), but it is easy to miss in a long page,
    # so it is said here too, at the one other moment it can still change
    # anything, with today's free staff - not a promise, since attrition
    # and hiring between now and completion can move either number.
    if sim.is_venture(node_id):
        _sup_sch, _sup_art = sim.venture_hands(node_id)
        _free_sch, _free_art = sim.venture_staff_free()
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
    # AND SAY WHEN THIS WOULD BORROW TO FINISH: `start` must not silently
    # finance the gap between what a project costs and what the household
    # has, at up to twelve per cent, leaving a player carried into debt
    # they did not decide to take on.
    #
    # Not a refusal: borrowing to build is a real and often correct move,
    # and the game already lets you. What must not happen is the
    # not-being-told, so this names the gap, the rate, and how much room
    # is left before the creditors stop being patient - and what they do
    # then.
    #
    # A FORECAST, NOT A RECEIPT - the keys have to say so. `start` itself
    # borrows nothing: credit only actually draws down at step resolution,
    # if and when cash genuinely goes negative paying this year's share.
    # These keys must describe what WILL happen if the project runs to
    # completion on today's cash, never what already has, or this screen
    # would contradict `money`'s own "(none used)" reading of the same
    # moment.
    _gap = bill - max(0.0, sim.capital)
    if _gap > 0:
        _lim = sim.credit_limit()
        _after = -(min(0.0, sim.capital) - _gap)
        out["on_credit"] = {
            "nothing_is_borrowed_yet": (
                "this is a forecast, not a receipt: credit only actually "
                "draws down at step resolution, if cash runs short paying "
                "this year's share. These figures are what happens if it "
                "does, on today's numbers."),
            "you_would_borrow": round(_gap, 1),
            "interest_rate_percent": round(sim.debt_interest_rate() * 100, 1),
            "estimated_annual_interest": round(
                _gap * sim.debt_interest_rate(), 1),
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
    # the exact same time: a Rome opening that starts scientific_method
    # (230) and then units_standards (444) would read "you would borrow: 44"
    # on the second start, because 444 against 400 capital is only a
    # 44-denarius gap taken alone, while capital actually falls past -150
    # within the year, because scientific_method's own 230 still unpaid is
    # drawing on the identical purse at the identical time. A per-project
    # forecast is not wrong about its own project; it is silent about
    # everyone else already in hand: two or three
    # foundations, each priced honestly on its own screen, can together
    # ask for more than the household currently holds. This is that
    # aggregate: committed_spend() (economy.py) is the exact same sum
    # `money`'s "still_owed_on_work_in_hand" already prints, read here
    # instead of re-totalled, and funding_capacity() is the identical
    # number the un-manual director's own start heuristic already uses
    # to avoid over-committing itself (step(), core.py) - given here as
    # the real ceiling, not a second formula that could drift from it.
    _committed = sim.committed_spend()
    _cash = max(0.0, sim.capital)
    if _committed > _cash and len(sim.active) > 1:
        _capacity = sim.funding_capacity()
        out["total_committed_across_active_work"] = {
            "you_have_promised": round(_committed, 1),
            "across_projects_in_hand": len(sim.active),
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
                % len(sim.active)),
        }
    # WARN, DO NOT SILENTLY ACCEPT. start_reason() already refuses a trade
    # that does not exist AT ALL (see "THE TRADE HAS TO EXIST" there), but
    # trade_available() goes true the moment you call `train`, two years
    # before anyone graduates - market_supply() is the stricter, honest
    # figure step() actually checks, and `start` must warn against it
    # here, not let a project needing a trade nobody can yet do come back
    # ok:true only to be HALTED years later with everything spent on it
    # lost and no earlier warning to act on. Name it here instead.
    short = sorted(trade for trade in node["lab"] if sim.market_supply(trade) <= 0.0)
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



def _cmd_stop(sim, nodes, cmd, ended):
    node_id = cmd.get("id")
    stopped, why = sim.stop_project(node_id)
    if not stopped:
        return {"ok": False, "error": why}
    # stop_project ITSELF never touches self.log - see its own docstring,
    # which is entirely about what the hours and money do, not about
    # recording the decision. A deliberate abandonment is exactly the
    # kind of thing a player asked `log` to be able to find again.
    sim.log.append((sim.year, "stopped: %s (%s)" % (nodes[node_id]["name"], why)))
    return {"ok": True, "stopped": node_id, "what_happened": why}



def _cmd_rush(sim, nodes, cmd, ended):
    # BULK START, FOG-SAFE: a late game can have dozens of things
    # startable at once, with nothing to do but type `start <id>`
    # repeatedly, when every one of those ids is already something
    # `can_start` has cleared - the same check `available` uses to decide
    # what to list at all - so acting on all of them at once hands back
    # nothing a player could not already see for themselves.
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
    _ok = [node_id for node_id in sim.order if sim.can_start(node_id, _memo=_memo)]
    # HIGHEST-LEVERAGE FIRST, INTERNALLY ONLY. This never shows a player
    # a downstream_count - that is a fog spoiler, see _node_explain's own
    # comment on it - it only uses the number to decide which of several
    # things your money cannot all cover gets it first, the same number
    # `available`'s own "most_rests_on_these" digest already uses to
    # decide what to show you. Ranking by it here leaks nothing, because
    # the ranking itself is never printed, only which ids got started.
    _ok.sort(key=lambda k: (-downstream_count(nodes, k), sim.project_cost(k)))
    # Discovery must not mutate dozens of portfolio entries. A numeric limit
    # is an explicit bounded instruction; an unbounded run needs confirmation.
    if limit is None and not cmd.get("force"):
        return {"ok": True, "preview": True,
                "count_would_start": len(_ok),
                "would_start": [{"id": node_id, "name": nodes[node_id]["name"],
                                  "cost": round(sim.project_cost(node_id), 1)}
                                 for node_id in _ok],
                "nothing_changed": True,
                "how_to_confirm": ("Use 'rush force' to begin this unbounded "
                                   "set, or 'rush limit:N' to begin at most N.")}
    # AND STOP WHEN THE YEAR IS FULL: an unbounded 'rush limit:1000' could
    # start hundreds of things at once - a plantation, a whaling industry,
    # a theatre, a gambling house, nitre beds and lens grinding, all in
    # the same year - owing tens of thousands of founder-hours against a
    # lifetime the game itself puts at about 72,000. The next step would
    # give hours to only a handful of them and the rest would sit inert
    # forever, so "RUNNING (N)" would be a fiction about most of them: the
    # command would be doing what it was asked, and what it was asked
    # would be incoherent.
    #
    # Committing a couple of years of everyone's attention is a decision a
    # player might reasonably make. Committing four centuries of it is not.
    _hours_room = max(0.0, sim.director_pool() - sim.director_hours_committed())
    _HORIZON_YEARS = 2.0
    _budget = sim.director_pool() * _HORIZON_YEARS
    started, not_started = [], []
    _owed = 0.0
    for node_id in _ok:
        if limit is not None and len(started) >= limit:
            break
        if started and _owed + nodes[node_id]["ph"] > _budget:
            not_started.append({
                "id": node_id, "name": nodes[node_id]["name"],
                "why": "not begun: the %d things already started this turn "
                       "owe %s of your hours, and you have about %s a year. "
                       "Beginning more would not make them go faster, only "
                       "leave them all standing still"
                       % (len(started), "{:,.0f}".format(_owed),
                          "{:,.0f}".format(sim.director_pool()))})
            continue
        ok2, why = sim.start_project(node_id)
        if ok2:
            _owed += nodes[node_id]["ph"]
            node = nodes[node_id]
            # SAY SO, for the same reason the single-id `start` does: a
            # player reading `log` back should see every begun-work as a
            # choice they made, not a completion that appeared unasked.
            if sim.active.get(node_id, {}).get("spent", 0.0) <= 0.5:
                sim.log.append((sim.year, "started: %s" % node["name"]))
            started.append({"id": node_id, "name": node["name"],
                            "cost": round(sim.active.get(node_id, {}).get(
                                "cost_left", sim.project_cost(node_id)), 1)})
        else:
            not_started.append({"id": node_id, "why": why})
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



def _cmd_mothball(sim, nodes, cmd, ended):
    _mb_id = cmd.get("id")
    mothballed, msg = sim.mothball_work(_mb_id)
    if not mothballed:
        return {"ok": False, "error": msg}
    # mothball_work does not log either - a deliberate shutdown reads no
    # differently from one the creditors forced on you (see economy.py's
    # own, separate log lines for THAT case) unless the player's own
    # choice gets a line of its own too.
    sim.log.append((sim.year, "mothballed: %s (%s)"
                 % (nodes[_mb_id]["name"] if _mb_id in nodes else _mb_id, msg)))
    out = {"ok": True, "mothballed": msg, "upkeep": round(sim.upkeep(), 1)}
    # SAY WHAT ELSE CLOSES WITH IT. A Mexica player shut capability
    # institutions for the capital back and lost two multi-year
    # stretches to it silently - the upkeep saving was the only thing
    # this reply ever mentioned. `mothball` takes effect before this
    # runs, so `s.CAPABILITY_INSTITUTIONS` already tells the truth about
    # what just stopped.
    if _mb_id in sim.CAPABILITY_INSTITUTIONS:
        out["but"] = (
            "this was a capability, not only an expense: scholars it "
            "supported, household places it added, credit or standing "
            "it lent you, or a future start it cleared have ALL stopped "
            "too, the same as its upkeep. 'restore %s' brings it back "
            "for a fraction of the original cost." % _mb_id)
    return out



def _cmd_restore(sim, nodes, cmd, ended):
    _rs_id = cmd.get("id")
    restored, msg = sim.restore_work(_rs_id)
    if not restored:
        return {"ok": False, "error": msg}
    sim.log.append((sim.year, "restored: %s (%s)"
                 % (nodes[_rs_id]["name"] if _rs_id in nodes else _rs_id, msg)))
    return {"ok": True, "restored": msg, "capital": round(sim.capital, 1)}



def _cmd_open(sim, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s). 'state' shows where you finished and how far you got" % ended}
    node_id = cmd.get("id")
    if not isinstance(node_id, str):
        return {"ok": False, "error": 'give an id, e.g. {"cmd":"open","id":"fin_pawnshop"}'}
    if node_id not in nodes:
        # `why` on a mistyped id suggests; `open` answered "no such node"
        # and stopped. Same typo, same player, two different games.
        near = _did_you_mean(node_id, nodes, sim=sim)
        return {"ok": False,
                "error": "no such thing as %r%s"
                         % (node_id, (". did you mean: " + ", ".join(near))
                            if near else "")}
    # UNITS: HOW A PLAYER FOUNDS A SECOND SCHOOL. See
    # ProjectsMixin.open_venture / _expand_institution (projects.py). A
    # call with no "units" field behaves exactly as it always has.
    _units = cmd.get("units")
    if _units is not None and not isinstance(_units, (int, float)):
        return {"ok": False, "error": "units must be a number"}
    opened, msg = sim.open_venture(node_id, units=_units)
    if not opened:
        return {"ok": False, "error": msg}
    # The single rule `help` calls out as the one that catches everybody -
    # finishing something earns nothing until you open it - deserves a
    # line in the player's own history, not just in the reply to this one
    # command. open_venture itself stays silent; see its docstring.
    sim.log.append((sim.year, "opened: %s (%s)" % (nodes[node_id]["name"], msg)))
    return {"ok": True, "opened": msg, "capital": round(sim.capital, 1),
            "revenue": round(sim.revenue(), 1), "upkeep": round(sim.upkeep(), 1)}



def _cmd_ventures(sim, nodes, cmd, ended):
    sch_free, art_free = sim.venture_staff_free()
    running = sorted(sim.operating)
    idle = sorted(node_id for node_id in sim.done
                  if sim.is_venture(node_id) and node_id not in sim.operating)

    def _vrow(node_id):
        node = nodes[node_id]
        # AT THE FIGURE THE LEDGER USES: printing the tree's raw revenue
        # would understate every concern by a uniform factor against what
        # `money` actually credits, since the ledger applies the economy,
        # the output factor, this society's prices and the ramp. NEEDS has
        # to print the SUPERVISION crew, not the BUILD crew - supervision
        # is a quarter of it, and it is the number the refusal actually
        # quotes.
        _scale = (sim.economy ** 0.75) * sim.output_factor * sim.price_index
        _sup_s, _sup_a = sim.venture_hands(node_id)
        _foreman_trade, _foreman_fte = sim.venture_foreman(node_id)
        # AT THE SAME MARKET PRICE `money` credits, for a goods-producing
        # concern: goods_market_factor() is 1.0 for anything not in
        # GOODS_CATEGORIES and for anything not yet open, so this changes
        # nothing for every other row. See that method's own comment.
        _mkt = sim.goods_market_factor(node_id) if node_id in sim.operating else 1.0
        row = {"id": node_id, "name": node["name"],
                "earns_a_year": round(node["rev"] * _scale
                                      * (sim.venture_ramp(node_id) if node_id in sim.operating
                                         else 1.0) * _mkt, 1),
                "costs_a_year": round(node["up"] * sim.price_index, 1),
                "needs": {"scholars": round(_sup_s, 2),
                          "craftsmen": round(_sup_a, 2)},
                "specialist_foreman": (
                    {"trade": _foreman_trade, "fte": round(_foreman_fte, 2)}
                    if _foreman_trade else None)}
        _note = sim.goods_market_note(node_id)
        if _note:
            row["market"] = _note
        # A CAPABILITY, NOT ONLY A BUSINESS: every other row here is a
        # straightforward earn-vs-cost decision; these are not, because
        # closing one loses scholars it supports, household places it
        # adds, credit or standing it lends, or a future start it clears
        # - none of which show up in earns/costs at all. Without marking
        # it, identity_cover and workshop_first (real capabilities) would
        # be indistinguishable from an ordinary shuttered business in
        # this exact table.
        if node_id in sim.CAPABILITY_INSTITUTIONS:
            row["capability"] = ("yes - more than income; see 'why %s'" % node_id)
        return row

    # CAPABILITY INSTITUTIONS GET THEIR OWN LIST. Sorting them into the
    # ordinary earn/cost table invited exactly the misreading above; a
    # separate heading says outright that these are not evaluated the
    # same way.
    _idle_ordinary = [node_id for node_id in idle if node_id not in sim.CAPABILITY_INSTITUTIONS]
    _idle_capability = [node_id for node_id in idle if node_id in sim.CAPABILITY_INSTITUTIONS]
    out = {"ok": True,
           "running": [_vrow(node_id) for node_id in running] or "nothing",
           "you_know_how_but_have_not_opened":
               [dict(_vrow(node_id), to_open_it=round(sim.venture_capex(node_id), 1))
                for node_id in _idle_ordinary[:20]] or "nothing",
           "capabilities_you_know_how_to_run_but_have_not_opened":
               [dict(_vrow(node_id), to_open_it=round(sim.venture_capex(node_id), 1))
                for node_id in _idle_capability] or "nothing",
           "people_free_to_run_something_new": {
               "scholars": round(sch_free, 2), "craftsmen": round(art_free, 2)},
           # YOU ARE IN THAT COUNT: leaving this unsaid would make
           # `ventures`, `labour` and `why` look like they disagree on how
           # many scholars and craftsmen you have, when they are all
           # counting the founder consistently, just not all saying so.
           # One person can keep an eye on one small shop, which is how
           # every one of these fortunes started; it just has to say that
           # the person is you.
           "one_of_each_of_those_is_you": bool(sim.founder_alive),
           # WHERE THE REST OF THEM ARE. See venture_staff_who_is_watching_what.
           "and_these_concerns_are_holding_the_rest":
               sim.venture_staff_who_is_watching_what()[:12] or "none",
           "held_in_all": {
               "scholars": round(sim.venture_staff_used()[0], 2),
               "craftsmen": round(sim.venture_staff_used()[1], 2)},
           "staffing_rule": (
               "Needs and held totals are full-time-equivalents. Free is "
               "clamped at zero, so a small deficit never appears negative. "
               "Concerns remain open until held staff exceeds effective "
               "capacity by more than the 0.50-FTE anti-churn margin."),
           "you_have_in_all": {
               "scholars": round(sim.effective_scholars(), 2),
               "craftsmen": round(sim.artisans
                                  + (sim.FOUNDER_IS_WORTH if sim.founder_alive
                                     else 0.0), 2)},
           # SCHOLARS AND CRAFTSMEN ARE NOT INTERCHANGEABLE, and nothing
           # else says so: engineers, chemists and machinists count as
           # scholars here and cannot keep an eye on a workshop, so a
           # household can sit unprofitable with the wrong kind of staff
           # on hand while `labour <trade>` shows only the wage, never
           # which of the two columns a trade lands in.
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
    # THE PRACTICE IS NOT A VENTURE, AND IT IS WHERE YOUR MONEY COMES FROM:
    # "RUNNING: nothing" next to a ledger paying real practice income reads
    # as the two screens flatly contradicting each other unless this says
    # which side the practice falls on.
    _prac_note = sim.practice_note()
    if _prac_note:
        out["your_practice_is_not_a_venture"] = (
            "%s You did not open it and you cannot close it; it is not "
            "listed here, and it is most of your income until you build "
            "something. See 'money'." % _prac_note)
    if len(_idle_ordinary) > 20:
        out["and_more_you_could_open"] = len(_idle_ordinary) - 20
    return out



def _cmd_policy(sim, nodes, cmd, ended):
    want = cmd.get("set")
    changed = {}
    if want is not None:
        if not isinstance(want, dict):
            return {"ok": False,
                    "error": 'set must be an object, e.g. '
                             '{"cmd":"policy","set":{"auto_hire":true}}'}
        for key, val in want.items():
            if key not in sim.policy:
                return {"ok": False, "error": "no such policy: %s. They are: %s"
                        % (key, ", ".join(sorted(sim.policy)))}
            sim.policy[key] = _flag(val)
            changed[key] = sim.policy[key]
    # WHICH OF THESE CAN ACTUALLY ACT TODAY: negative capital silently
    # disables both hiring and opening even while the switches read ON,
    # with the only clue otherwise being one refusal string somewhere
    # else. A switch that says ON while nothing happens is worse than one
    # that says OFF.
    _stopped = {}
    if sim.capital <= 0:
        if sim.policy.get("auto_hire"):
            _stopped["auto_hire"] = ("nothing to hire with: hiring is paid "
                                     "in advance and you are in arrears")
        if sim.policy.get("auto_open"):
            _stopped["auto_open"] = ("nothing to open with: opening a "
                                     "concern costs stock and premises")
    if sim.year < sim.credit_frozen_until:
        _stopped["credit"] = ("nobody will fund new work until %d"
                              % int(sim.credit_frozen_until))
    _pol = {"ok": True, "policy": dict(sim.policy), "changed": changed,
            # WHAT THESE ARE FOR, BEFORE WHAT EACH ONE DOES: a player who
            # switches one on believing the engine knows the best line and
            # is offering to walk it for them will read the result as a
            # bug when it is not one, unless this screen says plainly what
            # these actually are first.
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
                # SAY WHAT MIX: "grow the staff" alone does not say enough,
                # since the mix genuinely matters and is defended in code
                # - a player deciding whether to switch this on should be
                # able to read what it will do before it does it.
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
                # SAY WHAT IT WILL NOT DO - AND SAY THE EXCEPTION: an
                # ordinary shop that earns less than it costs stays shut,
                # but auto_open_ventures deliberately opens a capability
                # institution at a loss, because a school takes 2,500 a
                # year and hands back 800 and is where twelve of your
                # scholars come from, and the margin test would otherwise
                # shut it for ever. Describing only one half of that reads
                # as the automation being broken when it is doing the
                # other half correctly.
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
            # A note that reads as covering everything the game ever does
            # without being asked is too broad: a policy is something the
            # game DECIDES for you; a consequence is the world answering a
            # decision you already made, and no switch turns those off.
            "not_policies": "Some things are consequences, not automation, "
                            "and there is no switch for them: people you "
                            "cannot pay leave, mines you cannot pay for stop "
                            "being worked once your credit is gone, and "
                            "creditors take what they are owed. Those follow "
                            "from having no money, not from a setting."}
    if _stopped:
        _pol["switched_on_but_cannot_act_right_now"] = _stopped
    return _pol
