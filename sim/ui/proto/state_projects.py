"""State-reply builders for active projects, money, operations, spending and training hours."""

from .state_waiting import _agent_end_reason, _waiting_on, _worth_knowing_early
from .state_shut_staffing import shut_for_want_of_staff


def _agent_state_active_projects(sim, nodes):
    """Every project currently in progress, keyed by node id: hours spent
    and left, the bill, the abandonment countdown, what it is waiting on,
    and this year's allocator bookkeeping. Moved out of _agent_state
    unchanged - see that function's own docstring for why the assembly
    was split this way.
    """
    active = {}
    for node_id, progress in sim.active.items():
        node = nodes[node_id]
        _standing = sim.hour_standing(node_id) or (None, None, None)
        bill = progress.get("cost_left")
        _at_risk = progress.get("stalled_years", 0)
        if bill is None:
            bill = max(0.0, sim.project_cost(node_id) - progress["spent"])
        active[node_id] = {"name": node["name"], "founder_hours_left": round(progress["ph_left"], 1),
                     "founder_hours_total": node["ph"], "years_in_progress": progress["yrs"],
                     "spent": round(progress["spent"], 1), "still_to_pay": round(bill, 1),
                     # THE COUNTDOWN, WHERE IT CAN BE SEEN. It ran silently for
                     # three years and then took everything spent.
                     **({"will_be_abandoned_in_years": 4 - _at_risk,
                         "because_nobody_here_can": progress.get("blocked_on_trades")}
                        if _at_risk else {}),
                     # Say which of the three things a project is actually
                     # waiting for.
                     # WORKED OUT NOW, not read off what last year happened
                     # to record: short_of_trade is only written when a step
                     # actually ran the shortage branch, so reading it stale
                     # could report "your hours" for centuries while the
                     # founder's hours sit idle, when the real cause is a
                     # trade shortage. Telling somebody to spend hours they
                     # cannot spend is worse than saying nothing.
                     "waiting_on": _waiting_on(sim, nodes, node_id, progress, bill),
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
                     "pool_rank_this_year": _standing[0],
                     "pool_active_count_this_year": _standing[1],
                     "pool_total_this_year": _standing[2],
                     "pool_remaining_before_this_year":
                         progress.get("pool_remaining_before_this_year"),
                     "underfunded_this_year": progress.get("underfunded_this_year", False),
                     # Only present when it is underfunded, and it says
                     # why: hours offered and none effective, with nothing
                     # explaining the gap, is a shortfall in arrears with
                     # no visible cause.
                     "why_underfunded": progress.get("why_underfunded"),
                     # THE PLAYER'S OWN STANDING ORDER, READ BACK FROM THE
                     # SAME PLACE AS THE FOUR ABOVE - None when nothing was
                     # ever directed here, which keeps an undirected
                     # project's reply byte-for-byte what it always was.
                     # See `allocate` and core.py step()'s own comment on
                     # hour_allocations.
                     "hours_directed_this_year": progress.get("hours_directed_this_year"),
                     # THE LIVE RISK: what the dice use now, after any failed
                     # attempts, beside the first-attempt figure.
                     "chance_of_failure_now": sim.effective_risk(node_id),
                     "chance_of_failure_before_any_attempt": node["risk"] or None,
                     "bountied": node_id in sim.bountied}
    return active


def _agent_state_headline_money(sim, end_year):
    """year, horizon, capital, and the standing income/upkeep lines."""
    return {
        "year": sim.year,
        # HOW MUCH TIME IS LEFT: the horizon must not be announced only in
        # one help topic and nowhere in a reply anybody reads every turn.
        # A clock you cannot see is not a constraint, it is an ambush.
        "horizon_year": end_year, "years_left": max(0, end_year - sim.year),
        "capital": round(sim.capital, 1), "revenue": round(sim.revenue(), 1),
        "coin_hoard": sim.coin_hoard_report(),
        "upkeep": round(sim.upkeep(), 1),
        # Capital can fall even with both revenue and upkeep reported as
        # zero if nothing here shows where it went: living costs (food,
        # rent, tax and keeping up appearances) are charged regardless,
        # and anything that moves your money should be visible in the
        # state that claims to describe your money.
        # SPLIT, because one number under this name would otherwise be two
        # things: `living_cost` here has to report ONLY living-and-
        # appearances, separate from `wage_bill`, matching how `money`
        # already reports them as two separate lines - conflating them
        # under one label would read a growing payroll as a spiralling
        # cost of living to anyone watching only `state`, one of the four
        # screens the welcome text calls essential.
        "living_cost": round(sim.living_cost() - sim.labour.wage_bill(), 1),
        "wage_bill": round(sim.labour.wage_bill(), 1),
        "mine_operating_cost": round(sim.mine_operating_cost(), 1),
    }


