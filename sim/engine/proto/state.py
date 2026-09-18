"""The state/status screen and the event log: what has happened, what ended the run (or why it has not), and the small per-founder and per-goal accounting behind them."""

import math, re

from ..data import closure

def _agent_end_reason(s):
    """None while the run is live; otherwise why it stopped, for state() and
    to refuse further start/stop/bounty/buy commands once it has."""
    end_year = getattr(s, "end_year", s.cfg["start_year"] + s.cfg["horizon_years"])
    if s.dead_reason:
        return s.dead_reason
    # REACHING THE GOAL IS NOT AN ENDING ANY MORE. A player who won wrote: "I
    # wanted to keep going after the transistor. I had this enormous
    # industrial/research civilization and a giant untouched tree. Stopping
    # immediately after the victory screen would waste the most developed state
    # the player has ever created." They are right, and the tree agrees with
    # them - the goal's prerequisite closure is 168 nodes of 2,833, so a won run
    # has barely touched it. The win is recorded in s.goal_year for ever and the
    # run carries on until the founder dies or the horizon arrives.
    #
    # `run` and `compare` are unaffected: Sim.run() in core.py stops at the goal
    # on its own, which is what every measurement in this repository wants and
    # what keeps a dice-free trial cheap. This is the interactive path only.
    if s.year >= end_year:
        # Under fog there IS no stated goal, so saying the player failed to reach
        # one is incoherent. A tester finished a 500 year run and was told they
        # had missed a goal they were never shown and had no way to set.
        if getattr(s, "fog", False):
            # It said "there was no target to hit", which was false: there is
            # one, `help` names it now, and telling a player at the end that
            # they were never aiming at anything is the same lie the other way
            # round.
            #
            # AND IT NEVER CHECKED s.goal_year AT ALL. A player who reached
            # the goal under fog and kept building (exactly what the block
            # comment above this function describes as the normal case now)
            # still got "did not reach %s" here, unconditionally, because
            # this branch was written before goal completion stopped being
            # an ending and never grew the same s.goal_year check the
            # non-fog branch two lines below it already has. One rule,
            # living in two places, and only one copy got the fix. Found
            # while wiring the ending score's own end_reason field to a
            # save that had, in fact, reached the goal.
            _goal_name = (s.nodes[s.goal]["name"].lower() if s.goal in s.nodes
                         else "the goal")
            if s.goal_year:
                return ("the horizon at %d AD is reached. You reached %s in "
                        "%d AD and kept building for %d years after it."
                        % (end_year, _goal_name, s.goal_year,
                           end_year - s.goal_year))
            return ("the horizon at %d AD is reached. You built %d things of your "
                    "own and did not reach %s."
                    % (end_year, len(s.done - s.granted), _goal_name))
        if s.goal_year:
            return ("the horizon at %d AD is reached. You reached %s in %d AD "
                    "and kept building for %d years after it."
                    % (end_year,
                       s.nodes[s.goal]["name"].lower() if s.goal in s.nodes
                       else "the goal", s.goal_year, end_year - s.goal_year))
        return "ran out of horizon (%d AD) without reaching the goal" % end_year
    return None


def _risk_without_the_essays(kr):
    """knowledge_risk with the hazard prose stripped, for embedding in state."""
    if not isinstance(kr, dict):
        return kr
    out = dict(kr)
    ahead = out.get("known_hazards_ahead")
    if isinstance(ahead, list):
        out["known_hazards_ahead"] = [
            {key: value for key, value in hazard.items() if key not in ("note", "what_you_can_do")}
            for hazard in ahead if isinstance(hazard, dict)]
        out["the_full_account_of_each"] = '{"cmd":"risk"}'
    return out


def _staff_fraction_note(s):
    """Why a trade count on your own STAFF is not a whole number, in one
    place - `state` and `labour` both show it and must give the same
    explanation, not two that could drift apart (this codebase's own
    signature bug). None when every count already is whole, so a
    whole-number staff gets no footnote at all.

    THESE ARE REAL PEOPLE, JUST COUNTED CONTINUOUSLY. scholars/artisans/
    employees grow and decay a little every year - hiring phases in,
    training takes years, attrition trims a few percent rather than
    killing one named person - so at any moment the total is a partial
    year's worth of one more or one fewer person, the same way a
    company's headcount can be "40.5 FTE" without anyone being cut in
    half. Arithmetic is unchanged; this only names what the number means.
    """
    if (abs(s.scholars - round(s.scholars)) < 0.02
            and abs(s.artisans - round(s.artisans)) < 0.02
            and all(abs(value - round(value)) < 0.02 for value in s.employees.values())):
        return None
    return ("these are continuous full-time-equivalents, not a count of "
            "whole people: hiring phases in, training takes years, and "
            "attrition (about 3.5%/yr) trims everyone a little rather "
            "than dismissing one person at a time. 1.32 artisans is the "
            "wage and output of one artisan plus a third of another's.")


