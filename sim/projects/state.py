"""The state the projects module owns: one seat's standing choices about its works and what the staffing rule has done.

The projects in hand, what is done and what is running stay in the engine's record (`state.projects`), which the
screens, hazards, the credit freeze and ventures still write; they move with those writers."""
from dataclasses import dataclass, field
from typing import Dict, Optional, Set


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
