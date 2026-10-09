"""The yearly project-progress phase: hours, bills, affordability and finishing.

A part of the year's phases (core_step_phases.py); Sim inherits it through StepPhasesMixin."""

from sim.agents.api import edges


class ProjectProgressPhaseMixin:

    def _step_progress_project(self, node_id, pool_rank, pool_total_this_year,
                              pool_active_count_this_year, remaining, hired_left,
                              arrears_hours_lost, directed_hours_unused,
                              _afford_context=None):
        # One project's share of this year's director hours and money, pulled
        # out of the priority loop in _step_progress() so the loop itself reads
        # as "for each active project, in priority order, give it its turn"
        # rather than burying that in 374 lines of one project's turn. Threads
        # remaining/hired_left through by argument and return, the same shared
        # pool every project in the loop draws from in order; arrears_hours_lost
        # and directed_hours_unused are the two logging lists _step_progress()
        # reports from once, after every project has had its turn, and are
        # appended to here exactly where the original inline code appended to
        # them.
        _pool_rank = pool_rank
        _pool_total_this_year = pool_total_this_year
        _pool_active_count_this_year = pool_active_count_this_year
        _arrears_hours_lost = arrears_hours_lost
        _directed_hours_unused = directed_hours_unused
        project_state = self.state.projects.active[node_id]
        node = self.nodes[node_id]
        project_state["pool_total_this_year"] = _pool_total_this_year
        project_state["pool_active_count_this_year"] = _pool_active_count_this_year
        project_state["pool_rank_this_year"] = _pool_rank
        project_state["pool_remaining_before_this_year"] = round(remaining, 1)
        # A PIPELINE, ONE STAGE PER CONCERN, IN A FIXED ORDER: is there
        # anybody to do the work, how many hours does the project get this
        # year, what labour and bill follow from that, can the household
        # afford the bill, then the bookkeeping and completion check. Split
        # so this method reads as five sentences instead of one project's
        # whole turn in a single block. Every self.rng-touching call these
        # stages make (lab_year_draw is the only one that plausibly draws)
        # runs exactly once, in exactly this order, for exactly this
        # project - the stages are called unconditionally in sequence, and
        # only the two `continue`-turned-early-returns below skip any of
        # them.
        if self._project_progress_trade_gate(node_id, project_state, node):
            return remaining, hired_left, 0.0
        remaining, per, spent_hours, _dir_hours = self._project_progress_offer_hours(
            node_id, project_state, remaining, _pool_total_this_year, _directed_hours_unused)
        _labour = self._project_progress_labour_and_bill(
            node_id, project_state, node, hired_left, per, spent_hours)
        if _labour is None:
            return remaining, hired_left, 0.0
        hired_left, money, refunded = _labour
        money, refunded = self._project_progress_afford_gate(
            node_id, project_state, money, refunded, spent_hours, per, _arrears_hours_lost,
            _afford_context=_afford_context)
        self._project_progress_finish(
            node_id, project_state, money, refunded, spent_hours, _dir_hours,
            _directed_hours_unused, _afford_context=_afford_context)

        return remaining, hired_left, project_state["hours_effective_this_year"]

    def _project_progress_trade_gate(self, node_id, project_state, node):
        # Stage 1 of _step_progress_project: is there anybody to do the
        # work. Returns True when the project is stalled or just halted
        # this year, in which case the caller returns immediately with no
        # hours or money spent - the first of the two `continue`-turned-
        # early-returns the original loop already had. Returns False, and
        # clears stalled_years, when the project can proceed.
        # IS THERE ANYBODY TO DO THE WORK? If a trade this project needs
        # has vanished since it started (the machinists you taught died
        # out, say), nothing can be done on it this year, and your own
        # hours should go somewhere they are useful rather than into a
        # project that cannot absorb them.
        #
        # This matters more than it sounds. Without it a project whose
        # trade had disappeared sat in `active` for ever: hours went in,
        # no money was spent because no work was done, so the bill was
        # never paid, so it could never complete, so it never released
        # the slot. Four of those deadlocked a run at 98 technologies for
        # two hundred and fifty years.
        #
        # ONLY A TRADE THIS PROJECT STILL OWES SOMETHING TO: checked against
        # `_lab_left` (how much of each trade's hours remain to be drawn),
        # NOT node["lab"]'s ORIGINAL total (`want > 0`), which never goes back
        # to zero no matter how much of that trade's hours the project has
        # already drawn. lab_year_draw and trade_draw_plan both correctly
        # stop asking a trade for more once lab_left hits zero; checking the
        # original total here would keep vetoing the project on a trade it
        # no longer needs anything from - the same question `_waiting_on`
        # (protocol.py) already answers correctly off lab_left, so this
        # makes the stall check agree with the one that draws the hours.
        _lab_left = project_state.get("lab_left")
        if _lab_left is None:
            _lab_left = node["lab"]
        blocked = [trade_id for trade_id, want in node["lab"].items()
                   if want > 0 and _lab_left.get(trade_id, want) > 0
                   and self.labour.market_supply(trade_id) <= 0.0]
        if blocked:
            project_state["stalled_years"] = project_state.get("stalled_years", 0) + 1
            project_state["blocked_on_trades"] = blocked
            if project_state["stalled_years"] >= 4:
                self.state.household.log.append((self.state.scenario.year, "HALTED %s: there is nobody here who can "
                                     "do this work (%s). What you spent is lost"
                                 % (node_id, ", ".join(blocked[:2]))))
                self.state.projects.active.pop(node_id, None)
                self.state.projects.bountied.discard(node_id)
            else:
                # WARN BEFORE THE MONEY GOES: a countdown to abandonment
                # running silently, with nothing said until everything
                # spent is taken at once, gives no chance to act. Say it
                # each year, with the number of years left and what would
                # fix it.
                _left = 4 - project_state["stalled_years"]
                self.state.household.log.append((self.state.scenario.year, "%s cannot go on: no %s here. It has "
                                     "%d year%s before it is abandoned and "
                                     "what you spent on it is lost. Teach "
                                     "the trade, or 'stop %s' now and keep "
                                     "your hours"
                                 % (node_id, " or ".join(blocked[:2]), _left,
                                    "" if _left == 1 else "s", node_id)))
                # Nothing happened here this year - say so, rather than
                # leaving last year's hours_offered/effective sitting on
                # the entry looking like they still applied.
                project_state["hours_offered_this_year"] = 0.0
                project_state["hours_effective_this_year"] = 0.0
            return True
        project_state["stalled_years"] = 0
        return False

    def _project_progress_offer_hours(self, node_id, project_state, remaining,
                                     _pool_total_this_year, _directed_hours_unused):
        # Stage 2: how many hours the project gets this year (`per`), what
        # that leaves of the shared pool (`remaining`), and the first of the
        # two places a standing allocation can go unhonoured. Returns the
        # updated remaining, per, spent_hours (for the give-backs later
        # stages compute) and _dir_hours (read again by stage 5's inner-gap
        # check).
        # project_hour_pace (projects.py) is this same formula, read
        # rather than re-derived, so 'work's own pre-sale warning
        # about starving an active project can never disagree with
        # what this loop actually offers it.
        #
        # A STANDING ALLOCATION IS A CEILING, NOT A FLOOR. hour_
        # allocations.get(node_id) is only ever a THIRD candidate in this
        # min() - never a reason to offer MORE than remaining or the
        # project's own pace would otherwise allow - so a directed
        # project can still never outrun the pool it shares with
        # everything else, and never get hours faster than its own
        # calendar floor could ever use. What it changes is ORDER
        # (active_sorted, above) and that an undirected project
        # never crowds this one out of the share the player asked
        # for it to have.
        _dir_hours = self.state.household.hour_allocations.get(node_id)
        _pace_cap = self.project_hour_pace(node_id)
        _project_throttle = self.project_resource_throttle(node_id)
        if _dir_hours and _dir_hours > 0:
            per = min(remaining, _pace_cap, _dir_hours) * _project_throttle
        else:
            per = min(remaining, _pace_cap) * _project_throttle
        remaining -= per
        # WHAT WAS ACTUALLY TAKEN OFF, which is not the same as what was
        # offered: `per` is allowed to exceed ph_left (the max() above
        # offers a full year's worth even to a project with an hour to
        # run), and the subtraction clamps at zero. A refund computed from
        # `per` instead of from what was truly spent could hand back more
        # than was ever taken - a project with 10 hours left offered 500
        # would have its 10 taken and be handed 200 back, ending the year
        # with twenty times the hours it began with, founder_hours_left
        # larger than founder_hours_total. You cannot be refunded work you
        # never did.
        spent_hours = min(per, project_state["ph_left"])
        project_state["ph_left"] = max(0.0, project_state["ph_left"] - per)
        self.state.founder.director_hours_spent_founder += per if self.state.founder.founder_alive else 0
        # Hours OFFERED this year vs hours that actually did anything.
        # `refunded` tracks the difference: hours credited back to
        # ph_left below because a trade or the money to pay for it
        # fell short. This must stay visible to the player: showing only
        # the net hours left, with nothing recording what was offered
        # versus refunded, reads as confusing and artificial when half a
        # year's hours come back with no explanation of why. See
        # hours_this_year in `state`.
        project_state["hours_offered_this_year"] = round(per, 1)
        # WHAT THE PLAYER ACTUALLY ASKED FOR, READ BACK AT THE END OF
        # THE YEAR - `portfolio` and `why` print this field verbatim,
        # same reasoning as pool_total_this_year and its neighbours
        # just above: never recompute a number a player is told,
        # always read the one this loop actually used.
        project_state["hours_directed_this_year"] = (round(_dir_hours, 1)
                                          if _dir_hours else None)
        # SAY SO WHEN THE PROMISE ITSELF WAS NOT KEPT, before any
        # trade or money shortfall even has a chance to bite further
        # in. A directive can be cut short right here, two ways: the
        # POOL had already given the rest away (to a higher-priority
        # directed project, or simply was not big enough for every
        # standing order at once), or this project's OWN pace -
        # what is left to do, or its calendar floor - could not use
        # that many hours even with the whole pool behind it. Either
        # is a real, nameable reason; "it disappeared" is not.
        if _dir_hours and _dir_hours > 0 and _dir_hours - per > 1.0:
            if (_project_throttle < 0.98 and self.state.holdings.binding
                    and _pace_cap >= _dir_hours - 0.5):
                _directed_hours_unused.append((node_id, round(_dir_hours - per, 0),
                    "a shortage of %s has every project (this one "
                    "included) running at %d%% of the pace its "
                    "hours alone would allow"
                    % (self.state.holdings.binding, round(_project_throttle * 100))))
            elif _pace_cap * _project_throttle < _dir_hours - 0.5:
                _directed_hours_unused.append((node_id, round(_dir_hours - per, 0),
                    "its own pace this year - at most %s hours, set "
                    "by how much of it is left to do or its "
                    "calendar floor, not by your hours - could not "
                    "use the rest" % "{:,.0f}".format(
                        _pace_cap * _project_throttle)))
            else:
                _directed_hours_unused.append((node_id, round(_dir_hours - per, 0),
                    "your other standing allocations and active "
                    "work already claimed the rest of this year's "
                    "%s hours before this one's turn came ('priority "
                    "<id> first' moves a project up the queue)"
                    % "{:,.0f}".format(_pool_total_this_year)))
        return remaining, per, spent_hours, _dir_hours

    def _project_progress_labour_and_bill(self, node_id, project_state, node,
                                          hired_left, per, spent_hours):
        # Stage 3: the labour this project can actually hire this year and
        # the bill that follows from it. Returns None when the project was
        # abandoned this year - the second of the two `continue`-turned-
        # early-returns - in which case the caller returns immediately.
        # Otherwise returns the updated hired_left, money and refunded.
        refunded = 0.0
        project_state["yrs"] += 1
        frac = min(1.0, 1.0 / max(1.0, node["yrs"]))
        # Diagnostic callers can construct active-project dictionaries
        # directly, so initialise an omitted bill defensively.
        if project_state.get("cost_left") is None:
            project_state["cost_left"] = max(0.0, self.project_cost(node_id) - project_state["spent"])
        # LABOUR BY TRADE. The old model pooled every trade into one
        # bucket of hired hours, so 450 hours of engineer and 450 hours
        # of labourer were the same resource. They are not, and the wage
        # table has said so all along. What binds now is the scarcest
        # trade this project actually needs.
        #
        # HOURS ARE A TOTAL AND A CEILING NOW, NOT A FIXED ANNUAL TOLL.
        # See ProjectsMixin.lab_year_draw (projects.py) for the finding
        # that forced this and the reasoning behind the new shape; this
        # call site only has to act on what it returns.
        hired_hours, worst, frac, _abandon = self.lab_year_draw(node_id, project_state, frac, hired_left)
        if _abandon:
            self.state.household.log.append((self.state.scenario.year, "ABANDONED %s: %s" % (node_id, _abandon)))
            self.state.projects.active.pop(node_id, None)
            self.state.projects.bountied.discard(node_id)
            return None
        if worst < 1.0:
            # NEVER ALL OF IT: the refund says "hours offered but not
            # usable, because the trade was booked", and with no floor
            # under it could hand back every hour that had actually gone
            # in - leaving a project's founder-hours sit unchanged forever
            # whenever its scarcest trade stays short, the bill fully paid,
            # making no progress at all while holding an entire trade's
            # pool and freezing other projects behind it.
            #
            # If a fraction `worst` of the work could be done, then a
            # fraction `worst` of it WAS done, and that much can never
            # be given back. Progress is strictly positive whenever
            # anybody at all can be found.
            give_back = min(spent_hours - refunded,
                            per * 0.4 * (1.0 - worst),
                            spent_hours * (1.0 - worst))
            project_state["ph_left"] += max(0.0, give_back)
            refunded += max(0.0, give_back)
            # Remember it: `waiting_on` reporting "money" for a project
            # whose real block is a fully booked trade, not an actual spend
            # cap, is a misleading label even though the underlying
            # mechanic is correct - a player watching a large balance sit
            # unspent against "money" owed can reasonably conclude the
            # spend cap itself is broken. (short_of_trade itself is set
            # inside lab_year_draw, against the same pace this comment
            # describes.)
        if hired_hours > hired_left:
            frac *= hired_left / max(hired_hours, 1e-9)
            hired_hours = hired_left
        # THE INSTALMENT IS WHAT A CONSTRAINED YEAR CAN DO; THE BILL IS
        # WHAT IS LEFT: working from the already-scaled `frac`, applied
        # directly to `cost_left`, means a shortage sets how FAST a
        # project can be paid off and never stops the last payment
        # landing. Working the payment out first and then multiplying it
        # by each shortage in turn would instead pay a FRACTION OF WHAT
        # WAS LEFT every year, forever, once the remaining balance is
        # smaller than a year's instalment - a geometric decay that
        # approaches zero and never reaches it, while completion needs the
        # bill down to half a denarius.
        money = min(project_state["cost_left"], self.project_cost(node_id) * frac)
        hired_left -= hired_hours
        return hired_left, money, refunded

    def _project_progress_afford_gate(self, node_id, project_state, money, refunded,
                                     spent_hours, per, _arrears_hours_lost,
                                     _afford_context=None):
        # Stage 4: can the household actually afford this year's bill.
        # Returns the updated money and refunded.
        # You may spend into debt, up to what someone will lend you, and
        # no further. Beyond that the work simply does not get paid for
        # this year, and a year nobody was paid for is a year of little
        # progress. What must NOT happen is the bill being forgiven.
        #
        # The margin is deliberate. Spending to the last denarius of your
        # credit means next year's rent breaches the limit and the
        # creditors halt every project you have, which turns "I was
        # ambitious" into "everything I had in hand was destroyed". A
        # lender who will advance you a thousand will not let you draw
        # the last two hundred of it against a half-built balloon.
        # Reserve next year's fixed costs AND most of the credit line.
        # Drawing the line to its last denarius risks destroying everything
        # else in hand: the limit itself falls as reputation and revenue
        # fall, so a balance exactly at the limit this year is over it next
        # year, and over the line every project in progress is halted at
        # once.
        # Reserve only the SHORTFALL, not the whole running cost: this
        # year's rent and wages have already been taken out of capital at
        # the top of step(), so reserving them again would leave a
        # household whose income comfortably covers its costs unable to
        # spend a single denarius on its own projects.
        if _afford_context is not None:
            revenue = _afford_context["revenue"]
            upkeep = _afford_context["upkeep"]
            mine_operating = _afford_context["mine_operating"]
        else:
            revenue = self.revenue()
            upkeep = self.upkeep()
            mine_operating = self.mine_operating_cost()
        fixed = (
            self.living_cost(_rev=revenue, _upkeep=upkeep)
            + upkeep
            + mine_operating
        )
        reserve = max(0.0, fixed - revenue)
        purse = (
            self.state.household.capital
            + self.credit_limit(_rev=revenue, _upkeep=upkeep) * 0.6
            - reserve
        )
        # NOTHING OWED IS NOT THE SAME AS NOTHING AFFORDABLE: a project
        # with cost_left already at zero asks for money=0 this year, and
        # the money>purse test must not fire just because purse itself has
        # gone negative from deep arrears unrelated to this project's own
        # bill - a fully paid project, needing not one more denarius, must
        # still be free to make purely calendar-waiting progress. The gate
        # is on the household's purse only when this project actually
        # needs something from it.
        if money > 0 and money > purse:
            # PROPORTIONAL, not a flat half: the refund must scale by how
            # underfunded the purse actually is (`funded_frac`), the same
            # way the trade-shortage case two blocks up already scales its
            # refund by how much of the need went unmet (worst). A flat
            # per*0.5 refund whenever the purse falls short AT ALL, whether
            # by one denarius or by the whole bill, would give a project
            # funded to 95% of what it needed the same fixed half-progress
            # loss as one funded to 5%.
            funded_frac = 0.0 if money <= 0 else max(0.0, min(1.0, purse / money))
            money = max(0.0, purse)
            # Capped at what was actually taken off, and at what has not
            # already been handed back by the trade-shortage refund
            # above. See spent_hours: you cannot be refunded work you
            # never did, and you cannot be refunded the same hour twice.
            give_back = min(spent_hours - refunded, per * (1.0 - funded_frac))
            project_state["ph_left"] += max(0.0, give_back)
            refunded += max(0.0, give_back)
            project_state["underfunded_this_year"] = True
            # WHY, not just that: hours reported as "offered" with none
            # "effective" is meaningless without a reason. Arrears are the
            # reason: the purse a project may draw on is what you hold
            # plus part of your credit, less what your fixed costs need,
            # and in arrears that is nothing at all.
            project_state["why_underfunded"] = (
                "in arrears: after fixed costs there is nothing left to "
                "draw on, so the hours offered this year did almost "
                "nothing" if self.state.household.capital < 0 else
                "this year's instalment is more than the purse will bear")
            # SAY IT NOW, NOT ONLY WHEN ASKED. `why_underfunded` sits on
            # the project and answers the question if a player thinks
            # to check `why` or `portfolio` - but the founder-hours lost
            # here never come back, whatever the player does next, and
            # nothing prompted them to look. Recorded here (only the
            # arrears case, only if it actually cost real hours) and
            # logged once below, after the loop.
            if self.state.household.capital < 0 and give_back > 1.0:
                _arrears_hours_lost.append((node_id, round(give_back, 0)))
        else:
            project_state.pop("underfunded_this_year", None)
            project_state.pop("why_underfunded", None)
        return money, refunded

    def _project_progress_finish(self, node_id, project_state, money, refunded,
                                spent_hours, _dir_hours, _directed_hours_unused,
                                _afford_context=None):
        # Stage 5: spend the money, record the hours actually done, the
        # second place a standing allocation can go unhonoured, and the
        # completion check. Nothing to return - project_state carries every
        # result the caller (and the rest of the game) reads back.
        self.pay_edge(edges.EDGE_SUPPLIERS, money, "project payments")
        self.state.household.total_spend += money
        project_state["spent"] += money
        project_state["cost_left"] = max(0.0, project_state["cost_left"] - money)
        # spent_hours, NOT per. `per` is what was OFFERED, and it is
        # allowed to exceed the hours the project actually had left; the
        # refunds above are capped at spent_hours for exactly that
        # reason, and this line was left uncapped. A sweep of the
        # playtest notes found a project reporting 387.2 effective hours
        # a year for four consecutive years while founder_hours_left sat
        # unchanged at 112.8 - work reported that provably did not
        # happen, about the one resource the whole game is built on.
        project_state["hours_effective_this_year"] = round(max(0.0, spent_hours - refunded), 1)
        # Accumulated into hours_effective_total by the caller, _step_progress,
        # which sums this project's own returned effective hours into the
        # year's running total - see the return at the end of this method.
        # THE SECOND WAY A DIRECTIVE GOES UNHONOURED: OFFERED, THEN
        # HANDED BACK. Unlike the check above this one, it must NOT
        # fire just because spent_hours fell short of `per` - a
        # project a few hours from finished is offered a whole
        # year's pace and only needs a sliver of it, which is not a
        # shortage of anything, it is the project ending. Gated on
        # why_underfunded/short_of_trade actually being SET this
        # year - fields only the money and trade-shortage branches
        # above ever write - so this can only ever name a real
        # shortfall, never mistake "it finished" for one.
        if _dir_hours and _dir_hours > 0:
            _inner_gap = project_state["hours_offered_this_year"] - project_state["hours_effective_this_year"]
            # DEEP ARREARS ALREADY GETS ITS OWN LINE, BELOW - "IN
            # ARREARS: ... did almost nothing this year" - and it is
            # the sharper warning of the two. Saying the same
            # shortfall twice in two different voices is not
            # clearer, it is just noise; this fires only for the
            # money-short case arrears does NOT already cover (the
            # purse-can-only-absorb-so-much-a-year pace, which is
            # real money trouble without capital actually being
            # negative).
            if _inner_gap > 1.0 and project_state.get("why_underfunded") and self.state.household.capital >= 0:
                _directed_hours_unused.append(
                    (node_id, round(_inner_gap, 0), project_state["why_underfunded"]))
            elif _inner_gap > 1.0 and project_state.get("short_of_trade"):
                _directed_hours_unused.append((node_id, round(_inner_gap, 0),
                    self.trade_shortfall_note(project_state)))
        # Count it HERE, after the hired-hours scaling and the
        # affordability clamp, not before them: accumulating the notional
        # figure instead would make project_spend_last_year disagree with
        # the actual capital movement.
        self._spend_this_year = getattr(self, "_spend_this_year", 0.0) + money
        # calendar_floor(node_id), NOT a second copy of this formula -
        # expected_calendar_years (projects.py) needs the identical
        # figure to project retries honestly, and a rule living in
        # two places is how this kind of arithmetic drifts apart.
        floor = self.calendar_floor(node_id)
        # THE BILL HAS TO BE PAID. Hours done and years elapsed are not
        # enough; if the money never arrived, the thing was never built.
        # HALF AN HOUR IS NOTHING LEFT TO DO: the give-back hands back a
        # fraction of what was offered, so on a throttled project ph_left
        # decays geometrically towards zero and never exactly reaches it -
        # a project could otherwise sit at some vanishingly small residual,
        # bill paid, complete in every practical sense except an exact
        # comparison. The bill already has this exact fix and this exact
        # reason (see `money` just above, and cost_left <= 0.5 on the same
        # line); hours need it too.
        if project_state["ph_left"] < 0.5:
            project_state["ph_left"] = 0.0
        if project_state["ph_left"] <= 0 and project_state["yrs"] >= floor:
            self.settle_cost_tail(node_id, project_state)
        if project_state["ph_left"] <= 0 and project_state["yrs"] >= floor and project_state["cost_left"] <= 0.5:
            self._complete(node_id)
            if _afford_context is not None:
                _afford_context["revenue"] = self.revenue()
                _afford_context["upkeep"] = self.upkeep()
        elif project_state["ph_left"] <= 0 and project_state["yrs"] >= floor and project_state["cost_left"] > 0.5:
            project_state["waiting_on_money"] = True

    def _step_progress(self, pool, hired_left):
        # 5. progress. Director hours go to the HIGHEST-PRIORITY active projects
        #    first, not spread evenly: a director who gives every project equal
        #    attention finishes nothing, which is a real failure mode but not the
        #    one we are trying to model here.
        #
        active_sorted = self.hour_priority_queue()
        remaining = pool
        self.state.projects.trade_hours_used = {}
        # Summed as the loop runs, not re-read from self.state.projects.active afterwards,
        # because a project that completes THIS year is popped from
        # self.state.projects.active before we would get to it. See the hours_this_year
        # summary this feeds, below the loop.
        hours_effective_total = 0.0
        # NAMED, NOT JUST STORED ON THE PROJECT: `why_underfunded` (set below,
        # in the arrears branch) answers "why is this stalled" only when a
        # player thinks to ask `why` or `portfolio`, which is not the same
        # as announcing it. Founder-hours are the one resource that never
        # banks: a year of them lost to arrears and never
        # announced is the least fair thing a status screen can leave out.
        # Collected here and logged once, after the loop, so a step that
        # starves three projects at once gets one clear line, not three.
        _arrears_hours_lost = []
        # AN ALLOCATION THE PLAYER EXPLICITLY ASKED FOR, AND DID NOT GET.
        # hour_allocations is a promise the player made about their OWN one
        # resource that never banks; silently handing back less than it
        # asked for - because the project's own pace, its trade, or its
        # money was the real ceiling, not the founder's hours - is the same
        # unfairness the arrears line above exists to stop, aimed at a
        # player who took the extra step of directing their hours on
        # purpose. Collected here, per project, and logged once below.
        _directed_hours_unused = []
        # WHY A PROJECT IS GETTING THE SHARE IT IS GETTING, STORED HERE AND
        # NOWHERE ELSE: the only honest way to explain a project's share of
        # this year's directed hours is to read the numbers this loop
        # actually used, never to guess at them again from outside.
        # pool_total/active_count
        # are the same for every project processed this step; rank and
        # remaining_before are this project's own position in the queue and
        # what was left of the pool when its own turn came. _agent_state and
        # `portfolio` (protocol.py) read these fields back verbatim - they do
        # not, and must not, recompute a share that could then disagree with
        # what this loop actually handed out.
        _pool_total_this_year = pool
        _pool_active_count_this_year = len(active_sorted)
        _afford_context = {
            "revenue": self.revenue(),
            "upkeep": self.upkeep(),
            "mine_operating": self.mine_operating_cost(),
        }
        for _pool_rank, node_id in enumerate(active_sorted, start=1):
            remaining, hired_left, _effective = self._step_progress_project(
                node_id, _pool_rank, _pool_total_this_year, _pool_active_count_this_year,
                remaining, hired_left, _arrears_hours_lost, _directed_hours_unused,
                _afford_context=_afford_context)
            hours_effective_total += _effective
        # ARREARS COSTS YOU THE YEAR'S HOURS, NOT JUST THE MONEY - SAY SO:
        # a project sitting at "did almost nothing" with no explanation on
        # the turn itself leaves founder-hours lost to arrears
        # undiscoverable except by several turns of confusion. Founder-hours
        # are the one resource in this whole model that never banks (see step 5b and
        # `state`'s free_hours_going_unused): a year of them lost silently is
        # worse than a year of money lost, because money can be earned back
        # on the same footing next year and this cannot be earned back at
        # all. Named per project, so 'why <id>' and this line never disagree
        # about which project or how much.
        if _arrears_hours_lost:
            _total_lost = sum(hours for _, hours in _arrears_hours_lost)
            _names = ", ".join("%s (%s hr)" % (node_id, "{:,.0f}".format(hours))
                                for node_id, hours in _arrears_hours_lost)
            self.state.household.log.append((self.state.scenario.year, "IN ARREARS: %s founder-hours meant for %s did "
                                 "almost nothing this year, on top of the money "
                                 "- that time does not come back, arrears or not. "
                                 "'work' sells idle hours for wages instead of "
                                 "losing them here; clearing the arrears is what "
                                 "stops it happening again"
                             % ("{:,.0f}".format(_total_lost), _names)))

        # A STANDING ALLOCATION THE PLAYER GAVE, AND DID NOT GET - SAID, NOT
        # LEFT FOR THEM TO NOTICE. `allocate` is a promise about the one
        # resource that never banks; silently falling short of it is the
        # same unfairness the arrears line above exists to stop, aimed at a
        # player who took the extra step of directing their hours on
        # purpose rather than leaving the split to priority order. Sorted
        # by id for a deterministic order across runs with the same seed -
        # several projects can be cut short in the same year.
        self.report_unused_directed_hours(_directed_hours_unused)

        # Snapshot BEFORE 5b spends more of `remaining` on wage work: otherwise
        # offered_to_projects below double-counts wage hours as though they had
        # been offered to projects too, since 5b draws from the same pool.
        remaining_after_projects = remaining
        return remaining, remaining_after_projects, hours_effective_total
