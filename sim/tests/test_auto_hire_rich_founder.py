"""A founder holding a large purse, measured in what a labourer costs to hire,
and auto_hire on, ends up with staff. Run with `--only auto_hire_rich_founder`."""
from .harness import *  # noqa: F401,F403

rich_sim = sim(civ="han_china_100ad")
rich_sim.capital = 1000 * rich_sim.labour.market.quote_annual("labourer")
rich_sim.policy["auto_hire"] = True
for _ in range(4):
    rich_sim.step()
check("a rich founder with auto_hire hires within a few years",
      sum(rich_sim.employees.values()) >= 1.0,
      "staff %.2f on %.0f" % (sum(rich_sim.employees.values()), rich_sim.capital))

# The affordability reference for staffing must be what hiring costs now.
reference_sim = sim(civ="rome_100ad")
labour = reference_sim.labour
market_wages = [labour.market.unscarce_annual(trade) for trade in labour._world.wages
                if trade not in labour._world.trades_absent]
check("the staffing wage reference is in the money hiring is paid in",
      0.5 <= labour.staff_wage_reference() / (sum(market_wages) / len(market_wages)) <= 2.0,
      "%.1f against %.1f" % (labour.staff_wage_reference(), sum(market_wages) / len(market_wages)))
