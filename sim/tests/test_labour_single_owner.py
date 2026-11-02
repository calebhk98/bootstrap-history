"""Complaint 556: who can work and who is hired by whom has one owner, the labour package.

Rule tests (Complaint 640): the founder's book accessors and the reservation arithmetic run on a stub world."""
from types import SimpleNamespace

from sim.labour.staff_book import StaffBook

from .harness import *  # noqa: F401,F403

QUICK_TOPIC = True


def _Book(other_staff, supply):
    """The owner's book over a stub world: a household with a staff map and the other employers' staff."""
    return StaffBook(SimpleNamespace(
        workforce=SimpleNamespace(employees={}, staff_wanted={}),
        actors_staff_nationwide=lambda trade: other_staff.get(trade, 0.0),
        HOURS_PER_PERSON_YEAR=2000.0))


# ---- the founder's book is the owner's ----
book = _Book(other_staff={"artisan": 4.0}, supply={"artisan": 10.0, "labourer": 5.0})
household = book._world.workforce
household.employees["artisan"] = 3.0
check("the owner reads the founder's head count", book.employed("artisan") == 3.0)
book.set_employed("artisan", 2.0)
check("set_employed writes the household's book", household.employees["artisan"] == 2.0 and book.employed_total() == 2.0)
book.add_employed("artisan", -2.0)
check("a count of nothing leaves the trade off the book",
      "artisan" not in household.employees and book.employed_by_trade().get("artisan") is None)
book.add_employed("labourer", 3.0)
copy = book.employed_by_trade()
copy["labourer"] = 99.0
check("the staff the owner reports is a copy", household.employees["labourer"] == 3.0)

# ---- a reservation is the founder's staff plus the other employers' ----
book.set_employed("artisan", 2.0)
check("reserved people are the book plus the firms' and states' staff", book.reserved_people("artisan") == 6.0, book.reserved_people("artisan"))
check("reserved hours are people times hours a person-year", book.reserved_hours("artisan") == 6.0 * 2000.0)

from unittest import mock
from sim.labour import labour_supply


class _Estimate:
    """A supply part whose book holds the core's headcounts and whose trades are all available."""

    def __init__(self, in_core):
        world = SimpleNamespace(population=SimpleNamespace(total=1000.0, working_age=600.0),
                                urban_fraction=lambda: 0.2, trades_absent=())
        self._in_core = in_core
        self.supply = labour_supply.Supply(world, book=self, capacity=None, settlement=None, trades=self)

    def national_trade_population(self, trade):
        return self.supply.national_trade_population(trade)

    def trade_available(self, trade):
        return True

    def core_people_by_trade(self):
        return self._in_core


with mock.patch.object(labour_supply.trade_data, "drawn_from_unskilled_pool", lambda trade: False), \
        mock.patch.object(labour_supply.trade_data, "scholar_trade", lambda: "scholar"), \
        mock.patch.object(labour_supply.trade_data, "literate_trades", lambda registry, trades: []), \
        mock.patch.object(labour_supply.trade_data, "registry_of", lambda world: {}):
    check("the national estimate of a trade is the core's headcount where the core holds people of it",
          _Estimate({"smith": 42.0}).national_trade_population("smith") == 42.0)
