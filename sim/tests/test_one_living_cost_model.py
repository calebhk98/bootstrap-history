"""Complaint 564: the founder's household buys its needs through the economy's need basket and floors, so its living
cost is a read of that bill and a household of the same size pays the same. The bill is called on the markets module over a stand-in economy, the people on the workforce module, and the living cost on the finance module over plain values; the floors at the seat are in test_one_living_cost_floors."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.tests import finance_host, market_stand_in, module_harness
from sim.workforce.constants import HOUSEHOLD_DEPENDANT_PEOPLE
from sim.workforce.module import Workforce

QUICK_TOPIC = True

FLOORS = {"grain": 30.0, "cloth": 12.0, "fuel": 8.0}
BILL = sum(FLOORS.values())


def bill_module():
    """The markets module over an economy that reports these floors for the seat's tile."""
    return market_stand_in.markets_over(economy=SimpleNamespace(agent_need_floor_costs_at=lambda: dict(FLOORS)))


def dependants(freedmen=0, slaves=0):
    """The people the workforce module counts the household keeps besides the founder."""
    module = module_harness.build(Workforce)
    module.staff = lambda: {"freedmen": freedmen, "slaves": slaves}
    return module.household_dependant_people()


def seat(freedmen=0, slaves=0, capital=0.0, tax_share=0.0, wages=0.0):
    """The finance module over the bill and the people the economy reports for this household."""
    return finance_host.build(
        acting_balance=capital, civilisation={"starting_tax_share": tax_share}, wage_bill=wages, household_bill_per_person=BILL,
        household_dependant_people=dependants(freedmen, slaves), revenue_estimate=0.0, upkeep=0.0)


check("a person's bill is the sum of every need's floor", bill_module().household_bill_per_person() == BILL)
people = dependants(freedmen=2, slaves=3)
check("freedmen and slaves are people too", people == HOUSEHOLD_DEPENDANT_PEOPLE + 5, people)
check("the dependants are people with the founder's needs, one bill each",
      abs(seat(freedmen=2, slaves=3).dependants_cost() - people * BILL) < 1e-9)
check("with no tax, status or wages, the living cost is the founder's bill and the dependants'",
      abs(seat(freedmen=1).living_cost() - 3.0 * BILL) < 1e-9, seat(freedmen=1).living_cost())
check("wages the household pays add to its living cost",
      abs(seat(wages=100.0).living_cost() - (2.0 * BILL + 100.0)) < 1e-9)
check("tax is the civilisation's share of revenue",
      abs(seat(tax_share=0.1).living_cost(revenue=1000.0, upkeep=0.0) - (2.0 * BILL + 100.0)) < 1e-9,
      seat(tax_share=0.1).living_cost(revenue=1000.0, upkeep=0.0))