def _waiting_on(s, nodes, k, st, bill):
    """What is ACTUALLY holding this project up, checked against today."""
    node = nodes[k]
    frac = min(1.0, 1.0 / max(1.0, node["yrs"]))
    # WHAT IS LEFT OF EACH TRADE'S TOTAL, not the flat annual figure the
    # project was once billed whether or not it was still owed. See
    # ProjectsMixin.lab_year_draw (projects.py): hired-labour hours are a
    # total drawn down over the project's life, so near the end of a trade's
    # own balance the true ask is smaller than its nominal pace, and saying
    # "short" against the bigger, already-paid-down figure would name a
    # shortfall that no longer exists.
    lab_left = st.get("lab_left") or node["lab"]
    # TWO DIFFERENT FACTS, NOT ONE. "this society can field 3.5 scribes" and
    # "the scribes here can supply 8,750 but your other work has them booked"
    # used to share one label, "nobody to do the work", and a player with
    # one chemist left after attrition could not tell, in one glance, a
    # shortage no amount of portfolio management would fix from one their
    # OWN other projects were causing by outbidding this one for the same
    # trade - which 'stop' on something else actually answers. Kept as two
    # lists so the message - and _portfolio_constraint's classification of
    # it, below - can tell them apart.
    staffing_short = []
    booked_short = []
    portfolio_demand = s.trade_demand_vs_supply()
    for trade, want in (node["lab"] or {}).items():
        need = min(want / max(1.0, node["yrs"]), lab_left.get(trade, want))
        if need <= 0:
            continue
        supply = s.hours_you_can_call_on(trade)
        total_demand = portfolio_demand.get(trade, {}).get(
            "demand_hours_this_year", need)
        if supply < need or total_demand > supply + 1e-6:
            # The society's CAPACITY is the durable fact and the one a player
            # can act on; what is left after this year's bookings is noise that
            # changes every step. Say the first, and only mention the second
            # when it is what is actually binding.
            if supply < need:
                staffing_short.append(
                    "%s (wants %.0f hours a year; this society can "
                    "field %.0f at most)" % (trade, need, max(0.0, supply)))
            elif total_demand > supply + 1e-6:
                booked_short.append(
                    "%s (wants %.0f hours a year; the %ss here can "
                    "supply %.0f but your other work has them booked)"
                    % (trade, need, trade, max(0.0, supply)))
    # BOTH, WHEN BOTH ARE TRUE, NOT JUST THE FIRST ONE FOUND. This loop already
    # knows every trade this project is short on; returning the moment
    # staffing_short had anything in it silently dropped booked_short even
    # when both were populated by the SAME loop above - a project short one
    # trade absolutely and a second only to its own other work looked, from
    # here, exactly like the first shortage was the whole story. A Han
    # playtester who fired a specialist on the strength of a single named
    # blocker found a second, undisplayed one waiting behind it. _portfolio_
    # constraint still classifies this by its leading words, so the merged
    # sentence keeps "nobody to do the work" first and unchanged.
    if staffing_short and booked_short:
        return ("nobody to do the work: " + "; ".join(sorted(staffing_short)[:3])
                + ". Also short, but only because your own other work has it "
                  "booked: " + "; ".join(sorted(booked_short)[:3]))
    if staffing_short:
        return "nobody to do the work: " + "; ".join(sorted(staffing_short)[:3])
    if booked_short:
        # A DIFFERENT SENTENCE FOR A DIFFERENT REMEDY. The society CAN field
        # this trade; it is your own other active work that has it booked.
        # Teaching or hiring more does nothing here - 'portfolio' (the
        # aggregate demand-vs-supply view) or stopping something else does.
        return "trade hours already booked: " + "; ".join(sorted(booked_short)[:3])
    if st["ph_left"] <= 0 and bill > 0.5:
        # MONEY YOU HAVE IS NOT MONEY YOU ARE SHORT OF. step() pays at most one
        # year's instalment - the cost divided by the node's calendar floor -
        # so a ten-year work absorbs a tenth of its bill a year however rich
        # you are. This said "waiting on money" to a play tester holding
        # 73,234,107 denarii against 45,448 still owed, which is not a
        # diagnosis, it is a contradiction. What they were waiting on was the
        # calendar, and nothing anywhere said there was a pace at all.
        per_year = s.project_cost(k) * frac
        if per_year > 0.5 and s.spending_power("buy") >= per_year:
            return ("the pace it can absorb money: at most %s a year goes into "
                    "this (%s still owed, about %.0f more year%s at that rate). "
                    "Money in hand cannot buy it down faster"
                    % ("{:,.0f}".format(per_year), "{:,.0f}".format(bill),
                       math.ceil(bill / per_year),
                       "" if math.ceil(bill / per_year) == 1 else "s"))
        if s.spending_power("buy") <= 0.5:
            return ("money: fully blocked until funding is available; %s is "
                    "still owed and you cannot raise any of the next %s "
                    "instalment now"
                    % ("{:,.0f}".format(bill), "{:,.0f}".format(per_year)))
        return ("money: unfunded now; will fund opportunistically as revenue "
                "arrives this year: %s still owed and the next instalment of "
                "%s is more than you can raise at this moment"
                % ("{:,.0f}".format(bill), "{:,.0f}".format(per_year)))
    if st["ph_left"] <= 0:
        return "the calendar"
    # MATERIALS. A shortage scales only projects consuming its supply pool -
    # see core.py step() 5 - so a project with
    # founder-hours still to spend and nobody short on trade or money can
    # still be making less of them than the pool alone would suggest, for a
    # reason that is neither staffing, money nor the calendar. Only said when
    # it is genuinely biting (2% is noise); resource_throttle() itself is the
    # one place that number is computed, read here rather than re-derived.
    _thr = s.project_resource_throttle(k)
    if _thr < 0.98 and s.binding:
        return ("materials: this project consumes %s, whose shortage has it "
                "running at %d%% of the pace its hours alone "
                "would allow; 'capacity' shows the shortfall"
                % (s.binding, round(_thr * 100)))
    # FOUNDER HOURS - AND WHY THIS MUCH OF THEM. Before this, a project
    # sharing the pool with ten others and one sitting alone both said the
    # identical "your hours", and a player who had already won the game
    # asked for the difference in so many words: "This project is receiving
    # 420 of your 25,000 available directed hours this year because 11
    # active projects are sharing organizational attention." The numbers
    # below are read from step()'s own bookkeeping (core.py, "pool_rank_
    # this_year" and neighbours) - never recomputed - so this sentence and
    # what actually happened cannot disagree.
    _rank = st.get("pool_rank_this_year")
    _count = st.get("pool_active_count_this_year")
    _total = st.get("pool_total_this_year")
    if _rank and _count and _count > 1:
        return ("your hours: priority #%d of %d active projects sharing "
                "this year's %s directed hours; 'portfolio' shows what "
                "each one is getting and why"
                % (_rank, _count, "{:,.0f}".format(_total or 0.0)))
    return "your hours"


def _goal_progress_count(s, nodes):
    """How many of the goal's own prerequisites you already have, with
    nothing named and not even the total - see the block comment where this
    is used in _agent_state for why the total itself has to stay withheld
    until the run ends.
    """
    goal = getattr(s, "goal", None)
    if not goal or goal not in nodes:
        return None
    need = getattr(s, "_goal_closure", None)
    if need is None:
        try:
            need = s._goal_closure = closure(nodes, goal)
        except Exception:
            return None
    return sum(1 for node_id in need if node_id in s.done)


def _founder_death_info(s):
    """When and how old the founder was when they died, or None if not.

    core.py logs "the founder dies, aged about %d" the one time it happens
    and never stores the age anywhere else - a normal-play tester in mortal
    mode found their founder's death reported as one more line among sixty
    in a long `step`'s events, with no field anywhere a script would check
    first, and the age nowhere but that sentence.

    THE ATTRIBUTES, NOT ONLY THE LOG. `log` is not itself a saved field -
    see SAVE_FIELDS - so a save taken after the founder's death and resumed
    in a new process starts that process's `s.log` empty, and scanning it
    would silently un-report an age that had already been shown once. The
    step handler sets _founder_death_aged/_founder_death_year the moment it
    sees the line, and those two ARE saved fields, so this is the fast path
    and the one that survives a resume. Scanning the log is the fallback,
    for a Sim driven straight off the engine (as the test suite does) or a
    save written before this existed.
    """
    if s.founder_alive:
        return None
    aged = getattr(s, "_founder_death_aged", None)
    if aged is not None:
        return {"year": getattr(s, "_founder_death_year", None), "aged_about": aged}
    cache = getattr(s, "_founder_death_cache", None)
    if cache is not None:
        return cache
    for year, msg in s.log:
        if "founder dies" in msg.lower():
            match = re.search(r"aged about (\d+)", msg)
            cache = {"year": year, "aged_about": int(match.group(1)) if match else None}
            s._founder_death_cache = cache
            return cache
    return None


