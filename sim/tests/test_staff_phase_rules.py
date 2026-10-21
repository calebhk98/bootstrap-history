"""The yearly staff phase's hiring rules (Complaint 640): the room to hire and the move by whole people, called on
values built here, no game. (The payroll trim, the replacement and the scholar target have their own rule tests.)"""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.engine.staff_phase_rules import has_room_to_hire, hires_needed

# --- room to hire
check("a household in funds may hire", has_room_to_hire(10.0, 100.0, 0.5))
check("a household in arrears by less than the hiring share of its credit line may hire", has_room_to_hire(-40.0, 100.0, 0.5))
check("a household in arrears past that share may not", not has_room_to_hire(-60.0, 100.0, 0.5))
check("a household with no credit line and no cash may not hire once overdrawn", not has_room_to_hire(-1.0, 0.0, 0.5))
check("a household with nothing and nothing owed may hire", has_room_to_hire(0.0, 0.0, 0.5))

# --- moving by whole people
check("a shortfall of a whole person is hired", hires_needed(3.0, 4.0) == 1)
check("a shortfall of three whole people hires three", hires_needed(3.0, 6.4) == 3)
check("a gap of under a person is not acted on", hires_needed(3.0, 3.9) == 0)
check("a surplus of a whole person is released (a negative count)", hires_needed(5.0, 4.0) == -1)
check("a surplus of under a person is not acted on", hires_needed(5.0, 4.5) == 0)
check("a staff on its target does nothing", hires_needed(5.0, 5.0) == 0)
