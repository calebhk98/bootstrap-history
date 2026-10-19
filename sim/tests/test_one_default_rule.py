"""Complaint 589: the founder's household and a firm owing more than their ceilings go through one arrears-and-default rule.

The same state (debt past the ceiling, nothing paying it down) must reach default after the same
number of years in arrears for both, and each year the unpaid interest is arrears, not more debt.
"""
from .harness import *  # noqa: F401,F403

from sim.agents import borrowing_arrears
from sim.agents.api import ActorRecord, Business, ActorRegistry, ActorsState
from sim.agents.stratum import Stratum  # noqa: F401  (registers the kind)

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


def years_until_founder_defaults():
    founder = sim(capital=-99999.0)
    start = founder.year
    check("the founder's debt is past its ceiling in this state", -founder.capital > founder.credit_limit(),
          (founder.capital, founder.credit_limit()))
    debts = []
    for years in range(1, MAX_YEARS + 1):
        year = start + years
        founder.charge_interest(year)
        founder.enforce_credit_limit(year)
        debts.append(-founder.capital)
        if founder.last_settlement != -999:
            return years, debts
    return None, debts


firm_years, firm = years_until_firm_defaults()
founder_years, founder_debts = years_until_founder_defaults()
check("a firm past its ceiling defaults after the shared run of years in arrears",
      firm_years == borrowing_arrears.ARREARS_YEARS_BEFORE_DEFAULT, firm_years)
check("the founder past its ceiling defaults after the same run of years in arrears",
      founder_years == firm_years, (founder_years, firm_years))
check("the founder's debt does not compound past its ceiling while in arrears",
      founder_years is not None and all(abs(debt - founder_debts[0]) < 1e-6 for debt in founder_debts[:founder_years - 1]),
      founder_debts[:5])
