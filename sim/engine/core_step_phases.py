"""The year's phases: what step() calls, in the order it calls them.

These are methods of Sim, living in a mixin (StepPhasesMixin) rather than
directly in core.py's `class Sim(...)`. `Sim.step()` itself stays in
core.py: it is the orchestrator, not one of the phases, and it is short
(42 lines) because it only calls `self._step_apprenticeships()` and the
other named phases this file holds - method resolution walks the whole
MRO, so it does not matter to `step()` that these live on StepPhasesMixin
rather than directly on Sim.

Each phase method below still reads and writes exactly the self.* state it
needs, UNASSIGNED to any one domain mixin's territory: this file groups
the phases by "step() calls them in this order", not by "the labour phase
belongs to labour.py, the money phase belongs to economy.py". Assigning
each phase's state to a specific domain mixin is a distinct, harder job
(see docs/architecture/SIM_DECOMPOSITION_REVISITED.md's staged proposal)
that this file does not attempt - do not assume a phase here can be moved
into a domain file without first working out its self.* footprint.
"""
import random
from dataclasses import dataclass

from .hour_offer import work_order_shortfall
from .units_prose import plain_number
from .bondage_workshop_rules import bondage_repayment, serve_bondage_year
from .reteach_rules import past_cooldown, teaching_budget, trade_is_gone, PROJECT_IN_HAND_SCORE
from sim.polity.api import CloseStandingYear, RenewStanding
from .invariants import check_labour_market_invariants, check_yearly_invariants
from .step_phase_money import MoneyPhaseMixin
from .step_phase_projects import ProjectProgressPhaseMixin
from .step_phase_staff import StaffPhaseMixin
from sim.reporting.api import RecordEvent


@dataclass(frozen=True)
class StepContext:
    """Immutable dependencies used by the turn phases."""
    trade_family: object
    invariant_checker: object