def _worth_knowing_early(s):
    """Said once, ever, early in a run: `help commands` is the complete
    command index (log, values, money, automation, save/load and more, not
    only the five starter verbs), and `log` is an exact, paginated history of
    everything that happens from here on. Both are true from turn one, and
    neither was ever pointed at directly - the opening briefing names `help`
    in passing and lists its topics, but a player who won the whole game
    reported using specialised commands for a long while without realising
    how complete the index was, and separately flagged `log`'s depth (815
    entries by 200 AD in their run) as something worth knowing about sooner.

    ONCE, NOT EVERY TURN: gated on a flag this sets itself the first time it
    fires (see _said_command_index in SAVE_FIELDS - it has to survive a save
    or it would fire again every time a script reloads the game) and on
    still being early in the run, so resuming a save from deep into an
    existing game never springs a first-timer's tip on somebody who has long
    since found all of this themselves.
    """
    if getattr(s, "_said_command_index", False):
        return None
    if s.year > s.cfg.get("start_year", s.year) + 3:
        return None
    s._said_command_index = True
    return ("{\"cmd\":\"help\",\"topic\":\"commands\"} lists the entire "
            "command surface, not only the five you started with - log, "
            "values, money, automation, save/load and more, one line each. "
            "{\"cmd\":\"log\"} is a paginated, exact history of everything "
            "that happens from here on: starts, completions, failures, "
            "hazards, openings, closures, staffing. Both are worth a look "
            "now, before a hundred turns go by and you wish you had been "
            "reading it all along.")


def _agent_state_active_projects(s, nodes):
    """Every project currently in progress, keyed by node id: hours spent
    and left, the bill, the abandonment countdown, what it is waiting on,
    and this year's allocator bookkeeping. Moved out of _agent_state
    unchanged - see that function's own docstring for why the assembly
    was split this way.
    """
    active = {}
    for node_id, progress in s.active.items():
        node = nodes[node_id]
        bill = progress.get("cost_left")
        _at_risk = progress.get("stalled_years", 0)
        if bill is None:
            bill = max(0.0, s.project_cost(node_id) - progress["spent"])
        active[node_id] = {"name": node["name"], "founder_hours_left": round(progress["ph_left"], 1),
                     "founder_hours_total": node["ph"], "years_in_progress": progress["yrs"],
                     "spent": round(progress["spent"], 1), "still_to_pay": round(bill, 1),
                     # THE COUNTDOWN, WHERE IT CAN BE SEEN. It ran silently for
                     # three years and then took everything spent.
                     **({"will_be_abandoned_in_years": 4 - _at_risk,
                         "because_nobody_here_can": progress.get("blocked_on_trades")}
                        if _at_risk else {}),
                     # A tester poured 1,200 hours into a project that was
                     # calendar-locked and could not use them, and only noticed by
                     # reading state closely. Say which of the three things it is
                     # actually waiting for.
                     # WORKED OUT NOW, not read off what last year happened to
                     # record. short_of_trade is only written when a step
                     # actually ran the shortage branch, so a project could sit
                     # for centuries reporting "your hours" while the founder
                     # had 1,900 idle: a play tester watched `logarithms` stall
                     # from 325 AD to the horizon that way, and the real cause
                     # was 40,000 scribe-hours wanted from a society that can
                     # field three and a half scribes. Telling somebody to
                     # spend hours they cannot spend, for 275 years, is worse
                     # than saying nothing.
                     "waiting_on": _waiting_on(s, nodes, node_id, progress, bill),
                     # WHERE THIS YEAR'S HOURS WENT, for this project specifically.
                     # offered is what step() gave it a shot at; effective is
                     # how much of that actually came off founder_hours_left.
                     # The two differ when a trade or the money for it fell
                     # short - see hours_this_year for the whole year's picture.
                     "hours_offered_this_year": progress.get("hours_offered_this_year", 0.0),
                     "hours_effective_this_year": progress.get("hours_effective_this_year", 0.0),
                     # WHY THIS MUCH, READ BACK FROM THE ALLOCATOR ITSELF.
                     # core.py's step() (5. progress) writes these four onto
                     # the same st dict as it decides each project's share of
                     # the pool; `portfolio` and _waiting_on's own "your
                     # hours" sentence both read them from here, so the share
                     # a player is TOLD and the share that was actually
                     # applied are the same number by construction, not by
                     # agreement between two pieces of code that happen to
                     # compute it the same way. None before the first step()
                     # a fresh project has lived through.
                     "pool_rank_this_year": progress.get("pool_rank_this_year"),
                     "pool_active_count_this_year":
                         progress.get("pool_active_count_this_year"),
                     "pool_total_this_year": progress.get("pool_total_this_year"),
                     "pool_remaining_before_this_year":
                         progress.get("pool_remaining_before_this_year"),
                     "underfunded_this_year": progress.get("underfunded_this_year", False),
                     # Only present when it is underfunded, and it says why: a
                     # playtester in deep arrears saw hours offered and none
                     # effective, with nothing anywhere explaining the gap.
                     "why_underfunded": progress.get("why_underfunded"),
                     # THE PLAYER'S OWN STANDING ORDER, READ BACK FROM THE
                     # SAME PLACE AS THE FOUR ABOVE - None when nothing was
                     # ever directed here, which keeps an undirected
                     # project's reply byte-for-byte what it always was.
                     # See `allocate` and core.py step()'s own comment on
                     # hour_allocations.
                     "hours_directed_this_year": progress.get("hours_directed_this_year"),
                     "bountied": node_id in s.bountied}
    return active


def _agent_state_headline_money(s, end_year):
    """year, horizon, capital, and the standing income/upkeep lines."""
    return {
        "year": s.year,
        # HOW MUCH TIME IS LEFT. A weird-play tester ran to the end of a
        # five-hundred-year game and wrote that "the hidden 1800 horizon is
        # announced nowhere until you overshoot it". It was in one help topic
        # and in no reply anybody reads every turn. A clock you cannot see is
        # not a constraint, it is an ambush.
        "horizon_year": end_year, "years_left": max(0, end_year - s.year),
        "capital": round(s.capital, 1), "revenue": round(s.revenue(), 1),
        "upkeep": round(s.upkeep(), 1),
        # A playtester watched capital fall 400 to 184 on the first step with
        # nothing active and both revenue and upkeep reported as zero, and no
        # field in the protocol explained where the money went. It went on food,
        # rent, tax and keeping up appearances, which the model has always
        # charged and never showed. Anything that moves your money should be
        # visible in the state that claims to describe your money.
        # SPLIT, because one number under this name was two things. A break
        # tester proved `state.living_cost` was living_and_appearances PLUS the
        # entire payroll (224.9 + 884.2 = 1109.1, to the decimal), while `money`
        # reported those as two separate lines - the same quantity labelled two
        # incompatible ways by two commands in one program, and the misleading
        # label was on `state`, which the welcome text calls one of "the four
        # you need first". A player watching only `state` after hiring would
        # read their own payroll as their cost of living spiralling.
        "living_cost": round(s.living_cost() - s.wage_bill(), 1),
        "wage_bill": round(s.wage_bill(), 1),
        "mine_operating_cost": round(s.mine_operating_cost(), 1),
    }


