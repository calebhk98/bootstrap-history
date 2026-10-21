"""Complaint 564: the founder's household buys its needs through the economy's need basket and floors, so its living
cost is a read of that bill and a household of the same size pays the same. The rules are called on stubs that hold only
what each reads; the economy's floors against a running game are in test_one_living_cost_model_scenario."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.engine.economy_credit import CreditMixin
from sim.engine.economy_household_bill import HouseholdBillMixin

QUICK_TOPIC = True

FLOORS = {"grain": 30.0, "cloth": 12.0, "fuel": 8.0}


def seat(freedmen=0, slaves=0, capital=0.0, tax_share=0.0, wages=0.0, status_per_capital=0.0):
    """Just what the bill, the dependants' cost and the living cost read."""
    stub = SimpleNamespace(
        HOUSEHOLD_DEPENDANT_PEOPLE=1.0, LIVING_COST_STATUS_PER_CAPITAL=status_per_capital,
        LIVING_COST_APPEARANCES_SHARE_OF_ROOM=0.5, price_index=1.0, civ={"starting_tax_share": tax_share},
        state=SimpleNamespace(household=SimpleNamespace(freedmen=freedmen, slaves=slaves, capital=capital)),
        labour=SimpleNamespace(wage_bill=lambda: wages),
        household_need_floors_per_person=lambda: dict(FLOORS),
        effect_values=lambda name: [], upkeep=lambda: 0.0, revenue=lambda: 0.0)
    stub.household_bill_per_person = lambda: HouseholdBillMixin.household_bill_per_person(stub)
    stub.household_dependant_people = lambda: HouseholdBillMixin.household_dependant_people(stub)
    stub.dependants_cost = lambda: CreditMixin.dependants_cost(stub)
    return stub


bill = sum(FLOORS.values())
check("a person's bill is the sum of every need's floor", seat().household_bill_per_person() == bill)
check("freedmen and slaves are people too",
      seat(freedmen=2, slaves=3).household_dependant_people() == HouseholdBillMixin.HOUSEHOLD_DEPENDANT_PEOPLE + 5,
      seat(freedmen=2, slaves=3).household_dependant_people())
check("the dependants are people with the founder's needs, one bill each",
      abs(seat(freedmen=2, slaves=3).dependants_cost() - seat(freedmen=2, slaves=3).household_dependant_people() * bill) < 1e-9)
check("with no tax, status or wages, the living cost is the founder's bill and the dependants'",
      abs(CreditMixin.living_cost(seat(freedmen=1)) - 3.0 * bill) < 1e-9, CreditMixin.living_cost(seat(freedmen=1)))
check("wages the household pays add to its living cost",
      abs(CreditMixin.living_cost(seat(wages=100.0)) - (2.0 * bill + 100.0)) < 1e-9)
check("tax is the civilisation's share of revenue",
      abs(CreditMixin.living_cost(seat(tax_share=0.1), _rev=1000.0, _upkeep=0.0) - (2.0 * bill + 100.0)) < 1e-9,
      CreditMixin.living_cost(seat(tax_share=0.1), _rev=1000.0, _upkeep=0.0))