class StepPhasesMixin(StaffPhaseMixin, MoneyPhaseMixin, ProjectProgressPhaseMixin):
    """Composition point for the named phases Sim.step() calls, in order. The staff, money,
    materials and project-progress phases live in step_phase_*.py (the start of projects is the projects module's
    phase) and come in through the
    bases above; the rest are below. Sim inherits this mixin, so step() calls
    self._step_whatever() exactly as if these methods were defined directly on Sim.
    """

    def verify_step_invariants(self):
        """Validate this turn without reading configuration from globals."""
        self.step_context.invariant_checker(self.state)
        check_yearly_invariants(self)
        return check_labour_market_invariants(self)

    def _step_apprenticeships(self):
        # 0. PEOPLE WHOSE APPRENTICESHIP ENDED, FIRST, BEFORE THE YEAR'S WORK
        #    IS HANDED OUT: a man who finishes his training at the turn of the
        #    year works that year, so a machinist promised "ready in 102" must
        #    be usable in 102, not only from 103.
        # People bought this year are not artisans this year.
        if self.state.household.training:
            still = []
            for row in self.state.household.training:
                cap, completion_year = row[0], row[1]
                trade = row[2] if len(row) > 2 else None
                count = row[3] if len(row) > 3 else 0.0
                if self.state.scenario.year >= completion_year:
                    if trade:
                        # A trade you taught. They are now yours to pay, and
                        # they are that trade and no other.
                        self.labour.add_employed(trade, count)
                        self.send(RecordEvent.of("training_finished", "%g %s%s finish their training"
                                         % (count, trade, "s" if count != 1 else "")))
                        self.labour.resync_pools()
                    else:
                        # They are trained now, so _resync_pools counts them
                        # from the people you actually hold - see the note
                        # there about why adding to self.state.household.artisans directly was
                        # thrown away at the next call.
                        self.send(RecordEvent.of("bought_people_trained", "%g of the people you bought finish "
                                         "learning the work" % round(cap / 0.55, 1)))
                else:
                    still.append(row)
            # BEFORE the resync, not after: _resync_pools counts who is still
            # learning off this very list, so recomputing while the matured row
            # was still on it cost a whole extra year of everybody's time.
            self.state.household.training = still
            self.labour.resync_pools()

    def begin_world_year(self):
        """What the society notes before the year starts."""
        self.refresh_derived_nodes()
        self.refresh_farm_territory()
        # open every book entry at the year's start, so a read before the first step cannot open one at another state
        self._open_market_book()

    def _run_seat_prelude(self):
        """What the acting seat does before it starts new projects."""
        self._step_teach_trades()              # 4a. teach the trades this society does not have
        self._step_standing_work_directive()   # 4a(ii). the standing "work" directive

    def _run_seat_work(self):
        """What the acting seat does with its year once the projects are started and the materials seen to (the
        phases `seat_prelude`, `start_projects` and `materials` before it)."""
        pool, hired_left = self.view("start_hours")()   # 4b. measured by the start of projects
        # 5. progress, director hours
        remaining, remaining_after_projects, hours_effective_total = (
            self._step_progress(pool, hired_left))
        # 5b. if there is no work and no money, take a job
        remaining = self._step_wage_fallback(remaining)
        # 6. reputation, familiarity, protection, scandal
        self._step_reputation(pool, remaining, remaining_after_projects, hours_effective_total)
        self._step_bondage()                   # 6b. serving out a debt

    def _step_teach_trades(self):
        # 4a2. TEACH THE TRADES THIS SOCIETY DOES NOT HAVE. The optimizer has to
        #      do this for itself or half the tree is unreachable; a player does
        #      it with `train`, or turns this on.
        if self.state.founder.policy.get("auto_train", not self.manual):
            want = {}
            # LOCAL, PER-YEAR MEMO for market_supply()/trade_available().
            # Both are pure functions of staff and trades_created, which this
            # whole block only READS - train(), below, adds to trades_created,
            # but that happens once, at the very end, after every use of these
            # memos - so the same handful of distinct trade names (maybe
            # thirty) get recomputed from scratch once per NODE that lists
            # them in `lab`, and hundreds of nodes across the tree share the
            # same absent trade (machinist, engineer, ...). This dict is a
            # plain local, created fresh every call and discarded when the
            # block ends, so it needs no invalidation logic at all: nothing
            # outside this block ever reads it, so it cannot go stale.
            _ms_memo, _ta_memo = {}, {}
            def _market_supply(trade):
                value = _ms_memo.get(trade)
                if value is None:
                    value = _ms_memo[trade] = self.labour.market_supply(trade)
                return value
            def _trade_avail(trade):
                value = _ta_memo.get(trade)
                if value is None:
                    value = _ta_memo[trade] = self.labour.trade_available(trade)
                return value
            # Anything already in hand that has lost its trade comes FIRST: those
            # projects are burning a slot and will be halted if nobody turns up.
            for node_id in self.state.projects.active_keys_sorted():
                for trade_id in self.nodes[node_id]["lab"]:
                    if _market_supply(trade_id) <= 0.0:
                        want[trade_id] = want.get(trade_id, 0) + PROJECT_IN_HAND_SCORE
            # WORK THE PLAYER COULD START TODAY, not the whole tree. The old
            # test was "direct prerequisites satisfied", which is not "wanted":
            # it looked past cost, staff, state approval and every OTHER trade
            # a node needs, so it walked deep into the order training engineers,
            # then chemists, machinists and opticians, with no active project
            # asking for any of them. Its own description promises "when a
            # project needs them", and a project three tiers away with money
            # you do not have is not a project you need anything for yet.
            # ignore_trade asks the one question that answers that: if this
            # trade existed, would everything ELSE already let it start?
            # EXISTING IS NOT THE SAME AS ANYBODY BEING LEFT. A trade you
            # taught stays "available" for ever, so once the last machinist
            # had died of old age this loop skipped every node that needed
            # one and nobody was ever taught again. A Rome run built 829
            # technologies, sat on 31.9M denarii, and could not begin
            # precision_three_plate - which gates master_screw, the screw
            # lathe and the entire precision branch, ninety-nine of the
            # hundred and forty-six nodes on the road to the goal. This is
            # the same distinction start_reason learned an hour earlier.
            # Hoisted out of the loop below: it closes only over `self` and
            # the memos above, never over the loop variable `node_id`, so defining
            # it fresh on every one of ~2,800 iterations bought nothing.
            #
            # _is_gone(trade) ITSELF IS NOW MEMOIZED TOO (_gone_memo), for the same
            # reason _market_supply/_trade_avail already are: it reads only
            # _trade_avail(trade), _market_supply(trade) and
            # self._trade_headcount_pending(trade), and the last of those
            # (labour.py) reads only self.state.household.training and self.state.household.employees -
            # neither mutated anywhere in this block; train(), at the very
            # end of it, is the only thing that changes either, exactly as
            # the comment above already established for the other two. So
            # _is_gone(trade) is just as pure a function of (staff, trades_created)
            # across this whole block as they are, and is safe to cache the
            # same way.
            #
            # Caching matters here: `order` has ~2,800 nodes, many naming the
            # same handful of distinct trades, so recomputing `_is_gone(trade)` from
            # scratch for every node that names a trade costs one Python
            # function call per node even after the first node already
            # worked out the answer. `_is_gone` below answers the identical
            # question, through the identical `any()` (so a node whose FIRST
            # lab trade is already known gone, or one that fails
            # start_reason() right after, costs exactly what it always
            # did - no extra work done on the strength of a guess that it
            # would be needed), but every trade's verdict is computed once
            # and reused for every later node that names it, rather than
            # recomputed from scratch each time.
            _gone_memo = {}
            def _is_gone(trade):
                value = _gone_memo.get(trade)
                if value is None:
                    value = _gone_memo[trade] = trade_is_gone(
                        _trade_avail(trade), _market_supply(trade), self.labour.trade_headcount_pending(trade))
                return value
            for node_id in self.order:
                if node_id in self.state.projects.done or node_id in self.state.projects.active:
                    continue
                node = self.nodes[node_id]
                if not any(_is_gone(trade_id) for trade_id in node["lab"]):
                    continue
                if not self.start_reason(node_id, ignore_trade=True, _why=False)[0]:
                    continue
                for trade_id in node["lab"]:
                    if _is_gone(trade_id):
                        want[trade_id] = want.get(trade_id, 0) + 1
            # NOT EVERY YEAR: teaching two of a trade costs about nine hundred
            # of the founder's two thousand hours plus their keep, so
            # re-teaching a lost trade every single year it qualifies would
            # turn into a teaching treadmill that eats most of a run's
            # output. A trade is worth restoring; it is not worth half of
            # every year for ever.
            _taught = self.state.household.last_taught
            want = past_cooldown(want, _taught, self.state.scenario.year, self.RETEACH_EVERY)
            # AND ONLY IF YOU CAN PAY THEM: train() checks hours, literacy and
            # household room but nothing here about money, so teaching a
            # trade a household cannot actually afford to keep paid turns
            # every year after into a wage bill that eats its whole income.
            # A trade you cannot pay for is not a trade you have; it is a
            # wage bill that stops you building anything.
            #
            # Two standards, because the two cases are not alike. A trade a
            # project ALREADY IN HAND is waiting on (scored 500 above) is worth
            # borrowing against: that work is paid for and stops without it.
            # A trade for something you might start one day has to come out of
            # what you are actually clearing.
            _tr_rev = self.revenue()
            _tr_upkeep = self.upkeep()
            _spare_tr = _tr_rev - _tr_upkeep - self.living_cost(_rev=_tr_rev, _upkeep=_tr_upkeep)
            for trade_id, _score in sorted(want.items(), key=lambda kv: (-kv[1], kv[0]))[:1]:
                _wages = 2.0 * self.labour.market.quote_annual(trade_id)
                _budget = teaching_budget(_score, _spare_tr, self.state.household.capital)
                if _wages > _budget:
                    continue
                _first = trade_id not in self.state.household.trades_created
                taught, _msg = self.labour.train(trade_id, 2)
                # THE COOLDOWN IS ON TEACHING, NOT ON TRYING. Recording the
                # attempt meant a refusal - no room in the household, no hours
                # left, nobody to teach from - burned the trade's whole
                # twenty-five years, so the run went on needing machinists and
                # never asked again.
                if taught:
                    _taught[trade_id] = self.state.scenario.year
                    self.send(RecordEvent.of("teaching_begun", "you begin teaching the first %ss this "
                                         "world has ever had" % trade_id if _first else
                                     "the last %ss are gone; you begin teaching "
                                     "more" % trade_id))

    def _step_standing_work_directive(self):
        # 4a(ii). THE STANDING "WORK" DIRECTIVE. `work` (protocol.py) sells
        # hours for wages the moment a player types it; `allocate` lets them
        # say "sell N hours a year this way" ONCE and have it happen every
        # year without retyping it, the same standing-instruction idea as
        # the project directives just below. Run BEFORE `pool` is struck so
        # director_hours_committed() (which counts wage hours already sold
        # this year) sees it, exactly as it would if the player had typed
        # `work` by hand a moment ago.
        #
        # TOPPED UP, NOT DOUBLED. A player who already called `work` by hand
        # earlier this same turn has already sold some of the hours this
        # directive wants; this only sells the remainder, never the whole
        # directive again on top of what was already sold.
        _wd = self.state.household.hour_allocations.get("work")
        if _wd and _wd > 0 and self.state.household.work_trade:
            _already = self.state.household.wage_hours_this_year
            _want = work_order_shortfall(_wd, _already)
            if _want > 0.5:
                _room = max(0.0, self.labour.director_pool() - self.labour.director_hours_committed())
                _take = min(_want, _room)
                _got = 0.0
                if _take > 0.5:
                    _pay, _werr = self.labour.work_for_wages(self.state.household.work_trade, _take)
                    # pay > 0 with an error is a WARNING (a bad trade, or
                    # starving an active project of its last hours), not a
                    # refusal - see work_for_wages's own docstring. The sale
                    # happened either way; only a genuine refusal (pay <= 0)
                    # means none of it landed.
                    if _pay > 0 or not _werr:
                        _got = _take
                # SAY SO, THE SAME WAY AN UNHONOURED PROJECT DIRECTIVE DOES,
                # BELOW. A standing instruction nobody is told failed is the
                # same unfairness either way: the founder-hours it asked for
                # either went unsold or went somewhere the player never
                # chose.
                _work_reason = ("room" if _room < _want else "market")
                if _wd - (_already + _got) <= 1.0:
                    self.clear_unused_hours_report("work")
                elif self.unused_hours_is_news("work", [round(_wd), _work_reason]):
                    self.send(RecordEvent.of("directed_hours_unused", "DIRECTED HOURS UNUSED: your standing "
                        "order to sell %s hours a year as a "
                        "%s only managed %s this year - %s. "
                        "'allocate' changes or clears it"
                        % (plain_number(_wd), self.state.household.work_trade,
                           plain_number(_already + _got),
                           "no more of your own hours were left "
                           "to sell once your projects and "
                           "training had theirs"
                           if _room < _want else
                           "nobody here will pay for that trade "
                           "any longer"), trade=self.state.household.work_trade, reason="no_hours_left" if _room < _want else "nobody_pays"))

    def _step_wage_fallback(self, remaining):
        # 5b. IF THERE IS NO WORK AND NO MONEY, TAKE A JOB. A man who arrives
        #     with four hundred denarii and a lens does not sit watching his
        #     savings run out; he teaches, or writes, or sets bones for money. It
        #     is in the protocol as `work` for a player and the optimizer had no
        #     equivalent, so a single bad year in the opening decade could end a
        #     run: one Rome seed earned four technologies in five hundred years
        #     because a fire in 103 took a fifth of everything it had.
        if (not self.manual and remaining > self.WAGE_FALLBACK_MIN_HOURS
                and (self.state.household.capital < self.living_cost() * self.WAGE_FALLBACK_LIVING_COST_YEARS
                     or not self.state.projects.active)):
            trade = ("scholar" if self.labour.effective_scholars() >= 1 else "scribe")
            hours = min(remaining, self.WAGE_FALLBACK_MAX_HOURS)
            # ONLY IF IT PAYS BETTER THAN THE STANDING JOB IT TAKES THE HOURS FROM: a founder who already
            # sells these hours in a trade does not move them to a worse-paid one.
            # NOT `pool`: that name already holds the year's project budget,
            # computed at 4b. Reusing it here would overwrite it, so
            # hours_this_year would then report "offered_to_projects"
            # against the WHOLE year instead of against the project budget,
            # letting a year's hours add up to more than what was actually
            # available.
            held_trade = self.held_trade()
            standing_pay = (self.labour.wage_for_hours(held_trade, hours) if held_trade else 0.0)
            if self.labour.wage_for_hours(trade, hours) > standing_pay:
                _, err = self.labour.work_for_wages(trade, hours)
                # Kept in step with `remaining` so hours_this_year (below) does
                # not count hours sold for wages here as still unused.
                if err is None:
                    remaining -= hours
        return remaining

    def _step_reputation(self, pool, remaining, remaining_after_projects, hours_effective_total):
        # 6. reputation, familiarity, protection, scandal
        #
        # reputation decays toward what the household is known for, and familiarity is renewed: the polity module's
        self.send(RenewStanding())
        # WHERE THE YEAR'S HOURS WENT: captured here, before the tallies
        # below reset for the next year, the same way spend_last_year
        # already captures the year's spending, so a player can see the
        # breakdown as `hours_this_year` in `state` rather than only a
        # final hours-left figure with no way to tell where the rest went.
        self.hours_this_year = {
            "available": round(self.labour.director_pool(), 1),
            "wage_work": round(self.state.household.wage_hours_this_year, 1),
            "teaching": round(self.state.household.teaching_hours_this_year, 1),
            "moving": round(self.state.household.relocation_hours_this_year or 0.0, 1),
            "supervising": round(self.state.household.supervision_hours_this_year, 1),
            "offered_to_projects": round(max(0.0, pool - remaining_after_projects), 1),
            # OFFERED is what projects were given a shot at; EFFECTIVE is what
            # actually reduced their founder_hours_left. The gap between the
            # two is hours that went in and came straight back out again
            # because a trade or the money to pay for it fell short that year
            # - see hours_offered_this_year / hours_effective_this_year on
            # each project in `active`, and underfunded_this_year.
            "effective_on_projects": round(hours_effective_total, 1),
            "unused": round(max(0.0, remaining), 1),
        }
        # Reset AFTER the progress pass above, which is where the hours you sold
        # are subtracted from the hours you have left to direct.
        self.labour.close_wage_year()
        # Contracted work is bought for a year and expires with it: hours you
        # paid a shop for in 142 are not still sitting there in 143.
        self.state.household.contract_hours = {}
        self.state.household.teaching_hours_this_year = 0.0
        self.state.household.relocation_hours_this_year = 0.0
        self.state.household.supervision_hours_this_year = 0.0
        self.state.household.spend_last_year = getattr(self, "_spend_this_year", 0.0)
        self._spend_this_year = 0.0
        # Sellers restock, so the pressure your buying put on the market fades.
        self.state.holdings.market_pressure = max(0.0, self.state.holdings.market_pressure * self.MARKET_PRESSURE_DECAY - self.MARKET_PRESSURE_ANNUAL_FADE)
        # eminence's warning, protection, the state's pressure, scandal, bribery and the two hazards that end a run: the polity module's
        self.send(CloseStandingYear())

    def _step_bondage(self):
        # 6b. serving out a debt. The hours you owe go to the creditor and the
        #     debt falls; when it is done you are free, and you keep everything
        #     you know.
        household = self.state.household
        if household.bondage_years_left > 0:
            repayment = bondage_repayment(self.cfg["founder_hours_per_year"], self.BONDAGE_LABOUR_SHARE,
                                          self.BONDAGE_WAGE_MARKUP, self.labour.market.quote("labourer"))
            household.bondage_years_left, household.bondage_debt, served = serve_bondage_year(
                household.bondage_years_left, household.bondage_debt, repayment)
            if served:
                self.send(RecordEvent.of("bondage_served", "your term is served and the debt is discharged; "
                                     "you are your own man again"))

