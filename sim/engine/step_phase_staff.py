"""The yearly staff phase: attrition, wage affordability and keeping concerns staffed.

A part of the year's phases (core_step_phases.py); Sim inherits it through StepPhasesMixin."""
import math
import random

from sim.world.demography import BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE
from . import automation_audit
from .staff_replacement import REPLACE_ONLY, replace_lost_staff
from sim.agents.api import edges


class StaffPhaseMixin:

    def _step_staff(self):
        # 1. staff. ATTRITION IS UNCONDITIONAL: people die, are poached and grow
        #    old whatever your policy is. GROWTH IS NOT: growing the staff
        #    automatically, with no command issued, would be the same fault
        #    as buying people without being asked, so it is gated behind
        #    auto_hire.
        #
        #    With auto_hire on (the default for the optimizer, off for a player)
        #    staff smooths toward capacity, which is what the long civilization
        #    runs are calibrated against. With it off, the only things that
        #    change the staff are hire, fire, train, buy and manumit.
        sc_cap, ar_cap, di_cap = self.labour.staff_capacity()
        attrition_rate = self.STAFF_ATTRITION_RATE
        # PEOPLE ARE WHOLE: attrition rolls each actual person on the books
        # individually against self.rng, sorted by trade name so the draws
        # happen in the same order whatever PYTHONHASHSEED the process
        # started with, the same convention every other rng loop over this
        # dict uses (see the "cannot pay" shedding loop below). A death is a
        # discrete thing that either happens to a particular person this
        # year or does not, so no trade's headcount is ever a fraction of a
        # person - never "1.32 artisans" or "0.03 engineers" drawing a
        # fractional wage while supervising nothing. Summed over many people
        # this reproduces the same 3.5%-a-year average ATTRITION targets; no
        # single person is ever a third of a casualty.
        _lost = {}
        for trade_id in sorted(self.state.household.employees):
            head = int(round(self.state.household.employees[trade_id]))
            survivors = sum(1 for _ in range(head) if self.rng.random() >= attrition_rate)
            if head - survivors > 0:
                _lost[trade_id] = head - survivors
            if survivors > 0:
                self.state.household.employees[trade_id] = float(survivors)
            else:
                self.state.household.employees.pop(trade_id)
        # AND SAY SO: a death is a discrete event that HAPPENED, and a player
        # watching the payroll shrink with nothing in the log or the events
        # to say why cannot tell attrition from a bug - it looks exactly
        # like staff vanishing.
        if _lost:
            # Deaths follow the working-age mortality rate; the rest of the yearly loss is turnover to better offers.
            death_share = min(1.0, BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE / max(attrition_rate, 1e-9))
            died = {}
            for trade_id, count in _lost.items():
                labeller = random.Random("staff-loss-%s-%s" % (self.state.scenario.year, trade_id))
                died[trade_id] = sum(1 for _ in range(count) if labeller.random() < death_share)
            poached = {trade_id: count - died[trade_id] for trade_id, count in _lost.items()}
            for cause, counts in (("death", died), ("better offers", poached)):
                people = ", ".join("%d %s%s" % (count, trade_id, "" if count == 1 else "s")
                                   for trade_id, count in sorted(counts.items()) if count)
                if people:
                    self.state.household.log.append((self.state.scenario.year, "you lose %s to %s" % (people, cause)))
        # Rehire a specialist foreman an open concern just lost, before the
        # staffing rule closes the concern.
        if self.state.founder.policy.get("auto_replace_foreman", False):
            self.labour.replace_lost_foremen()
        # Hire for the concerns named with `keep <id> staffed`, before the closure rule.
        self.labour.keep_flagged_concerns_staffed()
        self.labour.resync_pools()
        # A HOUSEHOLD THAT CANNOT PAY ITS PEOPLE LETS THEM GO. This is the whole
        # answer to "you built it from nothing, so you must be able to rebuild
        # it": a payroll a household cannot carry and never reduces keeps a
        # ruined run frozen indefinitely, worse than shedding staff, living
        # cheaply and starting again.
        #
        # THE TRIGGER MUST BE "CANNOT PAY AFTER CREDIT", NOT `capital < 0`:
        # being overdrawn is not being unable to pay. A household with credit
        # left borrows and makes payroll; that is what credit is for, and
        # enforce_credit_limit already models the point where it runs out.
        # Letting staff go the first year capital dips a denarius below zero,
        # with the lender still willing, is not what an enterprise does.
        #
        # THE GAP BEING CLOSED MUST EXCLUDE living_cost()'S OWN WAGE BILL:
        # living_cost() INCLUDES the wage bill, so measuring the deficit
        # directly against it would close the payroll PLUS the founder's own
        # food, rent and appearances - firing people cannot buy your own
        # dinner. Whenever base living exceeds revenue, which it does in
        # every early game, that would run the shedding loop off the end of
        # the staff list and empty it.
        #
        # The honest rule is that your people are paid out of what is left after
        # everything else, INCLUDING what somebody will still lend you, and you
        # shed only the part of the payroll that will not cover.
        payroll = self.labour.wage_bill()
        other = (self.upkeep() + (self.living_cost() - payroll)
                 + self.mine_operating_cost())
        # capital is negative in arrears; credit_limit() is how far into arrears
        # anyone will let you go, so this is what you can actually still spend.
        headroom = max(0.0, self.state.household.capital + self.credit_limit())
        can_pay = self.revenue() - other + headroom
        # NOT GATED BY A POLICY, and this is the one automatic thing that is not.
        # A policy switch is for something the game decides FOR you - who to
        # hire, what to mothball - and every one of those is yours to turn off.
        # People leaving a household that has no money and no credit to pay them
        # is not a decision the game is making on your behalf, it is the world
        # answering one you already made, the same as the arrears bleed below.
        # The `policy` reply says so in as many words.
        if payroll > can_pay and self.state.household.employees:
            short = payroll - can_pay
            gone = 0.0
            _before_shed = self.labour.staff_snapshot()
            # shed, dearest first, until the wages you are left with fit
            for trade_id in sorted(self.state.household.employees, key=lambda t: -self.labour.market.quote_annual(t)):
                if short <= 0:
                    break
                wage = self.labour.market.quote_annual(trade_id)
                if wage <= 0:
                    continue
                # A WHOLE PERSON, ROUNDED UP. `short / wage` is a quantity of
                # wages, not a quantity of people: cutting that fraction
                # straight would leave "0.3 smiths" still on the books, still
                # drawing 0.3 of a wage that was just found unaffordable.
                # Rounding up sheds one whole person too many at worst,
                # which is the safe direction for a household that genuinely
                # cannot make payroll.
                cut = min(self.state.household.employees[trade_id], math.ceil(short / wage - 1e-9))
                self.state.household.employees[trade_id] -= cut
                short -= cut * wage
                gone += cut
                if self.state.household.employees[trade_id] < 0.5:
                    self.state.household.employees.pop(trade_id)
            self.labour.resync_pools()
            self.labour.log_staff_reduction("a payroll you cannot meet", _before_shed)
            # ALWAYS, not only when it worked. Losing the staff you paid to hire
            # is more consequential than any of the flavour events that do get
            # logged, and a player who is not told has to notice their own wage
            # bill hit zero to find out.
            if gone > 0.005:
                self.state.household.log.append((self.state.scenario.year, "you cannot pay everyone: %.1f of your staff "
                                     "leave for work that pays" % gone))
        # NOT `capital > 0`: gating hiring on a strictly positive balance
        # creates a catch-22, where a household in arrears could never take
        # on the people whose work is the only way out of arrears. A run
        # that keeps a project going can carry a balance in the red almost
        # permanently and legitimately - the gate is not "you are ruined",
        # it is "you are building something". The affordability arithmetic
        # below - which already subtracts living cost, upkeep and the wages
        # you are carrying - is what decides how many to hire, and correctly
        # says nobody when there is nothing spare.
        _hire_room = (self.state.household.capital >= 0
                      or -self.state.household.capital <= self.credit_limit() * self.AUTO_HIRE_CREDIT_ROOM_SHARE)
        _hire_mode = self.state.founder.policy.get("auto_hire", not self.manual)
        if _hire_mode == REPLACE_ONLY and _hire_room:
            replace_lost_staff(self, _lost)
            self.labour.resync_pools()
        if (_hire_mode and _hire_mode != REPLACE_ONLY and _hire_room):
            # Scaled by the SAME affordability figure staff_capacity() just
            # used for sc_cap/ar_cap (see the comment there): supervision-room
            # headroom is not a free six people, it is six people you still
            # have to pay for.
            extra = self.labour.supervision_room() * self.household._staff_scale
            # THE SAME WALL hire() AND train() ENFORCE: `target_sc` is capped
            # at `literate_capacity("scholar")`, the wall a player typing
            # `hire scholar N` is refused at, so auto_hire cannot grow the
            # scholar pool past a ceiling a manual hire command could not
            # cross either. See literate_capacity()'s own docstring for the
            # other half of this: widening the wall enough that clamping to
            # it here does not simply strand every long civilisation run
            # short of what the tree actually asks for (the goal wants 25;
            # building the institutions staff_capacity() already credits
            # widens this same wall past that well before the goal is in
            # reach).
            target_sc = min(sc_cap + extra * self.AUTO_HIRE_SCHOLAR_EXTRA_SHARE, self.labour.literate_capacity("scholar"))
            desired_sc = self.state.household.scholars + (target_sc - self.state.household.scholars) * self.AUTO_HIRE_SCHOLAR_APPROACH_RATE
            target_ar = ar_cap + extra
            desired_ar = self.state.household.artisans + (target_ar - self.state.household.artisans) * self.AUTO_HIRE_ARTISAN_APPROACH_RATE
            # Keep the per-trade books honest about the aggregate: staff taken on
            # for you are generic craftsmen and scribes, and that is all they are.
            craft = max(0.0, desired_ar - self.state.household.freedmen - self.state.household.slaves * self.AUTO_HIRE_SLAVE_CRAFT_CREDIT)
            specials = sum(value for trade_id, value in self.state.household.employees.items()
                           if trade_id not in ("artisan", "scholar") and self.step_context.trade_family(trade_id) == "craft")
            # SPECIALISTS MUST NOT EAT THE GENERALISTS: the generic bucket is
            # the remainder after every taught trade has taken its share,
            # so the top-up must not let specialist trades squeeze the
            # generic artisan count to nothing. Artisans are what supervise
            # a concern; a household of nothing but specialists cannot keep
            # its own doors open.
            #
            # PEOPLE ARE WHOLE: the smoothing above is a continuous approach
            # to a continuous target, by design, so writing that target
            # straight into `employees` would hand a fractional person
            # every single year, forever, never quite arriving.
            # _stochastic_round spends the fractional remainder as this
            # year's chance of the next whole hire, so the long-run average
            # this formula was tuned against is unchanged and every actual
            # year's headcount is an integer (see its own docstring).
            # THROUGH hire(), NOT AROUND IT: a direct write to the pools
            # here instead would mean every rule hire() enforces - the
            # advance, the household room, the literacy wall, the price
            # pressure, the refusals - has to be re-enforced by hand, and
            # any one left out silently diverges from what a player hitting
            # the same wall experiences. Routing through hire() makes that
            # impossible by construction rather than by vigilance: it is
            # whatever hire() says it is, for player and optimizer alike.
            # A refusal here is not an error - it is the same wall a
            # player hits - so it is simply not acted on.
            def _grow_to(trade, want):
                have = self.state.household.employees.get(trade, 0.0)
                delta = self.labour.stochastic_round(want) - have
                if delta >= 1.0:
                    _before = self.state.household.capital
                    _hired, _ = self.labour.hire(trade, int(delta))
                    if _hired:
                        # the people the market found, which can be fewer than sought
                        _found = round(self.state.household.employees.get(trade, 0.0) - have)
                        automation_audit.record(
                            self, "auto_hire", "hire", "%d %s" % (_found, trade),
                            "staff target %.1f against %.1f held, with %.1f supervision room"
                            % (want, have, self.labour.supervision_room()), _before)
                elif delta <= -1.0:
                    _before = self.state.household.capital
                    self.labour.fire(trade, int(-delta))
                    automation_audit.record(
                        self, "auto_hire", "release", "%d %s" % (int(-delta), trade),
                        "staff target %.1f is below the %.1f held" % (want, have), _before)
            _grow_to("artisan", max(craft * 0.25, craft - specials))
            if desired_sc > 0:
                _grow_to("scholar", desired_sc)
            # REPLACE THE PEOPLE YOU LOSE, trade by trade: attrition can erode
            # a taught trade toward zero, and nothing replaces it if the
            # top-up only knows about the two generic buckets. A programme
            # that trains the first machinists in the world and then lets
            # them die out has not trained anybody.
            # FROM THE TRADES YOU TAUGHT, not from the keys that happen to
            # be left: a trade falls out of `employees` entirely once the
            # last of them drops below 0.05, so iterating only over
            # `employees`'s own keys would stop replacing a taught trade,
            # permanently, the moment its last person is lost. Iterating
            # trades_created too is what keeps a trade whose last person
            # just died still eligible for replacement.
            # ONLY A TRADE SOMETHING DRAWS ON: a project in hand or an open
            # concern. Otherwise the top-up pays idle specialists for decades
            # and rehires ones the player fired (see idle_specialists).
            _drawn_on = self.labour.trades_drawn_on()
            for trade_id in sorted(set(self.state.household.employees) | set(self.state.household.trades_created)):
                if trade_id in ("artisan", "scholar") or trade_id not in _drawn_on:
                    continue
                have = self.state.household.employees.get(trade_id, 0.0)
                want = max(have, self.TRADE_REPLACEMENT_TARGET_HEADCOUNT if trade_id in self.state.household.trades_created else 0.0)
                short = want - have
                if short > 0.02 and self.state.household.capital > self.labour.market.quote_annual(trade_id) * self.TRADE_REPLACEMENT_AFFORDABILITY_YEARS:
                    _before = self.state.household.capital
                    self.state.household.employees[trade_id] = have + short
                    self.pay_edge(edges.EDGE_WORKERS, short * self.labour.market.quote_annual(trade_id), "wages advanced for replacement staff")
                    automation_audit.record(
                        self, "auto_hire", "replace", "%.1f %s" % (short, trade_id),
                        "something draws on the trade and %.1f are held against a target of %.1f" % (have, want), _before)
            self.labour.resync_pools()
        self.labour.hold_staff_reserve()
        # BUY A JOB WHEN A HANDFUL OF HANDS IS THE ONLY THING IN THE WAY:
        # letting contracted craftsmen count toward a project's staff
        # requirement only helps a person who thinks to type `commission`
        # unless the optimizer can call it too. A run that can see the
        # wall, has the money, and has no way to spend it on the wall is
        # the same dead end wearing a different hat.
        if self.state.founder.policy.get("auto_commission", not self.manual):
            _before = self.state.household.capital
            _commissioned = self.labour.auto_commission_for_blocked()
            if _commissioned:
                automation_audit.record(
                    self, "auto_commission", "commission",
                    "%.0f hours of %s" % (_commissioned[2], _commissioned[1]),
                    "%s is blocked only on craftsmen's hands" % _commissioned[0], _before)
        self.state.household.directors_extra += (di_cap - self.state.household.directors_extra) * self.DIRECTORS_EXTRA_APPROACH_RATE - self.state.household.directors_extra * attrition_rate
        self.state.household.artisans = max(0.0, self.state.household.artisans)
        self.state.household.scholars = max(0.0, self.state.household.scholars)
        self.state.household.directors_extra = max(0.0, self.state.household.directors_extra)
        # SAY IT WHEN IT CROSSES A WHOLE PERSON: the year's hour pool can
        # grow well past the founder's own baseline as institutions add
        # deputies, and the single largest change to the resource the
        # whole game is built on must not go unannounced.
        _whole = int(self.state.household.directors_extra)
        if _whole > self.state.household._said_deputies:
            self.state.household._said_deputies = _whole
            self.state.household.log.append((self.state.scenario.year, "you now have %d deput%s directing work in "
                                 "your name: your year is %s hours instead of "
                                 "%s. They came with the institutions you built"
                             % (_whole, "y" if _whole == 1 else "ies",
                                "{:,.0f}".format(self.labour.director_pool()),
                                "{:,.0f}".format(self.cfg["founder_hours_per_year"]))))
