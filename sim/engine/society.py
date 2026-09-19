"""What a society believes, fears, and does to you for being large.

These are methods of Sim; they are a mixin only so that they can live in
a file of their own.

This file is a pure composition point: one file holding all of a
household's social mechanics becomes a file nobody can edit without
colliding with everyone else touching them, so the 61 methods live in
four sibling modules, grouped by subject rather than by size, and this
file's only job is to compose them back into the single SocietyMixin that
sim/engine/core.py's `class Sim(...)` already expects, unchanged, to
inherit from:

    society_state_pressure.py  alarm, protection, eminence and the state's
                                own fiscal and military interest in a
                                household large enough to be worth leaning
                                on (StatePressureMixin)
    society_adoption.py        how THIS population takes up what has been
                                built - tech effects, agrarian slack,
                                literacy, trade absorption (AdoptionMixin)
    society_diffusion.py       how what has been built leaks to imitators
                                and spreads across civilisations
                                (DiffusionMixin)
    society_hazards.py         dated hazards, their timelines, and the
                                losses they cause, including the year-driver
                                _shocks (HazardsMixin)

No method appears in more than one of the four; see each module's own
docstring for exactly which methods it holds and why they sit together.
"""
from .society_hazards import HazardsMixin
from .society_state_pressure import StatePressureMixin
from .society_adoption import AdoptionMixin
from .society_diffusion import DiffusionMixin


class SocietyMixin(HazardsMixin, StatePressureMixin, AdoptionMixin, DiffusionMixin):
    """Composition point only: every method below is defined in one of the
    four sibling modules above, not here. This class exists so that
    sim/engine/core.py's `class Sim(..., SocietyMixin, ...)` keeps working
    unmodified - Sim, and everything that calls a society method on it,
    neither knows nor needs to know that the 61 methods it sees on
    SocietyMixin are spread across four files rather than gathered in one.
    """