def _agent_state_operations(s, nodes):
    """Whether the run has stalled, and what is sitting built but unrun."""
    return {
        # Knowing how and running it are different, so say how many you know
        # how to run and have not opened. Without this the difference is
        # invisible until a player wonders why building things stopped paying.
        # Only present when the run has effectively stopped. See stall_diagnosis.
        # NOT AFTER IT IS OVER. At the horizon this still printed "it is
        # escapable ... work for wages: you have 2000 of your own hours left
        # this year", and every action it recommended was then refused with
        # "the run has ended". Advice you cannot take is not advice.
        "stuck": (None if _agent_end_reason(s) else s.stall_diagnosis()),
        "concerns_you_run": len(getattr(s, "operating", ())),
        "you_know_how_to_run_but_have_not_opened": sum(
            1 for node_id in s.done if s.is_venture(node_id) and node_id not in s.operating),
        # WHAT THAT IS COSTING YOU, in money, on the main screen. A play tester
        # built twenty concerns, left them all shut for twenty-five years and
        # watched their income sit flat: the per-completion line saying "open
        # it" was one line in a log full of them, and a count of shut shops is
        # not a reason to act. A yearly figure is.
        "shut_concerns_would_earn_a_year": round(sum(
            nodes[node_id]["rev"] - nodes[node_id]["up"] for node_id in s.done
            if s.is_venture(node_id) and node_id not in s.operating
            and nodes[node_id]["rev"] > nodes[node_id]["up"]), 0) or None,
        # THE SAME GAP, for the handful of capabilities whose running()-gated
        # payout is not revenue at all - protection, standing, credit, a
        # staff ceiling - and so never showed up in shut_concerns above. This
        # is `state`, the screen a player actually rereads every year, which
        # is exactly where the corpus bug's lesson said a DONE/OPERATING
        # split has to be loud: see ProjectsMixin.capability_gaps.
        "critical_capabilities_not_operating": s.capability_gaps() or None,
    }


def _agent_state_spend_and_net(s):
    """This year's project spend, interest, and the two net-income figures
    (this year's actual, and the standing ordinary-year one).
    """
    _standing_revenue = s.revenue_capacity()
    _standing_upkeep = s.upkeep()
    _standing_living = s.living_cost(
        _rev=_standing_revenue, _upkeep=_standing_upkeep)
    return {
        # net_per_year counts the STANDING flows only. It never counted what
        # projects consume, which is usually the largest outflow by far, so a
        # playtester watched it report a healthy positive number for eight
        # consecutive years while capital sat at exactly 0.0, every denarius
        # going into the work in progress. A field that says you are making
        # money while you are visibly making none is worse than no field.
        # Named for what it is. The roll happens after the spending loop, so this
        # is the year just simulated, not the one before it.
        "project_spend_this_year": round(getattr(s, "spend_last_year", 0.0), 1),
        # INTEREST IS A COST AND BELONGS IN THE NET. A weird-play tester read
        # "+9.5 a year" for years while their capital fell 105, then 117,
        # accelerating - with the interest rate printed two lines below on the
        # same screen. Arrears compound; a net that ignores them tells a
        # household in a debt spiral that it is recovering.
        "interest_on_arrears_this_year": round(
            max(0.0, -s.capital) * s.debt_interest_rate(), 1),
        # LESS THE YEAR YOU HAVE ALREADY PAID FOR. `hire` takes a finder's fee
        # and the first year's wages in advance, and step() correctly nets that
        # advance off the living cost it charges - but this forecast did not,
        # so it billed the same year twice. A break tester hired four artisans,
        # read "Net/yr after it: -1,097", stepped once, and lost 61. Off by the
        # whole wage bill, in the one year the player is most likely to look.
        "wages_you_have_already_paid_this_year": round(
            getattr(s, "wages_prepaid", 0.0), 1) or None,
        "net_after_project_spend": round(s.revenue() - s.upkeep() - s.living_cost()
                                         + min(s.living_cost(),
                                               getattr(s, "wages_prepaid", 0.0))
                                         - s.mine_operating_cost()
                                         - max(0.0, -s.capital) * s.debt_interest_rate()
                                         - getattr(s, "spend_last_year", 0.0), 1),
        # THE STANDING FIGURE HAS TO READ THE STANDING REVENUE. This counts
        # "the STANDING flows only" per the comment on shut_concerns above -
        # the household's ordinary-year position, not this particular year's
        # - and was reading plain revenue(), which dips for a year whenever
        # `work` sells founder-hours: a player who sold hours watched this
        # swing to -193/yr and revert the moment the calendar rolled over.
        # revenue_capacity() (economy.py) exists for exactly this - it is
        # what credit_limit() already reads, with the identical reasoning in
        # its own docstring ("a lender does not cut your line because you
        # took a job this year") - and this field claimed to be the same
        # kind of number without actually being computed as one.
        "net_per_year": round(_standing_revenue - _standing_upkeep
                              - _standing_living
                              + min(_standing_living,
                                    getattr(s, "wages_prepaid", 0.0))
                              - s.mine_operating_cost()
                              - max(0.0, -s.capital) * s.debt_interest_rate(), 1),
    }


