"""What the module remembers for one seat between calls. None of it is saved: each is a table that holds while what it was
worked out from is unchanged, or the demand the last throttle saw."""
from typing import Any, Optional, Tuple


class Readings:
    def __init__(self) -> None:
        self.annual: Optional[Tuple[Any, Any]] = None          # (project versions, the year's demand) for the unchanged projects
        self.held: Any = None                                  # the demand the last throttle saw (the object, not a copy)
        self.by_tag: Optional[Tuple[Any, Any]] = None          # (demand it groups, the grouping)
        self.by_commodity: Optional[Tuple[Any, Any]] = None    # (demand it groups, the grouping by commodity)
        self.throttle_sig: Any = None                          # what the last throttle reading was worked out from
        self.throttle_cache: Optional[Tuple[float, Optional[str]]] = None   # and what it answered
