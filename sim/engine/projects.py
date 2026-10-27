"""The works a household has built: what is left of the projects topic in `Sim` once the projects and ventures modules have taken
the life of a project and of a concern.

This file is a pure composition point (the shape sim/engine/society.py and sim/engine/economy.py establish):

    forward_projects.py        one-line forwarders to the projects module (sim/projects), which owns whether a project may
                               begin, its progress, completion and failure, its staffing rule and the gates a node puts
                               on works that must be running (ProjectsForwardsMixin)
    forward_ventures.py        one-line forwarders to the ventures module (sim/ventures), which owns what a concern ties up and
                               earns, opening one, the founder's sales and the roll-out of public works (VenturesForwardsMixin)"""
from .forward_projects import ProjectsForwardsMixin
from .forward_ventures import VenturesForwardsMixin


class ProjectsMixin(ProjectsForwardsMixin, VenturesForwardsMixin):
    """Composition point only: see the module docstring."""
