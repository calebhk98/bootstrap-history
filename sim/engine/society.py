"""What a society believes, fears, and does to you for being large.

This file is a pure composition point: it composes the sibling mixins back into the single SocietyMixin that
sim/engine/core.py's `class Sim(...)` inherits from.

    society_state_pressure.py  alarm, protection, eminence and the state's own fiscal and military interest in a
                               household large enough to be worth leaning on (StatePressureMixin)

How literacy, techniques and disclosure spread is the diffusion module (sim/diffusion/).
"""
from .society_state_pressure import StatePressureMixin


class SocietyMixin(StatePressureMixin):
    """Composition point only: every method is defined in one of the sibling modules above."""
