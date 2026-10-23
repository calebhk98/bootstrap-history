"""A credit freeze still allows starts paid from cash (Complaints/150), and the save carries no version stamp
(Complaints/184).

What cash pays for during a freeze is tested on built numbers (`cash_covers_start`). The bounty through a save, a load
and a year, and a start through a freeze, are the named scenarios in test_bounty_save_and_credit_freeze_scenario."""
from .harness import *  # noqa: F401,F403
from sim.engine.project_funding import cash_covers_start
import sim.engine.saveload as _saveload_module

# --- 150: a credit freeze allows what cash in hand covers
check("a start the cash covers, on top of nothing owed, is allowed", cash_covers_start(1000.0, 0.0, 0.0, 1000.0))
check("a start needing credit is not covered by cash", not cash_covers_start(1000.0, 0.0, 0.0, 999.0))
check("cash already owed to work in hand is not spent twice", not cash_covers_start(600.0, 0.0, 500.0, 1000.0)
      and cash_covers_start(500.0, 0.0, 500.0, 1000.0))
check("what is already paid towards a start comes off its price", cash_covers_start(1000.0, 400.0, 0.0, 600.0)
      and not cash_covers_start(1000.0, 400.0, 0.0, 599.0))
check("what is paid towards a start never reduces the price below nothing, nor does a negative payment raise it",
      cash_covers_start(1000.0, 5000.0, 0.0, 0.0) and not cash_covers_start(1000.0, -50.0, 0.0, 999.0))
check("a household in arrears covers no start with cash but a free one", not cash_covers_start(1.0, 0.0, 0.0, -5.0)
      and cash_covers_start(0.0, 0.0, 0.0, 0.0))
check("saveload has no SAVE_VERSION", not hasattr(_saveload_module, "SAVE_VERSION"))
