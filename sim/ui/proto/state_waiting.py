"""What ended the run, what a project is waiting on, and the founder death and goal progress helpers behind the state screen."""

import sim.engine.ui_port as ui_port
import math, re
from sim.engine.ui_port import closure


def _agent_end_reason(sim):
    """None while the run is live; otherwise why it stopped, for state() and
    to refuse further start/stop/bounty/buy commands once it has."""
    end_year = getattr(sim, "end_year", sim.cfg["start_year"] + sim.cfg["horizon_years"])
    if sim.dead_reason:
        return sim.dead_reason
    # REACHING THE GOAL IS NOT AN ENDING: the goal's prerequisite closure
    # is 168 nodes of 2,833, so a won run has barely touched the tree, and
    # stopping immediately after the victory screen would waste the most
    # developed state a run can reach. The win is recorded in s.goal_year
    # for ever and the run carries on until the founder dies or the
    # horizon arrives.
    #
    # `run` and `compare` are unaffected: Sim.run() in core.py stops at the goal
    # on its own, which is what every measurement in this repository wants and
    # what keeps a dice-free trial cheap. This is the interactive path only.
    if sim.year >= end_year:
        # Under fog there IS no stated goal, so saying the player failed to
        # reach one is incoherent: a goal they were never shown and had no
        # way to set.
        if sim.fog:
            # AND IT MUST CHECK s.goal_year, the same as the non-fog branch
            # two lines below: telling a player at the end that they were
            # never aiming at anything is a lie when `help` already names
            # the goal, and a player who reached the goal under fog and
            # kept building must be told that, not unconditionally "did
            # not reach %s". One rule must not live differently in the two
            # branches.
            _goal_name = (sim.nodes[sim.goal]["name"].lower() if sim.goal in sim.nodes
                         else "the goal")
            if sim.goal_year:
                return ("the horizon at %d AD is reached. You reached %s in "
                        "%d AD and kept building for %d years after it."
                        % (end_year, _goal_name, sim.goal_year,
                           end_year - sim.goal_year))
            return ("the horizon at %d AD is reached. You built %d things of your "
                    "own and did not reach %s."
                    % (end_year, len(sim.done - sim.granted), _goal_name))
        if sim.goal_year:
            return ("the horizon at %d AD is reached. You reached %s in %d AD "
                    "and kept building for %d years after it."
                    % (end_year,
                       sim.nodes[sim.goal]["name"].lower() if sim.goal in sim.nodes
                       else "the goal", sim.goal_year, end_year - sim.goal_year))
        return "ran out of horizon (%d AD) without reaching the goal" % end_year
    return None


# Hazard fields only the `risk` screen needs.
_RISK_ONLY_KEYS = ("note", "what_you_can_do", "staff_loss_before_what_you_have_built",
                   "output_factor", "output_factor_after_what_you_have_built",
                   "national_public_health", "staff_loss_after_what_you_have_built",
                   "remaining_annual_wave_checks", "chance_of_at_least_one_staff_loss_wave",
                   "expected_cumulative_staff_loss")


def _risk_without_the_essays(knowledge_risk):
    """knowledge_risk with the hazard prose stripped, for embedding in state."""
    if not isinstance(knowledge_risk, dict):
        return knowledge_risk
    out = dict(knowledge_risk)
    ahead = out.get("known_hazards_ahead")
    if isinstance(ahead, list):
        out["known_hazards_ahead"] = [
            {key: value for key, value in hazard.items() if key not in _RISK_ONLY_KEYS}
            for hazard in ahead if isinstance(hazard, dict)]
        out["the_full_account_of_each"] = '{"cmd":"risk"}'
    return out


def _staff_fraction_note(sim):
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
    if (abs(sim.scholars - round(sim.scholars)) < 0.02
            and abs(sim.artisans - round(sim.artisans)) < 0.02
            and all(abs(value - round(value)) < 0.02 for value in sim.employees.values())):
        return None
    return ("these are continuous full-time-equivalents, not a count of "
            "whole people: hiring phases in, training takes years, and "
            "attrition (about 3.5%/yr) trims everyone a little rather "
            "than dismissing one person at a time. 1.32 artisans is the "
            "wage and output of one artisan plus a third of another's.")


_STAFFING_HINT = "'labour' shows who can be hired; 'hire <trade> 1' or 'train <trade>' adds one"


