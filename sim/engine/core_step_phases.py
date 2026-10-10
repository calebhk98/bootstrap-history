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
import math
import random
from dataclasses import dataclass

from sim.unit_conversions import PERCENT_SCALE
from . import automation_audit
from .invariants import check_labour_market_invariants
from .step_phase_money import MoneyPhaseMixin
from .step_phase_project_start import ProjectStartPhaseMixin
from .step_phase_projects import ProjectProgressPhaseMixin
from .step_phase_staff import StaffPhaseMixin
from sim.agents.api import edges, ledger


@dataclass(frozen=True)
class StepContext:
    """Immutable dependencies used by the turn phases."""
    trade_family: object
    invariant_checker: object


class StepPhasesMixin(StaffPhaseMixin, MoneyPhaseMixin, ProjectStartPhaseMixin, ProjectProgressPhaseMixin):
    """Composition point for the named phases Sim.step() calls, in order. The staff, money,
    project-start and project-progress phases live in step_phase_*.py and come in through the
    bases above; the rest are below. Sim inherits this mixin, so step() calls
    self._step_whatever() exactly as if these methods were defined directly on Sim.
    """

    def verify_step_invariants(self):
        """Validate this turn without reading configuration from globals."""
        self.step_context.invariant_checker(self.state)
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
                        self.state.household.employees[trade] = self.state.household.employees.get(trade, 0.0) + count
                        self.state.household.log.append((self.state.scenario.year, "%g %s%s finish their training"
                                         % (count, trade, "s" if count != 1 else "")))
                        self.labour.resync_pools()
                    else:
                        # They are trained now, so _resync_pools counts them
                        # from the people you actually hold - see the note
                        # there about why adding to self.state.household.artisans directly was
                        # thrown away at the next call.
                        self.state.household.log.append((self.state.scenario.year,
                                         "%g of the people you bought finish "
                                         "learning the work" % round(cap / 0.55, 1)))
                else:
                    still.append(row)
            # BEFORE the resync, not after: _resync_pools counts who is still
            # learning off this very list, so recomputing while the matured row
            # was still on it cost a whole extra year of everybody's time.
            self.state.household.training = still
            self.labour.resync_pools()

    def _step_dated_shocks(self, seats=None):
        # 3. dated shocks: the world is hit once, each seat in `seats` meets them with its own works
        self.disaster_this_year = None
        if self.events:
            year = self.state.scenario.year
            logged_before = len(self.log)
            self._shocks(year, seats)
            names = [hazard.get("name", "a hazard") for hazard in self.civ.get("hazards", [])
                     if hazard.get("years", [0, 0])[0] <= year <= hazard.get("years", [0, 0])[-1]]
            if names:
                self.disaster_this_year = {"name": ", ".join(names),
                                           "messages": [message for _, message in self.log[logged_before:]]}

    def begin_seat_year(self):
        """What the acting seat notes before its year starts."""
        # WHERE SCANDAL STOOD WHEN THE PLAYER LAST LOOKED: `state` prints the chance of being denounced from
        # the CURRENT scandal, and scandal moves DURING the step, so the direction needs the year's opening mark.
        self.state.household.scandal_last_year = self.state.household.scandal
        automation_audit.begin_year(self)
        self.hear_of_other_seats()

    def begin_world_year(self):
        """What the society notes before the year starts."""
        self.refresh_derived_nodes()
        # open every book entry at the year's start, so a read before the first step cannot open one at another state
        self._open_market_book()

    def _run_seat_work(self):
        """What the acting seat does with its year once the money and the shocks are settled."""
        self._step_teach_trades()              # 4a. teach the trades this society does not have
        self._step_standing_work_directive()   # 4a(ii). the standing "work" directive
        pool, hired_left = self._step_start_projects()   # 4b. start new projects
        self._step_materials()                 # 4c. materials
        # 5. progress, director hours
        remaining, remaining_after_projects, hours_effective_total = (
            self._step_progress(pool, hired_left))
        # 5b. if there is no work and no money, take a job
        remaining = self._step_wage_fallback(remaining)
        # 6. reputation, familiarity, protection, scandal
        self._step_reputation(pool, remaining, remaining_after_projects, hours_effective_total)
        self._step_bondage()                   # 6b. serving out a debt
        self._step_founder_mortality()          # 7. founder mortality

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
                        want[trade_id] = want.get(trade_id, 0) + 500
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
                    value = _gone_memo[trade] = (
                        not _trade_avail(trade)
                        or (_market_supply(trade) <= 0.0
                            and self.labour.trade_headcount_pending(trade) <= 0.0))
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
            want = {trade_id: value for trade_id, value in want.items()
                    if self.state.scenario.year - _taught.get(trade_id, -999) >= self.RETEACH_EVERY}
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
                _budget = (max(0.0, _spare_tr) + max(0.0, self.state.household.capital) * 0.10
                           if _score >= 500 else max(0.0, _spare_tr) * 0.5)
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
                    self.state.household.log.append((self.state.scenario.year, "you begin teaching the first %ss this "
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
            _want = max(0.0, _wd - _already)
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
                    self.state.household.log.append((self.state.scenario.year, "DIRECTED HOURS UNUSED: your standing "
                                         "order to sell %s hours a year as a "
                                         "%s only managed %s this year - %s. "
                                         "'allocate' changes or clears it"
                                     % ("{:,.0f}".format(_wd), self.state.household.work_trade,
                                        "{:,.0f}".format(_already + _got),
                                        "no more of your own hours were left "
                                        "to sell once your projects and "
                                        "training had theirs"
                                        if _room < _want else
                                        "nobody here will pay for that trade "
                                        "any longer" )))

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
            # ONLY IF IT PAYS BETTER THAN THE PRACTICE IT DISPLACES. Wage hours
            # now cost you the share of your practice they were sold out of
            # (see practice_attention), and without this check the optimizer
            # went on taking a scribe's wage at the price of a physician's fee
            # and lost Rome a sixth of its runs. A man with a practice does not
            # go and copy documents for less than the practice earns; that is
            # the whole reason `work` is the thing you do BEFORE you have one.
            # NOT `pool`: that name already holds the year's project budget,
            # computed at 4b. Reusing it here would overwrite it, so
            # hours_this_year would then report "offered_to_projects"
            # against the WHOLE year instead of against the project budget,
            # letting a year's hours add up to more than what was actually
            # available.
            year_hours = max(1.0, self.labour.director_pool())
            practice_lost = self.revenue() * (hours / year_hours) * (
                1.0 if self.practice_attention() > 0 else 0.0)
            if self.labour.wage_for_hours(trade, hours) > practice_lost:
                _, err = self.labour.work_for_wages(trade, hours)
                # Kept in step with `remaining` so hours_this_year (below) does
                # not count hours sold for wages here as still unused.
                if err is None:
                    remaining -= hours
        return remaining

    def _step_reputation(self, pool, remaining, remaining_after_projects, hours_effective_total):
        # 6. reputation, familiarity, protection, scandal
        #
        # Reputation DECAYS TOWARD WHAT YOU ARE ACTUALLY KNOWN FOR, not toward
        # zero: a physician with a practice, a school and a written corpus
        # does not become a man nobody has heard of because thirty quiet
        # years passed. What fades is novelty; what remains is the work.
        floor = self.standing_floor()
        self.state.household.reputation = floor + (self.state.household.reputation - floor) * self.REPUTATION_DECAY_TOWARD_FLOOR
        # ADAPTATION. Every year the world has known you, and every visible thing
        # you have already done, makes the next one less astonishing.
        pub = sum(1 for node_id in self.state.projects.done
                  if set(self.nodes[node_id].get("traits", [])) & {"spectacle", "inexplicable"})
        self.state.household.familiarity = min(
            self.FAMILIARITY_CEILING,
            1.0 - math.exp(-self.value_weights["adaptation_rate"]
                           * (self.FAMILIARITY_PUBLICATION_WEIGHT * pub
                              + self.FAMILIARITY_TENURE_WEIGHT * (self.state.scenario.year - 100))))
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
        self.state.household.spend_last_year = getattr(self, "_spend_this_year", 0.0)
        self._spend_this_year = 0.0
        # Sellers restock, so the pressure your buying put on the market fades.
        self.state.holdings.market_pressure = max(0.0, self.state.holdings.market_pressure * self.MARKET_PRESSURE_DECAY - self.MARKET_PRESSURE_ANNUAL_FADE)
        # WARN BEFORE IT KILLS YOU: eminence can end the run outright on a
        # roll with no escalation and nothing in the log ever mentioning
        # it beforehand. It is the one hazard that cannot be bribed away,
        # so the player must be told it is closing in.
        _danger = self.cfg["eminence_danger"]
        if self.state.household.eminence > _danger * 0.75:
            _said = self.state.household._said_eminence
            _band = int(self.state.household.eminence / max(1.0, _danger * 0.15))
            if _band > _said:
                self.state.household._said_eminence = _band
                self.state.household.log.append((self.state.scenario.year, "YOU ARE BECOMING CONSPICUOUS: eminence %.0f "
                                     "against a danger line of %.0f. This is the "
                                     "one thing no patron and no bribe protects "
                                     "you from, and it grows with reputation and "
                                     "visible wealth. A wide, dispersed "
                                     "institution is what survives you"
                                 % (self.state.household.eminence, _danger)))
        self.update_protection()
        # THE STATE NOTICES YOU. Requisition, the pressed office, a demand
        # for military supply, and the tail confiscation risk at the top of
        # the same scale - see SocietyMixin's own "THE STATE NOTICES YOU"
        # section (society.py) for the whole mechanic. Run after
        # update_protection() so this year's patronage and office standing
        # are what requisition/confiscation actually bargain against, and
        # before scandal/eminence below so a confiscation this mechanic
        # causes and the eminence-driven one further down are never
        # resolved in the same breath as two unrelated draws on the same
        # stale numbers.
        self._state_pressure(self.state.scenario.year)
        self.state.household.scandal *= self.SCANDAL_DECAY_RATE
        # Eminence accumulates in a SEPARATE pool, because bribery does not
        # touch it. You can buy a magistrate, an accuser and a jury. You cannot
        # buy an emperor's judgement that you have grown too large, and the
        # attempt is itself evidence against you.
        self.state.household.eminence = self.state.household.eminence * self.EMINENCE_DECAY_RATE + self.prominence_hazard()
        # you can buy your way out of trouble, and a sane player does
        if (self.state.household.scandal > self.AUTO_BRIBE_SCANDAL_THRESHOLD
                and self.state.household.capital > self.AUTO_BRIBE_CAPITAL_THRESHOLD
                and self.state.founder.policy.get("auto_bribe", not self.manual)):
            spend = min(self.state.household.capital * self.AUTO_BRIBE_CAPITAL_SHARE,
                        self.state.household.scandal * self.AUTO_BRIBE_COST_PER_SCANDAL_POINT)
            self.pay_edge(edges.EDGE_OFFICIALS, spend, "bribes")
            self.state.household.bribes_ytd = self.BRIBES_YTD_DECAY * self.state.household.bribes_ytd + spend
            self.state.household.scandal -= (spend / self.BRIBE_SCANDAL_REDUCTION_SCALE
                                       * self.value_weights["bribability"])
        else:
            self.state.household.bribes_ytd *= self.BRIBES_YTD_DECAY
        self.state.household.scandal = max(0.0, self.state.household.scandal)
        # WARN, THE WAY EMINENCE DOES: denunciation ends the run outright,
        # and a scandal figure with no threshold, no probability and no
        # note is not legible the way eminence's own warning already is.
        # Two hazards of the same shape must both be legible.
        _sd = self.cfg["suspicion_danger"]
        if self.state.household.scandal > _sd * 0.75:
            _band = int(self.state.household.scandal / max(1.0, _sd * 0.15))
            if _band > self.state.seat_progress._said_scandal:
                self.state.seat_progress._said_scandal = _band
                self.state.household.log.append((self.state.scenario.year, "YOU ARE BEING TALKED ABOUT: scandal %.0f "
                                     "against a line of %.0f. Past it you may be "
                                     "denounced, and that ends the run - about "
                                     "%.0f%% a year at this level. 'bribe' buys "
                                     "advocacy and piety; it falls a tenth a "
                                     "year on its own"
                                 % (self.state.household.scandal, _sd,
                                    PERCENT_SCALE * max(0.0, (self.state.household.scandal - _sd) / self.SCANDAL_HAZARD_SCALE))))
        elif self.state.household.scandal < _sd * 0.5:
            self.state.seat_progress._said_scandal = 0
        if self.events and self.state.household.scandal > self.cfg["suspicion_danger"]:
            probability = (self.state.household.scandal - self.cfg["suspicion_danger"]) / self.SCANDAL_HAZARD_SCALE
            if self.rng.random() < probability:
                self._catastrophe("denounced: %s" % ("as a sorcerer"
                                  if self.value_weights["w_magic_fear"] > 0.5
                                                     else "as a subversive"))
        # The eminence hazard is separate and unbribable. Its usual outcome is a
        # bad year rather than a death: a confiscation, a patron destroyed in
        # someone else's quarrel, a forced withdrawal from public life.
        if self.events and self.state.household.eminence > self.cfg["eminence_danger"]:
            probability = (self.state.household.eminence - self.cfg["eminence_danger"]) / self.EMINENCE_HAZARD_SCALE
            if self.rng.random() < probability:
                roll = self.rng.random()
                if roll < self.EMINENCE_OUTCOME_CONFISCATION_SHARE:
                    take = self.state.household.capital * self.EMINENCE_CONFISCATION_CAPITAL_LOSS
                    ledger.transfer(self.state.household, self.state_treasury(), take, "confiscation by the state")
                    self.state.household.reputation = max(0.0, self.state.household.reputation - self.EMINENCE_CONFISCATION_REPUTATION_LOSS)
                    self.state.household.eminence *= self.EMINENCE_CONFISCATION_RETENTION
                    self.state.household.log.append((self.state.scenario.year, "PROMINENCE: property confiscated, %d den lost, "
                                         "and you withdraw from public life for a while" % take))
                elif roll < (self.EMINENCE_OUTCOME_CONFISCATION_SHARE + self.EMINENCE_OUTCOME_PATRON_LOST_SHARE):
                    for pat in self.patrons_lost_to_eminence():
                        if pat in self.state.projects.done:
                            self.state.projects.done.discard(pat)
                            self._done_changed()
                            self.state.household.log.append((self.state.scenario.year, "PROMINENCE: your patron is destroyed in "
                                                 "someone else's quarrel and you lose %s" % pat))
                            break
                    self.state.household.eminence *= self.EMINENCE_PATRON_LOSS_RETENTION
                    self.state.household.reputation = max(0.0, self.state.household.reputation - self.EMINENCE_PATRON_LOSS_REPUTATION_LOSS)
                else:
                    self._catastrophe("too eminent: brought down not for what you built "
                                      "but for how large you had become")

    def _step_bondage(self):
        # 6b. serving out a debt. The hours you owe go to the creditor and the
        #     debt falls; when it is done you are free, and you keep everything
        #     you know.
        if self.state.household.bondage_years_left > 0:
            self.state.household.bondage_years_left -= 1
            paid = (self.cfg["founder_hours_per_year"] * self.BONDAGE_LABOUR_SHARE
                    * self.BONDAGE_WAGE_MARKUP * self.labour.market.quote("labourer"))
            self.state.household.bondage_debt = max(0.0, self.state.household.bondage_debt - paid)
            if self.state.household.bondage_debt <= 0 and self.state.household.bondage_years_left > 0:
                self.state.household.bondage_years_left = 0     # paid early
            if self.state.household.bondage_years_left <= 0:
                self.state.household.bondage_years_left = 0.0
                self.state.household.bondage_debt = 0.0
                self.state.household.log.append((self.state.scenario.year, "your term is served and the debt is discharged; "
                                     "you are your own man again"))

    def _deputy_hours_sentence(self):
        if self.state.household.directors_extra <= 0:
            return "You trained no deputy to take over."
        return ("Your deputies carry about %d hours a year, which is not enough "
                "to take over." % round(self.deputy_hours()))

    def _deputy_consequence(self):
        if self.deputies_carry_the_work():
            return ("Your %.1f deputies direct the work in your name and the "
                    "programme goes on without you." % self.state.household.directors_extra)
        return (self._deputy_hours_sentence() + " Nothing that needs your hours "
                "can be begun again, and what you built will be forgotten over "
                "the next twelve years unless deputies grow to carry the work.")

    def _what_survived_the_dissolution(self):
        kept = [node_id for node_id in self.state.projects.done
                if self.corpus_is_dispersed(node_id)]
        if kept:
            return ("the school dispersed, but its codices survive in other "
                    "hands (%d works of yours with them)"
                    % len(self.state.projects.done - self.state.projects.granted))
        return "the school dispersed and the work was forgotten"

    def _step_founder_mortality(self):
        # 7. founder mortality
        if self.state.founder.founder_alive:
            self.state.founder.life_left -= 1
            if self.running_with_mechanic("founder_life_extension"):
                self.state.founder.life_left += self.SANITATION_LIFE_EXTENSION_YEARS      # you at least do not die of a septic cut
            if self.state.founder.life_left <= 0:
                self.state.founder.founder_alive = False
                self.state.household.log.append(
                    (self.state.scenario.year, "THE FOUNDER DIES, aged about %d. %s"
                     % (self.founder_age(), self._deputy_consequence())))
        # a programme with no director is not paused, it is dissolving
        if not self.state.founder.founder_alive and not self.deputies_carry_the_work():
            self.state.projects.stalled += 1
            if self.state.projects.stalled >= self.DISSOLUTION_YEARS_BEFORE_FORGETTING:
                losable = self.losable_node_ids()
                # sorted() matters: self.state.projects.done is a SET, and a set iterates in an
                # order that depends on PYTHONHASHSEED, so feeding it unsorted to
                # rng.sample made the same --seed give a different answer on every
                # invocation. Every figure this project has reported was, strictly,
                # unreproducible.
                if losable:
                    for node_id in self.rng.sample(losable, max(1, len(losable) // self.DISSOLUTION_FORGET_FRACTION_DIVISOR)):
                        self.state.projects.operating.discard(node_id)
                        self.state.projects.done.discard(node_id)
                        self._done_changed()
            if self.state.projects.stalled in (3, 6, 9, 11):
                self.state.household.log.append((self.state.scenario.year, "THE PROGRAMME IS DISSOLVING: %d year(s) "
                                     "since the founder died. %s What you built is being "
                                     "forgotten. The run ends at twelve."
                                 % (self.state.projects.stalled, self._deputy_hours_sentence())))
            if self.state.projects.stalled >= self.DISSOLUTION_YEARS_UNTIL_END:
                self._catastrophe("the founder died without training successors; "
                                  + self._what_survived_the_dissolution())
        else:
            self.state.projects.stalled = 0
