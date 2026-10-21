"""The yearly staff phase's rules (Complaint 640): who is let go when the payroll cannot be met, the room to hire, the
staff targets and the replacement of a taught trade, called on values built here, no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.engine.staff_phase_rules import (has_room_to_hire, hires_needed, payroll_shortfall, replacement_shortfall,
                                          shed_for_payroll, staff_targets)

WAGES = {"scholar": 300.0, "smith": 100.0, "labourer": 40.0, "unpaid": 0.0}

# --- the payroll shortfall
check("a payroll the income covers has no shortfall", payroll_shortfall(500.0, 1000.0, 400.0, 0.0, 0.0) == 0.0)
check("a payroll beyond the income is short by the difference",
      payroll_shortfall(900.0, 1000.0, 400.0, 0.0, 0.0) == 300.0)
check("credit left to draw covers a shortfall: being overdrawn is not being unable to pay",
      payroll_shortfall(900.0, 1000.0, 400.0, -50.0, 400.0) == 0.0)
check("the arrears already carried come off the credit left",
      payroll_shortfall(900.0, 1000.0, 400.0, -300.0, 400.0) == 200.0)
check("past the credit limit there is no headroom, never a negative one",
      payroll_shortfall(900.0, 1000.0, 400.0, -500.0, 400.0) == 300.0)
check("cash in hand counts as headroom", payroll_shortfall(900.0, 1000.0, 400.0, 150.0, 0.0) == 150.0)
check("a payroll exactly met has no shortfall", payroll_shortfall(600.0, 1000.0, 400.0, 0.0, 0.0) == 0.0)

# --- who is let go
cuts = shed_for_payroll(250.0, {"smith": 5.0, "scholar": 2.0, "labourer": 9.0}, WAGES.get)
check("the dearest trade is let go first, whole people, rounded up", cuts == [("scholar", 1, 1.0)], cuts)
cuts = shed_for_payroll(700.0, {"smith": 5.0, "scholar": 2.0, "labourer": 9.0}, WAGES.get)
check("once the dearest trade is gone the next is cut until the wages fit",
      cuts == [("scholar", 2, 0.0), ("smith", 1, 4.0)], cuts)
cuts = shed_for_payroll(30.0, {"labourer": 9.0}, WAGES.get)
check("a shortfall under one wage still lets one whole person go", cuts == [("labourer", 1, 8.0)], cuts)
cuts = shed_for_payroll(1e6, {"smith": 2.0, "labourer": 1.0}, WAGES.get)
check("a shortfall beyond the whole payroll lets everyone go and no more",
      cuts == [("smith", 2.0, 0.0), ("labourer", 1.0, 0.0)], cuts)
check("a trade that draws no wage is skipped", shed_for_payroll(100.0, {"unpaid": 4.0}, WAGES.get) == [])
check("nothing short lets nobody go", shed_for_payroll(0.0, {"smith": 5.0}, WAGES.get) == [])
cuts = shed_for_payroll(60.0, {"smith": 0.6}, WAGES.get)
check("a remainder under half a person is let go with the rest", cuts == [("smith", 0.6, 0.0)], cuts)
cuts = shed_for_payroll(60.0, {"smith": 3.0}, WAGES.get)
check("a remainder of whole people is kept as it stands", cuts == [("smith", 1, 2.0)], cuts)

# --- room to hire
check("a household in funds may hire", has_room_to_hire(10.0, 100.0, 0.5))
check("a household in arrears by less than the hiring share of its credit line may hire", has_room_to_hire(-40.0, 100.0, 0.5))
check("a household in arrears past that share may not", not has_room_to_hire(-60.0, 100.0, 0.5))
check("a household with no credit line and no cash may not hire once overdrawn", not has_room_to_hire(-1.0, 0.0, 0.5))
check("a household with nothing and nothing owed may hire", has_room_to_hire(0.0, 0.0, 0.5))

# --- what the staff aims at
wanted_scholars, craft = staff_targets(4.0, 10.0, 6.0, 20.0, 5.0, 0.5, 100.0, 0.2, 0.1, 0.0, 0.0, 0.5)
check("the scholar target is capacity plus a share of the spare room, approached by a fraction of the gap",
      abs(wanted_scholars - (4.0 + (6.0 + 2.5 - 4.0) * 0.2)) < 1e-12, wanted_scholars)
check("the craftsmen target is capacity plus the spare room, approached by a fraction of the gap",
      abs(craft - (10.0 + (25.0 - 10.0) * 0.1)) < 1e-12, craft)
wanted_scholars, _ = staff_targets(4.0, 10.0, 60.0, 20.0, 50.0, 0.5, 5.0, 0.2, 0.1, 0.0, 0.0, 0.5)
check("the scholar target never passes the literacy ceiling", abs(wanted_scholars - (4.0 + (5.0 - 4.0) * 0.2)) < 1e-12,
      wanted_scholars)
_, craft = staff_targets(4.0, 10.0, 6.0, 20.0, 5.0, 0.5, 100.0, 0.2, 0.1, 3.0, 4.0, 0.5)
check("the freed and the enslaved already counted come off the generic craftsmen wanted",
      abs(craft - (10.0 + 1.5 - 3.0 - 2.0)) < 1e-12, craft)
_, craft = staff_targets(4.0, 0.0, 0.0, 0.0, 0.0, 0.5, 100.0, 0.2, 0.1, 30.0, 40.0, 0.5)
check("the craftsmen wanted are never negative", craft == 0.0, craft)
wanted_scholars, _ = staff_targets(8.0, 10.0, 2.0, 20.0, 0.0, 0.5, 100.0, 0.2, 0.1, 0.0, 0.0, 0.5)
check("a staff above its target moves down toward it", wanted_scholars < 8.0, wanted_scholars)

# --- moving by whole people
check("a shortfall of a whole person is hired", hires_needed(3.0, 4.0) == 1)
check("a shortfall of three whole people hires three", hires_needed(3.0, 6.4) == 3)
check("a gap of under a person is not acted on", hires_needed(3.0, 3.9) == 0)
check("a surplus of a whole person is released (a negative count)", hires_needed(5.0, 4.0) == -1)
check("a surplus of under a person is not acted on", hires_needed(5.0, 4.5) == 0)
check("a staff on its target does nothing", hires_needed(5.0, 5.0) == 0)

# --- replacing a taught trade
check("a taught trade down to nothing is replaced up to the target when the household can afford it",
      replacement_shortfall(0.0, True, 2.0, 1000.0, lambda: 100.0, 3.0) == 2.0)
check("a trade the founder never taught is not replaced", replacement_shortfall(0.0, False, 2.0, 1000.0, lambda: 100.0, 3.0) == 0.0)
check("a taught trade already at its target is not replaced", replacement_shortfall(2.0, True, 2.0, 1000.0, lambda: 100.0, 3.0) == 0.0)
check("a taught trade is not replaced without the money for the years of wage the rule asks for",
      replacement_shortfall(0.0, True, 2.0, 250.0, lambda: 100.0, 3.0) == 0.0)
check("a gap of a hundredth of a person is not replaced", replacement_shortfall(1.99, True, 2.0, 1000.0, lambda: 100.0, 3.0) == 0.0)
asked = []
replacement_shortfall(2.0, True, 2.0, 1000.0, lambda: asked.append(1) or 100.0, 3.0)
check("the wage is asked only when there is a shortfall to fill", asked == [])
