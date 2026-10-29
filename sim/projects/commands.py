"""The commands the projects module applies: starting, stopping and buying a project, and buying off scandal."""
from dataclasses import dataclass
from typing import Optional

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


@dataclass(frozen=True)
class AdvanceProjects(Command):
    """The year's progress step for the acting seat: every project in hand takes its turn at the director hours left in
    `pool` and the hired hours left in `hired_left`. Answers (hours left in the pool, the same before wage work, the
    hours the projects effectively used)."""
    pool: float
    hired_left: float


@dataclass(frozen=True)
class CompleteProject(Command):
    """Finish the project in hand at once, as the roll of the dice at its end would: a failed roll costs the attempt, a
    passed one makes the node a held technique. Answers nothing."""
    node_id: str


@dataclass(frozen=True)
class CloseWork(Command):
    """Shut a work and record why and since when (`reason`; `year` defaults to this year). Whatever requires it running
    shuts with it unless `cascade` is off."""
    node_id: str
    reason: str
    year: Optional[int] = None
    cascade: bool = True


@dataclass(frozen=True)
class CloseLapsedDependents(Command):
    """Close every open node whose required work is no longer running, down the chain. Answers the ids closed, in order."""
    year: int


@dataclass(frozen=True)
class CloseUnstaffedVentures(Command):
    """Shut just enough of what nobody is left to supervise, lowest net value first. Answers the ids closed."""
    year: int


@dataclass(frozen=True)
class ReopenRestaffedVentures(Command):
    """Bring back what the staffing rule shut, the moment there are people to watch it again. Answers the ids reopened."""
    year: int


@dataclass(frozen=True)
class AutoOpenVentures(Command):
    """Open what plainly pays for itself, best margin first, within the staff and money available. Answers the ids opened."""


@dataclass(frozen=True)
class NoteVentureYear(Command):
    """Tally each running plant's margin and the years running it has lost money (the loss rule's input)."""


@dataclass(frozen=True)
class ReviewVentures(Command):
    """The seat's business under the yearly review by the named `rules` (the rules of sim/agents/business_review.py);
    plants it shuts are dated `year` (None: this year). Answers what closed and why."""
    rules: tuple
    year: Optional[int] = None


@dataclass(frozen=True)
class HaltActiveProjects(Command):
    """Every project in hand stops, unfinished: what was paid towards each stands to its credit, and a bounty on it lapses.
    Answers (the names halted in order, the money that stands to the seat's credit)."""


@dataclass(frozen=True)
class MothballWork(Command):
    """Shut a completed work down to stop paying its upkeep. Answers (did it, the reply)."""
    node_id: str


@dataclass(frozen=True)
class RestoreWork(Command):
    """Bring a mothballed work back and open its doors again. Answers (did it, the reply)."""
    node_id: str


@dataclass(frozen=True)
class Exclude(Command):
    """Put an entry (a node id, `category:<category>` or `trait:<trait>`) on the acting seat's exclusion list: the automatic
    starters leave it out."""
    entry: str


@dataclass(frozen=True)
class Include(Command):
    """Take an entry off the exclusion list; `entry` None empties the list. Answers whether the entry was on it (True for an
    emptied list)."""
    entry: Optional[str] = None


@dataclass(frozen=True)
class KeepStaffed(Command):
    """Flag a concern to be hired for each year before the closure rule (`kept`), or take the flag off."""
    node_id: str
    kept: bool = True
