"""reserve_staff: the keep-N-spare part of complaint 176. `hold_staff_reserve` runs over the real labour mixin on a
stand-in world (free hands, room, cash, a recorder for hires and housing, no game); the `reserve` command and its typed
forms run on a household record. The default is
test_reserve_staff_default. The housing sum itself is held by test_auto_hire_buys_room."""
from types import SimpleNamespace

from .harness import check

from sim.labour.labour_staff_controls import StaffControlsMixin
from sim.labour import trade_data
from sim.ui.proto.dispatch_staff_controls import _cmd_reserve
from sim.ui.proto.typed import parse_typed

QUICK_TOPIC = True

CRAFT = trade_data.generic_craft_trade()
SCHOLAR = trade_data.scholar_trade()


class _Labour(StaffControlsMixin):
    """The real reserve rule; hiring and housing are recorded instead of done."""

    def __init__(self, free_craftsmen, free_scholars, reserve_craftsmen, reserve_scholars, policy_on,
                 room=100.0, price=10.0, spending=1.0e6):
        self.hired = []
        self.housing_built = []
        self.room = room
        household = SimpleNamespace(reserve_craftsmen=reserve_craftsmen, reserve_scholars=reserve_scholars,
                                    log=[])
        self._world = SimpleNamespace(
            state=SimpleNamespace(founder=SimpleNamespace(policy={"reserve_staff": policy_on}), household=household,
                                  scenario=SimpleNamespace(year=100)),
            venture_staff_free=lambda: (free_scholars, free_craftsmen),
            housing_price_per_place=lambda: price, spending_power=lambda kind: spending,
            build_worker_housing=lambda places: self.housing_built.append(places) or True)
        self.labour_market = SimpleNamespace(quote_annual=lambda trade: 50.0)

    def household_room(self):
        return self.room

    def hire_to_cover(self, trade, short, label, partial=False):
        self.hired.append((trade, short, label, partial))


# --- off by default: nothing is hired for a reserve
off = _Labour(0.0, 0.0, 5, 1, policy_on=False)
off.hold_staff_reserve()
check("with the policy off nothing is hired and no housing bought", off.hired == [] and off.housing_built == [], off.hired)

# --- on: the shortfall below the target is hired, trade by trade
on = _Labour(2.0, 0.0, 5, 1, policy_on=True)
on.hold_staff_reserve()
check("the spare hands short of the target are hired for each trade, labelled as the reserve and partial",
      on.hired == [(CRAFT, 3, "reserve_staff", True), (SCHOLAR, 1, "reserve_staff", True)], on.hired)

covered = _Labour(5.0, 1.0, 5, 1, policy_on=True)
covered.hold_staff_reserve()
check("a reserve already free is not topped up", covered.hired == [] and covered.housing_built == [], covered.hired)
nearly = _Labour(4.995, 0.0, 5, 0, policy_on=True)
nearly.hold_staff_reserve()
check("a shortfall under a hundredth of a hand is not hired for", nearly.hired == [], nearly.hired)
fraction = _Labour(2.4, 0.0, 5, 0, policy_on=True)
fraction.hold_staff_reserve()
check("a fractional shortfall is hired for in whole hands, rounded up", fraction.hired == [(CRAFT, 3, "reserve_staff", True)],
      fraction.hired)

# --- housing is bought first when the reserve does not fit, and only when cash covers it
roomy = _Labour(0.0, 0.0, 4, 0, policy_on=True, room=10.0)
roomy.hold_staff_reserve()
check("with room for the reserve no housing is bought", roomy.housing_built == [], roomy.housing_built)
cramped = _Labour(0.0, 0.0, 40, 0, policy_on=True, room=15.0)
cramped.hold_staff_reserve()
check("a reserve larger than the room buys the places short of it, then hires", cramped.housing_built == [25]
      and cramped.hired == [(CRAFT, 40, "reserve_staff", True)], (cramped.housing_built, cramped.hired))
broke = _Labour(0.0, 0.0, 40, 0, policy_on=True, room=0.0, spending=100.0)
broke.hold_staff_reserve()
check("with no cash for the housing and the hires, none is built", broke.housing_built == [], broke.housing_built)

# --- the `reserve` command and its typed forms
def _household():
    return SimpleNamespace(state=SimpleNamespace(household=SimpleNamespace(reserve_craftsmen=0, reserve_scholars=0)),
                           policy={"reserve_staff": False})


def _reserve(game, **fields):
    return _cmd_reserve(game, {}, dict(cmd="reserve", **fields), False)


game = _household()
check("typed 'reserve craftsmen 5' parses to the command", parse_typed("reserve craftsmen 5")[0] is not None,
      parse_typed("reserve craftsmen 5"))
reply = _reserve(game, craftsmen=5)
check("reserve craftsmen 5 is accepted and sets the craftsmen", reply["ok"] is True and reply["reserve"] == {"craftsmen": 5, "scholars": 0}, reply)
reply = _reserve(game, scholars=1)
check("reserve scholars 1 keeps the craftsmen", reply["reserve"] == {"craftsmen": 5, "scholars": 1}, reply)
check("bare reserve shows the standing sizes and that the policy is off",
      _reserve(game)["reserve"] == {"craftsmen": 5, "scholars": 1} and _reserve(game)["policy_reserve_staff"] is False)
check("a negative, fractional, flag or text size is refused and changes nothing",
      all(_reserve(game, craftsmen=value)["ok"] is False for value in (-1, 2.5, True, "five"))
      and _reserve(game)["reserve"]["craftsmen"] == 5)
