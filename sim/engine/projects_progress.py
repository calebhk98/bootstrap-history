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

from constants import declare


class ProgressMixin:
    # -- main loop ----------------------------------------------------------

    # A HIRED TRADE'S HOURS ARE A TOTAL, NOT A TOLL DUE EVERY YEAR. A project
    # wanting 1,200 smith-hours over a 4-year calendar floor must not demand
    # exactly 300 a year, every year, regardless of what the trade can
    # actually supply: three smiths free or thirty should not draw the same
    # 300 and waste the rest. Labour is a genuine CAP - nobody can do a
    # billion hours in a year - but a company able to field more hands must
    # be able to spend twice as much for half as long, not be held to a
    # fixed yearly toll. lab_year_draw is the honest shape of the
    # constraint: a TOTAL (n["lab"][t], drawn down in
    # st["lab_left"]), a per-year CEILING somewhat above the pace the node was
    # calibrated at (a site has only so many benches, so extra hands beyond a
    # multiple of that still go to waste), and a maximum calendar SPAN past
    # which the undertaking is abandoned rather than left to drift for
    # centuries - see lab_max_span just below for what that span is and why.
    #
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
        """How many of YOUR OWN hours active project `k` would draw this year
        if nothing else competed for the pool - step()'s own uncapped want,
        read here rather than re-derived, so anything reporting on it before
        the allocation runs (the 'work' warning below) cannot silently
        disagree with what step() actually offers.
        """
        project_state, node = self.household.active[node_id], self.nodes[node_id]
        # THE THROTTLE IS NOT APPLIED HERE, and must not be. step() spends
        # `min(remaining, this) * throttle`, and folding the throttle in
        # changes that to `min(remaining, this * throttle)`, which is a
        # different number whenever the founder's remaining hours are the
        # binding term: at remaining 100, a want of 500 and a throttle of
        # 0.5, the first gives the project 50 hours and the second gives it
        # 100. That is the material-shortage brake silently ceasing to apply
        # in exactly the case it matters most, a busy year with the founder
        # stretched thin, and no check in this suite caught it. What this
        # returns is the project's WANT; every caller applies the brake for
        # its own purpose.
        return max(project_state["ph_left"], node["ph"] / max(node["yrs"], 1.0))

    def active_hours_still_wanted(self):
        """{project id: hours} for every active project that would still like
        a real amount of your own time this year, at the pace project_hour_
        pace gives it - not what it will actually get (that depends on how
        many other projects are ahead of it in the pool this year), just what
        it is still asking for. Sorted iteration: this feeds a caller that
        may sum or rank it, and self.household.active's own order is not fixed.
        """
        out = {}
        for node_id in sorted(self.household.active):
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
        node whose OWN calendar floor (n["yrs"]) is already longer than ten
        years is one this tree already marks as diffusion-limited rather than
        personal - see core.py's POP_TECH_RAMP_YEARS and the `floor` logic in
        step() - so it earns proportionately more room, to a ceiling of four
        times its own floor rather than an unbounded one.
        """
        node = self.nodes[node_id]
        return max(self.LAB_MAX_SPAN_FLOOR_YEARS, float(node["yrs"]) * self.LAB_MAX_SPAN_MULTIPLE)

    def _effective_lab_left(self, node_id, project_state):
        """What is left of each hired trade's total for active project `k`,
        read-only: never writes st["lab_left"], unlike lab_year_draw (the
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
        """What project `k` would like to draw from each hired trade this
        year, if the trade could supply it without limit - the DEMAND side
        of lab_year_draw's per-trade loop, read-only and with no knowledge of
        what any OTHER project wants or what the trade can actually supply.

        `lab_left` is what is left of each trade's total: None means a
        project that has not started yet, so the full want is still owed.
        For an active project pass self._effective_lab_left(k, st) (or
        st["lab_left"] directly once lab_year_draw has initialised it).

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
        for trade_id, want in node["lab"].items():
            left = want if lab_left is None else lab_left.get(trade_id, 0.0)
            if left <= 0 or want <= 0:
                continue
            nominal = want / max(1.0, node["yrs"])
            ceiling = nominal * self.LAB_CREW_RATE_MULT
            out[trade_id] = {"nominal": nominal, "left": left, "ceiling": ceiling,
                      "desired": min(left, ceiling)}
        return out

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
        # sorted(): this feeds float sums, and self.household.active is a dict whose
        # key order depends on PYTHONHASHSEED.
        for node_id in sorted(self.household.active):
            project_state = self.household.active[node_id]
            for trade_id, plan in self.trade_draw_plan(
                    node_id, self._effective_lab_left(node_id, project_state)).items():
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
        """This year's hired-labour draw for active project `k`.

        Returns (hh, worst, frac, abandon): `hh` is the total hired hours
        drawn this year (what step() checks against `hired_left`), `worst` is
        the worst-supplied trade's shortfall against ITS OWN historical pace
        (unchanged meaning from before: this still drives the founder-hours
        give-back in step(), because a trade that came up short really did
        waste some of the year's effort), `frac` is the money-pacing fraction,
        reduced exactly as before when a trade came up short of its own pace,
        and `abandon` is None or a reason the project should be dropped
        because it ran out of calendar (see lab_max_span above).

        Mutates st["lab_left"] and self.household.trade_hours_used as a side effect,
        exactly where the code this replaced did. The DEMAND side of the
        numbers below (nominal, ceiling, left) comes from trade_draw_plan,
        the same read-only formula anything reporting on the portfolio before
        this runs also calls - only the SUPPLY clamp (`have`) and the mutation
        are done here, which is the real allocation and happens exactly once
        a year, inside step().
        """
        node = self.nodes[node_id]
        if project_state.get("lab_left") is None:
            project_state["lab_left"] = self._effective_lab_left(node_id, project_state)
        lab_left = project_state["lab_left"]
        hired_hours = 0.0
        worst = 1.0
        plan = self.trade_draw_plan(node_id, lab_left)
        for trade_id, plan_entry in plan.items():
            left, nominal = plan_entry["left"], plan_entry["nominal"]
            have = max(0.0, self.hours_you_can_call_on(trade_id)
                       - self.household.trade_hours_used.get(trade_id, 0.0))
            # THE CEILING IS A CREW, NOT A CALENDAR, so take whatever of this
            # is both USEFUL (no more than is left to do) and AVAILABLE (no
            # more than the trade can actually supply this year), up to the
            # site's own headroom above its calibrated pace.
            drawn = min(left, plan_entry["ceiling"], have)
            lab_left[trade_id] = max(0.0, left - drawn)
            self.household.trade_hours_used[trade_id] = self.household.trade_hours_used.get(trade_id, 0.0) + drawn
            hired_hours += drawn
            # THE WARNING IS STILL DRAWN AT THE OLD PACE. Extra capacity above
            # the historical figure is a bonus with no penalty either way; a
            # SHORTFALL below the pace the node was actually calibrated
            # against is what give-back and "short of trade" have always
            # meant, and moving the goalposts to the new, larger ceiling would
            # warn about a shortage of hands nobody ever expected to exist.
            target = min(nominal, left)
            if target > 0:
                worst = min(worst, drawn / target)
        if worst < 1.0:
            frac *= worst
            project_state["short_of_trade"] = sorted(
                trade_id for trade_id, left in lab_left.items()
                if left > 0 and (self.hours_you_can_call_on(trade_id)
                                  - self.household.trade_hours_used.get(trade_id, 0.0))
                < min(left, node["lab"][trade_id] / max(1.0, node["yrs"])))[:3]
        else:
            project_state.pop("short_of_trade", None)
        # THE DEADLINE: without one, a trade that never clears its balance
        # would let a project creep forward forever at whatever sliver of
        # progress could be found - technically still moving, never
        # actually finishing, and never SAID to have failed. People die
        # and what they knew goes with them; nothing here pretends
        # otherwise.
        if project_state["yrs"] >= self.lab_max_span(node_id) and any(value > 0.5 for value in lab_left.values()):
            unmet = sorted(trade_id for trade_id, value in lab_left.items() if value > 0.5)
            return hired_hours, worst, frac, (
                "after %d years there was still not enough %s here to finish "
                "it. What was spent is lost; you still know what you learned "
                "along the way" % (int(self.lab_max_span(node_id)), " or ".join(unmet[:2])))
        return hired_hours, worst, frac, None

    # ---- A FAILED ATTEMPT TEACHES YOU SOMETHING -----------------------------
    # A player who had already won the game objected to the mechanic just
    # below as it stood: a failure reset the calendar floor to zero and rolled
    # again at the SAME probability, which models a society trying the exact
    # same programme with the exact same odds as if the first attempt had
    # never happened. Their own words: "if I fail my first crystal-growing
    # programme, that failure itself teaches my engineers a huge amount. My
    # next attempt should not be probabilistically identical." They also
    # named the other half of it themselves - "the second attempt should
    # probably inherit some progress" - because a high-pressure steam system
    # or a zone-refining line is not only an engineering problem, it is a
    # SOCIAL one: workshops retooled, a workforce that has seen the process
    # once, suppliers who already adjusted, regulators or patrons who already
    # sat through the pitch. A technical failure at the end does not erase
    # that diffusion, which is most of what a long calendar floor represents
    # in the first place (see _calendar_floor_remaining's own comment on what
    # these floors are actually made of).
    #
    # So this does BOTH, because they answer two different questions the
    # player asked in the same breath: the risk term is the ENGINEERING
    # lesson (what failed, and why, is now known and will not recur in the
    # same way), the calendar term is the SOCIAL one (the groundwork already
    # laid does not have to be laid twice). Both are diminishing and both are
    # capped strictly short of removing the danger or the wait entirely -
    # "should never be free" was the explicit brief, and a mechanic that let
    # enough failures drive the risk to zero or the wait to nothing would
    # just be a slower way of removing the hazard altogether, which is not
    # what was asked for.
    #
    # RISK: multiplies the node's own base risk by a factor that starts at
    # 1.0 (attempt one is not "probabilistically identical" to anything - it
    # IS the first data point, nothing has been learned yet) and decays
    # toward RETRY_RISK_FLOOR as failures accumulate, geometrically, so the
    # first failure buys the most and every one after buys less. Floored well
    # above zero: an engineering team that has failed four times still faces
    # a real chance of failing a fifth, because "we now understand this
    # failure mode" does not mean "we have found every failure mode".
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
        attempt_count = self.household.failed_attempts.get(node_id, 0)
        if attempt_count <= 0:
            return 1.0
        return (self.RETRY_RISK_FLOOR
                + (1.0 - self.RETRY_RISK_FLOOR) * self.RETRY_RISK_DECAY ** attempt_count)

    # CALENDAR: a fraction of the years already spent on THIS attempt is
    # banked toward the next one instead of being erased, on the same
    # diminishing, capped shape as the risk term above and for the same
    # reason - RETRY_CALENDAR_CAP is comfortably short of 1.0 so a retried
    # programme is never instantly ready, only readier than the last one.
    # Read off self.household.active[k]["yrs"] AT THE MOMENT OF FAILURE, not off a
    # recomputed floor: core.py's own completion gate (the reputation-
    # shrinking floor for diffusion-limited nodes) already decided how many
    # years this attempt actually took before calling here, and banking a
    # share of THAT figure keeps this consistent with whatever the floor
    # happened to be without this file needing a second copy of core.py's
    # formula that could drift out of step with it.
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
        # See _retry_risk_multiplier's comment on `m` - same reason, same
        # contract: the real failure count still drives every actual retry;
        # `m` only lets a projection ask about a hypothetical one.
        if attempt_index is None:
            attempt_index = self.household.failed_attempts.get(node_id, 0)
        if attempt_index <= 0:
            return 0.0
        return self.RETRY_CALENDAR_CAP * (1.0 - self.RETRY_CALENDAR_DECAY ** attempt_index)

    # CONTROL RELIEF: a player who holds a working process controller faces
    # a lower chance of failing any node whose OWN stated failure mode is
    # holding a continuous process at temperature, rate or composition - a
    # zone-refining run, a Czochralski pull, a fractional distillation, a
    # high-pressure boiler - rather than a one-shot mechanical build. This
    # answers the player who reached zone_refining with a mature economy
    # and complete prerequisites and found only dice waiting: the historical
    # mitigation for "a process you cannot hold at temperature or rate" is
    # closed-loop control (Minorsky 1922, the pneumatic three-term
    # controller, Ziegler-Nichols tuning - see ctl_pneumatic_process_
    # controller in the tree), not a bigger workshop or more capital.
    #
    # WHICH NODES QUALIFY IS DATA, NOT A LIST HERE. A node opts in by
        # carrying failure_kind: "process_control" in the tree itself - the
        # tag lives beside the other properties of the technology (risk,
    # traits) in tech_tree.json / the branch files, the same place every
    # other fact about a node lives. Nine core nodes carry it today
    # (zone_refining, single_crystal, gecl4_purification, ge_reduction,
    # lead_chamber, crucible_steel, high_temp_furnace, steam_high_pressure,
    # electrolysis_industrial), chosen because each one's OWN note already
    # describes a continuous hold-at-setpoint failure character, not because
    # this function needed somewhere to point.
    #
    # BOUNDED, ON PURPOSE. CONTROL_RELIEF_FACTOR is a flat 35% cut, and nothing
    # about it depends on failed_attempts, so it neither stacks unboundedly
    # with retry-learning nor ever reaches zero by itself: a controlled
    # zone_refining run at 0.45 base risk drops to about 0.29 on a first
    # attempt, meaningfully more survivable, still a real coin's chance of
    # failing. RETRY_RISK_FLOOR is untouched (this multiplies alongside it,
    # not instead of it) so the worst case, many failures AND a controller,
    # is 0.45 * RETRY_RISK_FLOOR * CONTROL_RELIEF_FACTOR =~ 0.12, never a
    # formality. The brief was explicit that zone_refining's tension is the
    # game's best late tension and this must not remove it, only mitigate it.
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
    CONTROL_RELIEF_CAPABILITY = "ctl_pneumatic_process_controller"

    def _control_relief_multiplier(self, node_id):
        if self.nodes[node_id].get("failure_kind") != "process_control":
            return 1.0
        if self.CONTROL_RELIEF_CAPABILITY not in self.household.done:
            return 1.0
        return self.CONTROL_RELIEF_FACTOR

    def effective_risk(self, node_id):
        """This node's actual chance of failing on its NEXT attempt, after
        whatever retry-learning its past failures have already bought (see
        _retry_risk_multiplier just above) AND whatever control-theory relief
        a completed process controller has earned it (see
        _control_relief_multiplier just above). Equal to the bare node risk
        the first time anything is tried, with no controller built. A screen
        quoting a node's risk once failed_attempts[k] is above zero, or once
        the controller is done, should read THIS, not the tree's bare
        n["risk"] - that number is no longer what the dice use.
        """
        return (self.nodes[node_id]["risk"] * self._retry_risk_multiplier(node_id)
                * self._control_relief_multiplier(node_id))

    # ---- WHAT A RISKY NODE ACTUALLY COSTS IN CALENDAR TIME -----------------
    # `effective_risk` and `calendar_floor` answer two separate questions -
    # "how likely is the next roll to fail" and "how many years before there
    # even IS a next roll" - and must not be left for a player to multiply
    # together by hand. A 45%-per-attempt, 4-year-floor node is not a
    # 4-year project; on the bare geometric series 1/(1-p) it is 1.82
    # attempts, and even that understates it for anything past the first
    # failure, because retry learning (RETRY_RISK_FLOOR, RETRY_CALENDAR_CAP
    # above) means neither the odds nor the clock a plain geometric series
    # assumes are the ones a second, third or fourth attempt actually faces.
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
        `_complete` (see core.py, where a project's own `st["yrs"]` is
        compared against this), not a second copy of it. Diffusion-limited
        nodes (yrs >= 5) shrink as reputation grows: a civilisation that
        already does a hundred complicated things does not start the social
        diffusion of the hundred-and-first from zero credibility.
        """
        node = self.nodes[node_id]
        floor = node["yrs"]
        if node["yrs"] >= self.DIFFUSION_LIMITED_YEARS_THRESHOLD:   # diffusion-limited nodes, not physical curing
            floor = max(self.CALENDAR_FLOOR_MIN_YEARS,
                        node["yrs"] / (1.0 + self.household.reputation / self.CALENDAR_FLOOR_REPUTATION_SCALE))
        return floor

    def expected_calendar_years(self, node_id, _max_extra_attempts=500):
        """Expected calendar years to SUCCEED at k, counting every retry the
        dice force - not the bare calendar_floor, and not a plain geometric
        series on the raw risk field either. A failure does not roll the
        exact same dice again: the per-attempt risk and the per-attempt wait
        both move on every subsequent attempt, so the true expectation is a
        sum over "the first i attempts all failed" with a shrinking risk and
        a shrinking wait at each step.

        THE RISK TERM IS READ FROM effective_risk(k), NEVER REIMPLEMENTED.
        effective_risk is the one place allowed to know everything that
        moves a node's odds - today that is only retry learning
        (_retry_risk_multiplier), but it is the designated home for any
        OTHER multiplier this society's own choices might someday apply
        (a capability that makes a whole family of processes more
        reliable, say), and this function has no business knowing what
        those are or duplicating how they combine. To ask "what would
        attempt i+1's odds be" for a hypothetical future i without actually
        recording a failure, this stands in for "i failures so far" by
        briefly setting failed_attempts[k] to i, reads effective_risk(k),
        and restores the real count immediately after - in a `finally`, so
        a real failure count is never left clobbered even if something
        above raises. The calendar term has no such second multiplier (see
        _retry_calendar_retain) and is asked the same way, via its own `m`.

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
        floor = self.calendar_floor(node_id)
        initial_failed_attempts = self.household.failed_attempts.get(node_id, 0)
        _had_key = node_id in self.household.failed_attempts
        _active = self.household.active.get(node_id) if node_id in self.household.active else None
        total = 0.0
        survive = 1.0
        attempt_index = initial_failed_attempts
        try:
            while True:
                if attempt_index == initial_failed_attempts and _active is not None:
                    # ALREADY MID-ATTEMPT: use the real elapsed clock, not a
                    # recomputed banked fraction - more honest about a
                    # project already part-way through its current attempt.
                    years_this_attempt = max(0.0, floor - _active.get("yrs", 0.0))
                elif attempt_index == initial_failed_attempts:
                    # NOT ACTIVE: whether this is the very first attempt ever
                    # (i0 == 0) or a restart after a manual `stop` (i0 > 0),
                    # start_project always zeroes `yrs` - see assumption 3 -
                    # so the next attempt pays the full floor either way.
                    years_this_attempt = floor
                else:
                    years_this_attempt = floor * (1.0 - self._retry_calendar_retain(node_id, attempt_index))
                total += survive * years_this_attempt
                # STAND IN FOR "i FAILURES SO FAR", ask effective_risk, then
                # move on - the real count is restored in `finally` below,
                # not here, so an exception mid-loop can never leave it wrong.
                self.household.failed_attempts[node_id] = attempt_index
                survive *= self.effective_risk(node_id)
                attempt_index += 1
                if survive < 1e-12 or attempt_index - initial_failed_attempts > _max_extra_attempts:
                    break
        finally:
            if _had_key:
                self.household.failed_attempts[node_id] = initial_failed_attempts
            else:
                self.household.failed_attempts.pop(node_id, None)
        return total

