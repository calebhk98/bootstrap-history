"""The commands the labour package sends through its world, kept apart from the readers (world_reads.py)."""
from sim.seats.api import RememberGoalClosure

from .commands import BuildHousing
from .commands_bondage import NoteBuyRefusal


class WorldCommands:
    """Each method sends one command to the module that owns the fact it changes."""

    def __init__(self, needs, parts):
        self._needs = needs
        self._parts = parts

    def build_worker_housing(self, places):
        return self._needs.send(BuildHousing(places))

    def remember_goal_closure(self, closure):
        """Keep what the goal needs, once worked out."""
        self._needs.send(RememberGoalClosure(closure))

    def note_buy_refusal(self, refusal):
        """Keep why the acting seat's purchase of people was refused, for the screen that asked."""
        self._parts.core.note_buy_refusal(NoteBuyRefusal(refusal))
