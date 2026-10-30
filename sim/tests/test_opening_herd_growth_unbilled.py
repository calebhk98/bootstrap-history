"""The opening herds are kept by the herd producers (their recipes pay the labour), so the founder is not billed
for their growth; only head beyond the producers' is the founder's to raise (Complaints/558)."""
from .harness import *  # noqa: F401,F403

from sim.living_stock.api import rules

founder_billed_growth = rules.founder_billed_growth

QUICK_TOPIC = True

check("raising the society's own herd is billed to nobody", founder_billed_growth(10.0, 100.0, 100.0) == 0.0)
check("a society head beyond what is held is still billed to nobody", founder_billed_growth(10.0, 100.0, 500.0) == 0.0)
check("head the founder adds beyond the producers' is raised at the founder's expense, in proportion",
      abs(founder_billed_growth(10.0, 100.0, 60.0) - 4.0) < 1e-12, founder_billed_growth(10.0, 100.0, 60.0))
check("a herd the society keeps none of is all the founder's", founder_billed_growth(10.0, 100.0, 0.0) == 10.0)