def _agent_state_training_and_hours(s, active, full):
    """Where this year's founder-hours are going: training in the
    pipeline, what is still free, the one-time command-index tip, and the
    loud warning when hours are about to go to waste.
    """
    return {
        # Rows are [capacity, ready_year] for people bought and trained, and
        # [0, ready_year, trade, count] for a trade being taught, so read by
        # index. Unpacking two names off a four-wide row killed `state` outright
        # the moment anybody used `train`.
        "training_pending": [
            {"artisan_capacity": round(row[0], 2), "ready_year": row[1],
             "trade": (row[2] if len(row) > 2 else None),
             "people": (row[3] if len(row) > 3 else None)}
            for row in getattr(s, "training", [])],
        # LESS WHAT YOU HAVE ALREADY SOLD. A break tester worked 2,300 hours as
        # a scholar, was told "hours left: 0" by the work reply, and then read
        # "2,400 founder-hours free this year" in state and on the prompt in the
        # same breath - and was refused one more hour for having none. The pool
        # is the pool; what is FREE is the pool less the hours already spent on
        # wage work.
        "founder_hours_available": round(
            max(0.0, s.director_pool() - s.director_hours_committed()), 1),
        # FREE HOURS, SHOUTED, WHEN THEY ARE GOING TO WASTE, not one quiet
        # number among fifty. A blind playthrough treated a long
        # calendar-floor project as though it were the active research,
        # even with thousands of founder-hours spent on nothing that year,
        # and only started running several projects in parallel after an
        # outside hint changed the run materially - their own account calls
        # it probably decisive. This is the central mechanic of the game
        # (see help's "how a turn works") and nothing taught it. Every
        # active project's own hours are fully spent for the year exactly
        # when it is waiting on the calendar, not on you - _waiting_on
        # returns "the calendar" for precisely that case - so that is the
        # signal, not a guess at intent.
        # WHICH CONCERN SHUTS NEXT, while there is still time to hire. The
        # staffing rule closing a concern is not a policy a player can switch
        # off - it is the world taking back something nobody is left to watch -
        # and a concern that shuts itself now reopens once restaffed. What three
        # players still asked for was the year's notice, not the cure.
        "supervision_close_to_the_edge": s.staffing_closure_warnings() or None,
        # SAID ONCE, EARLY, NOT EVERY TURN. The opening briefing already names
        # `help` and lists its topics in passing, but a player who won the
        # whole game reported using specialised commands for a long while
        # without realising `help commands` was a complete index of
        # everything the game can do - log, values, money, automation,
        # save/load - and separately flagged `log` itself, an exact paginated
        # history of starts, completions, failures, hazards, openings,
        # closures and staffing, as something they wished they had leaned on
        # from the start rather than discovering was this thorough only after
        # hundreds of entries had piled up. Both are already true from turn
        # one; neither was ever pointed at directly. Fired once, only in the
        # first few years of a run (never on a save that is already well
        # under way), so a veteran resuming an old game is not told this
        # again on a whim - see _said_command_index in SAVE_FIELDS for why it
        # only ever fires once per game, not once per session.
        # full:true IS THE "EVERYTHING AT ONCE" POWER VIEW, already the
        # reply most often bumping its own readability ceiling (see the
        # "state full stays readable" checks) - not the screen a first
        # turn's plain `state` actually returns. Asking only there, never
        # under full:true, means the one-shot chance to say this is never
        # spent paying that screen's byte budget, and it still fires on the
        # very next ordinary `state` or `step` instead.
        **({"worth_knowing_early": _worth_knowing_early(s)} if not full else {}),
        "free_hours_going_unused": (
            ("%s founder-hours this year are going into nothing: every "
             "project you have in hand is only waiting on the calendar "
             "now, not on you or your money. A calendar floor is not "
             "exclusive research time - start something else alongside "
             "it while it runs. 'available' or 'stuck' says what you "
             "could begin today."
             % "{:,.0f}".format(max(0.0, s.director_pool()
                                    - s.director_hours_committed())))
            if (active
                and all(value["founder_hours_left"] <= 0 for value in active.values())
                and max(0.0, s.director_pool()
                        - s.director_hours_committed()) > 200)
            # AND WHEN NOTHING IS RUNNING AT ALL, which the first branch cannot
            # see because it requires `active` to be non-empty. A player who
            # steps a year with an empty slate loses those hours exactly as
            # completely, and hours do not carry.
            else ("%s founder-hours this year are going into nothing at all: "
                  "you have no work in hand. Hours do not carry to next year. "
                  "'available' or 'stuck' says what you could begin today."
                  % "{:,.0f}".format(max(0.0, s.director_pool()
                                         - s.director_hours_committed()))
                  if (not active
                      and max(0.0, s.director_pool()
                              - s.director_hours_committed()) > 200)
                  else None)),
        "founder_hours_sold_for_wages_this_year": round(
            getattr(s, "wage_hours_this_year", 0.0), 1),
        # WHERE THE HOURS COME FROM. A play tester watched their year grow from
        # 2,000 hours to 6,090 over a long run with nothing anywhere saying
        # why. It is not the founder working harder: it is the deputies an
        # institution gives you, each of whom directs work in your name.
        "where_your_hours_come_from": {
            "you": round(s.cfg["founder_hours_per_year"]
                         * (0.25 if s.bondage_years_left > 0 else 1.0), 1)
                   if s.founder_alive else 0.0,
            "deputies_who_direct_work_for_you": round(s.directors_extra, 2),
            "hours_each_deputy_adds": s.cfg["director_hours_per_year"],
        },
        "founder_hours_spent_teaching_this_year": round(
            getattr(s, "teaching_hours_this_year", 0.0), 1),
        # LAST YEAR'S HOURS, ACCOUNTED FOR. Set in step(); see the comment
        # there. available is this year's fresh figure, not last year's -
        # read it alongside, not in place of, hours_this_year.
        "hours_this_year": getattr(s, "hours_this_year", None),
    }


def _agent_state_founder(s):
    """Alive or not, and if not, when and how old - plus the two staff
    headline counts that sit next to it on the same screen.
    """
    return {
        "founder_alive": s.founder_alive,
        # THE AGE ITSELF, AS A FIELD, not only inside a log sentence a script
        # would have to parse. See _founder_death_info.
        "founder_died_aged": (_founder_death_info(s) or {}).get("aged_about"),
        "founder_died_in": (_founder_death_info(s) or {}).get("year"),
        "scholars": round(s.scholars, 2), "artisans": round(s.artisans, 2),
        "directors_extra": round(s.directors_extra, 2),
    }


def _agent_state_standing(s):
    """Reputation, scandal, eminence and the other soft-power gauges,
    literacy and its ceilings, and how far what you built has diffused.
    """
    # WHAT YOU BUILT HAS CHANGED THE COUNTRY - see SocietyMixin.
    # world_diffusion_report (society.py). Computed once here, gated to
    # None while dormant, so a fresh game's `state full` reply (already the
    # reply most often bumping the "state full stays readable" byte budget)
    # pays nothing for a mechanism that has not fired yet - same pattern as
    # _worth_knowing_early just below.
    _wd = s.world_diffusion_report()
    return {
        # NO "suspicion" FIELD. It was replaced by `scandal` (see core.py: "doing
        # something a society cannot explain is alarming; doing a lot of
        # ordinary things over decades is not"), and the attribute has been set
        # to 0.0 at startup and never written since. Two testers watched it read
        # exactly 0.0 for five hundred years - one with 388 employees and a
        # paved road network - and concluded the social-danger system never
        # fires. What never fired was a vestige. Reporting a dead number every
        # turn is worse than not having it: it teaches the player that a live
        # mechanic is broken.
        "reputation": round(s.reputation, 1),
        "scandal": round(s.scandal, 2), "eminence": round(s.eminence, 2),
        "protection": round(s.protection, 3), "familiarity": round(s.familiarity, 3),
        # HOW EDUCATED THIS SOCIETY IS, AND HOW FAR THAT COULD GO. Answering
        # the user's own question - "can I create a 90%+ literate
        # population" - needs the ceiling shown alongside the current
        # figure, not just the figure alone: a founder watching
        # literacy_general climb with no sense of where it stops cannot tell
        # a slow success from a mechanism that has already maxed out. See
        # SocietyMixin.literacy_ceiling_general/_elite and agrarian_slack
        # (society.py).
        "literacy": {
            "general": round(float(s.civ.get("literacy_general", 0.0)), 3),
            "general_ceiling_now": round(s.literacy_ceiling_general(), 3),
            "elite": round(float(s.civ.get("literacy_elite", 0.0)), 3),
            "elite_ceiling": round(s.literacy_ceiling_elite(), 3),
            "schools_actually_teaching": s._schooling_flow() > 0.0,
            "farm_labour_freed_by_mechanisation": round(s.agrarian_slack(), 3),
        },
        # HOW MUCH OF WHAT YOU RUN HAS LEAKED TO COMPETITORS. See
        # SocietyMixin.diffusion_share/diffusion_index (society.py) for what
        # moves this; it is not yet spent anywhere in this engine's own
        # pricing, only reported, because that spending is another agent's
        # seam to wire in (see that function's own docstring).
        "diffusion_index": round(s.diffusion_index(), 3),
        # THE COUNTRY, NOT ONLY YOUR OWN MARKET SHARE. Present only once
        # something the founder built has actually begun to spread - see
        # world_diffusion_report's own docstring for the None gate.
        **({"world_diffusion": _wd} if _wd else {}),
    }


