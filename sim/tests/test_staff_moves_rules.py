"""The rules behind hiring, teaching, dismissing, commissioning and selling the founder's own hours (Complaint 640),
called on values built here, no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.labour.staff_moves import (FOUNDER_DEAD, HOURS_NOT_POSITIVE, HOURS_SHORT, NO_SUCH_TRADE, TRADE_ABSENT,
                                    apprentices_of, commission_spare_hours, crosses_literacy_wall, dismiss,
                                    wage_work_blocker, whole_people_under_wall)

# --- the literacy wall
check("taking on more than the ceiling allows crosses the wall", crosses_literacy_wall(5.0, 2.0, 6.0))
check("taking on exactly the ceiling does not", not crosses_literacy_wall(5.0, 1.0, 6.0))
check("a millionth over the ceiling is tolerated", not crosses_literacy_wall(5.0, 1.0 + 1e-7, 6.0))
check("people already held count against the wall", crosses_literacy_wall(5.9, 1.0, 6.0) and not crosses_literacy_wall(0.0, 1.0, 6.0))
check("twenty cannot be taught into a society of twelve", crosses_literacy_wall(0.0, 20.0, 12.0))
check("the whole people still allowed are the room under the wall, rounded down", whole_people_under_wall(5.9, 0.0) == 5)
check("a full wall allows nobody", whole_people_under_wall(6.0, 6.0) == 0)
check("a wall already passed allows nobody, not a negative count", whole_people_under_wall(6.0, 9.0) == 0)
check("a float shortfall of a hair does not lose a whole person", whole_people_under_wall(6.0, 2.0 + 1e-12) == 4)

# --- letting people go
training = [[0.0, 120, "machinist", 3.0], [0.0, 121, "smith", 2.0], [0.0, 122, "machinist", 1.0]]
check("apprentices of a trade are summed over its records", apprentices_of(training, "machinist") == 4.0)
check("a trade nobody is teaching has none", apprentices_of(training, "chemist") == 0.0)
gone, left, stopped, still, unmet = dismiss(5.0, training, "smith", 2)
check("staff are let go before anyone is stopped being taught",
      (gone, left, stopped, unmet) == (2.0, 3.0, 0.0, 0.0) and still is training, (gone, left, stopped, unmet))
gone, left, stopped, still, unmet = dismiss(0.0, training, "machinist", 3)
check("dismissing a trade you only teach cancels the apprenticeship, earliest record first",
      (gone, left, stopped, unmet) == (0.0, 0.0, 3.0, 0.0) and [r for r in still if r[2] == "machinist"] == [[0.0, 122, "machinist", 1.0]],
      still)
check("...and other trades' records are untouched", [r for r in still if r[2] == "smith"] == [[0.0, 121, "smith", 2.0]], still)
check("...and the original records are not altered", training[0][3] == 3.0, training)
gone, left, stopped, still, unmet = dismiss(2.0, training, "machinist", 5)
check("staff go first and the rest of the count stops apprentices",
      (gone, left, stopped, unmet) == (2.0, 0.0, 3.0, 0.0), (gone, left, stopped, unmet))
gone, left, stopped, still, unmet = dismiss(0.0, training, "machinist", 9)
check("a count beyond everyone employed and taught is left unmet and stops every apprentice",
      (gone, stopped, unmet) == (0.0, 4.0, 5.0) and not [r for r in still if r[2] == "machinist"], (gone, stopped, unmet))
gone, left, stopped, still, unmet = dismiss(5.0, [], "smith", 2.5)
check("a fraction of a person asked for is rounded up to a whole one", gone == 3.0 and left == 2.0, (gone, left))
gone, left, stopped, still, unmet = dismiss(2.0, [], "smith", 2.5)
check("...unless that is more than are employed, when all of them go", gone == 2.0 and left == 0.0, (gone, left))
gone, left, _, _, _ = dismiss(3.0, [], "smith", 3)
check("letting the last person go leaves none, not a trace", left == 0.0)
gone, left, _, _, _ = dismiss(3.0000000001, [], "smith", 3)
check("a trace of a person under a billionth is let go with the rest", left == 0.0, left)
gone, left, stopped, still, unmet = dismiss(0.0, training, "chemist", 1)
check("nobody employed and nobody taught: nothing goes", (gone, stopped, unmet) == (0.0, 0.0, 1.0) and still is training)
short_record = [[0.0, 120]]
check("a record too short to name a trade is kept and ignored",
      dismiss(0.0, short_record + training, "machinist", 1)[3][0] == [0.0, 120])

# --- commissioning
check("the hours a trade can spare are its market supply less what is already commissioned",
      commission_spare_hours(10_000.0, 2_500.0) == 7_500.0)
check("a trade fully commissioned has none to spare", commission_spare_hours(10_000.0, 10_000.0) == 0.0)
check("a trade commissioned past its supply is negative, never spare", commission_spare_hours(10_000.0, 12_000.0) < 0.0)

# --- selling the founder's own hours
alive, known, open_trade = True, True, lambda: True


def blocked(founder_alive=True, known_trade=True, trade_open=lambda: True, hours=100.0, hours_left=lambda: 500.0):
    return wage_work_blocker(founder_alive, known_trade, trade_open, hours, hours_left)


check("a living founder selling known hours in an open trade is not blocked", blocked() is None)
check("a dead founder cannot sell hours he does not have", blocked(founder_alive=False) == FOUNDER_DEAD)
check("a trade that does not exist is refused", blocked(known_trade=False) == NO_SUCH_TRADE)
check("a trade nobody here employs is refused", blocked(trade_open=lambda: False) == TRADE_ABSENT)
check("no hours is refused", blocked(hours=0) == HOURS_NOT_POSITIVE and blocked(hours=-5) == HOURS_NOT_POSITIVE)
check("more hours than are uncommitted is refused", blocked(hours=600.0) == HOURS_SHORT)
check("exactly the uncommitted hours is allowed", blocked(hours=500.0) is None)
check("hours given as text are read as numbers", blocked(hours="100") is None)
check("death is reported before anything else", blocked(founder_alive=False, known_trade=False, hours=-1) == FOUNDER_DEAD)
check("an unknown trade is reported before its openness is asked",
      wage_work_blocker(True, False, lambda: 1 / 0, 100, lambda: 500.0) == NO_SUCH_TRADE)
check("the uncommitted hours are asked only when everything before them passes",
      wage_work_blocker(True, True, lambda: True, 0, lambda: 1 / 0) == HOURS_NOT_POSITIVE)