def _waiting_on(sim, nodes, node_id, progress, bill):
    """What is ACTUALLY holding this project up, checked against today."""
    node = nodes[node_id]
    frac = min(1.0, 1.0 / max(1.0, node["yrs"]))
    # WHAT IS LEFT OF EACH TRADE'S TOTAL, not the flat annual figure: see
    # ProjectsMixin.lab_year_draw (projects.py), hired-labour hours are a
    # total drawn down over the project's life, so near the end of a trade's
    # own balance the true ask is smaller than its nominal pace, and saying
    # "short" against the bigger, already-paid-down figure would name a
    # shortfall that does not actually exist.
    lab_left = progress.get("lab_left") or node["lab"]
    # TWO DIFFERENT FACTS, NOT ONE: "this society can field 3.5 scribes" and
    # "the scribes here can supply 8,750 but your other work has them
    # booked" need different remedies - a shortage no amount of portfolio
    # management would fix, versus one your OWN other projects are causing
    # by outbidding this one for the same trade, which 'stop' on something
    # else actually answers. Kept as two lists so the message - and
    # _portfolio_constraint's classification of it, below - can tell them
    # apart.
    staffing_short = []
    booked_short = []
    portfolio_demand = sim.trade_demand_vs_supply()
    for trade, want in (node["lab"] or {}).items():
        need = min(want / max(1.0, node["yrs"]), lab_left.get(trade, want))
        if need <= 0:
            continue
        supply = sim.labour.hours_you_can_call_on(trade)
        total_demand = portfolio_demand.get(trade, {}).get(
            "demand_hours_this_year", need)
        # The society's capacity is the durable fact a player can act on;
        # this year's bookings only matter when they are what binds.
        kind = sim.trade_shortage_kind(trade, need, total_demand)
        if kind == "staffing":
            staffing_short.append(
                "%s (wants %.0f hours a year; this society can "
                "field %.0f at most)" % (trade, need, max(0.0, supply)))
        elif kind == "booked":
            booked_short.append(
                "%s (wants %.0f hours a year; the %ss here can "
                "supply %.0f but your other work has them booked)"
                % (trade, need, trade, max(0.0, supply)))
    # BOTH, WHEN BOTH ARE TRUE, NOT JUST THE FIRST ONE FOUND: this loop
    # already knows every trade this project is short on, so returning the
    # moment staffing_short has anything in it would silently drop
    # booked_short even when both are populated by the SAME loop above - a
    # project short one trade absolutely and a second only to its own
    # other work would look, from here, exactly like the first shortage
    # was the whole story. _portfolio_constraint still classifies this by
    # its leading words, so the merged sentence keeps "nobody to do the
    # work" first and unchanged.
    if staffing_short and booked_short:
        return ("nobody to do the work: " + "; ".join(sorted(staffing_short)[:3])
                + ". Also short, but only because your own other work has it "
                  "booked: " + "; ".join(sorted(booked_short)[:3])
                + ". " + _STAFFING_HINT)
    if staffing_short:
        return "nobody to do the work: " + "; ".join(sorted(staffing_short)[:3]) + ". " + _STAFFING_HINT
    if booked_short:
        # A DIFFERENT SENTENCE FOR A DIFFERENT REMEDY. The society CAN field
        # this trade; it is your own other active work that has it booked.
        # Teaching or hiring more does nothing here - 'portfolio' (the
        # aggregate demand-vs-supply view) or stopping something else does.
        return ("trade hours already booked: " + "; ".join(sorted(booked_short)[:3])
                + ". 'portfolio' shows the competing demand; 'priority <id> first' or "
                  "'allocate <id> <hours>' decides who gets the hours")
    if progress["ph_left"] <= 0 and bill > 0.5:
        # MONEY YOU HAVE IS NOT MONEY YOU ARE SHORT OF: step() pays at most
        # one year's instalment - the cost divided by the node's calendar
        # floor - so a ten-year work absorbs a tenth of its bill a year
        # however rich you are. Saying "waiting on money" to a household
        # holding far more than what is owed is not a diagnosis, it is a
        # contradiction; what it is actually waiting on is the calendar
        # pace, and that has to be said.
        per_year = sim.project_cost(node_id) * frac
        if per_year > 0.5 and sim.spending_power("buy") >= per_year:
            return ("the pace it can absorb money: at most %s a year goes into "
                    "this (%s still owed, about %.0f more year%s at that rate). "
                    "Money in hand cannot buy it down faster"
                    % ("{:,.0f}".format(per_year), "{:,.0f}".format(bill),
                       math.ceil(bill / per_year),
                       "" if math.ceil(bill / per_year) == 1 else "s"))
        if sim.spending_power("buy") <= 0.5:
            return ("money: fully blocked until funding is available; %s is "
                    "still owed and you cannot raise any of the next %s "
                    "instalment now"
                    % ("{:,.0f}".format(bill), "{:,.0f}".format(per_year)))
        return ("money: unfunded now; will fund opportunistically as revenue "
                "arrives this year: %s still owed and the next instalment of "
                "%s is more than you can raise at this moment"
                % ("{:,.0f}".format(bill), "{:,.0f}".format(per_year)))
    if progress["ph_left"] <= 0:
        years_left = max(1, math.ceil(node["yrs"] - progress.get("yrs", 0.0) - 1e-9))
        return ("the calendar: the work and the money are done, and the least "
                "time it takes (%g years) has about %d more year%s to run"
                % (node["yrs"], years_left, "" if years_left == 1 else "s"))
    # MATERIALS. A shortage scales only projects consuming its supply pool -
    # see core.py step() 5 - so a project with
    # founder-hours still to spend and nobody short on trade or money can
    # still be making less of them than the pool alone would suggest, for a
    # reason that is neither staffing, money nor the calendar. Only said when
    # it is genuinely biting (2% is noise); resource_throttle() itself is the
    # one place that number is computed, read here rather than re-derived.
    _thr = sim.project_resource_throttle(node_id)
    if _thr < 0.98 and sim.binding:
        return ("materials: this project consumes %s, whose shortage has it "
                "running at %d%% of the pace its hours alone "
                "would allow; 'capacity' shows the shortfall"
                % (sim.binding, round(_thr * 100)))
    # Rank, count and pool come from the live queue the allocator also uses.
    _rank, _count, _total = sim.hour_standing(node_id) or (None, None, None)
    if _rank and _count and _count > 1:
        return ("your hours: priority #%d of %d active projects sharing "
                "this year's %s directed hours; 'portfolio' shows what "
                "each one is getting and why"
                % (_rank, _count, "{:,.0f}".format(_total or 0.0)))
    free_hours = max(0.0, sim.labour.director_pool() - sim.labour.director_hours_committed())
    return ("your hours: %s of your own hours of work are still to do, and "
            "you have %s uncommitted this year"
            % ("{:,.0f}".format(progress["ph_left"]), "{:,.0f}".format(free_hours)))


