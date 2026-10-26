"""What a society believes, fears, and does to you for being large.

This file is a pure composition point: it composes the sibling mixins back into the single SocietyMixin that
sim/engine/core.py's `class Sim(...)` inherits from.

    society_state_pressure.py  alarm, protection, eminence and the state's own fiscal and military interest in a
                               household large enough to be worth leaning on (StatePressureMixin)
    society_hazards.py         dated hazards, their timelines, and the losses they cause, including the
                               year-driver _shocks (HazardsMixin)
    hazard_relief.py           what relieves a hazard's harm (HazardReliefMixin)

How literacy, techniques and disclosure spread is the diffusion module (sim/diffusion/).
"""
from .hazard_relief import HazardReliefMixin
from .society_hazards import HazardsMixin
from .society_state_pressure import StatePressureMixin


class SocietyMixin(HazardReliefMixin, HazardsMixin, StatePressureMixin):
    """Composition point only: every method is defined in one of the sibling modules above."""
