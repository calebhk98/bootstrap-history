"""Complaint 648 item 3: a bonded person's yearly death rate depends on where the person lives (an urban household,
rural land, rural land in malarial terrain). The rule is a plain function; inputs are written out, no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

from sim.agents.bonded_residence import MALARIAL_EXCESS_DEATH_RATE, residence_death_rate

BASE = 0.03

check("no residence shares leave the base rate", residence_death_rate(BASE, {}, {"urban": 0.25}) == BASE)
check("a stratum wholly urban pays the urban premium as a share of the base rate",
      abs(residence_death_rate(BASE, {"urban": 1.0}, {"urban": 0.25}) - BASE * 1.25) < 1e-12)
check("a half urban stratum pays half the premium",
      abs(residence_death_rate(BASE, {"urban": 1.0, "rural": 1.0}, {"urban": 0.25}) - BASE * 1.125) < 1e-12)
check("shares are normalised, so 2 and 2 equal 0.5 and 0.5",
      residence_death_rate(BASE, {"urban": 2.0, "rural": 2.0}, {"urban": 0.25})
      == residence_death_rate(BASE, {"urban": 0.5, "rural": 0.5}, {"urban": 0.25}))
check("malarial land adds the sourced excess rate over the share living there",
      abs(residence_death_rate(BASE, {"malarial": 0.5, "rural": 0.5}, {}) - (BASE + 0.5 * MALARIAL_EXCESS_DEATH_RATE)) < 1e-12)
check("a residence with no figure adds nothing", residence_death_rate(BASE, {"mine": 1.0}, {"urban": 0.25}) == BASE)
check("a negative premium never lowers the rate below the base", residence_death_rate(BASE, {"urban": 1.0}, {"urban": -0.5}) == BASE)
check("a zero total share leaves the base rate", residence_death_rate(BASE, {"urban": 0.0}, {"urban": 0.25}) == BASE)

# the stratum's yearly growth takes the residence rule (grow is called on a stand-in stratum with the plan written out)
from sim.agents.stratum_year import grow
from sim.agents.tuning_strata import GROWTH_LAG_SHARE


class Record:
    def __init__(self, plan):
        self.plan = plan
        self.welfare = 1.0
        self.shortfall = {}
        self.last_growth = 0.0
        self.members = 1000.0


class Stand:
    def __init__(self, plan):
        self.record = Record(plan)


rural, urban = Stand({"bonded": True}), Stand({"bonded": True, "residence": {"urban": 1.0}})
grow(rural, 0.25)
grow(urban, 0.25)
check("an urban bonded stratum grows more slowly than one with no residence shares",
      urban.record.last_growth < rural.record.last_growth, (urban.record.last_growth, rural.record.last_growth))
check("the gap is the lagged urban premium on the base death rate",
      abs((rural.record.last_growth - urban.record.last_growth) - GROWTH_LAG_SHARE * 0.25 * 0.034) < 1e-12)