def _agent_state_operations(sim, nodes):
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
        "stuck": (None if _agent_end_reason(sim) else sim.stall_diagnosis()),
        "concerns_you_run": len(sim.operating),
        "you_know_how_to_run_but_have_not_opened": sum(
            1 for node_id in sim.done if sim.is_venture(node_id) and node_id not in sim.operating),
        # WHAT THAT IS COSTING YOU, in money, on the main screen: a
        # per-completion log line saying "open it" is easily lost among
        # many others, and a count of shut shops is not a reason to act.
        # A yearly figure is.
        "shut_concerns_would_earn_a_year": round(sum(
            sim.venture_real_earnings(node_id) - sim.venture_real_upkeep(node_id) for node_id in sim.done
            if sim.is_venture(node_id) and node_id not in sim.operating
            and sim.venture_real_earnings(node_id) > sim.venture_real_upkeep(node_id)), 0) or None,
        # THE SAME GAP, for the handful of capabilities whose running()-gated
        # payout is not revenue at all - protection, standing, credit, a
        # staff ceiling - and so never showed up in shut_concerns above. This
        # is `state`, the screen a player actually rereads every year, which
        # is exactly where the corpus bug's lesson said a DONE/OPERATING
        # split has to be loud: see ProjectsMixin.capability_gaps.
        "critical_capabilities_not_operating": sim.capability_gaps() or None,
        # Which people each shut, profitable concern is short of.
        "shut_for_want_of_staff": shut_for_want_of_staff(sim, nodes),
        # Specialists on the payroll that no project or open concern uses.
        "idle_specialists": sim.labour.idle_specialists() or None,
        # Open concerns that one death would close.
        "depends_on_one_person": sim.labour.sole_supervisors() or None,
    }


def _agent_state_spend_and_net(sim):
    """This year's project spend, interest, and the two net-income figures
    (this year's actual, and the standing ordinary-year one).
    """
    return {
        # net_per_year counts the STANDING flows only, never what projects
        # consume - usually the largest outflow by far - so it can report
        # a healthy positive number while capital sits at zero, every
        # denarius going into the work in progress. A field that says you
        # are making money while you are visibly making none is worse than
        # no field, so project_spend_this_year has to sit alongside it.
        # Named for what it is. The roll happens after the spending loop, so this
        # is the year just simulated, not the one before it.
        "project_spend_this_year": round(getattr(sim, "spend_last_year", 0.0), 1),
        # INTEREST IS A COST AND BELONGS IN THE NET: arrears compound, so a
        # net that ignores them can print a positive figure while capital
        # is actually falling and accelerating - it must not tell a
        # household in a debt spiral that it is recovering.
        "interest_on_arrears_this_year": round(
            max(0.0, -sim.capital) * sim.debt_interest_rate(), 1),
        # LESS THE YEAR YOU HAVE ALREADY PAID FOR: `hire` takes a finder's
        # fee and the first year's wages in advance, and step() nets that
        # advance off the living cost it charges. This forecast has to do
        # the same, or it double-bills the first year by the whole wage
        # bill, in the one year the player is most likely to look.
        "wages_you_have_already_paid_this_year": round(
            sim.wages_prepaid, 1) or None,
        "net_after_project_spend": round(sim.revenue() - sim.upkeep() - sim.living_cost()
                                         + min(sim.living_cost(),
                                               sim.wages_prepaid)
                                         - sim.mine_operating_cost()
                                         - max(0.0, -sim.capital) * sim.debt_interest_rate()
                                         - getattr(sim, "spend_last_year", 0.0), 1),
        # THE STANDING FIGURE HAS TO READ THE STANDING REVENUE: this counts
        # "the STANDING flows only" per the comment on shut_concerns above -
        # the household's ordinary-year position, not this particular
        # year's - so it must read revenue_capacity() (economy.py), not
        # plain revenue(), which dips for a year whenever `work` sells
        # founder-hours. revenue_capacity() exists for exactly this - it
        # is what credit_limit() already reads, with the identical
        # reasoning in its own docstring ("a lender does not cut your
        # line because you took a job this year").
        "net_per_year": round(sim.recurring_net(), 1),
        # The same figure `money` prints, from the one method both read.
        "sustainable_debt": round(sim.sustainable_debt(), 1),
    }