def _agent_state_progress(s, active):
    """What is done versus granted, the active projects themselves, staff
    and trades, and the household and policy figures that go with them.
    """
    return {
        # A playtester could not tell the difference between technologies the
        # society already had and ones they had earned: about 140 nodes complete
        # in year one and appeared in done_count as if the player had built
        # them. Separate the two, because "you have 140 technologies" and "you
        # have built 3 technologies" are very different situations.
        "done_count": len(s.done),
        "done_granted": len(s.granted & s.done),
        "done_earned": len(s.done - s.granted),
        "active": active,
        # A tester spent 284 years with scholars frozen at 1.0 and artisans
        # plateaued, and wrote that they never found any way to grow either. The
        # remedy was only ever mentioned in a refusal message, so a player who
        # never happened to try a staff-gated project never saw it at all. Staff
        # is not a technical prerequisite, so it appears in no dependency list
        # either. Tell them unprompted.
        "how_to_grow_staff": {
            "scholars": s._staff_advice("scholars"),
            "artisans": s._staff_advice("artisans"),
        },
        "where_the_money_comes_from": s.revenue_sources(),
        "employees": {trade: round(value, 2) for trade, value in sorted(s.employees.items()) if value > 0.005},
        "employees_total": round(sum(s.employees.values()), 2),
        "household_places_used_of_all": "%.1f of %.1f"
            % (s.headcount(), s.headcount() + max(0.0, s.household_room())),
        "annual_wage_bill": round(s.wage_bill(), 1),
        # WHAT THE PROMPT'S sch/art MEAN. Those two figures count yourself and
        # any hours you have bought, so the prompt can read "sch 1 art 1" on a
        # turn where you employ nobody - and a play tester who saw that beside
        # "EMPLOY: 0 people" reported it as the game losing count. Both are
        # right; they are answering different questions, and this says so.
        "what_you_can_field": (
            "counting yourself and hours you have bought: %.1f scholars and "
            "%.1f craft hands. That pair is what the prompt shows and what "
            "'why' and 'start' test a project against; the count above is "
            "people on your payroll."
            % (s.effective_scholars(), s.craft_hands_available())),
        # FRACTIONS ARE REAL, NOT A DISPLAY GLITCH. A tester reported "1.32
        # artisans" and "0.07 engineers" as if something had gone wrong. It
        # had not: staff grow and decay gradually (hiring phases in, training
        # takes years, attrition is a yearly 3.5%), so at any given moment a
        # trade you have IS a partial year's worth of one more or one fewer
        # person, the same way a company's headcount can be "40.5 FTE". Said
        # only when it would actually be confusing - a whole-number staff
        # needs no footnote.
        # _staff_fraction_note, NOT A SECOND COPY OF THIS EXPLANATION - see
        # its own docstring. `labour` shows the identical fractional counts
        # and must say the identical thing about them.
        "staff_are_fractional_because": _staff_fraction_note(s),
        "trades_you_created": sorted(s.trades_created),
        # WHICH OF THOSE THE SOCIETY NOW SUPPLIES ON ITS OWN. See
        # SocietyMixin.advance_society (society.py): once a taught trade has
        # been established long enough, with schools actually running, it
        # stops being only the founder's secret.
        "trades_society_now_has_on_its_own": sorted(s.trades_endemic),
        "mothballed": sorted(getattr(s, "mothballed", set())),
        "policy": dict(s.policy),
        "in_bondage_for_debt": round(getattr(s, "bondage_years_left", 0.0), 1),
        "debt_still_to_work_off": round(getattr(s, "bondage_debt", 0.0), 1),
    }


def _agent_state_risk_and_pressure(s):
    """The court's jealousy and the treasury's attention, credit and
    debt, the knowledge-loss risk, the scandal clock, and the physical
    resource figures (throttle, forest, mines, unfree labour).
    """
    return {
        # HOW CLOSE YOU ARE TO BEING DESTROYED FOR BEING TOO LARGE, and what
        # changes it. `eminence` was reported as a bare number with no threshold,
        # no trend and no lever, so a player sat at 24.9 against a danger line of
        # 26 with nothing telling them they were one bad year from the end. At a
        # successful late game the equilibrium lands within five per cent of the
        # threshold, which makes the outcome a coin toss decided by noise rather
        # than by anything the player chose. The mechanic is sound and the
        # levers are real - a dispersed academy network cuts it by a third, and
        # getting close to the throne raises it by half - but neither was
        # visible, and an unseen lever is not a choice.
        "prominence": s.eminence_report(),
        # THE OTHER HALF OF BEING LARGE. eminence_report() above is the
        # court's jealousy of a great man; this is the treasury's own
        # interest in a large enterprise - requisition, a pressed office, a
        # demand for military supply, and confiscation as a tail risk at the
        # top of the same scale - which used to not exist at all: a player
        # who had already won with 691 employees and 1.1 billion denarii
        # found the state had never once reacted to any of it. See
        # SocietyMixin.state_pressure_report (society.py).
        "state_attention": s.state_pressure_report(),
        "credit_limit": round(s.credit_limit(), 1),
        "debt_interest_rate": round(s.debt_interest_rate(), 4),
        "interest_paid_total": round(getattr(s, "interest_paid", 0.0), 1),
        # WITHOUT THE HISTORY ESSAYS. Each dated hazard now carries a real
        # historical note, several of them a couple of hundred words, and
        # embedding the lot here took one `state full` reply to nearly twenty
        # thousand bytes - the exact wall this reply was split up to stop
        # producing. The numbers stay; the prose lives in `risk`, which is the
        # command you type when you want it.
        "knowledge_risk": _risk_without_the_essays(s.knowledge_risk()),
        # THE OTHER HAZARD THAT ENDS THE RUN, on the same screen as the one that
        # already explains itself. See step() 6.
        "scandal_danger": s.cfg["suspicion_danger"],
        "chance_of_being_denounced_this_year": round(
            max(0.0, (s.scandal - s.cfg["suspicion_danger"]) / 60.0), 4),
        # AND WHICH WAY IT IS GOING. The chance above is computed from where
        # scandal stands now, and the roll happens after a year in which it
        # moves - so the figure is honest about today and says nothing about
        # the step you are about to take. A tester crossed from 21.9 to 29 and
        # was denounced inside one step, having last read "0%".
        "scandal_now": round(s.scandal, 1),
        "scandal_rose_by_last_year": (
            round(s.scandal - s.scandal_last_year, 1)
            if getattr(s, "scandal_last_year", None) is not None else None),
        "years_until_scandal_crosses_the_line": (
            int(max(0.0, (s.cfg["suspicion_danger"] - s.scandal))
                / (s.scandal - s.scandal_last_year)) + 1
            if (getattr(s, "scandal_last_year", None) is not None
                and s.scandal - s.scandal_last_year > 0.05
                and s.scandal < s.cfg["suspicion_danger"]) else None),
        "resource_throttle": round(s.throttle, 3), "throttle_binding": s.binding,
        "forest_ha": round(s.forest_ha, 1),
        "mine_capacity": {material: round(value, 1) for material, value in s.mine_capacity.items()},
        "slaves": s.slaves, "freedmen": s.freedmen,
        "scholars_including_you": round(s.effective_scholars(), 2),
    }


