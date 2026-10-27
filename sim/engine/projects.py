"""The works a household has built: what is left of the projects topic in `Sim` once the projects module has taken the life
of a project.

This file is a pure composition point (the shape sim/engine/society.py and sim/engine/economy.py establish), so the
methods can live in files of their own and `Sim` inherits one `ProjectsMixin`:

    forward_projects.py        one-line forwarders to the projects module (sim/projects), which owns whether a project may
                               begin, its progress, completion and failure, its staffing rule and the gates a node puts
                               on works that must be running (ProjectsForwardsMixin)
    projects_ventures.py       the cost and staff of a venture, and the two player-typed verbs that open or close one by
                               hand (VenturesMixin)
    projects_venture_quotes.py what a venture earns and what reopening one costs (VentureQuotesMixin)

The ventures move after the projects module; until then they read the module's views through the forwarders."""
from .forward_projects import ProjectsForwardsMixin
from .projects_venture_quotes import VentureQuotesMixin
from .projects_ventures import VenturesMixin


class ProjectsMixin(ProjectsForwardsMixin, VenturesMixin, VentureQuotesMixin):
    """Composition point only: see the module docstring."""
