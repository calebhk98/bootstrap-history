"""Hiring and firing: the checks `hire` and `quote hire` share, the standing bid for a trade's hours, and letting staff go."""
import math

from sim.refusal import Refusal
from . import trade_supply_rules
from .labour_refusals import cash_in_hand_refusal, economy_lacks, economy_lacks_refusal, literate_wall_refusal
from .request_rules import fire_refusal
from .room_advice import hire_room_refusal
from .staff_moves import apprentices_of, crosses_literacy_wall, dismiss


class Hiring:
    def __init__(self, world, advice, book, capacity, market, pools, supply, trades):
        self._world = world
        self.advice = advice
        self.book = book
        self.capacity = capacity
        self.market = market
        self.pools = pools
        self.supply = supply
        self.trades = trades

    def hire_check(self, trade, count):
        """Everything `hire` and `quote hire` agree on before a bid is posted: the whole-person count and the
        first year's wages the bid would put at stake, or a refusal. Returns (count, outlay, refusal)."""
        trade = str(trade or "").strip().lower()
        if trade not in self._world.wages:
            return None, None, Refusal("no_such_trade", "no such trade: %s. Trades: %s"
                                       % (trade, ", ".join(sorted(self._world.wages))))
        if isinstance(count, str) or isinstance(count, bool):
            return None, None, Refusal("count_not_a_number", "n must be a number, not %r" % (count,))
        if count <= 0:
            return None, None, Refusal("count_not_positive", "n must be greater than zero. Nothing was changed.")
        # a command asks for whole people (the staff on the books is the hours the labour core hired over the working year)
        if abs(count - round(count)) > 1e-6:
            return None, None, Refusal("count_not_whole", "you hire whole people, not %g of one. Hire %d or %d."
                                       % (count, math.floor(count), math.ceil(count)))
        count = float(round(count))
        if economy_lacks(self._world, trade):
            return None, None, economy_lacks_refusal(trade)
        if not self.trades.trade_available(trade):
            return None, None, Refusal("trade_absent", "there are no %ss to hire in this society at any price: %s "
                                       'Teach one: {"cmd":"train","trade":"%s","n":1}'
                                       % (trade, self._world.trade_notes.get(trade, ""), trade))
        if trade not in self._world.trades_absent:
            exist = self.supply.people_who_exist(trade)
            on_books = self.book.employed(trade)
            rivals = self._world.actor_staff_fte(trade)
            if trade_supply_rules.hire_leaves_nobody(on_books, rivals, count, exist):
                return None, None, Refusal("nobody_left", "only about %.1f %ss exist in this country and you "
                                           "already employ %.1f%s: there is nobody left to hire."
                                           % (exist, trade, on_books,
                                              " (firms and the state employ %.1f more)" % rivals if rivals > 0 else ""))
        # literacy is a wall, not a cost: money cannot buy people who do not exist
        if trade in self.trades.LITERATE_TRADES:
            cap = self.supply.literate_capacity(trade)
            have = self.book.trade_headcount_pending(trade)
            if crosses_literacy_wall(have, count, cap):
                return None, None, literate_wall_refusal(trade, cap, have)
        outlay = count * self.market.quote_annual(trade)
        if outlay > self._world.spending_power("buy"):
            return None, None, Refusal("cash_short", cash_in_hand_refusal(self._world, 
                "offering %g %s%s a year's wages" % (count, trade, "" if count == 1 else "s"), outlay).message)
        room = self.capacity.household_room() - self.book.staff_posted()
        if count > room:
            return None, None, hire_room_refusal(room, count, self.advice.room_advice())
        return count, outlay, None

    def hire(self, trade, count):
        """Offer `count` more places of a trade to the labour core: the household's standing bid for the trade's hours
        (sim/markets/port_staff.py). The people arrive at the year's clearing, at the economy's wage for the trade,
        and are paid by it there. Answers what was posted."""
        trade = str(trade or "").strip().lower()
        count, _outlay, refusal = self.hire_check(trade, count)
        if refusal:
            return False, refusal
        workforce = self._world.workforce
        workforce.staff_wanted[trade] = max(workforce.staff_wanted.get(trade, 0.0), self.book.employed(trade)) + count
        self.pools.resync_pools()
        return True, ("%g %s%s wanted: the labour market fills the places at the year's clearing, at its wage. You now "
                      "have %.1f and %.1f places posted."
                      % (count, trade, "" if count == 1 else "s", self.book.employed(trade),
                         workforce.staff_wanted[trade]))

    def fire(self, trade, count):
        """Let staff go. Their wages stop; so does what they were doing.

        AND IT CANCELS AN APPRENTICESHIP: turning `auto_train` off does not
        stop training already in flight, so there has to be some command
        that can. Dismissing a trade you are still teaching is the obvious
        reading of `fire`, and it is the missing lever: what you paid to
        feed them while they learned is spent, the way any abandoned work
        is, and they do not arrive.
        """
        trade = str(trade or "").strip().lower()
        workforce = self._world.workforce
        have = self.book.employed(trade)
        pending = apprentices_of(workforce.training, trade)
        refusal = fire_refusal(trade, have, pending)
        if refusal:
            return False, refusal
        # WHOLE PEOPLE, as hire() and train() enforce, so a roster cannot drift to "0.03 engineers" through `fire`:
        # a fraction asked for is rounded up rather than refused.
        gone, left, stopped, workforce.training, _unmet = dismiss(have, workforce.training, trade, count)
        note = None
        if have > 0:
            self.book.set_employed(trade, left)
            note = "let %g %s%s go" % (gone, trade, "s" if gone != 1 else "")
        if stopped > 0:
            note = ((note + "; " if note else "")
                    + "stopped teaching %g more (what you paid to keep them "
                      "while they learned is gone)" % stopped)
        self.pools.resync_pools()
        return True, note