def _agent_state_goal(s, nodes, end_reason):
    """The goal itself (fog-safe), whether and when it was reached, and
    whether the run itself has ended.
    """
    return {
        "founder_ages": not s.cfg.get("immortal", True),
        "goal": None if getattr(s, "fog", False) else s.goal,
        # The NAME, not the id, so it survives fog without handing back the
        # prerequisite crawl the visibility guard exists to stop.
        "goal_in_words": (s.nodes[s.goal]["name"]
                          if getattr(s, "goal", None) in s.nodes else None),
        "goal_reached": s.goal_year is not None, "goal_year": s.goal_year,
        # THE FOG-SAFE VERSION OF final_report's "146 nodes in all; you had
        # 122" - a tester called that the most useful line in the game, and
        # it is withheld until the run ends on purpose: the TOTAL is the size
        # of the tree's own spoiler surface (same reasoning as
        # downstream_count being hidden for a single node, just applied to
        # the whole road at once). So during play this says only how many of
        # the road's nodes you already have, never how many there are in
        # all and never which ones remain - you get a sense of progress
        # without being handed a map.
        "on_the_road_to_the_goal_so_far": (
            _goal_progress_count(s, nodes) if getattr(s, "fog", False) else None),
        "fog_of_war": getattr(s, "fog", False),
        "manual": s.manual, "ended": end_reason is not None, "end_reason": end_reason,
    }


def _agent_state_shorten(out, full):
    """`full:false` (the default): fold the heaviest blocks down to a
    pointer at the command that shows them in full, so an ordinary
    `state` stays short. See the comment above for why - unchanged from
    when this lived inline in _agent_state.
    """
    # A SHORT REPLY BY DEFAULT. `state` had grown to 55 fields and four
    # kilobytes, two of them a hazard briefing repeated verbatim on every single
    # call, and a tester said reading it back "made me double-check arithmetic
    # more than once". The three heaviest blocks now have commands of their own,
    # so you read them when you want them instead of every turn.
    if not full:
        moved = {"knowledge_risk": "risk", "how_to_grow_staff": "labour",
                 "policy": "policy", "where_the_money_comes_from": "money",
                 "training_pending": "labour"}
        elided = []
        for field, where in moved.items():
            if field in out:
                if field == "knowledge_risk":
                    knowledge_risk = out[field]
                    haz = [hazard["name"] for hazard in knowledge_risk.get("known_hazards_ahead", [])
                           if hazard.get("in_progress")]
                    out["at_risk"] = {
                        "technologies_you_could_lose": knowledge_risk.get("technologies_at_risk"),
                        "hedged_by": knowledge_risk.get("hedged_by"),
                        "happening_now": haz or None,
                        "hazards_still_ahead": len(knowledge_risk.get("known_hazards_ahead", [])),
                        "in_full": '{"cmd":"risk"}'}
                elif field == "training_pending" and out[field]:
                    out["in_training"] = len(out[field])
                del out[field]
                elided.append('%s -> {"cmd":"%s"}' % (field, where))
        # THE ONE COMMAND FOR "WHY AM I NOT GETTING ON", advertised where a
        # player will see it every turn. Three testers described the same
        # ninety- to two-hundred-and-fifty-year stalls and each found the cause
        # by typing `why` at a guess.
        elided.append('why_you_are_not_getting_on -> {"cmd":"stuck"}')
        out["also_available"] = elided
        out["everything_at_once"] = '{"cmd":"state","full":true}'
    return out


def _agent_state(s, nodes, cmd=None):
    """The JSON state reply: the single most-used command in the
    protocol, and the one an agent player reads every turn.

    Split into one function per concern, the same pattern _node_explain
    uses in techtree.py: each _agent_state_* helper returns its own
    dict and decides nothing about any other section, and this function
    only assembles their pieces, via out.update(), in the exact order
    the fields used to appear in when this was one long dict literal.
    """
    active = _agent_state_active_projects(s, nodes)
    end_reason = _agent_end_reason(s)
    full = bool((cmd or {}).get("full"))
    end_year = getattr(s, "end_year", s.cfg["start_year"] + s.cfg["horizon_years"])
    out = {}
    out.update(_agent_state_headline_money(s, end_year))
    out.update(_agent_state_operations(s, nodes))
    out.update(_agent_state_spend_and_net(s))
    # free_hours_going_unused (among the rest of this section's fields) is
    # produced by this call, inside _agent_state's own call graph, not by a
    # screen-specific layer wrapped around 'state' alone - see
    # test_parallelism_note.py's own check that `step`'s reply, which is
    # built from this exact same _agent_state() call, gets it too.
    out.update(_agent_state_training_and_hours(s, active, full))
    out.update(_agent_state_founder(s))
    out.update(_agent_state_standing(s))
    out.update(_agent_state_progress(s, active))
    out.update(_agent_state_risk_and_pressure(s))
    out.update(_agent_state_goal(s, nodes, end_reason))
    return _agent_state_shorten(out, full)


# A LOG LINE A PLAYER WOULD CALL BAD NEWS. Eleven rounds of playtesting kept
# coming back to the same complaint in different words - "failures are
# silent" - and the engine's own self.log already records every one of them,
# in the founder's own words, with no field anywhere marking which lines are
# the bad ones. Matched on the actual wording every append site already uses
# (self.log.append across core.py, projects.py, economy.py and society.py),
# not reinvented here.
_FAILURE_MARKERS = (
    "FAILED", "HALTED", "ABANDONED", "CREDIT EXHAUSTED", "CLOSE TO THE LIMIT",
    "IN ARREARS", "in arrears", "INSOLVENCY", "BONDAGE", "cannot go on",
    "cannot pay everyone", "SHORT OF", "nobody left to keep an eye",
    "disperses", "sacked", "KNOWLEDGE LOST", "destroyed", "confiscated",
    "founder dies", "RUN ENDS", "MOTHBALLED",
)


def _is_failure_line(msg):
    # CASE-INSENSITIVELY, because these markers are prose and prose gets
    # rewritten. The founder's death line was recapitalised to say what the
    # death MEANS rather than only that it happened, and silently stopped
    # being a failure line here, in `log failures`, which is the one screen a
    # player checks to find out what went wrong.
    _low = msg.lower()
    return any(marker.lower() in _low for marker in _FAILURE_MARKERS)


