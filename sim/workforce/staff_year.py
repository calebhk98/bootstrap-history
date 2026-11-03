"""The workforce module's yearly staff step: hiring toward capacity, replacing lost trades and director growth.

It runs as the `staff` phase of each seat's year."""
from sim.assembly.api import Part
from sim.labour.api import bonded_pseudo_trade, generic_craft_trade, generic_staff_trades, scholar_target, scholar_trade
from sim.reporting.api import RecordAutomation, RecordAutomationSkip, RecordEvent
from sim.world import demography

from .constants import (
    AUTO_HIRE_ARTISAN_APPROACH_RATE, AUTO_HIRE_CREDIT_ROOM_SHARE, AUTO_HIRE_SCHOLAR_APPROACH_RATE,
    AUTO_HIRE_SCHOLAR_EXTRA_SHARE, AUTO_HIRE_SLAVE_CRAFT_CREDIT, DIRECTORS_EXTRA_APPROACH_RATE,
    TRADE_REPLACEMENT_TARGET_HEADCOUNT,
)
from .staff_phase_rules import approach, artisan_goal, craft_headcount, directors_next, has_room_to_hire, scholar_goal
from .staff_replacement import GROW_STANCE, hire_stance, replacement_wanted


class StaffYear(Part):

    def step_staff(self, seat_id=None):
        workforce = self.seat
        # Staff grows only with auto_hire on (the optimizer's default, off for a player); with it off the staff changes
        # only by hire, fire, train, buy and manumit.
        sc_cap, ar_cap, di_cap = self.parts.core.labour.capacity.staff_capacity()
        attrition_rate = demography.BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE
        # Rehire a specialist foreman an open concern just lost, before the
        # staffing rule closes the concern.
        if self.needs.founder()["policy"].get("auto_replace_foreman", False):
            self.parts.core.labour.controls.replace_lost_foremen()
        # Hire for the concerns named with `keep <id> staffed`, before the closure rule.
        self.parts.core.labour.controls.keep_flagged_concerns_staffed()
        self.parts.core.labour.pools.resync_pools()
        # No attrition is applied to the staff here: the labour core fills the standing bid each clearing.
        # Hiring is not gated on a positive balance: a household in arrears must still be able to take on the people
        # whose work is the way out. The affordability arithmetic below decides how many.
        _hire_room = has_room_to_hire(self.needs.acting_balance(), self.needs.credit_limit(), AUTO_HIRE_CREDIT_ROOM_SHARE)
        _hire_mode = self.needs.founder()["policy"].get("auto_hire", not self.needs.automation()["manual"])
        _hire_stance = hire_stance(_hire_mode, _hire_room)
        if _hire_stance == GROW_STANCE:
            # Supervision-room headroom is scaled by the same affordability figure staff_capacity() used.
            extra = self.parts.core.labour.capacity.supervision_room() * self.parts.core.staff_scale()
            # The scholar target is capped at the literacy wall hire() and train() enforce.
            target_sc = scholar_target(sc_cap, extra, AUTO_HIRE_SCHOLAR_EXTRA_SHARE, self.parts.core.labour.supply.literate_capacity(scholar_trade()))
            desired_sc = approach(workforce.scholars, target_sc, AUTO_HIRE_SCHOLAR_APPROACH_RATE)
            target_ar = ar_cap + extra
            desired_ar = approach(workforce.artisans, target_ar, AUTO_HIRE_ARTISAN_APPROACH_RATE)
            # Staff taken on automatically are generic craftsmen and scribes.
            craft = craft_headcount(desired_ar, workforce.freedmen, workforce.slaves, AUTO_HIRE_SLAVE_CRAFT_CREDIT)
            specials = sum(value for trade_id, value in workforce.employees.items()
                           if trade_id not in (generic_craft_trade(), scholar_trade()) and self.needs.trade_family[trade_id] == "craft")
            # The generic artisan bucket is what is left after every taught trade took its share, and artisans supervise
            # a concern, so specialists must not squeeze it to nothing. A headcount may be fractional (hours over the year).
            # Growth goes through hire() so a refusal there (cash, room, literacy, price pressure) binds the optimizer as
            # it binds a player; a refusal is not an error and is not acted on.
            def _grow_to(trade, want, closure_need=0.0):
                self.parts.staff_hiring.grow_trade_toward(trade, want, closure_need)
            # THE HANDS A SHUT CONCERN NEEDS, within the affordability scale the extra room uses; hire() then
            # applies the cash, room and literacy rules, and a refusal is recorded as a skip with its reason.
            _closed_sc, _closed_ar = self.needs.staffing_closed_hand_shortfall()
            _closed_unscaled = _closed_sc + _closed_ar
            _closed_sc *= self.parts.core.staff_scale()
            _closed_ar *= self.parts.core.staff_scale()
            if _closed_unscaled >= 1.0 and _closed_sc + _closed_ar < 1.0:
                self.needs.send(RecordAutomationSkip("auto_hire", "hire for shut concerns", "concerns shut for want of staff need %.1f more people, but the income that pays staff covers "
                    "%.0f%% of them" % (_closed_unscaled, 100.0 * self.parts.core.staff_scale())))
            _grow_to(generic_craft_trade(), artisan_goal(craft, specials, workforce.employees.get(generic_craft_trade(), 0.0), _closed_ar),
                     closure_need=_closed_ar)
            if desired_sc > 0 or _closed_sc > 0:
                _grow_to(scholar_trade(), scholar_goal(desired_sc, workforce.scholars, _closed_sc),
                         closure_need=_closed_sc)
            # Replace people trade by trade, from the trades taught as well as the keys left in `employees` (a trade
            # drops out of `employees` once its last person is lost), and only for a trade a project or open concern
            # draws on (see idle_specialists).
            _drawn_on = self.parts.core.labour.ledger.trades_drawn_on()
            _generic = generic_staff_trades(self.parts.core.labour.allocation.unskilled_trade())
            for trade_id in sorted(set(workforce.employees) | set(workforce.trades_created)):
                have = workforce.employees.get(trade_id, 0.0)
                want = replacement_wanted(trade_id, have, trade_id in workforce.trades_created, _drawn_on,
                                          TRADE_REPLACEMENT_TARGET_HEADCOUNT, _generic)
                if want is None:
                    continue
                if want - have > 0.02:
                    _grow_to(trade_id, want)
            self.parts.core.labour.pools.resync_pools()
        self.parts.core.labour.controls.hold_staff_reserve()
        # Contracted craftsmen count toward a project's staff requirement; the optimizer commissions when hands are the only block.
        if self.needs.founder()["policy"].get("auto_commission", not self.needs.automation()["manual"]):
            _before = self.needs.acting_balance()
            _commissioned = self.parts.core.labour.commissions.auto_commission_for_blocked()
            if _commissioned:
                self.needs.send(RecordAutomation("auto_commission", "commission", "%.0f hours of %s" % (_commissioned[2], _commissioned[1]), "%s is blocked only on craftsmen's hands" % _commissioned[0], _before))
        workforce.directors_extra = directors_next(workforce.directors_extra, di_cap,
                                                              DIRECTORS_EXTRA_APPROACH_RATE, attrition_rate)
        workforce.artisans = max(0.0, workforce.artisans)
        workforce.scholars = max(0.0, workforce.scholars)
        # Announce when the director pool crosses a whole person.
        _whole = int(workforce.directors_extra)
        if _whole > workforce.said_deputies:
            workforce.said_deputies = _whole
            self.needs.send(RecordEvent.of("deputies_directing", "you now have %d deput%s directing work in "
                                 "your name: your year is %s hours instead of "
                                 "%s. They came with the institutions you built"
                             % (_whole, "y" if _whole == 1 else "ies",
                                self.needs.plain_number(self.parts.core.labour.hours.director_pool()),
                                self.needs.plain_number(self.needs.game_config()["founder_hours_per_year"]))))
