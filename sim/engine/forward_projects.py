"""One-line forwarders from the old `Sim` methods of the projects topic to the projects module's views and commands.

Callers outside the module (the screens, fog, the autostart rules, hazards, labour, ventures, the year's money phase) still
say `sim.can_start(node)` or `sim.close_work(node, reason)`; each line goes when its last caller reads the view or sends the
command itself."""
from sim.projects.api import BLOCKER_KINDS, closure_reasons, constants


class ProjectsForwardsMixin:

    BLOCKER_KINDS = BLOCKER_KINDS
    # numbers other topics' code, the screens and the tests still read off the game (sim/projects/constants.py declares them)
    vars().update({name: value for name, value in vars(constants).items() if name.isupper()})
    CLOSED_FOR_STAFF = closure_reasons.CLOSED_FOR_STAFF
    CLOSED_BY_CHOICE = closure_reasons.CLOSED_BY_CHOICE
    CLOSED_LOSS_MAKING = closure_reasons.CLOSED_LOSS_MAKING
    CLOSED_CREDITOR_SEIZURE = closure_reasons.CLOSED_CREDITOR_SEIZURE
    CLOSED_GATE_LAPSED = closure_reasons.CLOSED_GATE_LAPSED

    # ---- starting, stopping, buying ----

    # ---- risk, calendar and cost ----

    # ---- hours and trades ----

    # ---- the goal and what finishing does ----

    # ---- exclusions, gates and closures ----

    # ---- the staffing rule and the works built ----
