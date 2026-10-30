"""The bill a `start` reply states and the debt the surplus can carry. `settle_project_materials` splits the whole bill into the
materials paid now and the instalments left (so they add up to the cost quoted before starting) and `bill_parts` rounds them for
the reply; `sustainable_debt` and `debt_service_forecast` price a debt against the recurring surplus (the credit forecast of a
`start` and the `money` screen read them). Each is called on the finance module (or a stand-in) carrying only what it reads."""

QUICK_TOPIC = True

from .harness import check

from sim.tests import finance_host
from sim.materials.api import SettleProjectMaterials
from sim.tests import materials_stand_in
from sim.ui.proto.start_bill import bill_parts


class Materials:
    """The materials module with what settling a project's materials reads: the whole bill, the up-front money and what
    the market delivers."""

    def __init__(self, whole, up_front, delivered):
        self.bought = []
        module = materials_stand_in.build(project_cost_now=lambda node_id: whole)
        module.up_front_materials_money = lambda node_id: up_front
        module.buy_project_materials = lambda node_id: self.bought.append(node_id) or delivered
        self.settle_project_materials = lambda node_id: module.settle_project_materials(SettleProjectMaterials(node_id))


everything = Materials(1000.0, 300.0, 300.0)
instalments, paid_now = everything.settle_project_materials("mill")
check("the materials bought are paid now and the rest of the bill is left in instalments", (paid_now, instalments) == (300.0, 700.0))
partial = Materials(1000.0, 300.0, 120.0)
instalments, paid_now = partial.settle_project_materials("mill")
check("when the market delivers only part, only that part is paid now and the instalments take up the rest",
      (paid_now, instalments) == (120.0, 880.0) and instalments + paid_now == 1000.0)
none_needed = Materials(1000.0, 0.0, 0.0)
check("with no material to buy up front nothing is bought and the whole bill is instalments",
      none_needed.settle_project_materials("mill") == (1000.0, 0.0) and none_needed.bought == [])

check("the whole bill is the sum of the two rounded parts, so the printed figures add up",
      bill_parts(700.04, 299.96) == (1000.0, 300.0, 700.0) and bill_parts(0.26, 0.26) == (0.6, 0.3, 0.3))


def Debt(surplus, rate):
    """The finance module whose recurring surplus and arrears rate are given."""
    module = finance_host.build()
    module.recurring_net_before_interest = lambda: surplus
    module.debt_interest_rate = lambda: rate
    return module


check("the sustainable debt is the share of the surplus the interest may take, over the rate",
      Debt(1000.0, 0.1).sustainable_debt() == 5000.0)
check("with no surplus there is no sustainable debt", Debt(-50.0, 0.1).sustainable_debt() == 0.0)

forecast = Debt(1000.0, 0.1).debt_service_forecast(2000.0)
check("the forecast prices the interest on the draw and its share of the surplus",
      forecast["interest_per_year_at_that_draw"] == 200.0 and forecast["interest_as_share_of_recurring_surplus"] == 0.2
      and forecast["recurring_surplus_before_interest"] == 1000.0, forecast)
check("the forecast carries the sustainable debt beside the draw", forecast["sustainable_debt"] == 5000.0, forecast)
check("with no surplus the interest has no share to be a share of", Debt(0.0, 0.1).debt_service_forecast(2000.0)[
    "interest_as_share_of_recurring_surplus"] is None)
