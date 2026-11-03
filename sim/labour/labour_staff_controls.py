"""Staffing controls an actor can set: concerns to keep staffed, and a reserve of spare hands.

Both run in the yearly staff step, ahead of the closure rule, and hire through `hire` so its cash, room and
literacy limits apply unchanged."""
import math

from . import trade_data
from sim.refusal import Refusal, cause_of
from sim.reporting.api import RecordEvent


def housing_places_to_buy(count, room, cost_per_place, hiring_outlay, spending_power):
    """The worker housing to buy so `count` more people have room: the places short of `room`, or none when room
    suffices or the housing and the `hiring_outlay` together exceed `spending_power`."""
    places = math.ceil(count - max(0.0, room) - 1e-9)
    if places <= 0 or places * cost_per_place + hiring_outlay > spending_power:
        return 0
    return places


class StaffControls:
    def __init__(self, world, book, capacity, hiring, market):
        self._world = world
        self.book = book
        self.capacity = capacity
        self.hiring = hiring
        self.market = market

    def hire_to_cover(self, trade, short, label, partial=False):
        """Hire `short` whole people of `trade` for a stated policy; the count taken on.

        `partial` takes as many as the household has room for instead of
        refusing the lot. The wall, the cash and the literacy limit are
        `hire`'s own, so a refusal simply hires nobody."""
        if short <= 0:
            return 0
        if partial:
            short = min(short, max(0, int(self.capacity.household_room() + 1e-9)))
            if short <= 0:
                return 0
        hired, _why = self.hiring.hire(trade, short)
        found = int(round(short))
        if not hired:
            return 0
        self._world.send(RecordEvent.of("policy_hire", "%s: you hire %d %s%s to keep your concerns supervised"
            % (label, found, trade, "" if found == 1 else "s"), policy=label, trade=trade, count=found))
        return found

    def replace_lost_foremen(self):
        """auto_replace_foreman: hire the specialists open concerns need and lack."""
        for trade, used in sorted(self._world.ventures.venture_foremen_used().items()):
            short = math.ceil(used - self.book.employed(trade) - 0.01)
            self.hire_to_cover(trade, short, "auto_replace_foreman")

    def keep_flagged_concerns_staffed(self):
        """Hire what the flagged concerns need and the household lacks (the projects module works out how many).

        Hires through `hire` so its cash, room and literacy limits apply unchanged."""
        for resource, short in self._world.ventures.keep_staffed_hires().items():
            self.hire_to_cover(trade_data.staff_resource_trade(trade_data.registry_of(self._world), resource), short,
                               "keep_staffed", partial=True)

    def hold_staff_reserve(self):
        """reserve_staff: keep the set number of spare generic craftsmen and scholars.

        Spare means free after every open concern's claim (`venture_staff_free`).
        Buys housing first when the household has no room for them."""
        if not self._world.game.policy.get("reserve_staff", False):
            return
        workforce = self._world.workforce
        scholars_free, craftsmen_free = self._world.ventures.venture_staff_free()
        for trade, target, free in ((trade_data.generic_craft_trade(), workforce.reserve_craftsmen, craftsmen_free),
                                    (trade_data.scholar_trade(), workforce.reserve_scholars, scholars_free)):
            short = math.ceil(target - free - 0.01)
            if short <= 0:
                continue
            self._house_for_reserve(trade, short)
            self.hire_to_cover(trade, short, "reserve_staff", partial=True)

    def _house_for_reserve(self, trade, count):
        """Buy worker housing for `count` more people if room is short and cash covers both."""
        self.buy_room_for(count, count * self.market.quote_annual(trade), "reserve_staff")

    def buy_room_for(self, count, hiring_outlay, label):
        """Buy worker housing for `count` more people when room is short and the purchase budget covers
        the housing and the `hiring_outlay` together. The price and the budget are those of `buy housing`."""
        places = housing_places_to_buy(count, self.capacity.household_room(), self._world.finance.housing_price_per_place(),
                                       hiring_outlay, self._world.finance.spending_power("buy"))
        if places <= 0:
            return False
        built = self._world.commands.build_worker_housing(places)
        if isinstance(built, Refusal) or not built:
            return False
        self._world.send(RecordEvent.of("policy_housing", "%s: you build housing for %d more people" % (label, places), policy=label, places=places))
        return True

    def hire_buying_room(self, trade, count, label="auto_hire"):
        """`hire`, and when it is refused only for want of room, buy the room (see buy_room_for) and hire again."""
        hired, reply = self.hiring.hire(trade, count)
        if hired or cause_of(reply) != "household_room":
            return hired, reply
        if not self.buy_room_for(float(count), count * self.market.quote_annual(trade), label):
            return hired, reply
        return self.hiring.hire(trade, count)
