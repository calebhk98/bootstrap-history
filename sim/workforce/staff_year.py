"""The workforce module's yearly staff step: attrition, wage affordability and keeping concerns staffed.

It runs as the `staff` phase of each seat's year."""
from sim.labour.api import scholar_target
from sim.reporting.api import RecordAutomation, RecordAutomationSkip, RecordEvent
from sim.world import demography

from .constants import (
    AUTO_HIRE_ARTISAN_APPROACH_RATE, AUTO_HIRE_CREDIT_ROOM_SHARE, AUTO_HIRE_SCHOLAR_APPROACH_RATE,
    AUTO_HIRE_SCHOLAR_EXTRA_SHARE, AUTO_HIRE_SLAVE_CRAFT_CREDIT, DIRECTORS_EXTRA_APPROACH_RATE,
    TRADE_REPLACEMENT_TARGET_HEADCOUNT,
)
from .staff_phase_rules import approach, artisan_goal, craft_headcount, directors_next, has_room_to_hire, scholar_goal
from .staff_replacement import GROW_STANCE, hire_stance, replacement_wanted


class StaffYear:

    def step_staff(self, seat_id=None):
        workforce = self.seat
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
        sc_cap, ar_cap, di_cap = self.labour.capacity.staff_capacity()
        attrition_rate = demography.BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE
        # Rehire a specialist foreman an open concern just lost, before the
        # staffing rule closes the concern.
        if self.needs.founder()["policy"].get("auto_replace_foreman", False):
            self.labour.controls.replace_lost_foremen()
        # Hire for the concerns named with `keep <id> staffed`, before the closure rule.
        self.labour.controls.keep_flagged_concerns_staffed()
        self.labour.pools.resync_pools()
        # Nobody dies or leaves the household's staff here: the labour core fills the standing bid each clearing.
        # NOT `capital > 0`: gating hiring on a strictly positive balance
        # creates a catch-22, where a household in arrears could never take
        # on the people whose work is the only way out of arrears. A run
        # that keeps a project going can carry a balance in the red almost
        # permanently and legitimately - the gate is not "you are ruined",
        # it is "you are building something". The affordability arithmetic
        # below - which already subtracts living cost, upkeep and the wages
        # you are carrying - is what decides how many to hire, and correctly
        # says nobody when there is nothing spare.
        _hire_room = has_room_to_hire(self.needs.acting_balance(), self.needs.credit_limit(), AUTO_HIRE_CREDIT_ROOM_SHARE)
        _hire_mode = self.needs.founder()["policy"].get("auto_hire", not self.needs.automation()["manual"])
        _hire_stance = hire_stance(_hire_mode, _hire_room)
        if _hire_stance == GROW_STANCE:
            # Scaled by the SAME affordability figure staff_capacity() just
            # used for sc_cap/ar_cap (see the comment there): supervision-room
            # headroom is not a free six people, it is six people you still
            # have to pay for.
            extra = self.labour.capacity.supervision_room() * self.staff_scale()
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
            target_sc = scholar_target(sc_cap, extra, AUTO_HIRE_SCHOLAR_EXTRA_SHARE, self.labour.supply.literate_capacity("scholar"))
            desired_sc = approach(workforce.scholars, target_sc, AUTO_HIRE_SCHOLAR_APPROACH_RATE)
            target_ar = ar_cap + extra
            desired_ar = approach(workforce.artisans, target_ar, AUTO_HIRE_ARTISAN_APPROACH_RATE)
            # Keep the per-trade books honest about the aggregate: staff taken on
            # for you are generic craftsmen and scribes, and that is all they are.
            craft = craft_headcount(desired_ar, workforce.freedmen, workforce.slaves, AUTO_HIRE_SLAVE_CRAFT_CREDIT)
            specials = sum(value for trade_id, value in workforce.employees.items()
                           if trade_id not in ("artisan", "scholar") and self.needs.trade_family[trade_id] == "craft")
            # SPECIALISTS MUST NOT EAT THE GENERALISTS: the generic bucket is
            # the remainder after every taught trade has taken its share,
            # so the top-up must not let specialist trades squeeze the
            # generic artisan count to nothing. Artisans are what supervise
            # a concern; a household of nothing but specialists cannot keep
            # its own doors open.
            #
            # A hire is a whole number of people asked for the places, but a
            # staff is the hours the labour core hired over the working year,
            # so a headcount on the books may be fractional.
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
            _closed_sc *= self.staff_scale()
            _closed_ar *= self.staff_scale()
            if _closed_unscaled >= 1.0 and _closed_sc + _closed_ar < 1.0:
                self.needs.send(RecordAutomationSkip("auto_hire", "hire for shut concerns", "concerns shut for want of staff need %.1f more people, but the income that pays staff covers "
                    "%.0f%% of them" % (_closed_unscaled, 100.0 * self.staff_scale())))
            _grow_to("artisan", artisan_goal(craft, specials, workforce.employees.get("artisan", 0.0), _closed_ar),
                     closure_need=_closed_ar)
            if desired_sc > 0 or _closed_sc > 0:
                _grow_to("scholar", scholar_goal(desired_sc, workforce.scholars, _closed_sc),
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
            _drawn_on = self.labour.ledger.trades_drawn_on()
            for trade_id in sorted(set(workforce.employees) | set(workforce.trades_created)):
                have = workforce.employees.get(trade_id, 0.0)
                want = replacement_wanted(trade_id, have, trade_id in workforce.trades_created, _drawn_on,
                                          TRADE_REPLACEMENT_TARGET_HEADCOUNT)
                if want is None:
                    continue
                if want - have > 0.02:
                    _grow_to(trade_id, want)
            self.labour.pools.resync_pools()
        self.labour.controls.hold_staff_reserve()
        # BUY A JOB WHEN A HANDFUL OF HANDS IS THE ONLY THING IN THE WAY:
        # letting contracted craftsmen count toward a project's staff
        # requirement only helps a person who thinks to type `commission`
        # unless the optimizer can call it too. A run that can see the
        # wall, has the money, and has no way to spend it on the wall is
        # the same dead end wearing a different hat.
        if self.needs.founder()["policy"].get("auto_commission", not self.needs.automation()["manual"]):
            _before = self.needs.acting_balance()
            _commissioned = self.labour.commissions.auto_commission_for_blocked()
            if _commissioned:
                self.needs.send(RecordAutomation("auto_commission", "commission", "%.0f hours of %s" % (_commissioned[2], _commissioned[1]), "%s is blocked only on craftsmen's hands" % _commissioned[0], _before))
        workforce.directors_extra = directors_next(workforce.directors_extra, di_cap,
                                                              DIRECTORS_EXTRA_APPROACH_RATE, attrition_rate)
        workforce.artisans = max(0.0, workforce.artisans)
        workforce.scholars = max(0.0, workforce.scholars)
        # SAY IT WHEN IT CROSSES A WHOLE PERSON: the year's hour pool can
        # grow well past the founder's own baseline as institutions add
        # deputies, and the single largest change to the resource the
        # whole game is built on must not go unannounced.
        _whole = int(workforce.directors_extra)
        if _whole > workforce.said_deputies:
            workforce.said_deputies = _whole
            self.needs.send(RecordEvent.of("deputies_directing", "you now have %d deput%s directing work in "
                                 "your name: your year is %s hours instead of "
                                 "%s. They came with the institutions you built"
                             % (_whole, "y" if _whole == 1 else "ies",
                                self.needs.plain_number(self.labour.hours.director_pool()),
                                self.needs.plain_number(self.needs.game_config()["founder_hours_per_year"]))))
