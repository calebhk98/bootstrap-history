"""The state the projects module owns: one seat's standing choices about its works and what the staffing rule has done.

The projects in hand, what is done and what is running stay in the engine's record (`state.projects`), which the
screens, hazards, the credit freeze and ventures still write; they move with those writers."""
import collections
from dataclasses import dataclass, field
from typing import DefaultDict, Dict, List, Optional, Set


@dataclass
class ProjectsSeat:
	# node ids, `category:<cat>` and `trait:<trait>` the automatic starters (rush, auto_open, auto_commission) skip
	excluded: Set[str] = field(default_factory=set)
	# concerns whose staff the yearly step hires for before the closure rule (`keep <id> staffed`)
	keep_staffed: Set[str] = field(default_factory=set)
	# every work ever shut for want of staff; kept after it reopens
	ever_closed_for_staff: Set[str] = field(default_factory=set)
	# this year's staffing closures and reopenings: year, closed, reopened, short (resource -> amount)
	staffing_tally: Dict[str, object] = field(default_factory=dict)
	# concern id -> the year auto-open last said why it stayed shut (so it says it once in a while, not every year)
	said_autoopen: Optional[Dict[str, int]] = None
	# node id -> how many times the seat's attempt at it has failed (a read of an unseen node adds a zero)
	failed_attempts: DefaultDict[str, int] = field(default_factory=lambda: collections.defaultdict(int))
	# the projects in hand that a posted bounty pays someone else to do
	bountied: Set[str] = field(default_factory=set)
	# node id -> the money already paid into a project that was stopped, which comes off its bill if it begins again
	paid_towards: Dict[str, float] = field(default_factory=dict)
	# how many bounties the seat has posted
	bounties_paid: int = 0


@dataclass
class ProjectsWorld:
	# every node id in the order the household's hours serve projects (a started project goes first); opened from the tree's
	# order when a game is made, one order for every seat
	order: List[str] = field(default_factory=list)