def _log_scrub(s, text):
    """A log line, with anything the player cannot currently see redacted.

    self.log stores what happened IN THE YEAR IT HAPPENED, in plain English,
    and can go on naming a thing for centuries after fog would refuse to
    answer `why` about it - either because a sacking took it away (see
    knowledge_risk's `forgotten`) or, for a hazard's own advice, because it
    names a hedge the player never found. `fog_scrub` already strips ids out
    of a message; most of this engine's own log lines name the thing, not the
    id - "completed: Horizontal loom", not "completed: tex_horizontal_loom" -
    so this also strips NAMES of anything not currently visible.
    """
    text = s.fog_scrub(text)
    if not getattr(s, "fog", False) or not text:
        return text
    memo = {}
    for node_id, node in s.nodes.items():
        node_name = node.get("name")
        if node_name and node_name in text and not s.is_visible(node_id, _memo=memo):
            text = text.replace(
                node_name, "something you have since forgotten"
                    if node_id in (getattr(s, "forgotten", None) or {}) else
                    "something you have not heard of")
    return text


def _agent_log_parse_filters(cmd):
    """The which-lines filters from the raw cmd dict: whether to keep
    only failure lines, a lowercase search term, and a since/before year
    range. Garbage input is tolerated the same way the inline parsing
    inside _agent_log always did - a bad since/before falls back to None.
    """
    only_fail = bool(cmd.get("failures")
                     or str(cmd.get("only") or "").strip().lower() in
                        ("failures", "failure", "fails", "fail"))
    find = str(cmd.get("find") or cmd.get("search") or "").strip().strip('"\'').lower()
    try:
        since = int(cmd["since"]) if str(cmd.get("since", "")).strip() not in ("", "None") else None
    except (TypeError, ValueError):
        since = None
    try:
        before = int(cmd["before"]) if str(cmd.get("before", "")).strip() not in ("", "None") else None
    except (TypeError, ValueError):
        before = None
    return only_fail, find, since, before


def _agent_log_parse_paging(cmd):
    """Sort order, page size and offset from the raw cmd dict, with the
    hard cap on `limit` that keeps a single reply from ever dumping the
    whole log.
    """
    order = str(cmd.get("order") or "newest").strip().lower()
    if order not in ("newest", "oldest"):
        order = "newest"
    try:
        limit = int(cmd.get("limit", 20))
    except (TypeError, ValueError):
        limit = 20
    # THE HARD CAP THAT MAKES "NEVER DUMPED IN ONE GO" TRUE REGARDLESS OF WHAT
    # IS ASKED FOR. Every other paged screen in this game trusts `limit` to
    # whatever a script asks; this one cannot, because the failure mode this
    # command exists to prevent - a reply so large it overflows a reader's
    # context - is exactly what a script asking for {"limit":100000} would
    # otherwise get.
    limit = max(1, min(limit, 100))
    try:
        offset = max(0, int(cmd.get("offset", 0)))
    except (TypeError, ValueError):
        offset = 0
    return order, limit, offset


def _agent_log_filter_rows(log, since, before, only_fail):
    """The since/before year range and the failures-only filter, applied
    in that order to every (index, (year, msg)) row of the log.
    """
    rows = list(enumerate(log))
    if since is not None:
        rows = [row for row in rows if row[1][0] >= since]
    if before is not None:
        rows = [row for row in rows if row[1][0] <= before]
    if only_fail:
        rows = [row for row in rows if _is_failure_line(row[1][1])]
    return rows


def _agent_log_search_rows(s, rows, find, order):
    """The free-text search filter, confirmed against what fog actually
    lets the player see. Split from _agent_log_filter_rows because this
    filter alone needs the fog recheck below it - see its own comment.
    """
    if find:
        # CHEAP FIRST, then confirmed against what fog actually lets the
        # player see. A search that only matched a name fog is about to
        # redact would otherwise report "3 lines mention X" as proof
        # something called X exists, which is the same leak the visibility
        # guard on `why` exists to close, reached from a different command.
        rows = [row for row in rows if find in row[1][1].lower()]
        if getattr(s, "fog", False):
            # THE RECHECK IS THE EXPENSIVE HALF, one node sweep per candidate
            # line, so a common word over a run's whole history could be
            # thousands of sweeps. Capped to the most recent slice, which is
            # also the one this command defaults to showing: a search that
            # matches more than this has to narrow the word, the same as a
            # search with no fog concern at all would still have to page.
            _cap = rows[-2000:] if order != "oldest" else rows[:2000]
            rows = [row for row in _cap if find in _log_scrub(s, row[1][1]).lower()]
    return rows


def _agent_log_page(s, rows, order, offset, limit):
    """Order, then slice out the requested page, then scrub each
    surviving line for fog. Returns the total row count (before paging)
    and the page's own entries.
    """
    total = len(rows)
    ordered = list(reversed(rows)) if order == "newest" else rows
    page = ordered[offset:offset + limit]
    entries = [{"year": year, "what": _log_scrub(s, msg)} for _idx, (year, msg) in page]
    return total, entries


def _agent_log_reply(log, total, offset, entries, find, only_fail, since, before, order):
    """Assemble the JSON reply around one page of entries: the count,
    the human-readable "showing" line, "more" when there is another
    page, and a note when the log or the filtered result is empty.

    len(entries) stands in for the original len(page): _agent_log_page
    builds entries one-for-one from page, never dropping a row, so the
    two lengths are always equal.
    """
    out = {"ok": True, "count": total,
           "showing": ("nothing" if not entries else
                      "%d-%d of %d, %s first"
                      % (offset + 1, offset + len(entries), total, order)),
           "entries": entries}
    if offset + len(entries) < total:
        out["more"] = ('%d more; ask again with "offset": %d'
                       % (total - offset - len(entries), offset + len(entries)))
    if not log:
        out["note"] = "nothing has happened yet"
    elif not entries and (find or only_fail or since is not None or before is not None):
        out["note"] = "nothing in your history matches that."
    # DISCOVERABLE ON THE SCREEN ITSELF, not only in `help`. A naive player
    # is not going to guess that this command takes filters at all.
    out["to_filter_or_sort"] = (
        "add 'failures':true for only what went wrong, 'find' to search, "
        "'since'/'before' for a year range, 'order':'oldest' to read forward "
        "from the start instead of back from now, and 'offset' to page "
        "through to the end.")
    return out


def _agent_log(s, cmd=None):
    """The player's own history: what they did, and what followed from it.

    The commonest complaint across eleven rounds of playtesting was some
    version of "failures are silent" - a project stalling, a concern closing
    for want of staff, a hazard landing - none of it visible anywhere once
    the turn it happened had scrolled past. The engine has always kept every
    one of these in self.log; there was simply no command to read it back.

    NEVER THE WHOLE THING. A run of any length runs to tens of thousands of
    lines, more than an agent's whole context window, so this always pages
    and defaults to a recent window - `limit` is hard-capped, not merely
    suggested, and there is no `all:true` here the way `available` has one.
    """
    cmd = cmd or {}
    log = list(getattr(s, "log", None) or [])
    only_fail, find, since, before = _agent_log_parse_filters(cmd)
    order, limit, offset = _agent_log_parse_paging(cmd)
    rows = _agent_log_filter_rows(log, since, before, only_fail)
    rows = _agent_log_search_rows(s, rows, find, order)
    total, entries = _agent_log_page(s, rows, order, offset, limit)
    return _agent_log_reply(log, total, offset, entries, find, only_fail, since, before, order)
