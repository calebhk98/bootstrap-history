"""The grace window after a staffing closure (Complaint 640): the window, the discounted fee and the note, on built
inputs with no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.projects.closure_grace import fee_after_grace, grace_note, within_grace

GRACE, DISCOUNT = 6, 0.1

check("a closure as old as the grace years is still inside the window", within_grace(GRACE, GRACE))
check("a closure a year past the grace years is outside it", not within_grace(GRACE + 1, GRACE))
check("a closure the same year is inside it", within_grace(0, GRACE))
check("a work not shut for want of staff has no window", not within_grace(None, GRACE))
check("inside the window the fee is the discounted share", abs(fee_after_grace(1000.0, 3, GRACE, DISCOUNT) - 100.0) < 1e-9)
check("outside the window the fee is the whole fee", fee_after_grace(1000.0, GRACE + 1, GRACE, DISCOUNT) == 1000.0)
check("a work not shut for want of staff pays the whole fee", fee_after_grace(1000.0, None, GRACE, DISCOUNT) == 1000.0)
check("the lapsed-window fee is the inverse of the discount times the in-window one",
      abs(fee_after_grace(1000.0, GRACE + 1, GRACE, DISCOUNT) / fee_after_grace(1000.0, 0, GRACE, DISCOUNT) - 1.0 / DISCOUNT) < 1e-9)
check("a work not shut for want of staff gets no note", grace_note(None, GRACE) is None)
check("a note is given inside and outside the window and differs between them",
      grace_note(2, GRACE) and grace_note(GRACE + 2, GRACE) and grace_note(2, GRACE) != grace_note(GRACE + 2, GRACE))
# presentation: the note names the closure's age and the grace years it is measured against
check("the note names the closure's age and the years allowed",
      "2" in grace_note(2, GRACE) and str(GRACE) in grace_note(2, GRACE)
      and str(GRACE + 2) in grace_note(GRACE + 2, GRACE) and str(GRACE) in grace_note(GRACE + 2, GRACE))
