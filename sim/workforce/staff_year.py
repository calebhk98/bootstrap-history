"""The workforce module's yearly staff step: attrition, wage affordability and keeping concerns staffed.

It runs as the `staff` phase of each seat's year."""
from sim.agents.api import edges
from sim.labour.api import scholar_target
from sim.ledger.api import PayEdge
from sim.reporting.api import RecordAutomation, RecordAutomationSkip, RecordEvent
from sim.world import demography

from .constants import (AUTO_HIRE_ARTISAN_APPROACH_RATE, AUTO_HIRE_CREDIT_ROOM_SHARE, AUTO_HIRE_SCHOLAR_APPROACH_RATE,
                        AUTO_HIRE_SCHOLAR_EXTRA_SHARE, AUTO_HIRE_SLAVE_CRAFT_CREDIT, DIRECTORS_EXTRA_APPROACH_RATE,
                        TRADE_REPLACEMENT_AFFORDABILITY_YEARS, TRADE_REPLACEMENT_TARGET_HEADCOUNT)
from .payroll_trim import payroll_means
from .staff_phase_rules import approach, artisan_goal, can_afford_replacement, craft_headcount, directors_next, has_room_to_hire, scholar_goal
from .staff_replacement import GROW_STANCE, REPLACE_STANCE, hire_stance, replacement_wanted


