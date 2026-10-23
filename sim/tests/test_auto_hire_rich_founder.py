"""SCENARIO (Complaint 640): A founder holding a large purse, measured in what a labourer costs to hire,
and auto_hire on, ends up with staff. The staffing wage reference is tested in test_staff_wage_reference. Run with `--only auto_hire_rich_founder`."""
from .harness import *  # noqa: F401,F403

rich_sim = sim(civ="han_china_100ad")
rich_sim.capital = 1000 * rich_sim.labour.market.quote_annual("labourer")
rich_sim.policy["auto_hire"] = True
for _ in range(4):
    rich_sim.step()
check("scenario: a rich founder with auto_hire hires within a few years",
      sum(rich_sim.employees.values()) >= 1.0,
      "staff %.2f on %.0f" % (sum(rich_sim.employees.values()), rich_sim.capital))