def _agent_state_training_and_hours(sim, active, full):
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
            for row in sim.training],
        # LESS WHAT YOU HAVE ALREADY SOLD: the pool is the pool, but what is
        # FREE is the pool less the hours already spent on wage work, or
        # this would report free hours that `work` then refuses to honour.
        "founder_hours_available": round(
            max(0.0, sim.labour.director_pool() - sim.labour.director_hours_committed()), 1),
        # FREE HOURS, SHOUTED, WHEN THEY ARE GOING TO WASTE, not one quiet
        # number among fifty: running a single calendar-floor project can
        # leave thousands of founder-hours spent on nothing for a whole
        # year, and running several projects in parallel is the central
        # mechanic that fixes it (see help's "how a turn works"), so this
        # has to be surfaced loudly rather than left for a player to
        # notice by chance. Every active project's own hours are fully
        # spent for the year exactly when it is waiting on the calendar,
        # not on you - _waiting_on returns "the calendar" for precisely
        # that case - so that is the signal, not a guess at intent.
        # WHICH CONCERN SHUTS NEXT, while there is still time to hire: the
        # staffing rule closing a concern is not a policy a player can
        # switch off - it is the world taking back something nobody is
        # left to watch - and a concern that shuts itself now reopens once
        # restaffed. The year's notice matters here, not a cure.
        "supervision_close_to_the_edge": sim.staffing_closure_warnings() or None,
        # SAID ONCE, EARLY, NOT EVERY TURN: `help commands` is a complete
        # index of everything the game can do - log, values, money,
        # automation, save/load - and `log` is an exact paginated history
        # of starts, completions, failures, hazards, openings, closures and
        # staffing. Both are already true from turn one, but neither is
        # obvious without being pointed at directly. Fired once, only in
        # the first few years of a run (never on a save that is already
        # well under way), so a veteran resuming an old game is not told
        # this again on a whim - see _said_command_index in SAVE_FIELDS
        # for why it only ever fires once per game, not once per session.
        # full:true IS THE "EVERYTHING AT ONCE" POWER VIEW, already the
        # reply most often bumping its own readability ceiling (see the
        # "state full stays readable" checks) - not the screen a first
        # turn's plain `state` actually returns. Asking only there, never
        # under full:true, means the one-shot chance to say this is never
        # spent paying that screen's byte budget, and it still fires on the
        # very next ordinary `state` or `step` instead.
        **({"worth_knowing_early": _worth_knowing_early(sim)} if not full else {}),
        "free_hours_going_unused": (
            ("%s founder-hours this year are going into nothing: every "
             "project you have in hand is only waiting on the calendar "
             "now, not on you or your money. A calendar floor is not "
             "exclusive research time - start something else alongside "
             "it while it runs. 'available' or 'stuck' says what you "
             "could begin today; 'idle' splits the hours and names the delay."
             % "{:,.0f}".format(max(0.0, sim.labour.director_pool()
                                    - sim.labour.director_hours_committed())))
            if (active
                and all(value["founder_hours_left"] <= 0 for value in active.values())
                and max(0.0, sim.labour.director_pool()
                        - sim.labour.director_hours_committed()) > 200)
            # AND WHEN NOTHING IS RUNNING AT ALL, which the first branch cannot
            # see because it requires `active` to be non-empty. A player who
            # steps a year with an empty slate loses those hours exactly as
            # completely, and hours do not carry.
            else ("%s founder-hours this year are going into nothing at all: "
                  "you have no work in hand. Hours do not carry to next year. "
                  "'available' or 'stuck' says what you could begin today; 'idle' splits the hours and names the delay."
                  % "{:,.0f}".format(max(0.0, sim.labour.director_pool()
                                         - sim.labour.director_hours_committed()))
                  if (not active
                      and max(0.0, sim.labour.director_pool()
                              - sim.labour.director_hours_committed()) > 200)
                  else None)),
        "founder_hours_sold_for_wages_this_year": round(
            sim.wage_hours_this_year, 1),
        # WHERE THE HOURS COME FROM: the pool can grow well past a single
        # founder's own hours, and that has to be explained here rather
        # than left unexplained. It is not the founder working harder: it
        # is the deputies an institution gives you, each of whom directs
        # work in your name.
        "where_your_hours_come_from": {
            "you": round(sim.cfg["founder_hours_per_year"]
                         * (0.25 if sim.bondage_years_left > 0 else 1.0), 1)
                   if sim.founder_alive else 0.0,
            "deputies_who_direct_work_for_you": round(sim.directors_extra, 2),
            "hours_each_deputy_adds": sim.cfg["director_hours_per_year"],
        },
        "founder_hours_spent_teaching_this_year": round(
            sim.teaching_hours_this_year, 1),
        # LAST YEAR'S HOURS, ACCOUNTED FOR. Set in step(); see the comment
        # there. available is this year's fresh figure, not last year's -
        # read it alongside, not in place of, hours_this_year.
        "hours_this_year": getattr(sim, "hours_this_year", None),
    }
