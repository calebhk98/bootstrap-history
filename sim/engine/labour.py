"""People: hiring them, teaching them, buying them, paying them.

Split out of simulator.py, which had grown to 5,600 lines, then further
split as it grew again. These are methods of Sim; they are a mixin only so
that they can live in a file of their own. Behaviour is unchanged and
verified byte-identical.

This file grew to 3,214 lines and 50 methods on its own, at which point it
became the same problem simulator.py was: one file nobody could edit
without colliding with everyone else touching Sim's labour mechanics. It is
now a pure composition point. The 50 methods live in five sibling modules,
grouped by subject rather than by size, and this file's only job is to
compose them back into the single LabourMixin that sim/engine/core.py's
`class Sim(...)` already expects, unchanged, to inherit from:

    labour_capacity.py    literacy, institutional (staff_capacity) and
                           supervisory (supervision_room) ceilings on how
                           many people this household may hire, teach, own
                           or direct, plus the founder's own hour budget
                           the rest of the file spends (CapacityMixin)
    labour_population.py  the local labour market itself - depth, price
                           response to recent hiring, and the population
                           estimates the 'population' command shows
                           (PopulationMixin)
    labour_wages.py        what staff actually cost every year, and what
                           it costs to be one yourself (WagesMixin)
    labour_training.py    hiring, firing, teaching, commissioning, and
                           what a technology does to an hour once bought
                           (TrainingMixin)
    labour_bondage.py     buying people, freeing them, and the pool
                           bookkeeping that keeps trained/granted staff
                           honest (BondageMixin)

No method appears in more than one of the five; see each module's own
docstring for exactly which methods it holds and why they sit together.
"""
from .labour_capacity import CapacityMixin
from .labour_population import PopulationMixin
from .labour_wages import WagesMixin
from .labour_training import TrainingMixin
from .labour_bondage import BondageMixin


class LabourMixin(CapacityMixin, PopulationMixin, WagesMixin, TrainingMixin, BondageMixin):
    """Composition point only: every method below is defined in one of the
    five sibling modules above, not here. This class exists so that
    sim/engine/core.py's `class Sim(..., LabourMixin, ...)` keeps working
    unmodified - Sim, and everything that calls a labour method on it,
    neither knows nor needs to know that the 50 methods it sees on
    LabourMixin are spread across five files rather than gathered in one.
    """
