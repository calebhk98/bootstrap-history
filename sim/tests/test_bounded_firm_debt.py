"""Complaint 588: a borrower past its credit ceiling cannot draw to pay interest. The unpaid interest is arrears; a
borrower in arrears for too long defaults, the pool writes the claim off once, and a firm closes. A borrower that
pays its interest is untouched."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, Business, ActorRegistry, ActorsState
from sim.agents import borrowing_arrears
from sim.agents.purses import COIN, POOL
from sim.agents.stratum import Stratum  # noqa: F401  (registers the kind)

from .agents_fake_world import FakeWorld


def firm_owing(debt, margin):
	"""A firm with no concern and no income, whose standing earning is `margin`, owing `debt` on its facility."""
	world = FakeWorld(year=50)
	registry = ActorRegistry(ActorsState(home_country="home"))
	firm = registry.add("firm:1", ActorRecord(kind="firm", founded_year=0, last_margin=margin, business=Business()))
	firm.money = -debt
	return world, registry, firm


world, registry, firm = firm_owing(debt=50.0, margin=10.0)
purses = registry.state.purses
ceiling = firm.credit_ceiling(world)
check("the fixture has a ceiling to compound towards", 50.0 < ceiling < 1.0e6, ceiling)
highest = 0.0
excess = 0.0
years = 0
while firm.record.exited_year is None and years < 100:
	world.year += 1
	years += 1
	year_interest = firm.debt() * firm.borrowing_rate(world)
	firm.act(world)
	highest = max(highest, firm.debt() if firm.record.exited_year is None else 0.0)
	excess = max(excess, highest - ceiling - year_interest)
check("debt stays within the ceiling plus a year's interest", excess <= 1e-6, (highest, ceiling, excess))
check("a firm with no income and a facility defaults in bounded years", firm.record.exited_year is not None, (years, firm.debt()))
check("it takes the years of arrears, no fewer",
	years >= borrowing_arrears.ARREARS_YEARS_BEFORE_DEFAULT, years)
check("the claim is written off through the pool: nothing is owed", firm.debt() == 0.0 and not purses.claims.get(firm.account_id))
check("the pool's books balance after the default", purses.book.check_conservation(1e-9).ok)
check("the pool holds no negative balance", purses.purse(POOL) >= -1e-9, purses.purse(POOL))

# arrears: past its ceiling the firm draws nothing for interest and the interest is booked as owed
world, registry, firm = firm_owing(debt=5000.0, margin=10.0)
purses = registry.state.purses
debt_before = firm.debt()
firm.pay_interest(world)
check("a borrower past its ceiling draws nothing to pay interest", abs(firm.debt() - debt_before) < 1e-9, (debt_before, firm.debt()))
check("the unpaid interest is arrears", firm.record.interest_arrears > 0.0 and firm.record.arrears_years == 1, firm.record.interest_arrears)

# a borrower paying its interest is untouched
world, registry, firm = firm_owing(debt=5.0, margin=1.0e6)
for _ in range(10):
	world.year += 1
	firm.pay_interest(world)
check("a firm that can pay its interest has no arrears and does not default",
	firm.record.interest_arrears == 0.0 and firm.record.arrears_years == 0 and firm.record.exited_year is None, firm.record.arrears_years)
check("what it pays is drawn on the facility within its ceiling", firm.debt() > 5.0 and firm.debt() <= firm.credit_ceiling(world), firm.debt())
