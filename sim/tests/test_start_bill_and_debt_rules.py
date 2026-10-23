"""The bill a `start` reply states and the debt the surplus can carry. `settle_project_materials` splits the whole bill into the
materials paid now and the instalments left (so they add up to the cost quoted before starting) and `bill_parts` rounds them for
the reply; `sustainable_debt` and `debt_service_forecast` price a debt against the recurring surplus (the credit forecast of a
`start` and the `money` screen read them). Each is called on a stand-in carrying only what it reads."""

QUICK_TOPIC = True

from .harness import check

from sim.engine.economy_debt_service import DebtServiceMixin
from sim.engine.project_materials import ProjectMaterialsMixin
from sim.ui.proto.start_bill import bill_parts


class Materials(ProjectMaterialsMixin):
    """The parts of a Sim that settling a project's materials reads."""

    def __init__(self, whole, up_front, delivered):
        self.whole, self.up_front, self.delivered = whole, up_front, delivered
        self.bought = []

    def project_cost_now(self, node_id):
        return self.whole

    def _up_front_materials_money(self, node_id):
        return self.up_front

    def buy_project_materials(self, node_id):
        self.bought.append(node_id)
        return self.delivered


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


class Debt(DebtServiceMixin):
    """The parts of a Sim that the debt readings read."""
    DEBT_SERVICE_SHARE_OF_SURPLUS = 0.5

    def __init__(self, surplus, rate):
        self.surplus, self.rate = surplus, rate

    def recurring_net_before_interest(self):
        return self.surplus

    def debt_interest_rate(self):
        return self.rate


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
