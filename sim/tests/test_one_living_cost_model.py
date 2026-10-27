"""Complaint 564: the founder's household buys its needs through the economy's need basket and floors, so its living
cost is a read of that bill and a household of the same size pays the same. The bill is called on a stub that holds only what it
reads, and the living cost on the finance module over plain values; the floors at the seat are in test_one_living_cost_floors."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.engine.economy_household_bill import HouseholdBillMixin
from sim.tests import finance_host

QUICK_TOPIC = True

FLOORS = {"grain": 30.0, "cloth": 12.0, "fuel": 8.0}
BILL = sum(FLOORS.values())


def bill_stub(freedmen=0, slaves=0):
    """Just what the bill and the number of people read."""
    stub = SimpleNamespace(HOUSEHOLD_DEPENDANT_PEOPLE=HouseholdBillMixin.HOUSEHOLD_DEPENDANT_PEOPLE,
                           state=SimpleNamespace(household=SimpleNamespace(freedmen=freedmen, slaves=slaves)),
                           household_need_floors_per_person=lambda: dict(FLOORS))
    stub.household_bill_per_person = lambda: HouseholdBillMixin.household_bill_per_person(stub)
    return stub


def seat(freedmen=0, slaves=0, capital=0.0, tax_share=0.0, wages=0.0):
    """The finance module over the bill and the people the economy reports for this household."""
    stub = bill_stub(freedmen, slaves)
    return finance_host.build(
        acting_balance=capital, civilisation={"starting_tax_share": tax_share}, wage_bill=wages, household_bill_per_person=BILL,
        household_dependant_people=HouseholdBillMixin.household_dependant_people(stub), revenue_estimate=0.0, upkeep=0.0)


check("a person's bill is the sum of every need's floor", bill_stub().household_bill_per_person() == BILL)
people = HouseholdBillMixin.household_dependant_people(bill_stub(freedmen=2, slaves=3))
check("freedmen and slaves are people too", people == HouseholdBillMixin.HOUSEHOLD_DEPENDANT_PEOPLE + 5, people)
check("the dependants are people with the founder's needs, one bill each",
      abs(seat(freedmen=2, slaves=3).dependants_cost() - people * BILL) < 1e-9)
check("with no tax, status or wages, the living cost is the founder's bill and the dependants'",
      abs(seat(freedmen=1).living_cost() - 3.0 * BILL) < 1e-9, seat(freedmen=1).living_cost())
check("wages the household pays add to its living cost",
      abs(seat(wages=100.0).living_cost() - (2.0 * BILL + 100.0)) < 1e-9)
check("tax is the civilisation's share of revenue",
      abs(seat(tax_share=0.1).living_cost(revenue=1000.0, upkeep=0.0) - (2.0 * BILL + 100.0)) < 1e-9,
      seat(tax_share=0.1).living_cost(revenue=1000.0, upkeep=0.0))