def _goal_progress_count(sim, nodes):
    """How many of the goal's own prerequisites you already have, with
    nothing named and not even the total - see the block comment where this
    is used in _agent_state for why the total itself has to stay withheld
    until the run ends.
    """
    goal = sim.goal
    if not goal or goal not in nodes:
        return None
    need = ui_port.goal_closure(sim)
    if need is None:
        try:
            need = closure(nodes, goal)
            ui_port.set_goal_closure(sim, need)
        except Exception:
            return None
    return sum(1 for node_id in need if node_id in sim.done)


def _founder_death_info(sim):
    """When and how old the founder was when they died, or None if not.

    core.py logs "the founder dies, aged about %d" the one time it
    happens; leaving the age there alone means it can be buried as one
    line among sixty in a long `step`'s events, with no field anywhere a
    script would check first.

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
    if sim.founder_alive:
        return None
    aged = ui_port.founder_death_aged(sim)
    if aged is not None:
        return {"year": ui_port.founder_death_year(sim), "aged_about": aged}
    cache = ui_port.founder_death_cache(sim)
    if cache is not None:
        return cache
    for year, msg in sim.log:
        if "founder dies" in msg.lower():
            match = re.search(r"aged about (\d+)", msg)
            cache = {"year": year, "aged_about": int(match.group(1)) if match else None}
            ui_port.set_founder_death_cache(sim, cache)
            return cache
    return None


def _worth_knowing_early(sim):
    """Said once, ever, early in a run: `help commands` is the complete
    command index (log, values, money, automation, save/load and more, not
    only the five starter verbs), and `log` is an exact, paginated history of
    everything that happens from here on. Both are true from turn one, and
    neither is obvious from the opening briefing's passing mention of
    `help` and its topics: a player can go a long while without realising
    how complete the index is, or how much depth `log` accumulates.

    ONCE, NOT EVERY TURN: gated on a flag this sets itself the first time it
    fires (see _said_command_index in SAVE_FIELDS - it has to survive a save
    or it would fire again every time a script reloads the game) and on
    still being early in the run, so resuming a save from deep into an
    existing game never springs a first-timer's tip on somebody who has long
    since found all of this themselves.
    """
    if ui_port.said_command_index(sim):
        return None
    if sim.year > sim.cfg.get("start_year", sim.year) + 3:
        return None
    ui_port.set_said_command_index(sim, True)
    return ("{\"cmd\":\"help\",\"topic\":\"commands\"} lists the entire "
            "command surface, not only the five you started with - log, "
            "values, money, automation, save/load and more, one line each. "
            "{\"cmd\":\"log\"} is a paginated, exact history of everything "
            "that happens from here on: starts, completions, failures, "
            "hazards, openings, closures, staffing. Both are worth a look "
            "now, before a hundred turns go by and you wish you had been "
            "reading it all along.")
