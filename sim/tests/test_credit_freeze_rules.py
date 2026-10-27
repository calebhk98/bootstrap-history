"""The rules of a run in arrears (Complaint 640): the credit freeze a settlement leaves and when a run counts as
stalled, on built inputs with no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.finance.credit_freeze import (STALL_MINIMUM_INSOLVENT_YEARS, is_stalled, loss_makers, settlement_freeze,
                                       standing_net)

# --- the freeze a settlement leaves
until, moved = settlement_freeze(0, 105, 12)
check("a first-ever settlement freezes credit for the freeze years and moves no earlier date",
      until == 117 and not moved, (until, moved))
until, moved = settlement_freeze(110, 105, 12)
check("settling while an earlier freeze is still in force pushes the date out", until == 117 and moved, (until, moved))
until, moved = settlement_freeze(200, 105, 12)
check("a freeze that already runs past the new one is never shortened, and is not moved",
      until == 200 and not moved, (until, moved))
until, moved = settlement_freeze(90, 105, 12)
check("a freeze already over is replaced, and that is not a moved date", until == 117 and not moved, (until, moved))
until, moved = settlement_freeze(105, 105, 12)
check("a freeze ending the very year of the settlement is not still in force", until == 117 and not moved, (until, moved))

# --- the standing balance
check("the standing balance is what comes in less every recurring cost",
      standing_net(1000.0, 100.0, 300.0, 50.0, 25.0) == 525.0)
check("a household whose costs exceed its income has a negative balance", standing_net(10.0, 100.0, 300.0, 50.0, 25.0) < 0)

# --- when a run has stalled
check("a run in arrears long enough that still loses money has stalled",
      is_stalled(-100.0, STALL_MINIMUM_INSOLVENT_YEARS, -1.0))
check("a run that earns more than it spends has not stalled", not is_stalled(-100.0, 30, 0.0))
check("a run not yet long enough in arrears has not stalled",
      not is_stalled(-100.0, STALL_MINIMUM_INSOLVENT_YEARS - 1, -1.0))
check("a run with money in hand has not stalled, however it bleeds", not is_stalled(0.0, 30, -50.0))

# --- the concerns to close
takings = {"mill": 50.0, "forge": 10.0, "press": 80.0, "kiln": 10.0}
upkeep = {"mill": 80.0, "forge": 40.0, "press": 70.0, "kiln": 40.0}
check("the concerns that cost more than they bring in are named, worst first, ties by name",
      loss_makers(["mill", "forge", "press", "kiln"], takings, upkeep) == ["forge", "kiln", "mill"],
      loss_makers(["mill", "forge", "press", "kiln"], takings, upkeep))
check("a concern that breaks even is not a loss maker", loss_makers(["x"], {"x": 5.0}, {"x": 5.0}) == [])
check("only running concerns are weighed", loss_makers(["press"], takings, upkeep) == [])