class StaffYear:

    def step_staff(self, seat_id=None):
        household = self.needs.legacy_acting_household()
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
        attrition_rate = demography.BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE
        # PEOPLE ARE WHOLE: each person on the books is rolled individually against the game's dice (trades sorted so
        # draws are reproducible): they die at the working-age mortality rate, or take a better offer at the
        # rate the market moves workers off a lower payer, which is none when pay is at the going wage.
        self.labour.settle_staff_pay()
        _died, _left = self.labour.roll_staff_year(self.needs.legacy_dice())
        _lost = {trade: _died.get(trade, 0) + _left.get(trade, 0) for trade in set(_died) | set(_left)}
        # Rehire a specialist foreman an open concern just lost, before the
        # staffing rule closes the concern.
        if self.needs.founder()["policy"].get("auto_replace_foreman", False):
            self.labour.replace_lost_foremen()
        # Hire for the concerns named with `keep <id> staffed`, before the closure rule.
        self.labour.keep_flagged_concerns_staffed()
        self.labour.resync_pools()
        # AND SAY SO, once the rehiring has had its chance: a loss that still leaves a running concern short is
        # what the staffing rule is about to close.
        if _lost:
            for cause, counts in (("death", _died), ("better offers", _left)):
                self.labour.log_staff_lost(cause, {trade_id: count for trade_id, count in counts.items() if count})
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
        other = (self.needs.upkeep() + (self.needs.living_cost() - payroll)
                 + self.needs.mine_operating_cost())
        can_pay = payroll_means(self.needs.revenue_estimate(), other, household.capital, self.needs.credit_limit())
        # NOT GATED BY A POLICY, and this is the one automatic thing that is not.
        # A policy switch is for something the game decides FOR you - who to
        # hire, what to mothball - and every one of those is yours to turn off.
        # People leaving a household that has no money and no credit to pay them
        # is not a decision the game is making on your behalf, it is the world
        # answering one you already made, the same as the arrears bleed below.
        # The `policy` reply says so in as many words.
        self.shed_unpayable_staff(payroll, can_pay)
        # NOT `capital > 0`: gating hiring on a strictly positive balance
        # creates a catch-22, where a household in arrears could never take
        # on the people whose work is the only way out of arrears. A run
        # that keeps a project going can carry a balance in the red almost
        # permanently and legitimately - the gate is not "you are ruined",
        # it is "you are building something". The affordability arithmetic
        # below - which already subtracts living cost, upkeep and the wages
        # you are carrying - is what decides how many to hire, and correctly
        # says nobody when there is nothing spare.
        _hire_room = has_room_to_hire(household.capital, self.needs.credit_limit(), AUTO_HIRE_CREDIT_ROOM_SHARE)
        _hire_mode = self.needs.founder()["policy"].get("auto_hire", not self.needs.automation()["manual"])
        _hire_stance = hire_stance(_hire_mode, _hire_room)
        if _hire_stance == REPLACE_STANCE:
            self.replace_lost_staff(_lost)
            self.labour.resync_pools()
        if _hire_stance == GROW_STANCE:
            # Scaled by the SAME affordability figure staff_capacity() just
            # used for sc_cap/ar_cap (see the comment there): supervision-room
            # headroom is not a free six people, it is six people you still
            # have to pay for.
            extra = self.labour.supervision_room() * self.needs.legacy_household_actor()._staff_scale
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
            target_sc = scholar_target(sc_cap, extra, AUTO_HIRE_SCHOLAR_EXTRA_SHARE, self.labour.literate_capacity("scholar"))
            desired_sc = approach(household.scholars, target_sc, AUTO_HIRE_SCHOLAR_APPROACH_RATE)
            target_ar = ar_cap + extra
            desired_ar = approach(household.artisans, target_ar, AUTO_HIRE_ARTISAN_APPROACH_RATE)
            # Keep the per-trade books honest about the aggregate: staff taken on
            # for you are generic craftsmen and scribes, and that is all they are.
            craft = craft_headcount(desired_ar, household.freedmen, household.slaves, AUTO_HIRE_SLAVE_CRAFT_CREDIT)
            specials = sum(value for trade_id, value in household.employees.items()
                           if trade_id not in ("artisan", "scholar") and self.needs.trade_family[trade_id] == "craft")
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
            def _grow_to(trade, want, closure_need=0.0):
                self.grow_trade_toward(trade, want, closure_need)
            # THE HANDS A SHUT CONCERN NEEDS, within the affordability scale the extra room uses; hire() then
            # applies the cash, room and literacy rules, and a refusal is recorded as a skip with its reason.
            _closed_sc, _closed_ar = self.needs.staffing_closed_hand_shortfall()
            _closed_unscaled = _closed_sc + _closed_ar
            _closed_sc *= self.needs.legacy_household_actor()._staff_scale
            _closed_ar *= self.needs.legacy_household_actor()._staff_scale
            if _closed_unscaled >= 1.0 and _closed_sc + _closed_ar < 1.0:
                self.needs.send(RecordAutomationSkip("auto_hire", "hire for shut concerns", "concerns shut for want of staff need %.1f more people, but the income that pays staff covers "
                    "%.0f%% of them" % (_closed_unscaled, 100.0 * self.needs.legacy_household_actor()._staff_scale)))
            _grow_to("artisan", artisan_goal(craft, specials, household.employees.get("artisan", 0.0), _closed_ar),
                     closure_need=_closed_ar)
            if desired_sc > 0 or _closed_sc > 0:
                _grow_to("scholar", scholar_goal(desired_sc, household.scholars, _closed_sc),
                         closure_need=_closed_sc)
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
            for trade_id in sorted(set(household.employees) | set(household.trades_created)):
                have = household.employees.get(trade_id, 0.0)
                want = replacement_wanted(trade_id, have, trade_id in household.trades_created, _drawn_on,
                                          TRADE_REPLACEMENT_TARGET_HEADCOUNT)
                if want is None:
                    continue
                short = want - have
                if short > 0.02 and can_afford_replacement(household.capital, self.labour.market.quote_annual(trade_id),
                                                           TRADE_REPLACEMENT_AFFORDABILITY_YEARS):
                    _before = household.capital
                    self.labour.set_employed(trade_id, have + short)
                    self.needs.send(PayEdge(edges.EDGE_WORKERS, short * self.labour.market.quote_annual(trade_id), "wages advanced for replacement staff"))
                    self.needs.send(RecordAutomation("auto_hire", "replace", "%.1f %s" % (short, trade_id), "something draws on the trade and %.1f are held against a target of %.1f" % (have, want), _before))
            self.labour.resync_pools()
        self.labour.hold_staff_reserve()
        # BUY A JOB WHEN A HANDFUL OF HANDS IS THE ONLY THING IN THE WAY:
        # letting contracted craftsmen count toward a project's staff
        # requirement only helps a person who thinks to type `commission`
        # unless the optimizer can call it too. A run that can see the
        # wall, has the money, and has no way to spend it on the wall is
        # the same dead end wearing a different hat.
        if self.needs.founder()["policy"].get("auto_commission", not self.needs.automation()["manual"]):
            _before = household.capital
            _commissioned = self.labour.auto_commission_for_blocked()
            if _commissioned:
                self.needs.send(RecordAutomation("auto_commission", "commission", "%.0f hours of %s" % (_commissioned[2], _commissioned[1]), "%s is blocked only on craftsmen's hands" % _commissioned[0], _before))
        household.directors_extra = directors_next(household.directors_extra, di_cap,
                                                              DIRECTORS_EXTRA_APPROACH_RATE, attrition_rate)
        household.artisans = max(0.0, household.artisans)
        household.scholars = max(0.0, household.scholars)
        # SAY IT WHEN IT CROSSES A WHOLE PERSON: the year's hour pool can
        # grow well past the founder's own baseline as institutions add
        # deputies, and the single largest change to the resource the
        # whole game is built on must not go unannounced.
        _whole = int(household.directors_extra)
        if _whole > household._said_deputies:
            household._said_deputies = _whole
            self.needs.send(RecordEvent.of("deputies_directing", "you now have %d deput%s directing work in "
                                 "your name: your year is %s hours instead of "
                                 "%s. They came with the institutions you built"
                             % (_whole, "y" if _whole == 1 else "ies",
                                self.needs.plain_number(self.labour.director_pool()),
                                self.needs.plain_number(self.needs.game_config()["founder_hours_per_year"]))))
