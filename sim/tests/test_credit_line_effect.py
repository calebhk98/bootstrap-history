"""A `credit_line` effect widens the credit limit while the raw line is what binds, in flat or labour-hour form."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine.economy_credit import CreditMixin
from sim.mechanics import rules

MONEY_PER_LABOUR_HOUR = 2.0
FLOOR = 100.0
EARNING = 1000.0
STARTING_RATE = 0.1


class FakeSim(CreditMixin):
    """Just what credit_limit reads: one seat's reputation and forest, an earning, and the effect terms."""

    def __init__(self, specs, reputation=0.0, acting_seat="founder", room=None):
        self.specs = specs
        self.price_index = 1.0
        self.civ = {"starting_interest_rate": STARTING_RATE}
        self.labour = SimpleNamespace(money_per_labour_hour=lambda: MONEY_PER_LABOUR_HOUR)
        self.reputation = reputation
        self.state = SimpleNamespace(acting_seat=acting_seat, household=SimpleNamespace())
        self.room = room

    def view(self, name):   # no woodland held
        return lambda: 0.0

    def effect_sum(self, channel, start=0.0):
        terms = sorted(self.specs.items()) if channel == "credit_line" else []
        values = rules.grouped_values(terms, lambda node_id, spec: True,
                                      lambda node_id, spec: rules.effect_size(spec, lambda: 1.0, lambda: MONEY_PER_LABOUR_HOUR))
        return rules.sum_in_order(values, start)

    def revenue_capacity(self):
        return EARNING

    def upkeep(self):
        return 0.0

    def living_cost(self, _rev=None, _upkeep=None):
        return FLOOR

    def market_rate(self):
        return STARTING_RATE

    def market_credit_room(self, actor_id):
        return self.room


raw_from_earning = EARNING * FakeSim.CREDIT_LINE_EARNING_MULTIPLE
nothing = FakeSim({}).credit_limit()
check("with no effect and no standing the limit is the line earning alone gives", nothing == raw_from_earning, nothing)
flat = FakeSim({"mod_x:bank": {"flat": 150.0}}).credit_limit()
check("a flat credit_line effect widens the limit by its amount while the raw line binds",
      abs(flat - (raw_from_earning + 150.0)) < 1e-9 and flat > nothing, (flat, nothing))
hours = FakeSim({"mod_x:bank": {"flat": 100.0, "labour_hours": True}}).credit_limit()
check("a labour-hour credit_line effect is priced at the coin's money per labour hour",
      abs(hours - (raw_from_earning + 100.0 * MONEY_PER_LABOUR_HOUR)) < 1e-9, hours)
seat = FakeSim({"mod_x:bank": {"flat": 150.0}}, acting_seat="second_seat").credit_limit()
check("the effect widens the limit for any seat, not the founder's alone", seat == flat, (seat, flat))
capped = FakeSim({"mod_x:bank": {"flat": 1.0e9}}).credit_limit()
check("a wide effect stays bounded by what income can service",
      abs(capped - (FLOOR + (EARNING - FLOOR * STARTING_RATE) * FakeSim.CREDIT_SURPLUS_YEARS_MULTIPLE)) < 1e-9, capped)
