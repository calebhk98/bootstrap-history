"""A `credit_line` effect widens the credit limit while the raw line is what binds, in flat or labour-hour form."""

QUICK_TOPIC = True

from .harness import check

from sim.finance.constants import CREDIT_LINE_EARNING_MULTIPLE, CREDIT_SURPLUS_YEARS_MULTIPLE
from sim.economy.api import opening_market_rate
from sim.mechanics import rules
from sim.tests import finance_host

MONEY_PER_LABOUR_HOUR = 2.0
FLOOR = 100.0
EARNING = 1000.0
STARTING_RATE = opening_market_rate()   # the rate the opening solves; the credit line is scaled against it


def limit_of(specs, acting_seat="founder"):
    """Just what credit_limit reads: no standing and no woodland, an earning, the floor and the effect terms."""
    def effect_sum(channel, start=0.0):
        terms = sorted(specs.items()) if channel == "credit_line" else []
        values = rules.grouped_values(terms, lambda node_id, spec: True,
                                      lambda node_id, spec: rules.effect_size(spec, lambda: 1.0, lambda: MONEY_PER_LABOUR_HOUR))
        return rules.sum_in_order(values, start)
    module = finance_host.build(
        money_per_labour_hour=MONEY_PER_LABOUR_HOUR, effect_sum=effect_sum,
        revenue_capacity=EARNING, upkeep=0.0, agent_rate=STARTING_RATE)
    module.clock.acting_seat = acting_seat
    module.living_cost = lambda revenue=None, upkeep=None, capital=None: FLOOR
    return module.credit_limit()


raw_from_earning = EARNING * CREDIT_LINE_EARNING_MULTIPLE
nothing = limit_of({})
check("with no effect and no standing the limit is the line earning alone gives", nothing == raw_from_earning, nothing)
flat = limit_of({"mod_x:bank": {"flat": 150.0}})
check("a flat credit_line effect widens the limit by its amount while the raw line binds",
      abs(flat - (raw_from_earning + 150.0)) < 1e-9 and flat > nothing, (flat, nothing))
hours = limit_of({"mod_x:bank": {"flat": 100.0, "labour_hours": True}})
check("a labour-hour credit_line effect is priced at the coin's money per labour hour",
      abs(hours - (raw_from_earning + 100.0 * MONEY_PER_LABOUR_HOUR)) < 1e-9, hours)
seat = limit_of({"mod_x:bank": {"flat": 150.0}}, acting_seat="second_seat")
check("the effect widens the limit for any seat, not the founder's alone", seat == flat, (seat, flat))
capped = limit_of({"mod_x:bank": {"flat": 1.0e9}})
check("a wide effect stays bounded by what income can service",
      abs(capped - (FLOOR + (EARNING - FLOOR * STARTING_RATE) * CREDIT_SURPLUS_YEARS_MULTIPLE)) < 1e-9, capped)
