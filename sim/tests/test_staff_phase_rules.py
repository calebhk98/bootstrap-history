"""The yearly staff phase's hiring rules (Complaint 640): the room to hire and the move by whole people, called on
values built here, no game. (The payroll trim, the replacement and the scholar target have their own rule tests.)"""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.engine.staff_phase_rules import (approach, artisan_goal, can_afford_replacement, craft_headcount, directors_next,
                                            has_room_to_hire, hires_needed, scholar_goal)

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

# --- smoothing toward a target and the craft headcount the target pays for
check("a staff approaches its target by the share of the gap", abs(approach(10.0, 20.0, 0.25) - 12.5) < 1e-12)
check("a rate of nothing leaves it where it is and a whole rate arrives", approach(10.0, 20.0, 0.0) == 10.0 and approach(10.0, 20.0, 1.0) == 20.0)
check("freedmen and the slaves who craft are counted inside the artisan target",
      abs(craft_headcount(100.0, 10.0, 20.0, 0.5) - 80.0) < 1e-12)
check("the craft headcount is never negative", craft_headcount(5.0, 10.0, 20.0, 0.5) == 0.0)

# --- the artisans and scholars automatic hiring aims at
check("taught specialists cover part of the craft headcount", artisan_goal(100.0, 30.0, 0.0, 0.0) == 70.0)
check("specialists cannot squeeze the generic artisans below a quarter of the craft headcount", artisan_goal(100.0, 90.0, 0.0, 0.0) == 25.0)
check("hands a shut concern lacks are added to what is held when that is more",
      artisan_goal(100.0, 30.0, 80.0, 5.0) == 85.0)
check("the scholar goal is the smoothed target or the held plus the shut concerns' lack",
      scholar_goal(7.0, 4.0, 1.0) == 7.0 and scholar_goal(7.0, 4.0, 5.0) == 9.0)

# --- the deputies who direct work in the founder's name
check("deputies approach what the institutions allow", abs(directors_next(0.0, 10.0, 0.12, 0.0) - 1.2) < 1e-12)
check("deputies are lost at the attrition rate", abs(directors_next(10.0, 10.0, 0.12, 0.1) - 9.0) < 1e-12)
check("deputies never go below nothing", directors_next(0.0, 0.0, 0.12, 0.1) == 0.0 and directors_next(0.01, 0.0, 0.0, 5.0) == 0.0)

# --- a replacement is paid for only when the household can carry him
check("a household holding more than the years of a replacement's wage may advance it", can_afford_replacement(100.0, 20.0, 4.0))
check("a household holding exactly that or less may not", not can_afford_replacement(80.0, 20.0, 4.0) and not can_afford_replacement(10.0, 20.0, 4.0))
