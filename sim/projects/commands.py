"""The commands the projects module applies: starting, stopping and buying a project, and buying off scandal."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class StartProject(Command):
    """The acting seat begins a project: refused with the first blocker the start gate finds, otherwise the shared
    research path (every actor's start) takes the bill and registers the project. Answers (True, None) or
    (False, refusal) as `start_project` always did."""
    node_id: str
    precaution: bool = False       # also pay for the node's pilot plant or redundant team


@dataclass(frozen=True)
class StopProject(Command):
    """The acting seat stops a project in hand. The hours are gone; the money already spent stands to its credit
    and comes off the bill if it is begun again. Answers (True, text) or (False, "not active")."""
    node_id: str


@dataclass(frozen=True)
class PostBounty(Command):
    """The acting seat pays a public prize for a whole project, so someone else does the work. Answers whether it
    was posted (False when the prize is past the purse)."""
    node_id: str


@dataclass(frozen=True)
class Bribe(Command):
    """The acting seat buys down scandal and buys protection for a stated sum, never taking more than that can
    use. Answers (True, text) or (False, text) with the reason."""
    amount: float


@dataclass(frozen=True)
class ResetProjectProgress(Command):
    """Every project the acting seat has in hand goes back to the beginning: all its work left, none of its years
    done (a sack burns the site). Not applied by the projects module yet: the engine bridge applies it."""


@dataclass(frozen=True)
class ShutForgotten(Command):
    """The acting seat's works for `node_ids`, techniques it has just lost, are no longer running or shut for a time.
    Not applied by the projects module yet: the engine bridge applies it."""
    node_ids: tuple
