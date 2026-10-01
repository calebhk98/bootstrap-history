"""How an active project actually proceeds: hired labour, risk, and calendar.

Split out of sim/engine/projects.py (see that file's own docstring for why):
once a project is active this is everything about what happens to it each
further year - project_hour_pace()/active_hours_still_wanted() and the
hired-trade drawdown (lab_max_span, _effective_lab_left, trade_draw_plan,
trade_demand_vs_supply, lab_year_draw) answer how many of the founder's own
hours and how much of a hired trade's time it draws; _retry_risk_multiplier,
_retry_calendar_retain, _control_relief_multiplier and effective_risk answer
how likely THIS attempt is to fail, given how many times it already has; and
calendar_floor/expected_calendar_years answer how many years, at best and on
average across retries, an attempt of this kind takes. None of this decides
whether a project may start (that is projects_starting.py's start_reason)
or what happens once it succeeds or fails (that is projects_completion.py's
_complete); it is what happens to it in between.

These are methods of Sim; they are a mixin only so that they can live in a
file of their own. Behaviour is unchanged and verified byte-identical.
"""
import collections

from sim.constants import declare


class ProgressMixin:
    # -- main loop ----------------------------------------------------------

    # Hired trade hours: total drawn down, per-year ceiling, calendar span limit.
    # A site can field more than its calibrated crew, but not without limit.
    LAB_CREW_RATE_MULT = declare(
        "LAB_CREW_RATE_MULT", 4.0, kind="temporary_heuristic",
        unit="dimensionless multiple of the node's calibrated pace",
        source=None, confidence="D",
        why="A site can field more hands than its own historically-"
            "calibrated crew, but not without limit - a site has only so "
            "many benches, so extra hands beyond this multiple of the "
            "calibrated pace still go to waste. Tuned ceiling, not "
            "measured against any real crew-size elasticity.")

    def project_hour_pace(self, node_id):
        """How many of YOUR OWN hours active project `node_id` would draw this year
        if nothing else competed for the pool - step()'s own uncapped want,
        read here rather than re-derived, so anything reporting on it before
        the allocation runs (the 'work' warning below) cannot silently
        disagree with what step() actually offers.
        """
        project_state, node = self.state.projects.active[node_id], self.nodes[node_id]
        # A bounty is worked by whoever claims the prize, not by the poster.
        if node_id in self.state.projects.bountied:
            return 0.0
        # Throttle not applied here; caller applies. Returns WANT, not allocation.
        return max(project_state["ph_left"], node["ph"] / max(node["yrs"], 1.0))

    def active_hours_still_wanted(self):
        """{project id: hours} for every active project that would still like
        a real amount of your own time this year, at the pace project_hour_
        pace gives it - not what it will actually get (that depends on how
        many other projects are ahead of it in the pool this year), just what
        it is still asking for. Sorted iteration: this feeds a caller that
        may sum or rank it, and projects.active's own order is not fixed.
        """
        out = {}
        projects = self.state.projects
        for node_id in projects.active_keys_sorted():
            if node_id not in self.nodes:
                continue
            pace = self.project_hour_pace(node_id)
            if pace > 0.5:
                out[node_id] = pace
        return out

    LAB_MAX_SPAN_FLOOR_YEARS = declare(
        "LAB_MAX_SPAN_FLOOR_YEARS", 40.0, kind="engineering_estimate",
        unit="years",
        source="A working lifetime: the span between becoming competent "
               "at a trade and retiring from it.",
        confidence="C",
        why="No single personal undertaking should be allowed to out-live "
            "the people who began it - past this, the people who "
            "understood the early stages are dead or have moved on, and "
            "continuing is not finishing the same project, it is starting "
            "a new one that happens to reuse the site. Grounded in a real "
            "demographic fact (a working lifetime) rather than tuned to a "
            "gameplay feel, though the exact figure is a round number, "
            "not a measured career-length distribution for any period.")
    LAB_MAX_SPAN_MULTIPLE = declare(
        "LAB_MAX_SPAN_MULTIPLE", 4.0, kind="temporary_heuristic",
        unit="dimensionless multiple of the node's own calendar floor",
        source=None, confidence="D",
        why="A node whose own calendar floor already marks it as "
            "diffusion-limited (10+ years, a social process rather than a "
            "personal one) earns proportionately more room to find its "
            "hired trade before being abandoned - up to this multiple of "
            "its own floor, rather than an unbounded wait. Tuned "
            "multiple, not measured.")

    def lab_max_span(self, node_id):
        """The most years a project may spend trying to find enough of a
        hired trade before it is given up on.

        Forty years is a working lifetime - the span between becoming
        competent at a trade and retiring from it - and no single human
        undertaking should be allowed to out-live the people who began it:
        past that, the people who understood the early stages are dead or
        have moved on, and continuing is not finishing the same project, it
        is starting a new one that happens to reuse the site. A
        node whose OWN calendar floor (node["yrs"]) is already longer than ten
        years is one this tree already marks as diffusion-limited rather than
        personal - see core.py's POP_TECH_RAMP_YEARS and the `floor` logic in
        step() - so it earns proportionately more room, to a ceiling of four
        times its own floor rather than an unbounded one.
        """
        node = self.nodes[node_id]
        return max(self.LAB_MAX_SPAN_FLOOR_YEARS, float(node["yrs"]) * self.LAB_MAX_SPAN_MULTIPLE)

    def _effective_lab_left(self, node_id, project_state):
        """What is left of each hired trade's total for active project `node_id`,
        read-only: never writes project_state["lab_left"], unlike lab_year_draw (the
        only place that is allowed to initialise it for real, because doing
        so is itself a decision - the guess below - that should happen once
        per project, not once per caller that wants to look).

        Hand-built simulations and diagnostic callers may omit the field; in
        that case estimate the remaining trade work from founder-hour progress.
        """
        lab_left = project_state.get("lab_left")
        if lab_left is not None:
            return lab_left
        node = self.nodes[node_id]
        left_frac = min(1.0, project_state.get("ph_left", node["ph"]) / max(1.0, node["ph"]))
        return {trade: want * left_frac for trade, want in node["lab"].items()}

    def trade_draw_plan(self, node_id, lab_left=None):
        """What project `node_id` would like to draw from each hired trade this
        year, if the trade could supply it without limit - the DEMAND side
        of lab_year_draw's per-trade loop, read-only and with no knowledge of
        what any OTHER project wants or what the trade can actually supply.

        `lab_left` is what is left of each trade's total: None means a
        project that has not started yet, so the full want is still owed.
        For an active project pass self._effective_lab_left(node_id, project_state) (or
        project_state["lab_left"] directly once lab_year_draw has initialised it).

        lab_year_draw calls this for nominal/ceiling/left and then clamps
        each trade to what it can actually supply this year (hours_you_can_
        call_on minus what earlier-ranked projects already took) - the
        SUPPLY side. Anything reporting the portfolio's aggregate demand
        before that allocation runs (trade_demand_vs_supply below, and the
        oversubscription check `start` runs before committing) calls this
        the same way, so a forecast and the real allocator can disagree
        about what a project GETS, never about what it WANTS.
        """
        node = self.nodes[node_id]
        out = {}
        for trade_id in sorted(node["lab"]):
            want = node["lab"][trade_id]
            left = want if lab_left is None else lab_left.get(trade_id, 0.0)
            if left <= 0 or want <= 0:
                continue
            nominal = want / max(1.0, node["yrs"])
            ceiling = nominal * self.LAB_CREW_RATE_MULT
            out[trade_id] = {"nominal": nominal, "left": left, "ceiling": ceiling,
                      "desired": min(left, ceiling)}
        return out

    def trade_shortage_kind(self, trade_id, need, total_demand=None):
        """Why a trade is short for a project that wants `need` hours a year
        of it: "staffing" when the society cannot field that much at all,
        "booked" when it can but the portfolio's demand exceeds it, else None.
        `total_demand` None means the caller already knows the project fell
        short, so what the society can field decides between the two."""
        supply = self.hours_you_can_call_on(trade_id)
        if supply < need:
            return "staffing"
        if total_demand is None or total_demand > supply + 1e-6:
            return "booked"
        return None

    def trade_shortfall_note(self, project_state):
        """The step-log reason for a project short of hired trades: booked
        by other work, or more than the society can field at all."""
        short = sorted(project_state.get("short_of_trade") or [])
        staffing = [trade_id for trade_id in short
                    if trade_id in (project_state.get("short_of_trade_staffing") or [])]
        booked = [trade_id for trade_id in short if trade_id not in staffing]
        if booked:
            return "trade hours already booked: " + ", ".join(booked[:2])
        return "nobody to do the work: this society cannot field enough " + ", ".join(staffing[:2])

    def trade_demand_vs_supply(self):
        """Aggregate, by hired trade: what this year's ACTIVE portfolio
        wants from it (summed trade_draw_plan 'desired', the same demand
        figure lab_year_draw is about to act on) against what the trade can
        actually supply (hours_you_can_call_on) - read-only, so calling this
        to look never changes what lab_year_draw later does.

        A player who had already won the game asked for exactly this, to
        see BEFORE committing to one more project: "the portfolio UI could
        make aggregate trade-hour demand vs supply easier to see" - their
        own run had one chemist left, 3,000 trade-hours a year, and a dozen
        projects each quietly assuming they would get all of it.
        """
        demand = collections.defaultdict(float)
        by_trade = collections.defaultdict(list)
        # sorted(): this feeds float sums, and projects.active is a dict whose
        # key order depends on PYTHONHASHSEED.
        projects = self.state.projects
        for node_id in projects.active_keys_sorted():
            project_state = projects.active[node_id]
            for trade_id, plan in sorted(self.trade_draw_plan(
                    node_id, self._effective_lab_left(node_id, project_state)).items()):
                demand[trade_id] += plan["desired"]
                by_trade[trade_id].append(node_id)
        out = {}
        for trade_id in sorted(demand):
            supply = self.hours_you_can_call_on(trade_id)
            out[trade_id] = {"demand_hours_this_year": round(demand[trade_id], 1),
                      "supply_hours_this_year": round(supply, 1),
                      "oversubscribed": bool(demand[trade_id] > supply + 1e-6),
                      "projects_drawing_on_it": sorted(by_trade[trade_id])}
        return out

    def lab_year_draw(self, node_id, project_state, frac, hired_left):
        """This year's hired-labour draw for active project `node_id`.

        Returns (hh, worst, frac, abandon): `hh` is the total hired hours
        drawn this year (what step() checks against `hired_left`), `worst` is
        the worst-supplied trade's shortfall against ITS OWN historical pace
        (unchanged meaning from before: this still drives the founder-hours
        give-back in step(), because a trade that came up short really did
        waste some of the year's effort), `frac` is the money-pacing fraction,
        reduced exactly as before when a trade came up short of its own pace,
        and `abandon` is None or a reason the project should be dropped
        because it ran out of calendar (see lab_max_span above).

        Mutates project_state["lab_left"] and projects.trade_hours_used as a side effect,
        exactly where the code this replaced did. The DEMAND side of the
        numbers below (nominal, ceiling, left) comes from trade_draw_plan,
        the same read-only formula anything reporting on the portfolio before
        this runs also calls - only the SUPPLY clamp (`have`) and the mutation
        are done here, which is the real allocation and happens exactly once
        a year, inside step().
        """
        node = self.nodes[node_id]
        projects = self.state.projects
        if project_state.get("lab_left") is None:
            project_state["lab_left"] = self._effective_lab_left(node_id, project_state)
        lab_left = project_state["lab_left"]
        hired_hours = 0.0
        worst = 1.0
        plan = self.trade_draw_plan(node_id, lab_left)
        need_by_trade = {trade_id: min(entry["nominal"], entry["left"])
                         for trade_id, entry in plan.items()}
        for trade_id, plan_entry in sorted(plan.items()):
            left, nominal = plan_entry["left"], plan_entry["nominal"]
            have = max(0.0, self.hours_you_can_call_on(trade_id)
                       - projects.trade_hours_used.get(trade_id, 0.0))
            # Ceiling is crew, not calendar. Take what's useful and available.
            drawn = min(left, plan_entry["ceiling"], have)
            lab_left[trade_id] = max(0.0, left - drawn)
            projects.trade_hours_used[trade_id] = projects.trade_hours_used.get(trade_id, 0.0) + drawn
            hired_hours += drawn
            # Warning drawn at old pace. Shortfall triggers give-back.
            target = min(nominal, left)
            if target > 0:
                worst = min(worst, drawn / target)
        if worst < 1.0:
            project_state["status"] = "BLOCKED_INPUTS"
            frac *= worst
            short_trades = sorted(
                trade_id for trade_id, left in lab_left.items()
                if left > 0 and (self.hours_you_can_call_on(trade_id)
                                  - projects.trade_hours_used.get(trade_id, 0.0))
                < min(left, node["lab"][trade_id] / max(1.0, node["yrs"])))[:3]
            project_state["short_of_trade"] = short_trades
            project_state["short_of_trade_staffing"] = [
                trade_id for trade_id in short_trades
                if self.trade_shortage_kind(trade_id, need_by_trade.get(trade_id, 0.0)) == "staffing"]
        else:
            project_state["status"] = "ACTIVE"
            project_state.pop("short_of_trade", None)
            project_state.pop("short_of_trade_staffing", None)
        # DEADLINE: prevents creep. Unmet trades trigger abandonment.
        if project_state["yrs"] >= self.lab_max_span(node_id) and any(value > 0.5 for value in lab_left.values()):
            unmet = sorted(trade_id for trade_id, value in lab_left.items() if value > 0.5)
            return hired_hours, worst, frac, (
                "after %d years there was still not enough %s here to finish "
                "it. What was spent is lost; you still know what you learned "
                "along the way" % (int(self.lab_max_span(node_id)), " or ".join(unmet[:2])))
        return hired_hours, worst, frac, None

    # ---- A FAILED ATTEMPT TEACHES YOU SOMETHING -----------------------------
    # Risk (engineering lesson) and calendar (social groundwork) both decrease.
    # Both capped strictly short of zero; "should never be free".
    #
    # RISK: Multiplies base risk, decaying geometrically toward RETRY_RISK_FLOOR.
    RETRY_RISK_FLOOR = declare(
        "RETRY_RISK_FLOOR", 0.40, kind="temporary_heuristic",
        unit="fraction of the naive (bare node) risk", source=None,
        confidence="D",
        why="However many times a project has failed and learned from it, "
            "the next attempt's risk never drops below this share of the "
            "bare risk - understanding one failure mode does not mean "
            "every failure mode is found, so retries should never be "
            "free. Tuned floor, not measured against any real engineering "
            "learning curve.")
    RETRY_RISK_DECAY = declare(
        "RETRY_RISK_DECAY", 0.6, kind="temporary_heuristic",
        unit="fraction of the remaining risk closed per failure",
        source=None, confidence="D",
        why="Each failure closes 40% of the gap between the current risk "
            "and RETRY_RISK_FLOOR, geometrically - the first failure buys "
            "the most learning and every one after buys less. Tuned decay "
            "rate, not fitted to any real learning-curve data.")

    def _retry_risk_multiplier(self, node_id):
        attempt_count = self.state.projects.failed_attempts.get(node_id, 0)
        if attempt_count <= 0:
            return 1.0
        return (self.RETRY_RISK_FLOOR
                + (1.0 - self.RETRY_RISK_FLOOR) * self.RETRY_RISK_DECAY ** attempt_count)

    # CALENDAR: Fraction of elapsed years banked toward next attempt, capped.
    # Retried programmes readier than last, never instant.
    RETRY_CALENDAR_CAP = declare(
        "RETRY_CALENDAR_CAP", 0.65, kind="temporary_heuristic",
        unit="fraction of the elapsed calendar time on a failed attempt",
        source=None, confidence="D",
        why="At most this share of the years already spent on a failed "
            "attempt is banked toward the next one - comfortably short of "
            "1.0 so a retried programme is never instantly ready, only "
            "readier than the last one. The diminishing, capped SHAPE "
            "mirrors the risk term above for the same 'never free' brief; "
            "the specific cap is tuned, not measured.")
    RETRY_CALENDAR_DECAY = declare(
        "RETRY_CALENDAR_DECAY", 0.5, kind="temporary_heuristic",
        unit="fraction of the remaining calendar gap closed per failure",
        source=None, confidence="D",
        why="Each failure closes half of the gap between what is "
            "currently banked and RETRY_CALENDAR_CAP's own ceiling. Tuned "
            "decay rate, not fitted to any real social-diffusion recovery "
            "curve.")

    def _retry_calendar_retain(self, node_id, attempt_index=None):
        # See _retry_risk_multiplier's comment on `attempt_index` - same reason, same
        # contract: the real failure count still drives every actual retry;
        # `attempt_index` only lets a projection ask about a hypothetical one.
        if attempt_index is None:
            attempt_index = self.state.projects.failed_attempts.get(node_id, 0)
        if attempt_index <= 0:
            return 0.0
        return self.RETRY_CALENDAR_CAP * (1.0 - self.RETRY_CALENDAR_DECAY ** attempt_index)

    # CONTROL RELIEF: Process controller cuts risk by 35% for process-control nodes.
    # Earned once, independent of failed_attempts. Nodes opt in via tree data.
    CONTROL_RELIEF_FACTOR = declare(
        "CONTROL_RELIEF_FACTOR", 0.65, kind="temporary_heuristic",
        unit="fraction of risk remaining after relief (a flat 35% cut)",
        source=None, confidence="D",
        why="A completed process controller cuts a process-control node's "
            "risk by a flat 35%, earned once and never depending on "
            "failed_attempts, so it neither stacks unboundedly with retry "
            "learning nor reaches zero by itself - the brief was explicit "
            "that a real closed-loop controller (Minorsky 1922, "
            "Ziegler-Nichols tuning) genuinely mitigates a hold-at-"
            "setpoint failure mode, but the tension of a hard node like "
            "zone_refining must not be removed outright. The MECHANISM "
            "(control theory relieves this class of failure) is real and "
            "sourced; the specific 35% cut is tuned to leave meaningful "
            "risk, not measured from any real reliability improvement "
            "figure for early control systems.")

    def _control_relief_multiplier(self, node_id):
        failure_kind = self.nodes[node_id].get("failure_kind")
        for relief_id in self.nodes_with_mechanic("failure_relief"):
            if (self.mechanic(relief_id, "failure_relief")["failure_kind"] == failure_kind
                    and relief_id in self.state.projects.done):
                return self.CONTROL_RELIEF_FACTOR
        return 1.0

    def effective_risk(self, node_id):
        """This node's actual chance of failing on its NEXT attempt, after
        whatever retry-learning its past failures have already bought (see
        _retry_risk_multiplier just above) AND whatever control-theory relief
        a completed process controller has earned it (see
        _control_relief_multiplier just above). Equal to the bare node risk
        the first time anything is tried, with no controller built. A screen
        quoting a node's risk once failed_attempts[node_id] is above zero, or once
        the controller is done, should read THIS, not the tree's bare
        node["risk"] - that number is no longer what the dice use.
        """
        return (self.nodes[node_id]["risk"] * self._retry_risk_multiplier(node_id)
                * self._control_relief_multiplier(node_id))

    # ---- WHAT A RISKY NODE ACTUALLY COSTS IN CALENDAR TIME -----------------
    # effective_risk and calendar_floor answer separate questions about odds and wait.
    DIFFUSION_LIMITED_YEARS_THRESHOLD = declare(
        "DIFFUSION_LIMITED_YEARS_THRESHOLD", 5, kind="temporary_heuristic",
        unit="years (node['yrs'])", source=None, confidence="D",
        why="A node whose own calendar floor is at least this many years "
            "is treated as diffusion-limited (a social process reputation "
            "can shrink) rather than a physical curing or drying time "
            "reputation has no business touching. Declared as the INT the "
            "source wrote, compared directly against node['yrs'] (itself "
            "always a whole number of years in the tree data): no reason "
            "to widen it. Tuned cutoff, not measured.")
    CALENDAR_FLOOR_MIN_YEARS = declare(
        "CALENDAR_FLOOR_MIN_YEARS", 2.0, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="However much reputation shrinks a diffusion-limited node's "
            "calendar floor, it never falls below this - some minimum "
            "social process still has to happen. Tuned floor, not "
            "measured.")
    CALENDAR_FLOOR_REPUTATION_SCALE = declare(
        "CALENDAR_FLOOR_REPUTATION_SCALE", 90.0, kind="temporary_heuristic",
        unit="reputation points per doubling of diffusion speed",
        source=None, confidence="D",
        why="How much reputation it takes to roughly halve a diffusion-"
            "limited node's calendar floor - a civilisation that already "
            "does a hundred complicated things does not start the "
            "hundred-and-first's social diffusion from zero credibility. "
            "Tuned to a similar order of magnitude as economy.py's "
            "REPUTATION_EASE_SCALE (120.0) for a related but distinct "
            "effect; not fitted to any measured diffusion-speed curve.")

    def calendar_floor(self, node_id):
        """Calendar years THIS attempt needs to elapse before a completion
        roll can fire at all - the SAME formula step() uses to gate
        `_complete` (see core.py, where a project's own
        `projects.active[node_id]["yrs"]` is compared against this), not a
        second copy of it. Diffusion-limited
        nodes (yrs >= 5) shrink as reputation grows: a civilisation that
        already does a hundred complicated things does not start the social
        diffusion of the hundred-and-first from zero credibility.
        """
        node = self.nodes[node_id]
        floor = node["yrs"]
        if node["yrs"] >= self.DIFFUSION_LIMITED_YEARS_THRESHOLD:   # diffusion-limited nodes, not physical curing
            floor = max(self.CALENDAR_FLOOR_MIN_YEARS,
                        node["yrs"] / (1.0 + self.state.household.reputation / self.CALENDAR_FLOOR_REPUTATION_SCALE))
        return floor * self.rebuild_work_factor(node_id)

    def payment_schedule_years(self, node_id):
        """Years the bill takes to pay in full: it is paid in equal yearly
        instalments over the node's nominal years, which reputation never
        shortens."""
        return max(1.0, self.nodes[node_id]["yrs"] * self.rebuild_work_factor(node_id))

    def earliest_completion_years(self, node_id):
        """The soonest the project can finish, with no failure: the longer of
        the calendar floor and the payment schedule, less what a running
        attempt has already served."""
        earliest = max(self.calendar_floor(node_id), self.payment_schedule_years(node_id))
        running = self.state.projects.active.get(node_id)
        return max(0.0, earliest - running.get("yrs", 0.0)) if running else earliest

    def expected_calendar_years(self, node_id, _max_extra_attempts=500):
        """Expected calendar years to SUCCEED at node_id, counting every retry the
        dice force - not the bare calendar_floor, and not a plain geometric
        series on the raw risk field either. A failure does not roll the
        exact same dice again: the per-attempt risk and the per-attempt wait
        both move on every subsequent attempt, so the true expectation is a
        sum over "the first i attempts all failed" with a shrinking risk and
        a shrinking wait at each step.

        THE RISK TERM IS READ FROM effective_risk(node_id), NEVER REIMPLEMENTED.
        effective_risk is the one place allowed to know everything that
        moves a node's odds - today that is only retry learning
        (_retry_risk_multiplier), but it is the designated home for any
        OTHER multiplier this society's own choices might someday apply
        (a capability that makes a whole family of processes more
        reliable, say), and this function has no business knowing what
        those are or duplicating how they combine. To ask "what would
        attempt i+1's odds be" for a hypothetical future i without actually
        recording a failure, this stands in for "i failures so far" by
        briefly setting failed_attempts[node_id] to i, reads effective_risk(node_id),
        and restores the real count immediately after - in a `finally`, so
        a real failure count is never left clobbered even if something
        above raises. The calendar term has no such second multiplier (see
        _retry_calendar_retain) and is asked the same way, via its own `attempt_index`.

        Three assumptions, stated because a wrong number here is worse than
        none:
        1. The calendar floor used is TODAY's (today's reputation). It can
           only shrink as reputation grows, never grow back, so if anything
           this slightly OVERSTATES the wait for a civilisation still
           climbing - never understates it.
        2. Hours and money are assumed never to bind once the floor does -
           the late-game case this was written for (a mature economy with
           nothing between it and the node but dice and the calendar). A
           project still starved of hours or cash will take longer than
           this says, for reasons this number is not trying to capture.
        3. Attempts keep retrying automatically without the project being
           manually `stop`ped in between - which is how the engine actually
           runs retries: a failure never removes a project from `active`,
           only shrinks its clock and its odds (see `_complete`).
           Stop-and-restart forfeits the banked calendar progress
           (start_project always zeroes `yrs`) while keeping the risk
           learning (failed_attempts is never reset) - a real, separate
           wrinkle, and the player's own choice, not the dice's.
        """
        floor = max(self.calendar_floor(node_id), self.payment_schedule_years(node_id))
        projects = self.state.projects
        initial_failed_attempts = projects.failed_attempts.get(node_id, 0)
        _had_key = node_id in projects.failed_attempts
        _active = projects.active.get(node_id) if node_id in projects.active else None
        total = 0.0
        survive = 1.0
        attempt_index = initial_failed_attempts
        try:
            while True:
                if attempt_index == initial_failed_attempts and _active is not None:
                    # Mid-attempt: use real elapsed clock, not recomputed fraction.
                    years_this_attempt = max(0.0, floor - _active.get("yrs", 0.0))
                elif attempt_index == initial_failed_attempts:
                    # Not active: start_project zeroes yrs, so pay full floor.
                    years_this_attempt = floor
                else:
                    years_this_attempt = floor * (1.0 - self._retry_calendar_retain(node_id, attempt_index))
                total += survive * years_this_attempt
                # Stand in for i failures, read effective_risk, restore in finally.
                projects.failed_attempts[node_id] = attempt_index
                survive *= self.effective_risk(node_id)
                attempt_index += 1
                if survive < 1e-12 or attempt_index - initial_failed_attempts > _max_extra_attempts:
                    break
        finally:
            if _had_key:
                projects.failed_attempts[node_id] = initial_failed_attempts
            else:
                projects.failed_attempts.pop(node_id, None)
        return total
