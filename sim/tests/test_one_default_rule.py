"""Complaint 589: the founder's household and a firm owing more than their ceilings go through one arrears-and-default rule.

The same state (debt past the ceiling, nothing paying it down) must reach default after the same
number of years in arrears for both, and each year the unpaid interest is arrears, not more debt.
"""
from .harness import *  # noqa: F401,F403

from sim.agents import borrowing_arrears
from sim.agents.api import ActorRecord, Business, ActorRegistry, ActorsState
from sim.agents.stratum import Stratum  # noqa: F401  (registers the kind)

from sim.agents.borrowing import Borrower
from sim.agents.household_borrowing import FounderBorrowing

from .agents_fake_world import FakeWorld

MAX_YEARS = 12


def years_until_firm_defaults():
    world = FakeWorld(year=50)
    registry = ActorRegistry(ActorsState(home_country="home"))
    firm = registry.add("firm:1", ActorRecord(kind="firm", founded_year=0, last_margin=10.0, business=Business()))
    firm.money = -5000.0
    for years in range(1, MAX_YEARS + 1):
        world.year += 1
        firm.pay_interest(world)
        if firm.record.exited_year is not None:
            return years, firm
    return None, firm


class FounderBook:
	"""The household's finances as the arrears rule reads them."""

	def __init__(self):
		self.interest_arrears = 0.0
		self.arrears_years = 0


class NoBonds:
	def debt(self, account_id):
		return 0.0

	def coupons_due(self, account_id):
		return 0.0


class NoPurses:
	bonds = NoBonds()


class FounderStandIn(FounderBorrowing, Borrower):
	"""The founder's household reduced to what the shared rule reads: a purse, an arrears book, and a world that
	answers the founder's ceiling, rate and way of defaulting. No engine."""

	purses = NoPurses()
	account_id = "founder"

	def __init__(self, money):
		self.money = money
		self._state = type("StandInState", (), {"household": FounderBook()})()


class FounderWorld(FakeWorld):
	CEILING = 1000.0
	RATE = 0.06

	def __init__(self):
		super().__init__(year=50)
		self.defaults = 0

	def founder_credit_limit(self):
		return self.CEILING

	def founder_debt_rate(self):
		return self.RATE

	def founder_defaults(self):
		self.defaults += 1


def years_until_founder_defaults():
	world = FounderWorld()
	founder = FounderStandIn(money=-5000.0)
	book = founder.arrears_book
	arrears_by_year = []
	for years in range(1, MAX_YEARS + 1):
		founder.settle_interest(world)
		if world.defaults:
			return years, arrears_by_year, founder, world
		arrears_by_year.append(book.interest_arrears)
	return None, arrears_by_year, founder, world


firm_years, firm = years_until_firm_defaults()
founder_years, founder_arrears, founder, founder_world = years_until_founder_defaults()
check("a firm past its ceiling defaults after the shared run of years in arrears",
      firm_years == borrowing_arrears.ARREARS_YEARS_BEFORE_DEFAULT, firm_years)
check("the founder past its ceiling defaults after the same run of years in arrears",
      founder_years == firm_years, (founder_years, firm_years))
yearly_interest = 5000.0 * FounderWorld.RATE
check("the founder's unpaid interest each year is arrears, not more debt",
      founder.money == -5000.0 and all(
          abs(arrears - yearly_interest * (index + 1)) < 1e-6 for index, arrears in enumerate(founder_arrears)),
      (founder.money, founder_arrears))
check("the founder's default is called once and clears the arrears record",
      founder_world.defaults == 1 and founder.arrears_book.interest_arrears == 0.0
      and founder.arrears_book.arrears_years == 0, (founder_world.defaults, vars(founder.arrears_book)))


# Complaint 653: a debt over its ceiling is a breach at a rate of zero too (a margin call on the excess).
class NilRateWorld(FounderWorld):
	RATE = 0.0


def run_nil_rate(money):
	world = NilRateWorld()
	borrower = FounderStandIn(money=money)
	years_in_arrears = []
	for years in range(1, MAX_YEARS + 1):
		borrower.settle_interest(world)
		if world.defaults:
			return years, years_in_arrears, world
		years_in_arrears.append(borrower.arrears_book.arrears_years)
	return None, years_in_arrears, world


over_years, over_progress, over_world = run_nil_rate(-50000.0)
inside_years, inside_progress, inside_world = run_nil_rate(-500.0)
check("a debt far over its ceiling at nil interest enters arrears",
      over_progress[:1] == [1], over_progress)
check("a debt far over its ceiling at nil interest defaults after the shared run of years",
      over_years == borrowing_arrears.ARREARS_YEARS_BEFORE_DEFAULT, over_years)
check("a debt inside its ceiling at nil interest never enters arrears",
      inside_years is None and set(inside_progress) == {0} and inside_world.defaults == 0, (inside_years, inside_progress))
